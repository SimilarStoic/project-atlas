"""On-demand scheduled publishing (migration 31): the founder-confirmed scheduled videos.insert.

Disposable databases and synthetic bytes only; no provider key, network or YouTube call.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from project_atlas import persistence, publishing_cli
from project_atlas.media import LocalMediaStorage
from project_atlas.persistence import MIGRATIONS, AtlasRepository
from project_atlas.production_backup import database_sha256, table_fingerprint
from project_atlas.publishing import PublishingService, TransferResult
from project_atlas.publishing_credits import SourceCreditError, source_credits
from project_atlas.publishing_schema import MIGRATION_31
from project_atlas.publishing_state import (
    CONFIRMATION_TTL,
    ON_DEMAND_SERIES,
    ON_DEMAND_TIMING,
    ON_DEMAND_WEEK,
    SCHEDULED_TRANSITION_SCHEMA,
    SCHEDULED_UPLOAD_SCHEMA,
    TARGET_CHANNEL,
    publish_at_wire,
    validate_publish_at,
)
from project_atlas.youtube_upload import (
    YouTubeUploadAdapter,
    YouTubeUploadController,
    build_insert_body,
)
from tests.test_publishing import (
    NOW,
    FakePublishingAdapter,
    _artifact,
    _manifest,
    _never_release,
    _public,
)
from tests.test_publishing_retrospective import _chain, _production
from tests.test_youtube_adapter import Provider
from tests.test_youtube_upload import (
    FakeUploadClient,
    governance_for,
    upload_credentials,
)

T0 = datetime(2026, 10, 24, 12, 0, tzinfo=UTC)
PUBLISH_AT = "2026-10-24T18:30+01:00"  # 17:30Z, 5.5 hours after T0.
PUBLISH_AT_WIRE = "2026-10-24T17:30:00Z"
SERIES = ON_DEMAND_SERIES


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def _credits(repo, prefix: str, *, sources=None) -> None:
    """Two approved claims on the production's script, each supported by a cited source."""

    sources = sources or [
        (f"{prefix}-src-a", "Meditations", "Penguin Classics", "Marcus Aurelius", "2006-01-01"),
        (f"{prefix}-src-b", "Letters from a Stoic", "Penguin", None, "1969-05-01"),
    ]
    with repo.connection:
        for number, (source_id, title, publisher, author, date) in enumerate(sources):
            repo.connection.execute(
                "INSERT INTO sources (id, source_type, title, publisher, author, url, "
                "publication_date, accessed_at, created_at, updated_at) "
                "VALUES (?, 'book', ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    source_id,
                    title,
                    publisher,
                    author,
                    f"https://example.org/{source_id}",
                    date,
                    NOW,
                    NOW,
                    NOW,
                ),
            )
            claim_id = f"{prefix}-claim-{number}"
            repo.connection.execute(
                "INSERT INTO claims (id, research_pack_id, text, claim_type, risk_level, "
                "freshness_type, verification_status, verification_notes, created_at, "
                "updated_at) VALUES (?, ?, 'c', 'fact', 'low', 'evergreen', 'verified', '', ?, ?)",
                (claim_id, f"{prefix}-research", NOW, NOW),
            )
            repo.connection.execute(
                "INSERT INTO claim_evidence VALUES (?, ?, 'supports', NULL, '', ?, ?)",
                (claim_id, source_id, NOW, NOW),
            )
        repo.connection.execute(
            "INSERT INTO script_claim_sets VALUES (?, ?, ?)",
            (f"{prefix}-claim-set", f"{prefix}-script", NOW),
        )
        for number in range(len(sources)):
            repo.connection.execute(
                "INSERT INTO script_claim_links VALUES (?, ?, ?)",
                (f"{prefix}-claim-set", f"{prefix}-claim-{number}", NOW),
            )


def _world_rows(repo, storage, prefix: str, number: int, *, credits: bool = True) -> str:
    artifact_id = f"{prefix}-artifact"
    _chain(repo, storage, prefix, artifact_id, f"synthetic {prefix} mp4".encode(), number)
    _production(repo, f"{prefix}-run", f"{prefix}-plan", artifact_id)
    if credits:
        _credits(repo, prefix)
    return artifact_id


@pytest.fixture
def world(tmp_path):
    repo = AtlasRepository(tmp_path / "on-demand.sqlite")
    storage = LocalMediaStorage(tmp_path / "media")
    _artifact(repo, storage)  # The legacy pilot artifact ("fake-artifact").
    artifact = _world_rows(repo, storage, "od", 801)
    clock = Clock(T0)
    fake = FakePublishingAdapter()
    fake.transfer = _scheduled_result()
    service = PublishingService(repo, storage, fake, clock)
    yield repo, storage, fake, service, clock, artifact
    repo.close()


def _scheduled_result(publish_at=PUBLISH_AT_WIRE, privacy="private", remote="od-video-1"):
    return TransferResult(
        "succeeded",
        TARGET_CHANNEL,
        remote,
        evidence={"returned_privacy": privacy, "returned_publish_at": publish_at},
    )


def _od_manifest(repo, run_id: str = "od-run", slot: int = 1, **overrides) -> dict:
    text = source_credits(repo, run_id)["text"]
    manifest = {
        **_manifest(),
        "description": "A synthetic Stoic film.\n\n" + text,
        "publication_timing": dict(ON_DEMAND_TIMING),
        "pilot_slot": slot,
    }
    manifest.update(overrides)
    return manifest


def _approved_od(service, repo, artifact="od-artifact", package_id="od-1", slot=1, run="od-run"):
    package = service.prepare_package(
        package_id, SERIES, slot, 1, artifact, _od_manifest(repo, run, slot)
    )
    service.approve_package(f"{package_id}-approval", package.id, "founder")
    return package


def _confirmed(package, **overrides) -> dict:
    upload = {
        "title": package.manifest["title"],
        "description": package.manifest["description"],
        "privacy": "private",
        "publish_at": PUBLISH_AT,
        "founder_actor": "founder",
        "founder_confirmed": True,
    }
    upload.update(overrides)
    return upload


def _count(repo, table: str) -> int:
    return repo.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _events(repo, operation_id: str) -> list[str]:
    return [event.kind for event in repo.get_publication_operation_events(operation_id)]


# --- publishAt validation -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (None, "required"),
        ("", "required"),
        ("next tuesday", "ISO 8601"),
        ("2026-10-24T18:30", "timezone offset"),
        ("2026-10-24T18:30:15+01:00", "minute precision"),
        ("2026-10-24T12:29+00:00", "at least 30 minutes"),
        ("2026-10-24T11:00Z", "at least 30 minutes"),  # In the past.
        ("2026-11-07T12:01+00:00", "within 14 days"),
    ],
)
def test_publish_at_refuses_naive_imprecise_too_soon_and_too_far(value, message) -> None:
    with pytest.raises(ValueError, match=message):
        validate_publish_at(value, T0)


def test_publish_at_bounds_are_inclusive_and_normalised_to_utc() -> None:
    assert validate_publish_at("2026-10-24T12:30+00:00", T0) == T0 + timedelta(minutes=30)
    assert validate_publish_at("2026-11-07T12:00Z", T0) == T0 + timedelta(days=14)
    moment = validate_publish_at(PUBLISH_AT, T0)
    assert moment.tzinfo == UTC and publish_at_wire(moment) == PUBLISH_AT_WIRE
    with pytest.raises(ValueError, match="timezone-aware"):
        validate_publish_at(PUBLISH_AT, T0.replace(tzinfo=None))


# --- Source credits -----------------------------------------------------------------------------


def test_source_credits_are_projected_from_claim_provenance(world) -> None:
    repo, *_ = world
    credits = source_credits(repo, "od-run")
    assert credits["script_claim_set_id"] == "od-claim-set"
    assert credits["text"].splitlines() == [
        "Sources:",
        '- Marcus Aurelius. "Meditations". Penguin Classics, 2006. https://example.org/od-src-a',
        '- "Letters from a Stoic". Penguin, 1969. https://example.org/od-src-b',
    ]
    assert source_credits(repo, "od-run") == credits  # Deterministic, digest included.


def test_missing_claim_set_fails_closed(tmp_path) -> None:
    repo = AtlasRepository(tmp_path / "x.sqlite")
    storage = LocalMediaStorage(tmp_path / "media")
    try:
        _world_rows(repo, storage, "nc", 802, credits=False)
        with pytest.raises(SourceCreditError, match="no closed claim set"):
            source_credits(repo, "nc-run")
    finally:
        repo.close()


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (("s1", "Title", "", None, "2001-01-01"), "publisher"),
        (("s1", "Title", "Pub", None, None), "publication year"),
        (("s1", "  ", "Pub", None, "2001"), "title"),
        (("s1", "A <b> title", "Pub", None, "2001"), "< or >"),
    ],
)
def test_incomplete_source_attribution_fails_closed(tmp_path, source, message) -> None:
    repo = AtlasRepository(tmp_path / "x.sqlite")
    storage = LocalMediaStorage(tmp_path / "media")
    try:
        _world_rows(repo, storage, "bad", 803, credits=False)
        _credits(repo, "bad", sources=[source])
        with pytest.raises(SourceCreditError, match=message):
            source_credits(repo, "bad-run")
    finally:
        repo.close()


