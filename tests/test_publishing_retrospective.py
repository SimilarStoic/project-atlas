"""Founder-attested retrospective publications (migration 29 and the one-time P8/P9 recorder).

Every test uses a disposable database and synthetic artifact bytes; nothing reaches a network.
"""

from __future__ import annotations

import json
import socket
import sqlite3
import urllib.request
from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
from pathlib import Path

import pytest

from project_atlas import persistence
from project_atlas.media import LocalMediaStorage
from project_atlas.persistence import MIGRATIONS, AtlasRepository
from project_atlas.publishing import PublishingService
from project_atlas.publishing_retrospective import (
    P8_DESCRIPTION,
    P8_TITLE,
    PILOT_KEY,
    RetrospectiveRecordError,
    _record_all,
    _rows,
    main,
    p8_release,
    p9_release,
    record_release,
    verified_backup,
    verify_preconditions,
)
from project_atlas.publishing_schema import MIGRATION_29
from project_atlas.publishing_state import TARGET_CHANNEL
from tests.test_publishing import (
    LONDON_MINUTE,
    NOW,
    REVIEW_NOW,
    FakePublishingAdapter,
    _artifact,
    _manifest,
    _never_release,
    _public,
)

PUBLISHING_TABLES = (
    "publishing_packages",
    "publication_gate_decisions",
    "publication_operations",
    "publication_operation_events",
    "platform_publications",
    "publication_status_snapshots",
    "publication_receipts",
)
P9_FIXTURE = Path(__file__).parent / "fixtures" / "p9_publish_metadata.json"


def _rows_of(connection, table: str) -> list[tuple]:
    return [tuple(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY id")]


def _snapshot(connection) -> dict[str, list[tuple]]:
    return {table: _rows_of(connection, table) for table in PUBLISHING_TABLES}


def _p9_publish_dir(tmp_path: Path) -> Path:
    folder = tmp_path / "p9-publish"
    folder.mkdir(exist_ok=True)
    for name, text in json.loads(P9_FIXTURE.read_text(encoding="utf-8"))["files"].items():
        (folder / name).write_bytes(text.encode("utf-8"))
    return folder


def _chain(repo, storage, prefix: str, artifact_id: str, content: bytes, number: int) -> None:
    """A complete synthetic FK chain ending in one final-media artifact."""

    opportunity = repo.connection.execute("SELECT id FROM opportunities LIMIT 1").fetchone()[0]
    path, media_digest = storage.write("final", artifact_id, content, "video/mp4")
    connection = repo.connection
    with connection:
        connection.execute(
            "INSERT INTO research_packs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (f"{prefix}-research", opportunity, number, "test", None, "{}", NOW, NOW, None),
        )
        connection.execute(
            "INSERT INTO editorial_angles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"{prefix}-angle",
                opportunity,
                f"{prefix}-research",
                "t",
                "t",
                "t",
                "t",
                "[]",
                "{}",
                NOW,
                NOW,
                None,
            ),
        )
        connection.execute(
            "INSERT INTO content_pieces VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (f"{prefix}-piece", opportunity, f"{prefix}-angle", "video", "t", "{}", NOW, NOW),
        )
        connection.execute(
            "INSERT INTO scripts VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"{prefix}-script", f"{prefix}-piece", number, "t", "{}", NOW, NOW),
        )
        connection.execute(
            "INSERT INTO visual_plans VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"{prefix}-plan", f"{prefix}-piece", f"{prefix}-script", "t", "{}", NOW, NOW),
        )
        connection.execute(
            "INSERT INTO narration_assets VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"{prefix}-narration",
                f"{prefix}-script",
                "n.wav",
                "audio/wav",
                "imported",
                "a" * 64,
                1000,
                NOW,
            ),
        )
        connection.execute(
            "INSERT INTO final_media_input_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"{prefix}-input",
                f"{prefix}-plan",
                f"{prefix}-script",
                f"{prefix}-narration",
                "test-v1",
                "[]",
                "[]",
                "{}",
                NOW,
            ),
        )
        connection.execute(
            "INSERT INTO render_executions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"{prefix}-render",
                f"{prefix}-input",
                "t",
                "v1",
                "v1",
                "succeeded",
                None,
                None,
                "{}",
                NOW,
            ),
        )
        connection.execute(
            "INSERT INTO final_media_artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                artifact_id,
                f"{prefix}-render",
                path,
                "video/mp4",
                media_digest,
                1000,
                1080,
                1920,
                "{}",
                NOW,
            ),
        )


