"""Disposable, network-free proofs of the controlled-publishing foundation."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from project_atlas.media import LocalMediaStorage
from project_atlas.persistence import MIGRATIONS, AtlasRepository
from project_atlas.publishing import (
    AggregateObservation,
    PublishingService,
    RemoteObservation,
    TransferResult,
)
from project_atlas.publishing_state import TARGET_CHANNEL, canonical_json, digest

NOW = datetime.now(UTC).replace(microsecond=0).isoformat()
LATER = (datetime.now(UTC) + timedelta(days=1)).replace(microsecond=0).isoformat()
REVIEW_NOW = datetime.fromisoformat(NOW)
LONDON_MINUTE = REVIEW_NOW.astimezone(timezone(timedelta(hours=1))).replace(second=0)


class FakePublishingAdapter:
    """Synthetic outcomes only; no URL, token, live client or HTTP capability."""

    def __init__(self) -> None:
        self.channel = TARGET_CHANNEL
        self.transfer = TransferResult("succeeded", TARGET_CHANNEL, "fake-video-1")
        self.resume = self.transfer
        self.release = TransferResult("succeeded", TARGET_CHANNEL, "fake-video-1")
        self.remote = RemoteObservation(
            "fake-video-1",
            TARGET_CHANNEL,
            "private",
            "succeeded",
            True,
            False,
            NOW,
        )
        self.performance = AggregateObservation(
            LATER,
            LATER,
            {"metrics": ["views", "likes"]},
            {"metrics": ["views"]},
            {"views": 12},
            {},
            "immature",
            {"schema": "fake-v1"},
            {"synthetic_detail": "purge-me"},
        )
        self.calls: list[str] = []

    def authenticated_channel(self) -> str:
        self.calls.append("channel")
        return self.channel

    def begin_private_transfer(self, package, operation) -> TransferResult:
        self.calls.append("begin")
        return self.transfer

    def inspect_or_resume_transfer(self, operation) -> TransferResult:
        self.calls.append("resume")
        return self.resume

    def observe_remote(self, remote_id: str, package=None) -> RemoteObservation:
        self.calls.append("observe")
        return replace(self.remote, remote_id=remote_id)

    def request_public_transition(self, publication, operation) -> TransferResult:
        self.calls.append("release")
        return self.release

    def aggregate_performance(self, receipt, checkpoint: str) -> AggregateObservation:
        self.calls.append("performance")
        return self.performance


def _artifact(repo: AtlasRepository, storage: LocalMediaStorage) -> None:
    """Build a complete FK chain only in this test's disposable DB/media root."""

    opportunity = repo.connection.execute("SELECT id FROM opportunities LIMIT 1").fetchone()[0]
    path, media_digest = storage.write("final", "fake-artifact", b"synthetic-test-mp4", "video/mp4")
    with repo.connection:
        repo.connection.execute(
            "INSERT INTO research_packs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("fake-research", opportunity, 987, "test", None, "{}", NOW, NOW, None),
        )
        repo.connection.execute(
            "INSERT INTO editorial_angles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "fake-angle",
                opportunity,
                "fake-research",
                "test",
                "test",
                "test",
                "test",
                "[]",
                "{}",
                NOW,
                NOW,
                None,
            ),
        )
        repo.connection.execute(
            "INSERT INTO content_pieces VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("fake-piece", opportunity, "fake-angle", "video", "test", "{}", NOW, NOW),
        )
        repo.connection.execute(
            "INSERT INTO scripts VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("fake-script", "fake-piece", 987, "test", "{}", NOW, NOW),
        )
        repo.connection.execute(
            "INSERT INTO visual_plans VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("fake-plan", "fake-piece", "fake-script", "test", "{}", NOW, NOW),
        )
        repo.connection.execute(
            "INSERT INTO narration_assets VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "fake-narration",
                "fake-script",
                "fake.wav",
                "audio/wav",
                "imported",
                "a" * 64,
                1000,
                NOW,
            ),
        )
        repo.connection.execute(
            "INSERT INTO final_media_input_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "fake-input",
                "fake-plan",
                "fake-script",
                "fake-narration",
                "test-v1",
                "[]",
                "[]",
                "{}",
                NOW,
            ),
        )
        repo.connection.execute(
            "INSERT INTO render_executions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("fake-render", "fake-input", "test", "v1", "v1", "succeeded", None, None, "{}", NOW),
        )
        repo.connection.execute(
            "INSERT INTO final_media_artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "fake-artifact",
                "fake-render",
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


@pytest.fixture
def setup(tmp_path: Path):
    repo = AtlasRepository(tmp_path / "offline-test.sqlite")
    storage = LocalMediaStorage(tmp_path / "media")
    _artifact(repo, storage)
    fake = FakePublishingAdapter()
    yield repo, storage, fake, PublishingService(repo, storage, fake, lambda: REVIEW_NOW)
    repo.close()


def _manifest(mode: str = "api", release: str = "api") -> dict:
    return {
        "title": "Synthetic test",
        "description": "Synthetic test",
        "tags": ["test"],
        "language": "en-GB",
        "caption_artifact": "synthetic-caption",
        "cover_choice": "A",
        "compliance": {"checked": True},
        "audience": {"made_for_kids": False},
        "private_first": True,
        "transfer_route": mode,
        "release_route": release,
        "publication_timing": (
            {"timezone": "Europe/London", "mode": "exact", "at": LONDON_MINUTE.isoformat()}
            if release == "api"
            else {
                "timezone": "Europe/London",
                "mode": "window",
                "start": (LONDON_MINUTE - timedelta(minutes=1)).isoformat(),
                "end": (LONDON_MINUTE + timedelta(minutes=2)).isoformat(),
            }
        ),
        "pilot_slot": 1,
    }


def _approved(service: PublishingService, mode: str = "api", release: str = "api"):
    package = service.prepare_package(
        "package-1", "synthetic-pilot", 1, 1, "fake-artifact", _manifest(mode, release)
    )
    service.approve_package("founder-approval-1", package.id, "synthetic-founder")
    return package


def _private(service: PublishingService, mode: str = "api", release: str = "api"):
    package = _approved(service, mode, release)
    operation = service.reserve_upload(package.id)
    if mode == "api":
        publication = service.begin_api_upload(operation.id)
    else:
        publication = service.complete_manual_private_upload(
            operation.id,
            "fake-video-1",
            "synthetic-founder",
        )
    status = service.observe_status("private-status", publication.id)
    return package, operation, publication, status


def _public(
    service: PublishingService, fake: FakePublishingAdapter, mode: str = "api", release: str = "api"
):
    package, upload, publication, private = _private(service, mode, release)
    operation = service.reserve_release(publication.id)
    if release == "api":
        service.begin_api_release(operation.id, publication.id)
    fake.remote = replace(fake.remote, privacy="public", observed_at=LATER, public_at=LATER)
    receipt = service.reconcile_public_receipt(
        "receipt-1",
        "public-status",
        publication.id,
        operation.id,
        "synthetic-founder" if release == "manual" else None,
    )
    return package, upload, publication, private, operation, receipt


def test_migration_25_fresh_schema_integrity_and_legacy_path_guard(tmp_path):
    assert [version for version, _ in MIGRATIONS] == list(range(1, 28))
    repo = AtlasRepository(tmp_path / "schema.sqlite")
    assert [
        row[0]
        for row in repo.connection.execute("SELECT version FROM schema_migrations ORDER BY version")
    ] == list(range(1, 28))
    assert repo.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert repo.connection.execute("PRAGMA foreign_key_check").fetchall() == []
    repo.close()
    protected = Path(__file__).resolve().parents[1] / "data" / "atlas.db"
    with pytest.raises(ValueError, match="protected legacy"):
        AtlasRepository(protected)


def test_portable_default_repository_uses_a_separate_dev_path(tmp_path, monkeypatch):
    monkeypatch.delenv("ATLAS_DB_PATH", raising=False)
    monkeypatch.chdir(tmp_path)
    repo = AtlasRepository()
    assert repo.database_path.resolve() == (tmp_path / "data" / "atlas-local.db").resolve()
    assert repo.connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 27
    repo.close()


def test_migration_24_to_25_preserves_historical_data(tmp_path, monkeypatch):
    from project_atlas import persistence

    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:24])
    path = tmp_path / "historical.sqlite"
    old = AtlasRepository(path)
    before = old.connection.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
    old.close()
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS)
    upgraded = AtlasRepository(path)
    assert (
        upgraded.connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        == 27
    )
    assert upgraded.connection.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0] == before
    assert upgraded.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert upgraded.connection.execute("PRAGMA foreign_key_check").fetchall() == []
    upgraded.close()


