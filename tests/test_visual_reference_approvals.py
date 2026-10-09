"""Migration 30: the founder-attested visual reference (plate) approval gate."""

from __future__ import annotations

import sqlite3
from hashlib import sha256
from pathlib import Path

import pytest

from project_atlas import visual_reference_approvals
from project_atlas.generation import LocalAssetStorage
from project_atlas.persistence import AtlasRepository
from project_atlas.visual_authorities import CANONICAL_REFERENCES
from project_atlas.visual_reference_approvals import HISTORICAL_ALLOWLIST
from tests.reference_approvals import CRITERIA

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCENE = "scene-isa-deadline-video-v1-01"
GLOBAL = "visual-reference-authority-gate-global"


def _image(repository: AtlasRepository, root: Path, key: str, content: bytes | None = None) -> str:
    spec = repository.create_asset_spec(
        f"asset-spec-gate-{key}", SCENE, "environment", "Gate test.", "Gate test.", "Import."
    )
    content = content or b"\x89PNG\r\n\x1a\n" + key.encode()
    storage = LocalAssetStorage(root)
    asset_id = f"asset-gate-{key}"
    stored = storage.write(spec.id, asset_id, content, "image/png")
    repository.create_asset(
        asset_id,
        spec.id,
        1,
        storage.relative_path(stored),
        "image/png",
        "imported",
        content_digest=sha256(content).hexdigest(),
    )
    return asset_id


def _decide(repository, asset_id, decision, sheet=None, number=None):
    history = repository.list_plate_approvals(asset_id)
    return repository.record_visual_plate_decision(
        f"decision-{asset_id}-{number or len(history) + 1}",
        asset_id,
        decision,
        "founder",
        "founder message 2026-10-09 13:00",
        contact_sheet_asset_id=sheet if decision == "approved" else None,
        criteria=dict(CRITERIA) if decision == "approved" else {},
    )


@pytest.fixture
def repository(tmp_path):
    repo = AtlasRepository(tmp_path / "gate.db", tmp_path / "assets")
    yield repo
    repo.close()