def _production(repo, run_id: str, plan_id: str, artifact_id: str, *, accepted: bool = True):
    connection = repo.connection
    with connection:
        connection.execute(
            "INSERT INTO production_runs VALUES (?, ?, '{}', ?, ?)",
            (run_id, plan_id, "a" * 64, NOW),
        )
        statuses = ["created", "founder_accepted" if accepted else "qa_review_pending"]
        for sequence, status in enumerate(statuses, 1):
            connection.execute(
                "INSERT INTO production_run_events VALUES "
                "(?, ?, ?, ?, 'test', '{}', NULL, NULL, ?)",
                (f"{run_id}:event:{sequence}", run_id, sequence, status, NOW),
            )
        connection.execute(
            "INSERT INTO production_run_evidence (id, production_run_id, evidence_type, "
            "final_media_artifact_id, payload_json, payload_digest, created_at) "
            "VALUES (?, ?, 'render', ?, '{}', ?, ?)",
            (f"{run_id}:render:evidence:1", run_id, artifact_id, "b" * 64, NOW),
        )
        connection.execute(
            "INSERT INTO production_qa_reviews VALUES (?, ?, 'whole_video', 'passed', 'human', "
            "'{}', '{}', ?, ?)",
            (f"{run_id}:qa:whole-video:1", run_id, artifact_id, NOW),
        )
        if accepted:
            connection.execute(
                "INSERT INTO production_founder_reviews VALUES (?, ?, 'accepted', 'founder', "
                "'test', '', ?)",
                (f"{run_id}:founder-review:1", run_id, NOW),
            )


@pytest.fixture
def world(tmp_path):
    """P8 and P9 founder-accepted runs (synthetic bytes) plus the P9 never-release audit copy."""

    repo = AtlasRepository(tmp_path / "retrospective.sqlite")
    storage = LocalMediaStorage(tmp_path / "media")
    _artifact(repo, storage)
    contents = {}
    for number, (prefix, run_id, artifact_id) in enumerate(
        (
            ("p8", "production-8-attempt-2", "production-8-attempt-2-artifact-2"),
            ("p9", "production-9-attempt-2", "production-9-attempt-2-artifact-3"),
        ),
        700,
    ):
        content = f"synthetic {prefix} final mp4".encode()
        _chain(repo, storage, prefix, artifact_id, content, number)
        _production(repo, run_id, f"{prefix}-plan", artifact_id)
        contents[prefix] = sha256(content).hexdigest()
    fake = FakePublishingAdapter()
    service = PublishingService(repo, storage, fake, lambda: REVIEW_NOW)
    audit = service.prepare_package(
        "audit-package",
        "similarstoic-youtube-controlled-pilot-v1",
        2,
        1,
        "production-9-attempt-2-artifact-3",
        _never_release(),
    )
    service.approve_package("audit-approval", audit.id, "founder")
    upload = service.reserve_upload(audit.id)
    service.begin_api_upload(upload.id)
    p8 = replace(p8_release(), artifact_sha256=contents["p8"])
    p9 = replace(p9_release(_p9_publish_dir(tmp_path)), artifact_sha256=contents["p9"])
    yield repo, storage, service, fake, p8, p9, tmp_path
    repo.close()


def _media(tmp_path: Path) -> Path:
    return tmp_path / "media"


# --- Migration 29 ------------------------------------------------------------------------------