def test_migration_25_rolls_back_atomically_on_failure(tmp_path, monkeypatch):
    from project_atlas import persistence

    path = tmp_path / "rollback.sqlite"
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:24])
    old = AtlasRepository(path)
    old.close()
    failed = MIGRATIONS[:24] + (
        (25, MIGRATIONS[24][1] + ("INSERT INTO nonexistent_test_table VALUES (1)",)),
    )
    monkeypatch.setattr(persistence, "MIGRATIONS", failed)
    with pytest.raises(sqlite3.OperationalError):
        AtlasRepository(path)
    connection = sqlite3.connect(path)
    assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 24
    assert (
        connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name = 'publishing_packages'"
        ).fetchone()[0]
        == 0
    )
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    connection.close()


def test_package_determinism_immutability_and_artifact_integrity(setup):
    repo, storage, fake, service = setup
    assert canonical_json({"é": 1, "a": 2}) == '{"a":2,"é":1}'
    assert digest({"é": 1, "a": 2}) == digest({"a": 2, "é": 1})
    package = service.prepare_package(
        "package-1", "synthetic-pilot", 1, 1, "fake-artifact", _manifest()
    )
    expected = digest(
        {
            "schema": "publishing-package-v1",
            "pilot_key": "synthetic-pilot",
            "pilot_slot": 1,
            "version": 1,
            "predecessor_id": None,
            "artifact_id": "fake-artifact",
            "artifact_digest": package.artifact_digest,
            "platform": "youtube",
            "channel_id": TARGET_CHANNEL,
            "manifest": _manifest(),
        }
    )
    assert package.package_digest == expected
    with pytest.raises(sqlite3.IntegrityError, match="immutable"), repo.connection:
        repo.connection.execute(
            "UPDATE publishing_packages SET manifest_json = '{}' WHERE id = ?", (package.id,)
        )
    with pytest.raises(ValueError, match="digest mismatch"):
        repo.create_publishing_package(
            "bad", "bad", 2, 1, "fake-artifact", "0" * 64, TARGET_CHANNEL, _manifest()
        )
    storage.path("final/fake-artifact.mp4").write_bytes(b"tampered")
    with pytest.raises(Exception, match="digest"):
        service.prepare_package("bad-2", "bad", 2, 1, "fake-artifact", _manifest())
    assert fake.calls == []