def test_claim_without_supporting_source_fails_closed(world) -> None:
    repo, *_ = world
    with repo.connection:
        repo.connection.execute(
            "UPDATE claim_evidence SET stance = 'contradicts' WHERE claim_id = 'od-claim-1'"
        )
    with pytest.raises(SourceCreditError, match="od-claim-1 has no supporting source"):
        source_credits(repo, "od-run")


# --- Packaging ----------------------------------------------------------------------------------


def test_package_freezes_credits_and_requires_them_in_the_description(world) -> None:
    repo, _storage, _fake, service, _clock, artifact = world
    credits = source_credits(repo, "od-run")
    with pytest.raises(ValueError, match="projected source credits exactly"):
        service.prepare_package(
            "od-1", SERIES, 1, 1, artifact, _od_manifest(repo, description="No sources.")
        )
    forged = {**credits, "text": credits["text"] + "\n- extra"}
    with pytest.raises(ValueError, match="differ from the production's provenance"):
        service.prepare_package(
            "od-1", SERIES, 1, 1, artifact, _od_manifest(repo, source_credits=forged)
        )
    package = service.prepare_package("od-1", SERIES, 1, 1, artifact, _od_manifest(repo))
    assert package.manifest["source_credits"] == credits
    assert package.manifest["production_run_id"] == "od-run"
    assert package.pilot_week == ON_DEMAND_WEEK
    assert _count(repo, "publishing_packages") == 1


@pytest.mark.parametrize("defect", ["not-accepted", "superseded", "qa-failed"])
def test_package_requires_the_founder_accepted_current_render(world, defect) -> None:
    repo, storage, _fake, service, _clock, artifact = world
    run = "od-run"
    with repo.connection:
        if defect == "not-accepted":
            repo.connection.execute(
                "INSERT INTO production_run_events VALUES "
                "(?, ?, 3, 'qa_review_pending', 'test', '{}', NULL, NULL, ?)",
                (f"{run}:event:3", run, NOW),
            )
        elif defect == "superseded":
            repo.connection.execute(
                "INSERT INTO production_run_evidence (id, production_run_id, evidence_type, "
                "final_media_artifact_id, payload_json, payload_digest, created_at) "
                "VALUES (?, ?, 'render', 'fake-artifact', '{}', ?, ?)",
                (f"{run}:render:evidence:2", run, "c" * 64, NOW),
            )
        elif defect == "qa-failed":
            repo.connection.execute(
                "INSERT INTO production_qa_reviews VALUES (?, ?, 'whole_video', 'failed', "
                "'human', '{}', '{}', ?, ?)",
                (f"{run}:qa:whole-video:2", run, artifact, "9999-01-01T00:00:00+00:00"),
            )
    with pytest.raises(ValueError, match="founder-accepted|current render|whole-video"):
        service.prepare_package("od-1", SERIES, 1, 1, artifact, _od_manifest(repo))
    assert _count(repo, "publishing_packages") == 0


def test_artifact_outside_any_production_cannot_be_packaged_on_demand(world) -> None:
    repo, _storage, _fake, service, _clock, _artifact_id = world
    with pytest.raises(ValueError, match="exactly one production run"):
        service.prepare_package("od-1", SERIES, 1, 1, "fake-artifact", _od_manifest(repo))


def test_series_and_timing_are_coupled_and_slots_are_unbounded_only_on_demand(world) -> None:
    repo, _storage, _fake, service, _clock, artifact = world
    with pytest.raises(ValueError, match="on_demand timing"):
        service.prepare_package(
            "od-1",
            SERIES,
            1,
            1,
            artifact,
            _od_manifest(repo, publication_timing=_manifest()["publication_timing"]),
        )
    with pytest.raises(ValueError, match="on_demand timing"):
        service.prepare_package(
            "legacy-x",
            "synthetic-pilot",
            1,
            1,
            "fake-artifact",
            {**_manifest(), "publication_timing": dict(ON_DEMAND_TIMING)},
        )
    with pytest.raises(ValueError, match="pilot slot"):
        service.prepare_package(
            "legacy-4", "synthetic-pilot", 4, 1, "fake-artifact", {**_manifest(), "pilot_slot": 4}
        )
    with pytest.raises(ValueError, match="API transfer, API"):
        service.prepare_package(
            "od-1", SERIES, 1, 1, artifact, _od_manifest(repo, release_route="manual")
        )
    package = service.prepare_package("od-12", SERIES, 12, 1, artifact, _od_manifest(repo, slot=12))
    assert package.pilot_slot == 12


# --- Founder confirmation -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"founder_confirmed": False}, "founder-confirmed"),
        ({"founder_actor": " "}, "founder-confirmed"),
        ({"privacy": "public"}, "uploaded private"),
        ({"privacy": "unlisted"}, "uploaded private"),
        ({"publish_at": "2026-10-24T18:30"}, "timezone offset"),
        ({"publish_at": "2026-10-24T12:10Z"}, "at least 30 minutes"),
        ({"publish_at": "2027-01-01T00:00Z"}, "within 14 days"),
        ({"description": "Credits removed."}, "keep the source credits"),
    ],
)
def test_scheduled_confirmation_gate_refuses_before_reserving(world, overrides, message) -> None:
    repo, _storage, fake, service, _clock, _artifact_id = world
    package = _approved_od(service, repo)
    with pytest.raises(ValueError, match=message):
        service.reserve_upload(package.id, upload=_confirmed(package, **overrides))
    with pytest.raises(ValueError, match="founder-confirmed"):
        service.reserve_upload(package.id)
    assert _count(repo, "publication_operations") == 0 and "begin" not in fake.calls


def test_unapproved_package_cannot_be_scheduled(world) -> None:
    repo, _storage, fake, service, _clock, artifact = world
    package = service.prepare_package("od-1", SERIES, 1, 1, artifact, _od_manifest(repo))
    with pytest.raises(ValueError):
        service.reserve_upload(package.id, upload=_confirmed(package))
    assert _count(repo, "publication_operations") == 0 and "begin" not in fake.calls


def test_confirmation_binds_digests_metadata_privacy_publish_at_and_expiry(world) -> None:
    repo, _storage, _fake, service, _clock, _artifact_id = world
    package = _approved_od(service, repo)
    operation = service.reserve_upload(package.id, upload=_confirmed(package))
    intent = operation.intent
    assert intent["schema"] == SCHEDULED_UPLOAD_SCHEMA
    assert (intent["package_digest"], intent["artifact_digest"]) == (
        package.package_digest,
        package.artifact_digest,
    )
    assert (intent["privacy"], intent["publish_at"]) == ("private", PUBLISH_AT_WIRE)
    assert intent["description"] == package.manifest["description"]
    assert intent["source_credits_digest"] == package.manifest["source_credits"]["digest"]
    confirmation = intent["founder_confirmation"]
    assert (
        datetime.fromisoformat(confirmation["expires_at"])
        - datetime.fromisoformat(confirmation["confirmed_at"])
        == CONFIRMATION_TTL
    )


def test_expired_confirmation_is_refused_and_closed_before_dispatch(world) -> None:
    repo, _storage, fake, service, clock, _artifact_id = world
    package = _approved_od(service, repo)
    operation = service.reserve_upload(package.id, upload=_confirmed(package))
    clock.now = T0 + CONFIRMATION_TTL + timedelta(seconds=1)
    with pytest.raises(ValueError, match="expired.*Nothing was sent to YouTube"):
        service.begin_api_upload(operation.id)
    assert "begin" not in fake.calls
    assert _events(repo, operation.id) == ["reserved", "failed"]
    # The closed confirmation can never be used again.
    with pytest.raises(ValueError):
        service.begin_api_upload(operation.id)
    assert "begin" not in fake.calls
    # A fresh founder confirmation is a new operation.
    fresh = service.reserve_upload(package.id, attempt=2, upload=_confirmed(package))
    assert fresh.id != operation.id


def test_publish_at_that_drifts_inside_the_lead_is_refused_before_dispatch(world) -> None:
    repo, _storage, fake, service, clock, _artifact_id = world
    package = _approved_od(service, repo)
    operation = service.reserve_upload(
        package.id, upload=_confirmed(package, publish_at="2026-10-24T12:31Z")
    )
    clock.now = T0 + timedelta(minutes=2)  # Confirmation still fresh; lead now 29 minutes.
    with pytest.raises(ValueError, match="no longer valid.*Nothing was sent"):
        service.begin_api_upload(operation.id)
    assert "begin" not in fake.calls and _events(repo, operation.id)[-1] == "failed"


def test_a_used_confirmation_cannot_be_replayed(world) -> None:
    repo, _storage, fake, service, _clock, _artifact_id = world
    package = _approved_od(service, repo)
    operation = service.reserve_upload(package.id, upload=_confirmed(package))
    service.begin_api_upload(operation.id)
    assert fake.calls.count("begin") == 1
    with pytest.raises(ValueError, match="inspected, not begun again"):
        service.begin_api_upload(operation.id)
    # A different confirmation for the same package after a success is refused.
    with pytest.raises(ValueError):
        service.reserve_upload(
            package.id, attempt=2, upload=_confirmed(package, publish_at="2026-10-25T18:30+01:00")
        )
    assert fake.calls.count("begin") == 1


# --- Commitment versus public outcome ----------------------------------------------------------


def _scheduled(world):
    repo, _storage, fake, service, _clock, _artifact_id = world
    package = _approved_od(service, repo)
    upload = service.reserve_upload(package.id, upload=_confirmed(package))
    publication = service.begin_api_upload(upload.id)
    return package, upload, publication