def test_fresh_schema_is_contiguous_1_to_29_with_intact_references(tmp_path) -> None:
    assert [version for version, _ in MIGRATIONS] == list(range(1, 30))
    repo = AtlasRepository(tmp_path / "fresh.sqlite")
    try:
        connection = repo.connection
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 29
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        sql = dict(connection.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table'"))
        assert not [name for name in sql if name.endswith("_v28")]
        assert (
            "REFERENCES publication_gate_decisions(id, package_id)" in sql["publication_operations"]
        )
        assert "REFERENCES publication_receipts(id)" in sql["performance_snapshots"]
        assert "public_status_id TEXT NULL UNIQUE" in sql["publication_receipts"]
    finally:
        repo.close()


def test_upgrade_28_to_29_preserves_every_publishing_row(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:28])
    path = tmp_path / "upgrade.sqlite"
    repo = AtlasRepository(path)
    storage = LocalMediaStorage(tmp_path / "media")
    _artifact(repo, storage)
    fake = FakePublishingAdapter()
    service = PublishingService(repo, storage, fake, lambda: REVIEW_NOW)
    _public(service, fake, "manual", "manual")  # An ordinary observed public receipt.
    service.repository.record_publication_gate_decision(
        "revoke-1",
        "package-1",
        repo.get_publishing_package("package-1").package_digest,
        "founder",
        "revoke",
        "manual",
        "manual",
        _manifest("manual", "manual")["publication_timing"],
    )
    before = _snapshot(repo.connection)
    assert repo.connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 28
    assert before["publication_receipts"] and before["publication_gate_decisions"]
    repo.close()
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS)
    upgraded = AtlasRepository(path)
    try:
        connection = upgraded.connection
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 29
        assert _snapshot(connection) == before
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        # Immutability survives the rebuild.
        for statement in (
            "UPDATE publication_gate_decisions SET comment = 'x'",
            "DELETE FROM publication_receipts",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                connection.execute(statement)
    finally:
        upgraded.close()


def test_failed_migration_29_is_atomic_and_leaves_28_intact(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:28])
    path = tmp_path / "atomic.sqlite"
    repo = AtlasRepository(path)
    schema_before = sorted(
        tuple(r) for r in repo.connection.execute("SELECT type, name, sql FROM sqlite_master")
    )
    data_before = _snapshot(repo.connection)
    broken = MIGRATIONS[:28] + ((29, MIGRATION_29[1] + ("INVALID SQL",)),)
    with pytest.raises(sqlite3.DatabaseError):
        repo.apply_migrations(broken)
    connection = repo.connection
    assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 28
    assert (
        sorted(tuple(r) for r in connection.execute("SELECT type, name, sql FROM sqlite_master"))
        == schema_before
    )
    assert _snapshot(connection) == data_before
    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    repo.close()


# --- Authority -----------------------------------------------------------------------------------


def test_attest_external_is_never_ordinary_publish_authority(world) -> None:
    repo, storage, service, fake, p8, _p9, tmp_path = world
    record_release(repo, _media(tmp_path), p8)
    package = repo.get_publishing_package(f"publishing-package-{PILOT_KEY}-slot-1-v1")
    assert repo.effective_publication_approval(package.id) is None
    with pytest.raises(ValueError, match="allowed outcome"):
        repo.record_publication_gate_decision(
            "x",
            package.id,
            package.package_digest,
            "founder",
            "attest_external",
            None,
            None,
            package.manifest["publication_timing"],
        )
    # A retrospective package can never be approved, even directly in SQL.
    with pytest.raises(sqlite3.IntegrityError, match="retrospective"):
        repo.connection.execute(
            "INSERT INTO publication_gate_decisions VALUES (?, ?, ?, 2, 'approve', 'f', "
            "'manual', 'manual', '{}', NULL, ?)",
            ("approve-retro", package.id, package.package_digest, NOW),
        )
    repo.connection.rollback()
    publication = repo.connection.execute(
        "SELECT id FROM platform_publications WHERE package_id = ?", (package.id,)
    ).fetchone()["id"]
    release = repo.connection.execute(
        "SELECT id FROM publication_operations WHERE package_id = ? AND action_kind = 'release'",
        (package.id,),
    ).fetchone()["id"]
    calls_before = len(fake.calls)
    for action in (
        lambda: service.reserve_upload(package.id),
        lambda: service.observe_status("retro-status", publication),
        lambda: service.reserve_release(publication),
        lambda: service.reconcile_public_receipt("r", "s", publication, release, "founder"),
    ):
        with pytest.raises(ValueError):
            action()
    # Refused before any adapter (provider) access.
    assert len(fake.calls) == calls_before
    # The ordinary path cannot create a retrospective package either.
    manifest = {**_manifest("manual", "manual"), "release_policy": "retrospective_external"}
    with pytest.raises(ValueError, match="recorder"):
        service.prepare_package("sneak", "x", 1, 1, "fake-artifact", manifest)