def test_approval_exact_package_revision_revocation_and_readiness_not_authority(setup):
    repo, storage, fake, service = setup
    first = service.prepare_package(
        "package-1", "synthetic-pilot", 1, 1, "fake-artifact", _manifest()
    )
    with pytest.raises(ValueError, match="founder"):
        service.reserve_upload(first.id)
    with pytest.raises(ValueError, match="digest"):
        repo.record_publication_gate_decision(
            "bad", first.id, "0" * 64, "founder", "approve", "api", "api", {"window": "x"}
        )
    service.approve_package("founder-approval-1", first.id, "founder")
    second = service.prepare_package(
        "package-2",
        "synthetic-pilot",
        1,
        2,
        "fake-artifact",
        {**_manifest(), "title": "new"},
        first.id,
    )
    with pytest.raises(ValueError, match="founder"):
        service.reserve_upload(second.id)
    repo.record_publication_gate_decision(
        "reject-2",
        second.id,
        second.package_digest,
        "founder",
        "reject",
        None,
        None,
        {"window": "x"},
    )
    with pytest.raises(ValueError, match="founder"):
        service.reserve_upload(second.id)
    repo.record_publication_gate_decision(
        "revoke-1", first.id, first.package_digest, "founder", "revoke", None, None, {"window": "x"}
    )
    with pytest.raises(ValueError, match="founder"):
        service.reserve_upload(first.id)
    assert "begin" not in fake.calls and "release" not in fake.calls


def test_wrong_channel_and_deterministic_duplicate_reservation(setup):
    repo, storage, fake, service = setup
    package = _approved(service)
    fake.channel = "wrong-synthetic-channel"
    with pytest.raises(ValueError, match="channel"):
        service.reserve_upload(package.id)
    assert "begin" not in fake.calls
    assert repo.connection.execute("SELECT COUNT(*) FROM publication_operations").fetchone()[0] == 0
    fake.channel = TARGET_CHANNEL
    first = service.reserve_upload(package.id)
    second = service.reserve_upload(package.id)
    assert first.id == second.id and first.operation_key == second.operation_key
    assert len(repo.get_publication_operation_events(first.id)) == 1
    with pytest.raises(ValueError, match="differs"):
        repo.reserve_publication_operation(package.id, "upload", "manual", {"attempt": 2})


def test_crash_before_dispatch_retry_and_dispatch_uncertainty_blocks_successor(setup):
    repo, storage, fake, service = setup
    package = _approved(service)
    operation = service.reserve_upload(package.id)
    assert service.reserve_upload(package.id).id == operation.id
    fake.transfer = TransferResult("unknown", TARGET_CHANNEL, reason="response-lost")
    assert service.begin_api_upload(operation.id) is None
    assert repo.get_publication_operation(operation.id).outcome == "unknown"
    assert [event.kind for event in repo.get_publication_operation_events(operation.id)] == [
        "reserved",
        "dispatch_started",
        "outcome_unknown",
    ]
    with pytest.raises(ValueError, match="inspected"):
        service.begin_api_upload(operation.id)
    with pytest.raises(ValueError, match="unresolved"):
        repo.reserve_publication_operation(package.id, "upload", "api", {"attempt": 2})
    fake.remote = replace(fake.remote, metadata_matches=None)
    with pytest.raises(ValueError, match="exact"):
        service.reconcile_upload_identity(operation.id, "fake-video-1", "founder")
    fake.remote = replace(fake.remote, metadata_matches=True, privacy="private")
    publication = service.reconcile_upload_identity(operation.id, "fake-video-1", "founder")
    assert publication.remote_id == "fake-video-1"
    assert publication.identity_source == "founder_manual"
    repo.purge_publication_api_data(publication.id)
    assert repo.get_platform_publication(publication.id).remote_id == "fake-video-1"
    assert repo.get_publication_operation(operation.id).outcome == "succeeded"