def _transition(repo, package_id: str):
    [row] = repo.connection.execute(
        "SELECT id FROM publication_operations WHERE package_id = ? AND action_kind = 'release'",
        (package_id,),
    ).fetchall()
    return repo.get_publication_operation(row["id"])


def test_accepted_schedule_is_a_pending_commitment_not_a_publication(world) -> None:
    repo, _storage, fake, *_ = world
    package, upload, publication = _scheduled(world)
    assert upload.id and publication.remote_id == "od-video-1"
    transition = _transition(repo, package.id)
    assert transition.intent["schema"] == SCHEDULED_TRANSITION_SCHEMA
    assert transition.intent["upload_operation_id"] == upload.id
    assert transition.outcome == "pending"
    events = repo.get_publication_operation_events(transition.id)
    assert [event.kind for event in events] == ["reserved", "progress"]
    assert events[-1].actor == "YouTube"
    assert events[-1].evidence["conveyor_dispatch"] is False
    assert _count(repo, "publication_receipts") == 0
    assert "release" not in fake.calls  # Conveyor never requests the public transition.


@pytest.mark.parametrize(
    "result",
    [
        _scheduled_result(publish_at=None),
        _scheduled_result(publish_at="2026-10-24T17:31:00Z"),
        _scheduled_result(privacy="public"),
    ],
)
def test_unconfirmed_schedule_stays_unknown_until_observed(world, result) -> None:
    """A schedule YouTube did not echo is an unknown outcome, never a refusal."""

    repo, _storage, fake, service, clock, _artifact_id = world
    fake.transfer = result
    package, _upload, publication = _scheduled(world)
    transition = _transition(repo, package.id)
    assert transition.outcome == "pending"
    assert _events(repo, transition.id) == ["reserved"]  # No accepted-commitment claim.
    # It still blocks another scheduled upload of the same artifact.
    with pytest.raises(ValueError):
        service.reserve_upload(package.id, attempt=2, upload=_confirmed(package))
    clock.now = T0 + timedelta(hours=6)
    fake.remote = replace(
        fake.remote,
        privacy="public",
        public_at=clock.now.isoformat(),
        observed_at=clock.now.isoformat(),
    )
    receipt = service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    assert receipt.release_operation_id == transition.id
    assert _events(repo, transition.id) == ["reserved", "succeeded"]


def test_uncertain_upload_outcome_records_no_commitment(world) -> None:
    repo, _storage, fake, service, _clock, _artifact_id = world
    fake.transfer = TransferResult("unknown", TARGET_CHANNEL, reason="response-lost")
    package = _approved_od(service, repo)
    upload = service.reserve_upload(package.id, upload=_confirmed(package))
    assert service.begin_api_upload(upload.id) is None
    assert repo.get_publication_operation(upload.id).outcome == "unknown"
    assert _count(repo, "publication_operations") == 1  # No transition, no receipt.
    with pytest.raises(ValueError):
        service.reserve_upload(package.id, attempt=2, upload=_confirmed(package))


def test_receipt_only_after_independent_public_observation(world) -> None:
    repo, _storage, fake, service, clock, _artifact_id = world
    package, _upload, publication = _scheduled(world)
    statuses = _count(repo, "publication_status_snapshots")
    with pytest.raises(ValueError, match="has not arrived"):
        service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    clock.now = T0 + timedelta(hours=6)
    fake.remote = replace(fake.remote, remote_id="od-video-1", privacy="private")
    with pytest.raises(ValueError, match="not yet independently observed public"):
        service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    fake.remote = replace(fake.remote, privacy="public", metadata_matches=False, public_at=NOW)
    with pytest.raises(ValueError, match="not yet independently observed public"):
        service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    assert _count(repo, "publication_status_snapshots") == statuses
    assert _count(repo, "publication_receipts") == 0
    assert _transition(repo, package.id).outcome == "pending"
    early = (T0 + timedelta(hours=1)).isoformat()  # Public before publishAt: manual action.
    fake.remote = replace(
        fake.remote, metadata_matches=True, public_at=early, observed_at=clock.now.isoformat()
    )
    with pytest.raises(ValueError, match="before its scheduled time"):
        service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    assert _count(repo, "publication_status_snapshots") == statuses
    public_at = (T0 + timedelta(hours=5, minutes=30)).isoformat()
    fake.remote = replace(
        fake.remote, metadata_matches=True, public_at=public_at, observed_at=clock.now.isoformat()
    )
    receipt = service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    assert receipt.public_at == public_at and receipt.pilot_week == ON_DEMAND_WEEK
    transition = _transition(repo, package.id)
    assert transition.outcome == "succeeded"
    assert receipt.release_operation_id == transition.id
    with pytest.raises(ValueError):
        service.reconcile_scheduled_publication("r-2", "s-2", publication.id)
    assert "release" not in fake.calls


def test_on_demand_publications_have_no_channel_week_limit(world) -> None:
    repo, storage, fake, service, clock, _artifact_id = world
    _world_rows(repo, storage, "od2", 804)
    receipts = []
    for number, (package_id, artifact, run) in enumerate(
        (("od-1", "od-artifact", "od-run"), ("od-2", "od2-artifact", "od2-run")), 1
    ):
        clock.now = T0
        fake.transfer = _scheduled_result(remote=f"od-video-{number}")
        package = _approved_od(service, repo, artifact, package_id, number, run)
        upload = service.reserve_upload(package.id, upload=_confirmed(package))
        publication = service.begin_api_upload(upload.id)
        clock.now = T0 + timedelta(hours=6)
        fake.remote = replace(
            fake.remote,
            privacy="public",
            public_at=clock.now.isoformat(),
            observed_at=clock.now.isoformat(),
        )
        receipts.append(
            service.reconcile_scheduled_publication(f"r-{number}", f"s-{number}", publication.id)
        )
    assert [receipt.pilot_week for receipt in receipts] == [ON_DEMAND_WEEK, ON_DEMAND_WEEK]


def test_scheduled_insert_body_carries_publish_at_and_stays_private(world) -> None:
    repo, _storage, _fake, service, _clock, _artifact_id = world
    package = _approved_od(service, repo)
    operation = service.reserve_upload(package.id, upload=_confirmed(package))
    body = build_insert_body(package, operation.intent)
    assert body["status"]["privacyStatus"] == "private"
    assert body["status"]["publishAt"] == PUBLISH_AT_WIRE
    assert body["snippet"]["description"] == package.manifest["description"]
    with pytest.raises(ValueError):
        build_insert_body(package, {**operation.intent, "privacy": "public"})
    legacy = build_insert_body(package, {**operation.intent, "schema": "confirmed-upload-v1"})
    assert "publishAt" not in legacy["status"]


# --- Legacy series keep their windows -----------------------------------------------------------


def test_legacy_series_still_refuse_release_outside_their_window(tmp_path) -> None:
    repo = AtlasRepository(tmp_path / "legacy.sqlite")
    storage = LocalMediaStorage(tmp_path / "media")
    _artifact(repo, storage)
    fake = FakePublishingAdapter()
    late = Clock(datetime.now(UTC) + timedelta(days=3))
    service = PublishingService(repo, storage, fake, late)
    try:
        package = service.prepare_package(
            "package-1", "synthetic-pilot", 1, 1, "fake-artifact", _manifest()
        )
        service.approve_package("approval-1", package.id, "founder")
        upload = service.reserve_upload(package.id)
        publication = service.begin_api_upload(upload.id)
        service.observe_status("private-status", publication.id)
        with pytest.raises(ValueError, match="exact active approved slot"):
            service.reserve_release(publication.id)
        assert "release" not in fake.calls
        with pytest.raises(ValueError):
            service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    finally:
        repo.close()


# --- Migration 31 -------------------------------------------------------------------------------


def _fingerprint(path: Path) -> dict:
    """Every table's row count and digest, read through a plain read-only connection."""

    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        return table_fingerprint(connection)
    finally:
        connection.close()


def _schema(connection) -> dict[tuple[str, str], str]:
    return {
        (kind, name): sql
        for kind, name, sql in connection.execute(
            "SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL"
        )
    }


def test_fresh_schema_has_unbounded_slots_and_a_week_rule_scoped_to_legacy(tmp_path) -> None:
    repo = AtlasRepository(tmp_path / "fresh.sqlite")
    try:
        connection = repo.connection
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 32
        sql = dict(connection.execute("SELECT name, sql FROM sqlite_master WHERE type = 'table'"))
        assert "CHECK (pilot_slot >= 1)" in sql["publishing_packages"]
        assert "BETWEEN 1 AND 3" not in sql["publishing_packages"]
        assert "UNIQUE(channel_id, pilot_week)" not in sql["publication_receipts"]
        names = {name for _kind, name in _schema(connection)}
        assert "idx_publishing_packages_artifact" in names
        scoped = {
            name: text
            for (_kind, name), text in _schema(connection).items()
            if name in {"publication_receipt_weekly_limit", "idx_publication_receipts_channel_week"}
        }
        assert len(scoped) == 2
        assert all("pilot_week <> 'on-demand'" in text for text in scoped.values())
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert not [name for name in sql if re.search(r"_v\d+$", name)]
    finally:
        repo.close()