def test_ordinary_receipts_still_need_verified_public_status(tmp_path) -> None:
    repo = AtlasRepository(tmp_path / "ordinary.sqlite")
    storage = LocalMediaStorage(tmp_path / "media")
    _artifact(repo, storage)
    fake = FakePublishingAdapter()
    service = PublishingService(repo, storage, fake, lambda: REVIEW_NOW)
    package, _u, publication, _priv, operation, receipt = _public(service, fake, "manual", "manual")
    assert receipt.public_status_id is not None
    connection = repo.connection
    base = (
        "INSERT INTO publication_receipts VALUES (?, ?, ?, ?, ?, ?, 'manual', ?, '2099-W01', "
        "'2026-01-01T00:00:00+00:00', ?, 'second', NULL, ?, ?, NULL)"
    )
    # No status under an ordinary approval: refused.
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            base,
            (
                "bad-1",
                "pub-x",
                package.id,
                operation.gate_decision_id,
                "op-x",
                None,
                TARGET_CHANNEL,
                "founder-attestation",
                "c" * 64,
                NOW,
            ),
        )
    connection.rollback()
    # A founder-attestation source can never ride on an observed status.
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            base,
            (
                "bad-2",
                publication.id,
                package.id,
                operation.gate_decision_id,
                operation.id,
                receipt.public_status_id,
                TARGET_CHANNEL,
                "founder-attestation",
                "c" * 64,
                NOW,
            ),
        )
    connection.rollback()
    repo.close()


# --- Recording -----------------------------------------------------------------------------------


def test_p8_and_p9_record_exactly_the_attested_rows(world) -> None:
    repo, _storage, _service, _fake, p8, p9, tmp_path = world
    first = record_release(repo, _media(tmp_path), p8)
    second = record_release(repo, _media(tmp_path), p9)
    assert (first["written"], second["written"]) == (8, 8)
    connection = repo.connection
    for release, slot, week, public_at, precision in (
        (p8, 1, "2026-W40", "2026-10-04T13:57:41+01:00", "second"),
        (p9, 2, "2026-W41", "2026-10-05", "day"),
    ):
        package = repo.get_publishing_package(f"publishing-package-{PILOT_KEY}-slot-{slot}-v1")
        assert (package.pilot_key, package.pilot_slot, package.version) == (PILOT_KEY, slot, 1)
        assert package.pilot_week == week and package.channel_id == TARGET_CHANNEL
        assert package.final_media_artifact_id == release.artifact_id
        assert package.artifact_digest == release.artifact_sha256
        manifest = package.manifest
        assert manifest["release_policy"] == "retrospective_external"
        assert (manifest["title"], manifest["description"]) == (release.title, release.description)
        assert manifest["remote_id"] == release.remote_id
        assert manifest["founder_review_id"] == f"{release.production_run_id}:founder-review:1"
        [decision] = connection.execute(
            "SELECT * FROM publication_gate_decisions WHERE package_id = ?", (package.id,)
        ).fetchall()
        assert (decision["decision"], decision["transfer_route"], decision["release_route"]) == (
            "attest_external",
            None,
            None,
        )
        operations = connection.execute(
            "SELECT * FROM publication_operations WHERE package_id = ? ORDER BY action_kind",
            (package.id,),
        ).fetchall()
        assert [(o["action_kind"], o["execution_mode"]) for o in operations] == [
            ("release", "manual"),
            ("upload", "manual"),
        ]
        for operation in operations:
            events = repo.get_publication_operation_events(operation["id"])
            assert [(e.sequence, e.kind, e.actor) for e in events] == [(1, "succeeded", "founder")]
            assert events[0].evidence["conveyor_dispatched"] is False
            assert repo.get_publication_operation(operation["id"]).outcome == "succeeded"
        [publication] = connection.execute(
            "SELECT * FROM platform_publications WHERE package_id = ?", (package.id,)
        ).fetchall()
        assert (publication["remote_id"], publication["identity_source"]) == (
            release.remote_id,
            "founder_manual",
        )
        [receipt] = connection.execute(
            "SELECT * FROM publication_receipts WHERE package_id = ?", (package.id,)
        ).fetchall()
        assert receipt["public_status_id"] is None
        assert (receipt["public_at"], receipt["timestamp_precision"]) == (public_at, precision)
        assert receipt["timestamp_source"] == "founder-attestation"
        assert receipt["first_public_observed_at"] is None and receipt["pilot_week"] == week
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    # The frozen P8 founder text and P9 preserved files are stored exactly.
    assert p8.title == P8_TITLE and p8.description == P8_DESCRIPTION
    assert "2026–27" in P8_DESCRIPTION and P8_DESCRIPTION.endswith("#pensions")
    assert p9.title == "Buy now, pay later just got grown-up rules (UK)"
    assert p9.description.endswith("#Shorts") and not p9.description.endswith("\n")