def test_revocation_blocks_new_action_but_not_unknown_upload_reconciliation(setup):
    repo, storage, fake, service = setup
    package = _approved(service)
    operation = service.reserve_upload(package.id)
    fake.transfer = TransferResult("unknown", TARGET_CHANNEL, reason="synthetic-response-lost")
    service.begin_api_upload(operation.id)
    repo.record_publication_gate_decision(
        "revocation",
        package.id,
        package.package_digest,
        "founder",
        "revoke",
        None,
        None,
        {"window": "revoked"},
    )
    with pytest.raises(ValueError, match="founder"):
        repo.reserve_publication_operation(package.id, "upload", "api", {"attempt": 2})
    publication = service.reconcile_upload_identity(operation.id, "fake-video-1", "founder")
    assert publication.upload_operation_id == operation.id


def test_partial_transient_failure_and_definitive_successor(setup):
    repo, storage, fake, service = setup
    package = _approved(service)
    op = service.reserve_upload(package.id)
    fake.transfer = TransferResult(
        "partial", TARGET_CHANNEL, acknowledged_bytes=7, session_ref="synthetic-opaque-reference"
    )
    assert service.begin_api_upload(op.id) is None
    fake.resume = TransferResult("transient", TARGET_CHANNEL, reason="synthetic-timeout")
    assert service.inspect_or_resume_upload(op.id) is None
    fake.resume = TransferResult("failed", TARGET_CHANNEL, reason="definitive-synthetic-failure")
    assert service.inspect_or_resume_upload(op.id) is None
    assert repo.get_publication_operation(op.id).outcome == "failed"
    successor = repo.reserve_publication_operation(package.id, "upload", "api", {"attempt": 2})
    assert successor.id != op.id
    events = repo.get_publication_operation_events(op.id)
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    with pytest.raises(sqlite3.IntegrityError, match="immutable"), repo.connection:
        repo.connection.execute(
            "DELETE FROM publication_operation_events WHERE id = ?", (events[0].id,)
        )
    assert "synthetic-opaque-reference" in canonical_json(events[2].provider_evidence)
    assert "synthetic-opaque-reference" not in canonical_json(events[2].evidence)
    assert "session_uri" not in canonical_json(events[2].provider_evidence)


def test_wrong_provider_channel_and_post_dispatch_exception_fail_closed(setup):
    repo, storage, fake, service = setup
    package = _approved(service)
    first = service.reserve_upload(package.id)
    fake.transfer = TransferResult("succeeded", "wrong-synthetic-channel", "wrong-video")
    with pytest.raises(ValueError, match="wrong channel"):
        service.begin_api_upload(first.id)
    assert repo.get_publication_operation(first.id).outcome == "unknown"
    assert repo.connection.execute("SELECT COUNT(*) FROM platform_publications").fetchone()[0] == 0
    assert repo.get_publication_operation_events(first.id)[-1].evidence["reason"] == (
        "wrong-channel-after-dispatch"
    )
    with pytest.raises(ValueError, match="unresolved"):
        repo.reserve_publication_operation(package.id, "upload", "api", {"attempt": 2})

    # A separate disposable DB tests a client exception after dispatch.


def test_post_dispatch_exception_blocks_successor(setup):
    repo, storage, fake, service = setup
    package = _approved(service)
    second = service.reserve_upload(package.id)

    def lost_response(package, operation):
        raise RuntimeError("synthetic response lost after dispatch")

    fake.begin_private_transfer = lost_response
    with pytest.raises(RuntimeError, match="response lost"):
        service.begin_api_upload(second.id)
    assert repo.get_publication_operation(second.id).outcome == "unknown"
    with pytest.raises(ValueError, match="unresolved"):
        repo.reserve_publication_operation(package.id, "upload", "api", {"attempt": 3})


def test_remote_identity_status_and_public_receipt_are_separate(setup):
    repo, storage, fake, service = setup
    package, upload, publication, status = _private(service)
    assert status.privacy == "private"
    with pytest.raises(ValueError, match="Receipt requires"):
        repo.create_publication_receipt(
            "bad", publication.id, upload.id, status.id, NOW, "test", "second"
        )
    with pytest.raises(sqlite3.IntegrityError):
        repo.bind_platform_publication(
            "duplicate",
            package.id,
            upload.id,
            TARGET_CHANNEL,
            publication.remote_id,
            {"synthetic": True},
        )
    fake.remote = replace(
        fake.remote,
        processing="failed",
        observed_at=(datetime.fromisoformat(NOW) + timedelta(minutes=1)).isoformat(),
    )
    service.observe_status("processing-failed", publication.id)
    with pytest.raises(ValueError, match="private-ready"):
        service.reserve_release(publication.id)
    fake.remote = replace(
        fake.remote,
        processing="succeeded",
        metadata_matches=False,
        observed_at=(datetime.fromisoformat(NOW) + timedelta(minutes=2)).isoformat(),
    )
    service.observe_status("metadata-failed", publication.id)
    with pytest.raises(ValueError, match="private-ready"):
        service.reserve_release(publication.id)
    fake.remote = replace(
        fake.remote,
        metadata_matches=True,
        api_locked=True,
        observed_at=(datetime.fromisoformat(NOW) + timedelta(minutes=3)).isoformat(),
    )
    service.observe_status("api-locked", publication.id)
    with pytest.raises(ValueError, match="private-ready"):
        service.reserve_release(publication.id)
    assert (
        repo.connection.execute("SELECT COUNT(*) FROM publication_status_snapshots").fetchone()[0]
        == 4
    )
    assert repo.connection.execute("SELECT COUNT(*) FROM publication_receipts").fetchone()[0] == 0