def test_decisions_are_founder_attested_sequential_and_immutable(repository, tmp_path) -> None:
    plate = _image(repository, tmp_path / "assets", "plate")
    sheet = _image(repository, tmp_path / "assets", "sheet")
    first = repository.record_visual_plate_decision(
        "desk-r3-approval",
        plate,
        "approved",
        "founder",
        "founder message 2026-10-09 13:00",
        contact_sheet_asset_id=sheet,
        criteria=dict(CRITERIA),
        exceptions=[{"element": "calendar", "note": "P11 study element; stays blank"}],
        notes="Agent review findings are evidence only.",
    )
    assert (first.sequence, first.decision, first.attestation) == (
        1,
        "approved",
        "founder-attested",
    )
    assert first.plate_sha256 == repository.get_asset(plate).content_digest
    assert first.contact_sheet_sha256 == repository.get_asset(sheet).content_digest
    assert first.exceptions[0]["element"] == "calendar" and len(first.record_digest) == 64
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        repository.connection.execute(
            "UPDATE visual_plate_approvals SET decision='rejected' WHERE id=?", (first.id,)
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        repository.connection.execute("DELETE FROM visual_plate_approvals WHERE id=?", (first.id,))
    row = repository.connection.execute(
        "SELECT * FROM visual_plate_approvals WHERE id=?", (first.id,)
    ).fetchone()
    for column, value, match in (
        ("plate_sha256", "0" * 64, "plate digest"),
        ("contact_sheet_sha256", "0" * 64, "contact sheet digest"),
        ("sequence", 3, "sequential"),
    ):
        values = dict(row) | {"id": f"forged-{column}", column: value}
        if column != "sequence":
            values["sequence"] = 2
        with pytest.raises(sqlite3.IntegrityError, match=match):
            repository.connection.execute(
                f"INSERT INTO visual_plate_approvals ({', '.join(values)}) "
                f"VALUES ({', '.join('?' for _ in values)})",
                tuple(values.values()),
            )
    with pytest.raises(ValueError, match="contact sheet and criteria"):
        repository.record_visual_plate_decision(
            "no-sheet", plate, "approved", "founder", "ref", criteria=dict(CRITERIA)
        )
    with pytest.raises(ValueError, match="PASS or FAIL"):
        repository.record_visual_plate_decision(
            "bad-criteria",
            plate,
            "approved",
            "founder",
            "ref",
            contact_sheet_asset_id=sheet,
            criteria={"linework": "OK"},
        )
    with pytest.raises(ValueError, match="decision reference"):
        repository.record_visual_plate_decision("no-ref", plate, "withdrawn", "founder", " ")


def test_the_latest_decision_governs_eligibility(repository, tmp_path) -> None:
    plate = _image(repository, tmp_path / "assets", "history")
    assert repository.reference_image_eligibility(plate)["basis"] == "no_eligible_approval"
    _decide(repository, plate, "approved", sheet=plate)
    assert repository.reference_image_eligibility(plate)["eligible"] is True
    _decide(repository, plate, "withdrawn")
    assert repository.reference_image_eligibility(plate) | {} == {
        "asset_id": plate,
        "eligible": False,
        "basis": "founder_decision",
        "decision_id": f"decision-{plate}-2",
        "decision": "withdrawn",
    }
    _decide(repository, plate, "approved", sheet=plate)
    assert repository.reference_image_eligibility(plate)["eligible"] is True
    _decide(repository, plate, "rejected")
    assert repository.reference_image_eligibility(plate)["eligible"] is False
    assert [item.decision for item in repository.list_plate_approvals(plate)] == [
        "approved",
        "withdrawn",
        "approved",
        "rejected",
    ]
    assert [item.sequence for item in repository.list_plate_approvals()] == [1, 2, 3, 4]


@pytest.mark.parametrize(
    "role",
    ["global_illustration_style", "environment_family", "composition_depth", "special_break_frame"],
)
def test_authority_creation_of_every_role_refuses_unapproved_members(
    repository, tmp_path, role
) -> None:
    style = _image(repository, tmp_path / "assets", "global-style")
    _decide(repository, style, "approved", sheet=style)
    repository.create_visual_reference_authority(
        GLOBAL, "gate-global", "global_illustration_style", "Global", "Style.", [(style, "style")]
    )
    member = _image(repository, tmp_path / "assets", f"member-{role}")
    parent = None if role == "global_illustration_style" else GLOBAL
    metadata = {"environment_family": "gate-room"} if role == "environment_family" else None

    def create(suffix: str):
        return repository.create_visual_reference_authority(
            f"authority-{role}-{suffix}",
            f"gate-{role}-{suffix}",
            role,
            "Gate",
            "Guidance.",
            [(member, "member")],
            parent_authority_id=parent,
            metadata=metadata,
        )

    with pytest.raises(ValueError, match="without an eligible founder approval"):
        create("unapproved")
    _decide(repository, member, "approved", sheet=member)
    assert create("approved").role == role
    _decide(repository, member, "withdrawn")
    with pytest.raises(ValueError, match=r"withdrawn"):
        create("withdrawn")


def test_historical_allowlist_is_exact_and_only_a_fallback(repository, tmp_path) -> None:
    # Every canonical repository reference is allowlisted with its exact hash.
    for reference in CANONICAL_REFERENCES:
        assert HISTORICAL_ALLOWLIST[reference.asset_id] == reference.content_digest
    assert {
        "asset-production-8-office-anchor-v1",
        "asset-production-8-storeroom-anchor-v1",
        "asset-4b30cc2631964e3ea9ea87985ba434fc",
        "asset-3888589e5e684985949ff716f6fbe5c6",
    } <= set(HISTORICAL_ALLOWLIST)
    assert len(HISTORICAL_ALLOWLIST) == 11
    # The real canonical global style bytes, imported under their canonical ID, are eligible.
    reference = next(item for item in CANONICAL_REFERENCES if item.key == "default-scene-language")
    content = (REPOSITORY_ROOT / reference.repository_path).read_bytes()
    storage = LocalAssetStorage(tmp_path / "assets")
    spec = repository.create_asset_spec(
        reference.asset_spec_id, SCENE, "environment", "Canonical.", "Canonical.", "Import."
    )
    stored = storage.write(spec.id, reference.asset_id, content, "image/png")
    repository.create_asset(
        reference.asset_id,
        spec.id,
        1,
        storage.relative_path(stored),
        "image/png",
        "imported",
        content_digest=sha256(content).hexdigest(),
    )
    assert repository.reference_image_eligibility(reference.asset_id)["basis"] == (
        "historical_allowlist"
    )
    repository.create_visual_reference_authority(
        GLOBAL,
        "gate-global",
        "global_illustration_style",
        "Global",
        "Style.",
        [(reference.asset_id, "primary_style")],
    )
    # An allowlisted ID with different bytes is not eligible.
    forged = _image(repository, tmp_path / "assets", "forged")
    assert repository.reference_image_eligibility(forged)["eligible"] is False
    # Once a decision exists, it governs: a withdrawn allowlisted image is refused.
    _decide(repository, reference.asset_id, "withdrawn")
    eligibility = repository.reference_image_eligibility(reference.asset_id)
    assert (eligibility["eligible"], eligibility["basis"]) == (False, "founder_decision")
    with pytest.raises(ValueError, match="withdrawn"):
        repository.create_visual_reference_authority(
            "authority-after-withdrawal",
            "gate-after",
            "global_illustration_style",
            "Global",
            "Style.",
            [(reference.asset_id, "primary_style")],
        )


def test_allowlist_fallback_applies_only_without_any_decision(
    repository, tmp_path, monkeypatch
) -> None:
    image = _image(repository, tmp_path / "assets", "anchor")
    monkeypatch.setitem(
        visual_reference_approvals.HISTORICAL_ALLOWLIST,
        image,
        repository.get_asset(image).content_digest,
    )
    assert repository.reference_image_eligibility(image)["basis"] == "historical_allowlist"
    _decide(repository, image, "rejected")
    assert repository.reference_image_eligibility(image)["eligible"] is False