def test_recorded_weeks_block_any_pilot_key_on_the_channel(world) -> None:
    repo, _storage, service, _fake, p8, p9, tmp_path = world
    record_release(repo, _media(tmp_path), p8)
    record_release(repo, _media(tmp_path), p9)

    def window(day: str) -> dict:
        start = LONDON_MINUTE.replace(year=2026, month=10, day=int(day), hour=12, minute=0)
        return {
            "timezone": "Europe/London",
            "mode": "window",
            "start": start.isoformat(),
            "end": (start + timedelta(hours=1)).isoformat(),
        }

    for index, (day, blocked) in enumerate((("4", True), ("7", True), ("12", False))):
        manifest = {
            **_manifest("manual", "manual"),
            "publication_timing": window(day),
            "pilot_slot": 3,
        }
        package = service.prepare_package(
            f"other-{index}",
            "similarstoic-youtube-controlled-pilot-v1",
            3,
            index + 1,
            "fake-artifact",
            manifest,
            f"other-{index - 1}" if index else None,
        )
        conflict = repo.release_week_conflict(package)
        assert (conflict is not None) is blocked, (day, package.pilot_week, conflict)


def test_a_second_release_in_an_occupied_week_is_refused(world) -> None:
    repo, _storage, _service, _fake, p8, _p9, tmp_path = world
    record_release(repo, _media(tmp_path), p8)
    before = _snapshot(repo.connection)
    clash = replace(p8, label="P8-clash", pilot_slot=3, remote_id="another-video")
    with pytest.raises(RetrospectiveRecordError, match="already occupied"):
        record_release(repo, _media(tmp_path), clash)
    assert _snapshot(repo.connection) == before


# --- Refusals ------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", ["sha", "bytes", "not-current", "not-accepted", "qa-elsewhere"])
def test_preconditions_fail_closed_without_writing(world, case) -> None:
    repo, storage, _service, _fake, p8, _p9, tmp_path = world
    connection = repo.connection
    release = p8
    if case == "sha":
        release = replace(p8, artifact_sha256="0" * 64)
    elif case == "bytes":
        path = connection.execute(
            "SELECT storage_path FROM final_media_artifacts WHERE id = ?", (p8.artifact_id,)
        ).fetchone()[0]
        (_media(tmp_path) / path).write_bytes(b"tampered")
    elif case == "not-current":
        with connection:
            connection.execute(
                "INSERT INTO production_run_evidence (id, production_run_id, evidence_type, "
                "final_media_artifact_id, payload_json, payload_digest, created_at) "
                "VALUES (?, ?, 'render', 'fake-artifact', '{}', ?, ?)",
                (f"{p8.production_run_id}:render:evidence:2", p8.production_run_id, "b" * 64, NOW),
            )
    elif case == "not-accepted":
        _chain(repo, storage, "p8x", "p8x-artifact", b"p8x", 990)
        _production(repo, "p8x-run", "p8x-plan", "p8x-artifact", accepted=False)
        release = replace(
            p8,
            production_run_id="p8x-run",
            artifact_id="p8x-artifact",
            artifact_sha256=sha256(b"p8x").hexdigest(),
        )
    elif case == "qa-elsewhere":
        with connection:
            connection.execute(
                "INSERT INTO production_qa_reviews VALUES (?, ?, 'whole_video', 'passed', "
                "'human', '{}', '{}', 'fake-artifact', '9999-12-31T00:00:00+00:00')",
                (f"{p8.production_run_id}:qa:whole-video:2", p8.production_run_id),
            )
    before = _snapshot(connection)
    with pytest.raises(RetrospectiveRecordError):
        record_release(repo, _media(tmp_path), release)
    assert _snapshot(connection) == before