def test_stale_private_state_blocks_api_release_before_dispatch(setup):
    repo, storage, fake, service = setup
    package, upload, publication, private = _private(service)
    release = service.reserve_release(publication.id)
    fake.remote = replace(fake.remote, processing="failed")
    with pytest.raises(ValueError, match="Current remote state"):
        service.begin_api_release(release.id, publication.id)
    assert [event.kind for event in repo.get_publication_operation_events(release.id)] == [
        "reserved"
    ]
    assert "release" not in fake.calls


def test_manual_identity_mismatch_remains_uncertain_not_a_new_upload(setup):
    repo, storage, fake, service = setup
    package = _approved(service, "manual", "manual")
    operation = service.reserve_upload(package.id)
    fake.remote = replace(fake.remote, metadata_matches=False)
    with pytest.raises(ValueError, match="independent exact"):
        service.complete_manual_private_upload(operation.id, "fake-video-1", "synthetic-founder")
    assert repo.get_publication_operation(operation.id).outcome == "unknown"
    with pytest.raises(ValueError, match="unresolved"):
        repo.reserve_publication_operation(package.id, "upload", "manual", {"attempt": 2})


def test_public_transition_timeout_reconciles_observed_state_without_repeat(setup):
    repo, storage, fake, service = setup
    package, upload, publication, private = _private(service)
    release = service.reserve_release(publication.id)
    fake.release = TransferResult(
        "unknown", TARGET_CHANNEL, publication.remote_id, reason="synthetic-timeout"
    )
    service.begin_api_release(release.id, publication.id)
    assert repo.get_publication_operation(release.id).outcome == "unknown"
    with pytest.raises(ValueError, match="untouched"):
        service.begin_api_release(release.id, publication.id)
    fake.remote = replace(fake.remote, privacy="public", observed_at=LATER, public_at=LATER)
    receipt = service.reconcile_public_receipt(
        "receipt", "public-status", publication.id, release.id
    )
    assert receipt.public_at == LATER and receipt.public_at != publication.identified_at
    assert repo.get_publication_operation(release.id).outcome == "succeeded"
    assert fake.calls.count("release") == 1


def test_revoked_release_still_records_actual_public_receipt(setup):
    repo, storage, fake, service = setup
    package, upload, publication, private = _private(service)
    release = service.reserve_release(publication.id)
    fake.release = TransferResult(
        "unknown", TARGET_CHANNEL, publication.remote_id, reason="synthetic-response-lost"
    )
    service.begin_api_release(release.id, publication.id)
    repo.record_publication_gate_decision(
        "revocation",
        package.id,
        package.package_digest,
        "founder",
        "revoke",
        None,
        None,
        {"window": "revoked"},
    )
    fake.remote = replace(fake.remote, privacy="public", observed_at=LATER, public_at=LATER)
    receipt = service.reconcile_public_receipt(
        "receipt",
        "verified-public-status",
        publication.id,
        release.id,
    )
    assert receipt.gate_decision_id == release.gate_decision_id
    assert repo.get_publication_operation(release.id).outcome == "succeeded"


def test_public_receipt_rejects_private_state_and_private_identification_time(setup):
    repo, storage, fake, service = setup
    package, upload, publication, private = _private(service)
    release = service.reserve_release(publication.id)
    service.begin_api_release(release.id, publication.id)
    with pytest.raises(ValueError, match="Public receipt"):
        service.reconcile_public_receipt("receipt", "still-private", publication.id, release.id)
    fake.remote = replace(
        fake.remote, privacy="public", observed_at=LATER, public_at=publication.identified_at
    )
    with pytest.raises(ValueError, match="Private identification"):
        service.reconcile_public_receipt("receipt", "public-status", publication.id, release.id)
    assert repo.connection.execute("SELECT COUNT(*) FROM publication_receipts").fetchone()[0] == 0