def test_upgrade_30_to_31_preserves_every_row_trigger_and_reference(tmp_path, monkeypatch):
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:30])
    path = tmp_path / "upgrade.sqlite"
    repo = AtlasRepository(path)
    storage = LocalMediaStorage(tmp_path / "media")
    _artifact(repo, storage)
    fake = FakePublishingAdapter()
    service = PublishingService(repo, storage, fake, lambda: datetime.fromisoformat(NOW))
    _public(service, fake, "manual", "manual")  # A legacy observed public receipt.
    _world_rows(repo, storage, "nr", 805)
    fake.transfer = replace(fake.transfer, remote_id="fake-video-2")
    audit = service.prepare_package(
        "audit", "synthetic-pilot", 2, 1, "nr-artifact", _never_release()
    )
    service.approve_package("audit-approval", audit.id, "founder")
    service.begin_api_upload(service.reserve_upload(audit.id).id)
    assert repo.connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 30
    before_schema = _schema(repo.connection)
    repo.close()
    before_rows = _fingerprint(path)
    # Exactly migration 31 (32 has its own upgrade test).
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:31])
    upgraded = AtlasRepository(path)
    try:
        connection = upgraded.connection
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 31
        after_rows = _fingerprint(path)
        assert {k: v for k, v in after_rows.items() if k != "schema_migrations"} == {
            k: v for k, v in before_rows.items() if k != "schema_migrations"
        }
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        after_schema = _schema(connection)
        assert set(before_schema) - set(after_schema) == set()
        changed = {
            key
            for key in before_schema.keys() & after_schema.keys()
            if before_schema[key] != after_schema[key]
        }
        assert changed == {
            ("table", "publishing_packages"),
            ("table", "publication_receipts"),
            ("trigger", "publication_receipt_weekly_limit"),
        }
        assert set(after_schema) - set(before_schema) == {
            ("index", "idx_publication_receipts_channel_week")
        }
        for statement in (
            "UPDATE publishing_packages SET version = 2",
            "DELETE FROM publication_receipts",
            "UPDATE publication_receipts SET public_at = 'x'",
        ):
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                connection.execute(statement)
    finally:
        upgraded.close()


def test_failed_migration_31_is_atomic_and_leaves_30_intact(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:30])
    path = tmp_path / "atomic.sqlite"
    repo = AtlasRepository(path)
    try:
        schema_before = _schema(repo.connection)
        rows_before = _fingerprint(path)
        broken = MIGRATIONS[:30] + ((31, MIGRATION_31[1] + ("INVALID SQL",)),)
        with pytest.raises(sqlite3.DatabaseError):
            repo.apply_migrations(broken)
        connection = repo.connection
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 30
        assert _schema(connection) == schema_before
        assert _fingerprint(path) == rows_before
    finally:
        repo.close()


# --- Upload screen ------------------------------------------------------------------------------


class ScheduledUploadClient(FakeUploadClient):
    def insert_video(self, credentials, media_path: Path, body: dict) -> dict:
        resource = super().insert_video(credentials, media_path, body)
        if "publishAt" in body["status"]:
            resource["status"]["publishAt"] = body["status"]["publishAt"].replace("Z", ".000Z")
        return resource


@pytest.fixture
def screen(world, tmp_path):
    repo, storage, _fake, _service, clock, _artifact_id = world
    client = ScheduledUploadClient()

    def media_for(package):
        artifact = repo.get_final_media_artifact(package.final_media_artifact_id)
        storage.read_verified(artifact.storage_path, package.artifact_digest)
        return storage.path(artifact.storage_path)

    adapter = YouTubeUploadAdapter(Provider(upload_credentials()), media_for, client, clock)
    service = PublishingService(repo, storage, adapter, clock)
    package = _approved_od(service, repo)
    controller = YouTubeUploadController(
        service, adapter, governance_for(repo, tmp_path), monotonic=lambda: 0.0
    )
    return repo, client, service, package, controller, clock


def _form(controller, package, **overrides) -> dict:
    status, page = controller.page(package.id)
    assert status == 200
    nonce = re.search(r"name='nonce' value='([^']+)'", page).group(1)
    values = {
        "nonce": nonce,
        "package_id": package.id,
        "package_digest": package.package_digest,
        "title": package.manifest["title"],
        "description": package.manifest["description"],
        "privacy": "private",
        "publish_at": PUBLISH_AT,
        "founder_confirmation": "confirmed",
    }
    values.update(overrides)
    return {key: value for key, value in values.items() if value is not None}


def test_screen_shows_schedule_credits_artifact_digest_and_no_cancel_notice(screen) -> None:
    _repo, _client, _service, package, controller, _clock = screen
    status, page = controller.page(package.id)
    assert status == 200
    assert "name='publish_at'" in page and "id='scheduled-cancel-notice'" in page
    assert "name='privacy' value='private'" in page and "value='public'" not in page
    assert package.artifact_digest in page.split("founder_confirmation")[1]
    assert "Marcus Aurelius" in page and "Sources:" in page


def test_screen_sends_one_scheduled_private_insert_and_refuses_replay(screen) -> None:
    repo, client, _service, package, controller, _clock = screen
    form = _form(controller, package)
    status, page = controller.submit(form)
    assert status == 200 and "YouTube accepted the scheduled upload" in page
    [sent] = client.inserts
    assert sent["body"]["status"] == {
        **sent["body"]["status"],
        "privacyStatus": "private",
        "publishAt": PUBLISH_AT_WIRE,
    }
    assert "Scheduled publication time" in page
    assert controller.submit(form)[0] == 409  # The screen nonce is single-use.
    status, page = controller.submit(_form(controller, package, publish_at="2026-10-25T09:00Z"))
    assert status == 409 and len(client.inserts) == 1
    transition = _transition(repo, package.id)
    assert transition.outcome == "pending"


@pytest.mark.parametrize(
    "overrides",
    [
        {"publish_at": None},
        {"publish_at": "2026-10-24T18:30"},
        {"privacy": "public"},
        {"description": "Credits removed."},
    ],
)
def test_screen_refuses_invalid_schedules_before_anything_is_sent(screen, overrides) -> None:
    repo, client, _service, package, controller, _clock = screen
    status, page = controller.submit(_form(controller, package, **overrides))
    assert status == 409 and "refused before anything was sent" in page
    assert client.inserts == [] and _count(repo, "publication_operations") == 0


# --- publishing_cli -----------------------------------------------------------------------------


@pytest.fixture
def cli_world(tmp_path, monkeypatch):
    for name in ("ATLAS_DB_PATH", "ATLAS_MEDIA_STORAGE_ROOT"):
        monkeypatch.delenv(name, raising=False)
    db = tmp_path / "runtime.sqlite"
    repo = AtlasRepository(db)
    storage = LocalMediaStorage(tmp_path / "media")
    _world_rows(repo, storage, "od", 806)
    repo.close()
    metadata = tmp_path / "metadata.json"
    metadata.write_text(
        json.dumps(
            {
                key: value
                for key, value in _manifest().items()
                if key
                in {"title", "tags", "language", "caption_artifact", "cover_choice", "compliance"}
                | {"audience"}
            }
            | {"description_body": "A synthetic Stoic film."}
        ),
        encoding="utf-8",
    )
    return db, tmp_path / "media", metadata, tmp_path


def _cli(capsys, *argv) -> tuple[int, dict]:
    code = publishing_cli.main([str(arg) for arg in argv])
    out, err = capsys.readouterr()
    return code, json.loads(out or err)


def test_cli_status_is_read_only(cli_world, capsys) -> None:
    db, media, _metadata, _root = cli_world
    before = database_sha256(db)
    code, report = _cli(capsys, "status", "--db", db, "--media", media)
    assert code == 0 and report["schema_version"] == 32 and report["on_demand"] == []
    assert database_sha256(db) == before == report["db_sha256"]


def test_cli_prepare_dry_run_changes_nothing_and_live_backs_up_first(cli_world, capsys) -> None:
    db, media, metadata, root = cli_world
    before = database_sha256(db)
    common = ("--db", db, "--media", media, "--expect-db-sha256", before)
    prepare = (
        "prepare",
        "od-artifact",
        "--package-id",
        "od-1",
        "--slot",
        1,
        "--metadata",
        metadata,
    )
    code, report = _cli(capsys, *prepare, *common, "--dry-run")
    assert code == 0 and report["mode"] == "dry-run" and report["rehearsal"]["error"] is None
    assert "Sources:" in report["rehearsal"]["result"]["source_credits"]
    assert database_sha256(db) == before
    code, report = _cli(capsys, *prepare, *common, "--backup-root", root / "backups")
    assert code == 0 and report["mode"] == "live" and report["backup"]
    assert report["live"]["result"] == report["rehearsal"]["result"]
    digest = report["live"]["result"]["package_digest"]
    after = database_sha256(db)
    assert after != before
    # Stale hash: refused, unchanged.
    code, report = _cli(capsys, *prepare, *common, "--dry-run")
    assert code == 2 and "not" in report["refused"] and database_sha256(db) == after
    approve = ("approve", "od-1", "--decision-id", "d-1", "--founder-actor", "founder")
    common = ("--db", db, "--media", media, "--expect-db-sha256", after)
    code, report = _cli(capsys, *approve, "--package-digest", "0" * 64, *common, "--dry-run")
    assert code == 2 and report["mode"] == "refused-by-rehearsal"
    assert "differs" in report["rehearsal"]["error"] and database_sha256(db) == after
    code, report = _cli(
        capsys, *approve, "--package-digest", digest, *common, "--backup-root", root / "backups"
    )
    assert code == 0 and report["live"]["result"]["package_digest"] == digest
    code, report = _cli(capsys, "status", "--db", db, "--media", media)
    [package] = report["on_demand"]
    assert package["decisions"] == [{"id": "d-1", "sequence": 1, "decision": "approve"}]