def test_p9_metadata_must_match_its_recorded_sha256(tmp_path) -> None:
    folder = _p9_publish_dir(tmp_path)
    (folder / "title.txt").write_bytes(b"Buy now, pay later just got grown-up rules\n")
    with pytest.raises(RetrospectiveRecordError, match="title.txt"):
        p9_release(folder)


# --- Isolation and durability --------------------------------------------------------------------


def test_audit_rows_untouched_and_attested_rows_survive_purge(world) -> None:
    repo, _storage, _service, _fake, p8, p9, tmp_path = world
    connection = repo.connection

    def audit_rows():
        return {
            table: [
                tuple(row)
                for row in connection.execute(
                    f"SELECT * FROM {table} WHERE id LIKE 'audit%' OR id IN (SELECT id FROM "
                    "publication_operations WHERE package_id = 'audit-package') ORDER BY id"
                )
            ]
            for table in (
                "publishing_packages",
                "publication_gate_decisions",
                "publication_operations",
            )
        }

    audit_before = audit_rows()
    record_release(repo, _media(tmp_path), p8)
    record_release(repo, _media(tmp_path), p9)
    assert audit_rows() == audit_before
    receipts_before = _rows_of(connection, "publication_receipts")
    repo.purge_all_youtube_api_data()
    assert _rows_of(connection, "publication_receipts") == receipts_before
    attested = connection.execute(
        "SELECT remote_id, provider_purged_at FROM platform_publications "
        "WHERE identity_source = 'founder_manual' ORDER BY remote_id"
    ).fetchall()
    assert [tuple(row) for row in attested] == [("Dd76ERbxg_w", None), ("MbVZPnX_b_s", None)]
    # The audit copy's API identity is still purged normally.
    audit = connection.execute(
        "SELECT remote_id, provider_purged_at FROM platform_publications "
        "WHERE package_id = 'audit-package'"
    ).fetchone()
    assert audit["remote_id"] is None and audit["provider_purged_at"] is not None
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        connection.execute(
            "UPDATE publication_receipts SET public_at = NULL, receipt_digest = NULL, "
            "provider_purged_at = 'x' WHERE public_status_id IS NULL"
        )


def test_exact_rerun_is_a_no_op_and_partial_state_fails_closed(world) -> None:
    repo, _storage, _service, _fake, p8, p9, tmp_path = world
    record_release(repo, _media(tmp_path), p8)
    before = _snapshot(repo.connection)
    again = record_release(repo, _media(tmp_path), p8)
    assert again == {"release": "P8", "written": 0, "state": "already recorded"}
    assert _snapshot(repo.connection) == before
    # A different actor is a conflicting fact, not a rerun.
    with pytest.raises(RetrospectiveRecordError, match="conflicts"):
        record_release(repo, _media(tmp_path), p8, founder_actor="someone-else")
    # Partial state: only P9's package exists.
    lineage = verify_preconditions(repo, _media(tmp_path), p9)
    [(package_id, values)] = _rows(p9, lineage, "founder")["publishing_packages"].items()
    columns = ", ".join(["id", *values, "created_at"])
    marks = ", ".join("?" for _ in range(len(values) + 2))
    with repo.connection:
        repo.connection.execute(
            f"INSERT INTO publishing_packages ({columns}) VALUES ({marks})",
            (package_id, *values.values(), NOW),
        )
    with pytest.raises(RetrospectiveRecordError, match="partial"):
        record_release(repo, _media(tmp_path), p9)