def test_manual_studio_routes_are_attested_not_claimed_as_conveyor_execution(setup):
    repo, storage, fake, service = setup
    package, upload, publication, private, release, receipt = _public(
        service,
        fake,
        "manual",
        "manual",
    )
    assert upload.execution_mode == "manual" and release.execution_mode == "manual"
    assert receipt.execution_mode == "manual"
    assert "manual-attestation" in receipt.timestamp_source
    assert "begin" not in fake.calls and "release" not in fake.calls


def test_manual_public_state_uncertainty_reconciles_same_operation(setup):
    repo, storage, fake, service = setup
    package, upload, publication, private = _private(service, "manual", "manual")
    release = service.reserve_release(publication.id)
    with pytest.raises(ValueError, match="Public receipt"):
        service.reconcile_public_receipt(
            "receipt", "unverified-status", publication.id, release.id, "synthetic-founder"
        )
    assert repo.get_publication_operation(release.id).outcome == "unknown"
    fake.remote = replace(fake.remote, privacy="public", observed_at=LATER, public_at=LATER)
    receipt = service.reconcile_public_receipt(
        "receipt", "verified-status", publication.id, release.id, "synthetic-founder"
    )
    assert receipt.release_operation_id == release.id
    assert repo.get_publication_operation(release.id).outcome == "succeeded"
    assert "release" not in fake.calls


def test_performance_purge_and_learning_linkage(setup):
    repo, storage, fake, service = setup
    fake.remote = replace(fake.remote, provider_payload={"synthetic_detail": "purge-me"})
    package, upload, publication, private, release, receipt = _public(service, fake)
    public_time = datetime.fromisoformat(receipt.public_at)
    due = {
        key: (public_time + offset).isoformat()
        for key, offset in {
            "24h": timedelta(hours=24),
            "72h": timedelta(hours=72),
            "7d": timedelta(days=7),
            "28d": timedelta(days=28),
        }.items()
    }
    fake.performance = replace(
        fake.performance,
        due_at=due["24h"],
        collected_at=due["24h"],
        retention={
            "availability": "available",
            "points": [
                {"elapsedVideoTimeRatio": 0.0, "audienceWatchRatio": 1.1},
                {"elapsedVideoTimeRatio": 1.0, "audienceWatchRatio": 0.2},
            ],
        },
    )
    snapshot = service.collect_performance("snapshot-24h", receipt.id, "24h")
    assert snapshot.metrics["views"]["value"] == 12
    assert snapshot.metrics["likes"] == {
        "value": None,
        "availability": "not_returned",
        "reason": "requested-but-absent",
        "unit": None,
        "requested": True,
    }
    assert snapshot.requested_coverage != snapshot.returned_coverage
    assert snapshot.retention["points"][0]["audienceWatchRatio"] == 1.1
    assert "engagement_rate" not in snapshot.metrics
    for checkpoint in ("72h", "7d", "28d"):
        fake.performance = replace(
            fake.performance,
            maturity="partial",
            returned_coverage=None,
            metrics={"views": None},
            availability={"views": "not_returned"},
            due_at=due[checkpoint],
            collected_at=due[checkpoint],
        )
        service.collect_performance(f"snapshot-{checkpoint}", receipt.id, checkpoint)
    assert repo.connection.execute("SELECT COUNT(*) FROM performance_snapshots").fetchone()[0] == 4
    assert (
        len({row[0] for row in repo.connection.execute("SELECT due_at FROM performance_snapshots")})
        == 4
    )
    assessment = service.assess(
        "assessment-1",
        [snapshot.id],
        "opening",
        "uncertain",
        "One item is a hypothesis only",
        "low",
        ["sample size"],
        "Observe another item",
        "hypothesis",
        "analyst",
    )
    assert assessment.evidence_snapshot_ids == (snapshot.id,)
    assert assessment.publication_ids == (publication.id,)
    application = repo.record_learning_application(
        "application-1",
        assessment.id,
        "script",
        "fake-script",
        "future-decision",
        {"synthetic": True},
        "analyst",
    )
    assert application.target_kind == "script" and application.target_id == "fake-script"
    before = repo.get_publication_status(private.id).observation_digest
    assert repo.get_publication_status(private.id).provider_payload is not None
    repo.purge_publication_api_data(publication.id)
    assert before is not None
    assert repo.get_publication_status(private.id).observation_digest is None
    assert repo.get_publication_status(private.id).provider_payload is None
    assert repo.get_publication_status(private.id).provider_purged_at is not None
    assert repo.get_performance_snapshot(snapshot.id).metrics is None
    assert repo.get_performance_snapshot(snapshot.id).retention is None
    assert repo.get_performance_snapshot(snapshot.id).provider_payload is None
    assert repo.get_performance_snapshot(snapshot.id).provider_purged_at is not None
    assert repo.get_platform_publication(publication.id).remote_id is None
    assert repo.get_platform_publication(publication.id).binding_digest is None
    assert repo.get_publication_receipt(receipt.id).public_at is None
    assert repo.get_publication_receipt(receipt.id).receipt_digest is None
    api_event = next(
        event
        for event in repo.get_publication_operation_events(upload.id)
        if event.kind == "remote_identity_observed"
    )
    assert api_event.provider_evidence is None and api_event.provider_purged_at is not None
    assert repo.get_publication_operation(upload.id).outcome == "succeeded"
    assert repo.get_learning_assessment(assessment.id).publication_ids == (publication.id,)
    assert repo.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert repo.connection.execute("PRAGMA foreign_key_check").fetchall() == []
    with pytest.raises(sqlite3.IntegrityError, match="immutable"), repo.connection:
        repo.connection.execute(
            "UPDATE performance_snapshots SET metrics_json = '{}' WHERE id = ?", (snapshot.id,)
        )