def test_cli_prepare_refuses_missing_credits(cli_world, capsys) -> None:
    db, media, metadata, _root = cli_world
    connection = sqlite3.connect(db)
    with connection:
        connection.execute("DELETE FROM script_claim_links")
        connection.execute("DELETE FROM script_claim_sets")
    connection.close()
    before = database_sha256(db)
    code, report = _cli(
        capsys,
        "prepare",
        "od-artifact",
        "--package-id",
        "od-1",
        "--slot",
        1,
        "--metadata",
        metadata,
        "--db",
        db,
        "--media",
        media,
        "--expect-db-sha256",
        before,
        "--dry-run",
    )
    assert code == 2 and "no closed claim set" in report["rehearsal"]["error"]
    assert database_sha256(db) == before


def test_cli_rehearsal_never_observes_youtube(cli_world, capsys) -> None:
    db, media, _metadata, _root = cli_world
    adapter = publishing_cli._BlockedAdapter()
    with pytest.raises(publishing_cli.RehearsalObservationBlocked):
        adapter.observe_remote("video")
    assert adapter.authenticated_channel() == TARGET_CHANNEL


# --- Security-review regressions ----------------------------------------------------------------


def test_uncertain_upload_blocks_the_same_artifact_in_another_slot(world) -> None:
    repo, _storage, fake, service, _clock, _artifact_id = world
    fake.transfer = TransferResult("unknown", TARGET_CHANNEL, reason="response-lost")
    first = _approved_od(service, repo)
    service.begin_api_upload(service.reserve_upload(first.id, upload=_confirmed(first)).id)
    second = _approved_od(service, repo, package_id="od-2", slot=2)
    with pytest.raises(ValueError, match="already has an unresolved or successful"):
        service.reserve_upload(second.id, upload=_confirmed(second))
    assert fake.calls.count("begin") == 1


def test_scheduled_intents_are_refused_on_legacy_packages_and_vice_versa(world) -> None:
    repo, _storage, _fake, service, _clock, _artifact_id = world
    legacy = service.prepare_package(
        "legacy-1", "synthetic-pilot", 1, 1, "fake-artifact", _manifest()
    )
    service.approve_package("legacy-approval", legacy.id, "founder")
    with pytest.raises(ValueError, match="only scheduled intents"):
        repo.reserve_publication_operation(
            legacy.id, "upload", "api", {"schema": SCHEDULED_UPLOAD_SCHEMA, "privacy": "private"}
        )
    package = _approved_od(service, repo)
    with pytest.raises(ValueError, match="only scheduled intents"):
        repo.reserve_publication_operation(
            package.id, "upload", "api", {"schema": "private-transfer-v1", "privacy": "private"}
        )
    assert _count(repo, "publication_operations") == 0


def test_commitment_lost_to_a_stop_is_recovered_at_reconciliation(world, monkeypatch) -> None:
    repo, _storage, fake, service, clock, _artifact_id = world
    package = _approved_od(service, repo)
    upload = service.reserve_upload(package.id, upload=_confirmed(package))

    def stop(*_args):
        raise KeyboardInterrupt  # The process stops after the upload was recorded.

    monkeypatch.setattr(service, "_record_scheduled_commitment", stop)
    with pytest.raises(KeyboardInterrupt):
        service.begin_api_upload(upload.id)
    monkeypatch.undo()
    assert repo.get_publication_operation(upload.id).outcome == "succeeded"
    assert _count(repo, "publication_operations") == 1
    publication_id = repo.connection.execute("SELECT id FROM platform_publications").fetchone()[0]
    clock.now = T0 + timedelta(hours=6)
    fake.remote = replace(
        fake.remote,
        privacy="public",
        public_at=clock.now.isoformat(),
        observed_at=clock.now.isoformat(),
    )
    receipt = service.reconcile_scheduled_publication("r-1", "s-1", publication_id)
    transition = _transition(repo, package.id)
    assert transition.outcome == "succeeded" and receipt.release_operation_id == transition.id


def test_inconsistent_public_time_is_refused_before_anything_is_written(world) -> None:
    repo, _storage, fake, service, clock, _artifact_id = world
    package, _upload, publication = _scheduled(world)
    clock.now = T0 + timedelta(hours=6)
    statuses = _count(repo, "publication_status_snapshots")
    fake.remote = replace(
        fake.remote,
        privacy="public",
        public_at=clock.now.isoformat(),
        observed_at=(clock.now - timedelta(minutes=5)).isoformat(),  # Observed before public.
    )
    with pytest.raises(ValueError, match="inconsistent; nothing recorded"):
        service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    assert _count(repo, "publication_status_snapshots") == statuses
    assert _transition(repo, package.id).outcome == "pending"


def test_empty_claim_set_fails_closed(tmp_path) -> None:
    repo = AtlasRepository(tmp_path / "x.sqlite")
    storage = LocalMediaStorage(tmp_path / "media")
    try:
        _world_rows(repo, storage, "empty", 807, credits=False)
        with repo.connection:
            repo.connection.execute(
                "INSERT INTO script_claim_sets VALUES ('empty-set', 'empty-script', ?)", (NOW,)
            )
        with pytest.raises(SourceCreditError, match="declares no sourced claims"):
            source_credits(repo, "empty-run")
    finally:
        repo.close()


def test_rebuild_migration_with_dangling_references_rolls_back(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:30])
    path = tmp_path / "fk.sqlite"
    repo = AtlasRepository(path)
    try:
        rows_before = _fingerprint(path)
        dangling = (
            "INSERT INTO publishing_packages_v30 VALUES ('dangling', 'k', 1, 1, NULL, "
            f"'missing-artifact', '{'a' * 64}', 'youtube', 'c', 'w', '{{}}', '{'b' * 64}', 'now')"
        )
        statements = list(MIGRATION_31[1])
        statements.insert(1, dangling)  # After the rename, before the copy.
        with pytest.raises(sqlite3.IntegrityError, match="foreign-key violations"):
            repo.apply_migrations(MIGRATIONS[:30] + ((31, tuple(statements)),))
        version = repo.connection.execute("SELECT MAX(version) FROM schema_migrations")
        assert version.fetchone()[0] == 30
        assert _fingerprint(path) == rows_before
        assert repo.connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        repo.close()


def test_cli_refuses_live_commands_below_the_code_schema_head(tmp_path, monkeypatch, capsys):
    for name in ("ATLAS_DB_PATH", "ATLAS_MEDIA_STORAGE_ROOT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:30])
    db = tmp_path / "v30.sqlite"
    AtlasRepository(db).close()
    (tmp_path / "media").mkdir()
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS)
    before = database_sha256(db)
    code, report = _cli(capsys, "status", "--db", db, "--media", tmp_path / "media")
    assert code == 0 and (report["schema_version"], report["code_schema_head"]) == (30, 32)
    code, report = _cli(
        capsys,
        "approve",
        "od-1",
        "--package-digest",
        "0" * 64,
        "--decision-id",
        "d",
        "--founder-actor",
        "founder",
        "--db",
        db,
        "--media",
        tmp_path / "media",
        "--expect-db-sha256",
        before,
        "--backup-root",
        tmp_path / "backups",
    )
    assert code == 2 and "migration 30" in report["refused"]
    assert database_sha256(db) == before and not (tmp_path / "backups").exists()


def test_receipt_failure_after_success_recovers_without_youtube_or_duplicates(
    world, monkeypatch
) -> None:
    repo, _storage, fake, service, clock, _artifact_id = world
    package, _upload, publication = _scheduled(world)
    clock.now = T0 + timedelta(hours=6)
    public_at = (T0 + timedelta(hours=5, minutes=30)).isoformat()
    fake.remote = replace(
        fake.remote, privacy="public", public_at=public_at, observed_at=clock.now.isoformat()
    )
    create = repo.create_publication_receipt

    def fail(*_args, **_kwargs):
        raise sqlite3.OperationalError("disk I/O error")  # Injected at receipt creation.

    monkeypatch.setattr(repo, "create_publication_receipt", fail)
    with pytest.raises(sqlite3.OperationalError):
        service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    transition = _transition(repo, package.id)
    assert transition.outcome == "succeeded" and _count(repo, "publication_receipts") == 0
    statuses, events = _count(repo, "publication_status_snapshots"), _events(repo, transition.id)
    monkeypatch.setattr(repo, "create_publication_receipt", create)
    fake.calls.clear()
    fake.remote = replace(fake.remote, privacy="private")  # A retry must not re-observe.
    receipt = service.reconcile_scheduled_publication("r-1", "s-2", publication.id)
    # Only the existing read-only channel check; no observation, upload or transition request.
    assert fake.calls == ["channel"]
    assert (receipt.release_operation_id, receipt.public_status_id) == (transition.id, "s-1")
    assert receipt.public_at == public_at and receipt.pilot_week == ON_DEMAND_WEEK
    assert _count(repo, "publication_status_snapshots") == statuses
    assert _events(repo, transition.id) == events
    with pytest.raises(ValueError, match="already has receipt r-1"):
        service.reconcile_scheduled_publication("r-2", "s-3", publication.id)
    assert _count(repo, "publication_receipts") == 1
    assert not {"observe", "begin", "resume", "release"} & set(fake.calls)