def test_a_failure_mid_record_writes_nothing(world) -> None:
    repo, _storage, _service, _fake, p8, _p9, tmp_path = world
    connection = repo.connection
    connection.execute(
        "CREATE TEMP TRIGGER fail_receipt BEFORE INSERT ON publication_receipts "
        "BEGIN SELECT RAISE(ABORT, 'simulated failure'); END"
    )
    before = _snapshot(connection)
    with pytest.raises(sqlite3.IntegrityError, match="simulated"):
        record_release(repo, _media(tmp_path), p8)
    assert _snapshot(connection) == before


def test_recording_reaches_no_network(world, monkeypatch) -> None:
    repo, _storage, _service, _fake, p8, p9, tmp_path = world

    def refuse(*_args, **_kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    record_release(repo, _media(tmp_path), p8)
    record_release(repo, _media(tmp_path), p9)


# --- Live-command safety ------------------------------------------------------------------------


def test_verified_backup_checks_and_refuses_sidecars(tmp_path) -> None:
    repo = AtlasRepository(tmp_path / "live.sqlite")
    repo.close()
    report = verified_backup(tmp_path / "live.sqlite", tmp_path / "backups")
    assert report["integrity"] == "ok" and report["foreign_key_violations"] == 0
    assert report["row_counts_match"] is True and Path(report["backup"]).is_file()
    (tmp_path / "live.sqlite-wal").write_bytes(b"")
    with pytest.raises(RetrospectiveRecordError, match="sidecar"):
        verified_backup(tmp_path / "live.sqlite", tmp_path / "backups")


def test_record_all_on_a_rehearsal_copy_and_dry_run_never_touches_the_source(world, monkeypatch):
    repo, _storage, _service, _fake, p8, p9, tmp_path = world
    database = Path(repo.database_path)
    repo.close()
    source_hash = sha256(database.read_bytes()).hexdigest()
    backup = verified_backup(database, tmp_path / "rehearsal")
    rehearsal = Path(backup["backup"])
    monkeypatch.setattr("project_atlas.publishing_retrospective.p8_release", lambda: p8)
    monkeypatch.setattr("project_atlas.publishing_retrospective.p9_release", lambda _dir: p9)
    results = _record_all(rehearsal, _media(tmp_path), tmp_path, "founder")
    assert [r["written"] for r in results] == [8, 8]
    assert [r["state"] for r in _record_all(rehearsal, _media(tmp_path), tmp_path, "founder")] == [
        "already recorded",
        "already recorded",
    ]
    assert (
        main(
            [
                "record",
                "--db",
                str(database),
                "--media-root",
                str(_media(tmp_path)),
                "--p9-publish-dir",
                str(tmp_path),
                "--dry-run",
            ]
        )
        == 0
    )
    assert sha256(database.read_bytes()).hexdigest() == source_hash
    check = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    assert check.execute("SELECT COUNT(*) FROM publication_receipts").fetchone()[0] == 0
    check.close()


def test_frozen_release_facts_match_the_attested_record(tmp_path) -> None:
    p8, p9 = p8_release(), p9_release(_p9_publish_dir(tmp_path))
    assert (p8.production_run_id, p8.artifact_id, p8.remote_id, p8.expected_week) == (
        "production-8-attempt-2",
        "production-8-attempt-2-artifact-2",
        "MbVZPnX_b_s",
        "2026-W40",
    )
    assert p8.artifact_sha256 == "6f2b248a14002efc1a2e39ba930efb442a5b7a2eb8e293e6924334379a95c000"
    assert p8.timing["public_at"] == "2026-10-04T13:57:41+01:00"
    assert (p9.production_run_id, p9.artifact_id, p9.remote_id, p9.expected_week) == (
        "production-9-attempt-2",
        "production-9-attempt-2-artifact-3",
        "Dd76ERbxg_w",
        "2026-W41",
    )
    assert p9.artifact_sha256 == "4c0a8bb23cff0ba8487f0ca0aa92950d60c100e75b63f463b1f6ea26f6b2132f"
    assert p9.timing == {
        "mode": "retrospective",
        "timezone": "Europe/London",
        "precision": "day",
        "public_date": "2026-10-05",
    }
    assert (p8.pilot_slot, p9.pilot_slot) == (1, 2)
    assert p8.metadata_provenance["metadata_source"] == (
        "founder-pasted from YouTube Studio 2026-10-07"
    )