def test_provenance_rejects_raw_secret_or_session_material(setup):
    repo, storage, fake, service = setup
    package = _approved(service)
    op = service.reserve_upload(package.id)
    with pytest.raises(ValueError, match="Secret/session"):
        repo.append_publication_operation_event(
            op.id, "dispatch_started", "test", {"session_url": "synthetic-hidden"}
        )
    with pytest.raises(ValueError, match="Secret/session"):
        repo.append_publication_operation_event(
            op.id, "dispatch_started", "test", {"resumableURL": "synthetic-hidden"}
        )
    fake.transfer = TransferResult(
        "partial",
        TARGET_CHANNEL,
        acknowledged_bytes=4,
        session_ref="https://synthetic.invalid/session",
    )
    with pytest.raises(ValueError, match="opaque"):
        service.begin_api_upload(op.id)
    assert repo.get_publication_operation(op.id).outcome == "unknown"
    rows = repo.connection.execute(
        "SELECT evidence_json FROM publication_operation_events"
    ).fetchall()
    assert all("synthetic.invalid" not in row[0] for row in rows)


def test_london_week_conflicts_revision_retry_and_expired_exact_time(setup):
    repo, storage, fake, service = setup
    package, upload, publication, private = _private(service)
    release = service.reserve_release(publication.id)
    assert package.pilot_week == repo.get_publishing_package(package.id).pilot_week
    service.clock = lambda: REVIEW_NOW + timedelta(minutes=2)
    assert service.reserve_release(publication.id).id == release.id  # same key, no new dispatch
    with pytest.raises(ValueError, match="expired"):
        service.begin_api_release(release.id, publication.id)
    assert repo.get_publication_operation_events(release.id)[-1].kind == "reserved"

    second_manifest = _manifest()
    second_manifest["pilot_slot"] = 2
    second = service.prepare_package(
        "package-2", "another-pilot", 2, 1, "fake-artifact", second_manifest
    )
    service.approve_package("approval-2", second.id, "founder")
    intent = {"pilot_slot": 2, "timing": second.manifest["publication_timing"]}
    with pytest.raises(ValueError, match="active approved slot"):
        repo.reserve_publication_operation(second.id, "release", "api", intent, service.clock())
    with pytest.raises(ValueError, match="pilot week"):
        repo.reserve_publication_operation(second.id, "release", "api", intent, REVIEW_NOW)

    revision = service.prepare_package(
        "package-1-v2", "synthetic-pilot", 1, 2, "fake-artifact", _manifest(), package.id
    )
    service.approve_package("approval-v2", revision.id, "founder")
    with pytest.raises(ValueError, match="pilot week"):
        repo.reserve_publication_operation(
            revision.id,
            "release",
            "api",
            {"pilot_slot": 1, "timing": revision.manifest["publication_timing"]},
            REVIEW_NOW,
        )


def test_manual_window_expires_without_catchup(setup):
    repo, storage, fake, service = setup
    package, upload, publication, private = _private(service, "manual", "manual")
    service.clock = lambda: REVIEW_NOW - timedelta(minutes=3)
    with pytest.raises(ValueError, match="active approved slot"):
        service.reserve_release(publication.id)
    service.clock = lambda: REVIEW_NOW
    release = service.reserve_release(publication.id)
    service.clock = lambda: REVIEW_NOW + timedelta(minutes=3)
    with pytest.raises(ValueError, match="Manual public window"):
        service.reconcile_public_receipt(
            "late", "late-status", publication.id, release.id, "founder"
        )
    assert repo.get_publication_operation_events(release.id)[-1].kind == "reserved"
    assert "release" not in fake.calls


def test_receipt_week_uniqueness_is_independent_of_service(setup):
    repo, storage, fake, service = setup
    package, upload, publication, private, release, receipt = _public(service, fake)
    with pytest.raises(sqlite3.IntegrityError, match="channel pilot week"), repo.connection:
        repo.connection.execute(
            "INSERT INTO publication_receipts SELECT 'other-receipt', 'other-publication', "
            "package_id, gate_decision_id, 'other-release', 'other-status', execution_mode, "
            "channel_id, pilot_week, public_at, timestamp_source, timestamp_precision, "
            "first_public_observed_at, receipt_digest, created_at, NULL "
            "FROM publication_receipts WHERE id = ?",
            (receipt.id,),
        )
    assert repo.connection.execute("SELECT COUNT(*) FROM publication_receipts").fetchone()[0] == 1