# --- Browser form submission: textarea line breaks arrive as CRLF ------------------------------


def _browser_round_trip(screen, tmp_path, edit=None):
    """GET the screen and POST its textarea exactly as a browser serializes it (CRLF breaks)."""

    import html as html_module
    import threading
    from urllib.error import HTTPError
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

    from project_atlas.web import create_server

    _repo, _client, _service, package, controller, _clock = screen
    server = create_server(
        port=0, database_path=tmp_path / "web.db", youtube_upload=lambda _r: controller
    )

    def serve(request):
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            with urlopen(request) as response:
                return response.status, response.read().decode()
        except HTTPError as error:
            return error.code, error.read().decode()
        finally:
            thread.join(timeout=5)

    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        status, page = serve(f"{base}/youtube/upload?package={package.id}")
        assert status == 200
        textarea = re.search(
            r"<textarea id='description' name='description'>(.*?)</textarea>", page, re.S
        ).group(1)
        value = html_module.unescape(textarea)
        assert value == package.manifest["description"]  # The screen shows the frozen text.
        if edit is not None:
            value = edit(value)
        fields = {
            "nonce": re.search(r"name='nonce' value='([^']+)'", page).group(1),
            "package_id": package.id,
            "package_digest": package.package_digest,
            "title": html_module.unescape(
                re.search(r"id='title' name='title' maxlength='\d+' value='([^']*)'", page).group(1)
            ),
            "description": value.replace("\r\n", "\n").replace("\n", "\r\n"),
            "privacy": "private",
            "publish_at": PUBLISH_AT,
            "founder_confirmation": "confirmed",
        }
        request = Request(
            f"{base}/youtube/upload",
            data=urlencode(fields).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded", "Origin": base},
            method="POST",
        )
        return serve(request)
    finally:
        server.server_close()


def test_browser_crlf_submission_of_the_unchanged_description_is_accepted(screen, tmp_path):
    repo, client, _service, package, _controller, _clock = screen
    status, page = _browser_round_trip(screen, tmp_path)
    assert status == 200 and "YouTube accepted the scheduled upload" in page
    [sent] = client.inserts
    # Exactly the frozen description (LF), sources intact and in order, sent once.
    assert sent["body"]["snippet"]["description"] == package.manifest["description"]
    assert "\r" not in sent["body"]["snippet"]["description"]
    assert sent["body"]["status"]["privacyStatus"] == "private"
    assert sent["body"]["status"]["publishAt"] == PUBLISH_AT_WIRE
    [row] = repo.connection.execute(
        "SELECT id FROM publication_operations WHERE action_kind = 'upload'"
    )
    intent = repo.get_publication_operation(row["id"]).intent
    assert intent["description"] == package.manifest["description"]
    assert intent["package_digest"] == package.package_digest


def _sources_lines(text):
    head, sources = text.split("Sources:\n", 1)
    return head, sources.split("\n")


def _edit_source_title(text):
    return text.replace('"Meditations"', '"Meditations (abridged)"')


def _remove_sources(text):
    return _sources_lines(text)[0].rstrip()


def _reorder_sources(text):
    head, lines = _sources_lines(text)
    return head + "Sources:\n" + "\n".join(reversed(lines))


def _drop_one_source(text):
    head, lines = _sources_lines(text)
    return head + "Sources:\n" + lines[0]


@pytest.mark.parametrize(
    "edit", [_edit_source_title, _remove_sources, _reorder_sources, _drop_one_source]
)
def test_browser_submission_with_changed_sources_is_still_refused(screen, tmp_path, edit):
    repo, client, _service, _package, _controller, _clock = screen
    status, page = _browser_round_trip(screen, tmp_path, edit)
    assert status == 409 and "refused before anything was sent" in page
    assert "keep the source credits exactly" in page
    assert client.inserts == []
    assert _count(repo, "publication_operations") == 0


# --- Backup labels: every publishing command yields a label verified_backup accepts -----------

P11_PREPARE = "prepare-publishing-package-similarstoic-youtube-on-demand-v1-slot-1-v1"
P11_RECONCILE = (
    "reconcile-platform-publication-"
    "2a975ee56f0b5558f46fc781a302211db54d21f57b667f37cd303a81e212124a"
)


def test_valid_backup_labels_are_unchanged() -> None:
    from project_atlas.publishing_cli import backup_label

    # The labels already used for P11's prepare and approve backups stay exactly as they were.
    assert backup_label(P11_PREPARE) == f"pre-publishing-{P11_PREPARE}"
    approve = P11_PREPARE.replace("prepare-", "approve-", 1)
    assert backup_label(approve) == f"pre-publishing-{approve}"
    assert backup_label("prepare-od-1") == "pre-publishing-prepare-od-1"


def test_oversized_backup_label_is_readable_fingerprinted_and_deterministic() -> None:
    from hashlib import sha256

    from project_atlas.production_backup import _LABEL
    from project_atlas.publishing_cli import backup_label

    full = f"pre-publishing-{P11_RECONCILE}"
    assert len(full) == 110 and not _LABEL.fullmatch(full)  # The refused live label.
    label = backup_label(P11_RECONCILE)
    assert _LABEL.fullmatch(label) and len(label) == 100
    assert label == backup_label(P11_RECONCILE)  # Deterministic.
    assert label.startswith("pre-publishing-reconcile-platform-publication-2a975ee5")
    assert label.endswith("-" + sha256(full.encode()).hexdigest()[:12])
    # Two long identifiers sharing the readable prefix still get different labels.
    other = P11_RECONCILE[:-1] + "f"
    assert backup_label(other) != label and len(backup_label(other)) == 100


@pytest.mark.parametrize(
    "identifier",
    [
        "x" * 300,
        "Mixed-Case_ID.With.Dots",
        "spaces and / slashes \\ and ünïcode",
        "-leading-dash",
        "...",
        "a" * 84 + "-" * 30,
        "",
    ],
)
def test_no_publishing_command_builds_an_invalid_backup_label(identifier) -> None:
    from project_atlas.production_backup import _LABEL
    from project_atlas.publishing_cli import backup_label

    for command in ("prepare", "approve", "reconcile"):
        label = backup_label(f"{command}-{identifier}")
        assert _LABEL.fullmatch(label) and len(label) <= 100
        assert label == backup_label(f"{command}-{identifier}")


def _backup_dir(report: dict) -> Path:
    backup = report["backup"]
    assert backup["integrity"] == "ok" and backup["content_identical"] is True
    assert backup["foreign_key_violations"] == 0
    path = Path(backup["backup"])
    assert path.is_file()
    return path.parent


def test_cli_prepare_and_approve_live_with_an_oversized_package_id(cli_world, capsys) -> None:
    from project_atlas.publishing_cli import backup_label

    db, media, metadata, root = cli_world
    package_id = "publishing-package-similarstoic-youtube-on-demand-v1-slot-1-v1-" + "x" * 60
    backups = root / "backups"
    code, report = _cli(
        capsys,
        "prepare",
        "od-artifact",
        "--package-id",
        package_id,
        "--slot",
        1,
        "--metadata",
        metadata,
        "--db",
        db,
        "--media",
        media,
        "--expect-db-sha256",
        database_sha256(db),
        "--backup-root",
        backups,
    )
    assert code == 0 and report["mode"] == "live", report
    label = backup_label(f"prepare-{package_id}")
    assert len(f"pre-publishing-prepare-{package_id}") > 100 and len(label) == 100
    assert _backup_dir(report).name.startswith(label + "-")
    digest = report["live"]["result"]["package_digest"]
    code, report = _cli(
        capsys,
        "approve",
        package_id,
        "--package-digest",
        digest,
        "--decision-id",
        "d-1",
        "--founder-actor",
        "founder",
        "--db",
        db,
        "--media",
        media,
        "--expect-db-sha256",
        database_sha256(db),
        "--backup-root",
        backups,
    )
    assert code == 0 and report["mode"] == "live", report
    assert _backup_dir(report).name.startswith(backup_label(f"approve-{package_id}") + "-")
    assert report["live"]["result"]["package_digest"] == digest


def test_cli_reconcile_scheduled_live_with_a_full_length_publication_id(
    cli_world, capsys, monkeypatch
) -> None:
    from project_atlas import youtube_adapter
    from project_atlas.publishing_cli import backup_label

    db, media, _metadata, root = cli_world
    start = datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(hours=2)
    publish_at = start + timedelta(hours=1)  # Already passed for the real-clock CLI.
    repo = AtlasRepository(db)
    try:
        fake = FakePublishingAdapter()
        fake.transfer = _scheduled_result(publish_at=publish_at_wire(publish_at))
        service = PublishingService(repo, LocalMediaStorage(media), fake, lambda: start)
        package = _approved_od(service, repo)
        upload = service.reserve_upload(
            package.id, upload=_confirmed(package, publish_at=publish_at.isoformat())
        )
        publication = service.begin_api_upload(upload.id)
    finally:
        repo.close()
    assert len(f"pre-publishing-reconcile-{publication.id}") == 110  # As for P11.
    observer = FakePublishingAdapter()
    moment = datetime.now(UTC).replace(microsecond=0)
    observer.remote = replace(
        observer.remote,
        privacy="public",
        public_at=(moment + timedelta(seconds=30)).isoformat(),
        observed_at=(moment + timedelta(seconds=60)).isoformat(),
    )
    monkeypatch.setattr(
        youtube_adapter.YouTubeReadOnlyObservationAdapter,
        "from_client_config",
        lambda *_args, **_kwargs: observer,  # Fake observer: no credential, no network.
    )
    code, report = _cli(
        capsys,
        "reconcile-scheduled",
        publication.id,
        "--receipt-id",
        "r-1",
        "--status-id",
        "s-1",
        "--client-config",
        root / "client-config.json",
        "--consent-state",
        root / "consent-state.json",
        "--db",
        db,
        "--media",
        media,
        "--expect-db-sha256",
        database_sha256(db),
        "--backup-root",
        root / "backups",
    )
    assert code == 0 and report["mode"] == "live", report
    assert "observe_remote" in report["rehearsal"]["stopped_at"]  # Rehearsal never observes.
    assert _backup_dir(report).name.startswith(backup_label(f"reconcile-{publication.id}") + "-")
    assert report["live"]["result"]["receipt_id"] == "r-1"
    assert observer.calls.count("observe") == 1
    connection = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        assert (
            connection.execute(
                "SELECT release_operation_id FROM publication_receipts WHERE id = 'r-1'"
            ).fetchone()
            is not None
        )
    finally:
        connection.close()


# --- Retention of YouTube's public time (future writes) ------------------------------------------


def _published(world):
    """A scheduled upload observed public, with its receipt; returns the moving parts."""

    repo, _storage, fake, service, clock, _artifact_id = world
    package, _upload, publication = _scheduled(world)
    clock.now = T0 + timedelta(hours=6)
    public_at = (T0 + timedelta(hours=5, minutes=30)).isoformat()
    fake.remote = replace(
        fake.remote, privacy="public", public_at=public_at, observed_at=clock.now.isoformat()
    )
    return package, publication, public_at


def test_success_event_keeps_public_time_only_in_purgeable_provider_evidence(world) -> None:
    repo, _storage, _fake, service, _clock, _artifact_id = world
    package, publication, public_at = _published(world)
    receipt = service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    transition = _transition(repo, package.id)
    succeeded = repo.get_publication_operation_events(transition.id)[-1]
    assert succeeded.kind == "succeeded"
    assert succeeded.evidence == {
        "method": "independent-public-observation",
        "public_status_id": "s-1",
    }
    assert succeeded.provider_evidence == {"public_at": public_at}
    assert receipt.public_at == public_at
    # The existing purge clears it with the rest of the provider evidence; lineage stays.
    repo.purge_provider_operation_evidence(transition.id)
    purged = repo.get_publication_operation_events(transition.id)[-1]
    assert purged.provider_evidence is None and purged.provider_purged_at is not None
    assert purged.evidence == succeeded.evidence


def test_stale_purge_rule_clears_the_success_event_public_time_unchanged(world) -> None:
    repo, _storage, _fake, service, clock, _artifact_id = world
    package, publication, _public_at = _published(world)
    service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    transition = _transition(repo, package.id)
    counts = repo.purge_stale_youtube_api_data(datetime.now(UTC) + timedelta(days=31))
    assert counts["operations"] >= 1 and counts["publications"] == 1
    succeeded = repo.get_publication_operation_events(transition.id)[-1]
    assert succeeded.provider_evidence is None
    assert "public_at" not in json.dumps(succeeded.evidence)


def _interrupted(world, monkeypatch):
    """Reconciliation that stopped after the success event, before the receipt."""

    repo, _storage, _fake, service, _clock, _artifact_id = world
    package, publication, public_at = _published(world)
    create = repo.create_publication_receipt

    def fail(*_args, **_kwargs):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(repo, "create_publication_receipt", fail)
    with pytest.raises(sqlite3.OperationalError):
        service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    monkeypatch.setattr(repo, "create_publication_receipt", create)
    assert _transition(repo, package.id).outcome == "succeeded"
    assert _count(repo, "publication_receipts") == 0
    return package, publication, public_at


def test_interrupted_reconciliation_recovers_from_unpurged_provider_evidence(
    world, monkeypatch
) -> None:
    repo, _storage, fake, service, _clock, _artifact_id = world
    _package, publication, public_at = _interrupted(world, monkeypatch)
    fake.calls.clear()
    receipt = service.reconcile_scheduled_publication("r-1", "s-2", publication.id)
    assert (receipt.public_at, receipt.public_status_id) == (public_at, "s-1")
    assert "observe" not in fake.calls


def test_recovery_refuses_once_the_provider_public_time_is_purged(world, monkeypatch) -> None:
    repo, _storage, fake, service, _clock, _artifact_id = world
    package, publication, _public_at = _interrupted(world, monkeypatch)
    repo.purge_provider_operation_evidence(_transition(repo, package.id).id)
    fake.calls.clear()
    with pytest.raises(ValueError, match="purged under the 30-day rule"):
        service.reconcile_scheduled_publication("r-1", "s-2", publication.id)
    assert _count(repo, "publication_receipts") == 0 and "observe" not in fake.calls


def test_recovery_refuses_an_earlier_format_event_with_immutable_public_time(world) -> None:
    """Earlier code stored YouTube's public time in the immutable evidence; never reuse it."""

    repo, _storage, fake, service, clock, _artifact_id = world
    package, publication, public_at = _published(world)
    transition = _transition(repo, package.id)
    repo.append_publication_status(
        "s-1",
        publication.id,
        "public",
        "succeeded",
        "passed",
        False,
        "offline-adapter-v1",
        clock.now.isoformat(),
        None,
    )
    repo.append_publication_operation_event(
        transition.id,
        "succeeded",
        "Conveyor",
        {
            "method": "independent-public-observation",
            "public_status_id": "s-1",
            "public_at": public_at,
        },
    )
    fake.calls.clear()
    with pytest.raises(ValueError, match="earlier format"):
        service.reconcile_scheduled_publication("r-1", "s-2", publication.id)
    assert _count(repo, "publication_receipts") == 0 and "observe" not in fake.calls


# --- publishing_cli observe ----------------------------------------------------------------------


def _cli_publication(db: Path, media: Path) -> str:
    """A real-format on-demand publication (full-length id) in an isolated database."""

    start = datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(hours=2)
    publish_at = start + timedelta(hours=1)
    repo = AtlasRepository(db)
    try:
        fake = FakePublishingAdapter()
        fake.transfer = _scheduled_result(publish_at=publish_at_wire(publish_at))
        service = PublishingService(repo, LocalMediaStorage(media), fake, lambda: start)
        package = _approved_od(service, repo)
        upload = service.reserve_upload(
            package.id, upload=_confirmed(package, publish_at=publish_at.isoformat())
        )
        return service.begin_api_upload(upload.id).id
    finally:
        repo.close()


def _observe_args(publication_id, db, media, root, *mode):
    return (
        "observe",
        publication_id,
        "--status-id",
        "observe-status-1",
        "--client-config",
        root / "client-config.json",
        "--consent-state",
        root / "consent-state.json",
        "--db",
        db,
        "--media",
        media,
        "--expect-db-sha256",
        database_sha256(db),
        *mode,
    )


def _fake_observer(monkeypatch, **changes) -> FakePublishingAdapter:
    from project_atlas import youtube_adapter

    observer = FakePublishingAdapter()
    fields = {
        "privacy": "public",
        "observed_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
    }
    fields.update(changes)
    observer.remote = replace(observer.remote, **fields)
    monkeypatch.setattr(
        youtube_adapter.YouTubeReadOnlyObservationAdapter,
        "from_client_config",
        lambda *_args, **_kwargs: observer,  # Fake observer: no credential, no network.
    )
    return observer


def test_cli_observe_requires_publication_status_and_credentials_paths() -> None:
    parser = publishing_cli._parser()
    args = parser.parse_args(
        [
            "observe",
            "pub-1",
            "--status-id",
            "s-1",
            "--client-config",
            "c.json",
            "--consent-state",
            "s.json",
            "--expect-db-sha256",
            "0" * 64,
            "--dry-run",
        ]
    )
    assert (args.command, args.publication_id, args.status_id) == ("observe", "pub-1", "s-1")
    assert publishing_cli.COMMANDS["observe"] is publishing_cli.cmd_observe
    with pytest.raises(SystemExit):
        parser.parse_args(["observe", "pub-1", "--expect-db-sha256", "0" * 64, "--dry-run"])


def test_cli_observe_dry_run_stops_before_youtube_and_changes_nothing(
    cli_world, capsys, monkeypatch
) -> None:
    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    observer = _fake_observer(monkeypatch)
    before = database_sha256(db)
    code, report = _cli(capsys, *_observe_args(publication_id, db, media, root, "--dry-run"))
    assert code == 0 and report["mode"] == "dry-run", report
    assert "observe_remote" in report["rehearsal"]["stopped_at"]
    assert database_sha256(db) == before and observer.calls == []