def test_scalar_availability_and_raw_retention_append_only(setup):
    repo, storage, fake, service = setup
    package, upload, publication, private, release, receipt = _public(service, fake)
    curve = {
        "availability": "available",
        "points": [
            {"elapsedVideoTimeRatio": 1.0, "audienceWatchRatio": 0.3},
            {"elapsedVideoTimeRatio": 0.0, "audienceWatchRatio": 1.25},
            {"elapsedVideoTimeRatio": 0.5, "audienceWatchRatio": 0.6},
        ],
    }
    fake.performance = replace(
        fake.performance,
        requested_coverage={"metrics": ["likes", "views", "engagedViews"]},
        returned_coverage={"metrics": ["likes", "engagedViews"]},
        metrics={"likes": 0, "engagedViews": None},
        availability={"engagedViews": "immature"},
        missing_reasons={"engagedViews": "reporting-period-immature"},
        retention=curve,
    )
    first = service.collect_performance("metrics-first", receipt.id, "24h")
    assert first.metrics["likes"]["value"] == 0
    assert first.metrics["views"]["availability"] == "not_returned"
    assert first.metrics["views"]["value"] is None
    assert first.metrics["engagedViews"]["availability"] == "immature"
    assert first.retention["points"][0]["audienceWatchRatio"] == 1.25
    assert [point["elapsedVideoTimeRatio"] for point in first.retention["points"]] == [
        0.0,
        0.5,
        1.0,
    ]
    fake.performance = replace(
        fake.performance,
        metrics={"likes": 0, "views": 12, "engagedViews": 2},
        availability={},
        missing_reasons=None,
        retention={"availability": "immature", "reason": "not-yet-reported", "points": None},
    )
    later = service.collect_performance("metrics-later", receipt.id, "72h")
    assert later.metrics["views"]["value"] == 12
    assert later.retention["availability"] == "immature"
    assert repo.get_performance_snapshot(first.id).metrics["views"]["value"] is None
    for bad in (
        [
            {"elapsedVideoTimeRatio": 0.5, "audienceWatchRatio": 1},
            {"elapsedVideoTimeRatio": 0.5, "audienceWatchRatio": 2},
        ],
        [{"elapsedVideoTimeRatio": 1.1, "audienceWatchRatio": 1}],
    ):
        fake.performance = replace(
            fake.performance, retention={"availability": "available", "points": bad}
        )
        with pytest.raises(ValueError, match="retention|Retention"):
            service.collect_performance("bad-retention", receipt.id, "7d")


def test_provider_purge_preserves_manual_founder_identity(setup):
    repo, storage, fake, service = setup
    fake.remote = replace(fake.remote, provider_payload={"synthetic_detail": "delete-me"})
    package, upload, publication, private, release, receipt = _public(
        service, fake, "manual", "manual"
    )
    assert publication.identity_source == "founder_manual"
    founder_event = next(
        event
        for event in repo.get_publication_operation_events(upload.id)
        if event.kind == "remote_identity_observed"
    )
    assert founder_event.evidence["remote_id"] == publication.remote_id
    repo.purge_publication_api_data(publication.id)
    assert repo.get_platform_publication(publication.id).remote_id == publication.remote_id
    assert repo.get_publication_operation_events(upload.id)[2].evidence == founder_event.evidence
    assert repo.get_publication_status(private.id).provider_payload is None
    assert repo.get_publication_status(private.id).privacy is None
    assert repo.get_publication_receipt(receipt.id).public_at is None
    assert repo.connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_unbound_provider_operation_evidence_is_purgeable(setup):
    repo, storage, fake, service = setup
    package = _approved(service)
    operation = service.reserve_upload(package.id)
    fake.transfer = TransferResult(
        "partial", TARGET_CHANNEL, acknowledged_bytes=7, session_ref="opaque-disposable-ref"
    )
    assert service.begin_api_upload(operation.id) is None
    event = repo.get_publication_operation_events(operation.id)[-1]
    assert event.provider_evidence["protected_session_ref"] == "opaque-disposable-ref"
    repo.purge_provider_operation_evidence(operation.id)
    event = repo.get_publication_operation_events(operation.id)[-1]
    assert event.provider_evidence is None
    assert event.provider_purged_at is not None
    row = repo.connection.execute(
        "SELECT provider_evidence_digest FROM publication_operation_events WHERE id = ?",
        (event.id,),
    ).fetchone()
    assert row[0] is None
    assert repo.get_publication_operation(operation.id).outcome == "pending"


def test_unauthenticated_web_has_no_publishing_mutation_surface():
    source = (Path(__file__).resolve().parents[1] / "src" / "project_atlas" / "web.py").read_text(
        encoding="utf-8"
    )
    assert "publishing_packages" not in source
    assert "PublicationOperation" not in source
    assert "/publish" not in source