def test_cli_observe_live_records_one_status_after_a_verified_backup(
    cli_world, capsys, monkeypatch
) -> None:
    from project_atlas.publishing_cli import backup_label

    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    observer = _fake_observer(monkeypatch)
    code, report = _cli(
        capsys,
        *_observe_args(publication_id, db, media, root, "--backup-root", root / "backups"),
    )
    assert code == 0 and report["mode"] == "live", report
    assert len(f"pre-publishing-observe-{publication_id}") > 100  # Full-length identifier.
    label = backup_label(f"observe-{publication_id}")
    assert len(label) <= 100 and _backup_dir(report).name.startswith(label + "-")
    result = report["live"]["result"]
    assert (result["status_id"], result["publication_id"]) == ("observe-status-1", publication_id)
    assert (result["privacy"], result["verification"]) == ("public", "passed")
    assert observer.calls.count("observe") == 1
    connection = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        assert connection.execute(
            "SELECT COUNT(*) FROM publication_status_snapshots WHERE id = 'observe-status-1'"
        ).fetchone() == (1,)
        assert connection.execute("SELECT COUNT(*) FROM publication_receipts").fetchone() == (0,)
    finally:
        connection.close()


@pytest.mark.parametrize(("matches", "verification"), [(False, "failed"), (None, "unknown")])
def test_cli_observe_records_unverified_observations_but_not_as_a_refresh(
    cli_world, capsys, monkeypatch, matches, verification
) -> None:
    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    _fake_observer(monkeypatch, metadata_matches=matches)
    code, report = _cli(
        capsys,
        *_observe_args(publication_id, db, media, root, "--backup-root", root / "backups"),
    )
    result = report["live"]["result"]
    assert report["mode"] == "live" and result["verification"] == verification, report
    assert result["qualifies_as_identity_refresh"] is False
    assert "does NOT count as an identity refresh" in result["note"]
    assert code == 3  # Recorded, but not a passed identity refresh.


def test_cli_observe_reports_a_passed_observation_as_an_identity_refresh(
    cli_world, capsys, monkeypatch
) -> None:
    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    _fake_observer(monkeypatch)
    code, report = _cli(
        capsys,
        *_observe_args(publication_id, db, media, root, "--backup-root", root / "backups"),
    )
    result = report["live"]["result"]
    assert code == 0 and result["verification"] == "passed", report
    assert result["qualifies_as_identity_refresh"] is True


def test_cli_observe_reports_an_inaccessible_video_as_a_youtube_refusal(
    cli_world, capsys, monkeypatch
) -> None:
    from project_atlas.youtube_adapter import YouTubeObservationBlocked

    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    observer = _fake_observer(monkeypatch)

    def inaccessible(remote_id, package=None):
        raise YouTubeObservationBlocked("remote_video_inaccessible")

    observer.observe_remote = inaccessible
    rows_before = _fingerprint(db)
    code, report = _cli(
        capsys,
        *_observe_args(publication_id, db, media, root, "--backup-root", root / "backups"),
    )
    assert code == 2 and report["mode"] == "refused-live", report
    live = report["live"]
    assert (live["refusal"], live["category"]) == ("youtube", "remote_video_inaccessible")
    assert "may have deleted" in live["warning"]  # A warning, not a claim that it did.
    assert report["db_sha256_before"] and report["db_sha256_after"]
    assert _fingerprint(db) == rows_before  # Here nothing was recorded or purged.


def test_cli_observe_reports_a_real_adapter_authorization_failure(
    cli_world, capsys, monkeypatch
) -> None:
    """The real read-only adapter turns a definitive preflight failure into a refusal."""

    from project_atlas import youtube_adapter
    from project_atlas.youtube_preflight import PreflightBlocked

    class RevokedProvider:
        def acquire(self):
            raise PreflightBlocked("authorization_revoked")

    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    monkeypatch.setattr(
        youtube_adapter.YouTubeReadOnlyObservationAdapter,
        "from_client_config",
        lambda *_a, **_k: youtube_adapter.YouTubeReadOnlyObservationAdapter(
            RevokedProvider(), client=object()
        ),
    )
    code, report = _cli(
        capsys,
        *_observe_args(publication_id, db, media, root, "--backup-root", root / "backups"),
    )
    assert code == 2 and report["mode"] == "refused-live", report
    assert (report["live"]["refusal"], report["live"]["category"]) == (
        "youtube",
        "authorization_revoked",
    )


def test_cli_observe_reports_a_policy_acceptance_refusal_before_any_call(
    cli_world, capsys, monkeypatch
) -> None:
    from project_atlas import youtube_adapter
    from project_atlas.youtube_consent import PolicyAcceptanceRequired

    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)

    def refuse(*_a, **_k):
        raise PolicyAcceptanceRequired()

    monkeypatch.setattr(
        youtube_adapter.YouTubeReadOnlyObservationAdapter, "from_client_config", refuse
    )
    code, report = _cli(
        capsys,
        *_observe_args(publication_id, db, media, root, "--backup-root", root / "backups"),
    )
    assert code == 2 and report["mode"] == "refused-live", report
    assert report["live"]["category"] == "privacy_policy_acceptance_required"


def test_cli_live_unexpected_failure_is_not_reported_as_a_refusal(
    cli_world, capsys, monkeypatch
) -> None:
    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    observer = _fake_observer(monkeypatch)

    def broken(remote_id, package=None):
        raise RuntimeError("implementation defect")

    observer.observe_remote = broken
    with pytest.raises(RuntimeError, match="implementation defect"):
        publishing_cli.main(
            [
                str(arg)
                for arg in _observe_args(
                    publication_id, db, media, root, "--backup-root", root / "backups"
                )
            ]
        )


def _reconcile_args(publication_id, db, media, root, *mode):
    return (
        "reconcile-scheduled",
        publication_id,
        "--receipt-id",
        "r-1",
        "--status-id",
        "s-1",
        "--client-config",
        root / "client-config.json",
        "--consent-state",
        root / "consent-state.json",
        "--db",
        db,
        "--media",
        media,
        "--expect-db-sha256",
        database_sha256(db),
        *mode,
    )


def test_cli_reconcile_partial_evidence_reports_the_recovery_path(
    cli_world, capsys, monkeypatch
) -> None:
    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    moment = datetime.now(UTC).replace(microsecond=0)
    _fake_observer(
        monkeypatch,
        public_at=(moment + timedelta(seconds=30)).isoformat(),
        observed_at=(moment + timedelta(seconds=60)).isoformat(),
    )
    create = AtlasRepository.create_publication_receipt

    def refuse(*_args, **_kwargs):
        raise ValueError("receipt refused after the success event")

    # The rehearsal stops at the blocked observation, so only the live step reaches this.
    monkeypatch.setattr(AtlasRepository, "create_publication_receipt", refuse)
    code, report = _cli(
        capsys,
        *_reconcile_args(publication_id, db, media, root, "--backup-root", root / "backups"),
    )
    assert code == 2 and report["mode"] == "refused-live", report
    live = report["live"]
    assert live["refusal"] == "service" and live["partial_reconciliation"] is True
    assert "rerun reconcile-scheduled" in live["recovery"]
    assert "refuses purged or earlier-format evidence" in live["recovery"]
    monkeypatch.setattr(AtlasRepository, "create_publication_receipt", create)
    code, report = _cli(  # Separate backup root: both runs may fall in the same second.
        capsys,
        *_reconcile_args(publication_id, db, media, root, "--backup-root", root / "backups-2"),
    )
    assert code == 0 and report["live"]["result"]["receipt_id"] == "r-1", report


def test_cli_reconcile_refusal_without_partial_evidence_promises_no_recovery(
    cli_world, capsys, monkeypatch
) -> None:
    from project_atlas.youtube_adapter import YouTubeObservationBlocked

    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    observer = _fake_observer(monkeypatch)

    def inaccessible(remote_id, package=None):
        raise YouTubeObservationBlocked("remote_video_inaccessible")

    observer.observe_remote = inaccessible
    code, report = _cli(
        capsys,
        *_reconcile_args(publication_id, db, media, root, "--backup-root", root / "backups"),
    )
    assert code == 2 and report["live"]["refusal"] == "youtube", report
    assert report["live"]["partial_reconciliation"] is False
    assert "recovery" not in report["live"]


def test_cli_observe_refuses_a_different_remote_identity_in_the_live_step(
    cli_world, capsys, monkeypatch
) -> None:
    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    observer = _fake_observer(monkeypatch)
    observer.observe_remote = lambda remote_id, package=None: replace(
        observer.remote, remote_id="someone-elses-video"
    )
    rows_before = _fingerprint(db)
    code, report = _cli(
        capsys,
        *_observe_args(publication_id, db, media, root, "--backup-root", root / "backups"),
    )
    assert code == 2 and report["mode"] == "refused-live", report
    assert "differs from bound lineage" in report["live"]["error"]
    # Nothing recorded: every table's content is unchanged (opening the database may still
    # rewrite SQLite's file header, so the file hash is not the measure).
    assert _fingerprint(db) == rows_before


def test_cli_observe_refuses_a_purged_api_identity(cli_world, capsys, monkeypatch) -> None:
    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    repo = AtlasRepository(db)
    try:
        repo.purge_publication_api_data(publication_id)
    finally:
        repo.close()
    observer = _fake_observer(monkeypatch)
    before = database_sha256(db)
    code, report = _cli(capsys, *_observe_args(publication_id, db, media, root, "--dry-run"))
    assert code == 2 and report["mode"] == "refused-by-rehearsal", report
    assert "Purged API identity" in report["rehearsal"]["error"]
    assert database_sha256(db) == before and observer.calls == []
