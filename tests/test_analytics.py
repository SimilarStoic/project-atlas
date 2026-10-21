"""YouTube Analytics (Option B), offline: migration 32, governance, retention and collection.

Disposable databases, fixtures and fakes only: no credential, network or provider access.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from project_atlas import persistence, publishing_cli, youtube_consent
from project_atlas.media import LocalMediaStorage
from project_atlas.persistence import MIGRATIONS, AtlasRepository
from project_atlas.production_backup import database_sha256
from project_atlas.publishing import PublishingService
from project_atlas.publishing_analytics import (
    ANALYTICS_METRICS,
    checkpoint_window,
    maturity,
    pacific_date,
    pacific_midnight_utc,
    parse_metrics_report,
    window_due_at,
)
from project_atlas.publishing_schema import MIGRATION_32
from project_atlas.publishing_state import TARGET_CHANNEL
from project_atlas.youtube_adapter import YouTubeAnalyticsAdapter, YouTubeObservationBlocked
from project_atlas.youtube_consent import (
    ANALYTICS_KEYRING_ACCOUNT,
    UPLOAD_KEYRING_ACCOUNT,
    authorize_analytics,
)
from project_atlas.youtube_preflight import (
    ANALYTICS_SCOPES,
    KEYRING_ACCOUNT,
    YOUTUBE_READONLY_SCOPE,
    PreflightBlocked,
)
from tests.test_publishing import FakePublishingAdapter, _artifact, _public
from tests.test_publishing_on_demand import (  # noqa: F401 - pytest fixtures
    T0,
    _cli,
    _cli_publication,
    _fingerprint,
    _published,
    _schema,
    cli_world,
    world,
)
from tests.test_youtube_adapter import Credentials, Provider
from tests.test_youtube_consent import CountingChannels
from tests.test_youtube_upload import CLOCK, FakeStore, governance_for

RETENTION = {
    "columnHeaders": [
        {"name": "elapsedVideoTimeRatio", "columnType": "DIMENSION", "dataType": "FLOAT"},
        {"name": "audienceWatchRatio", "columnType": "METRIC", "dataType": "FLOAT"},
    ],
    "rows": [[0.0, 1.0], [0.5, 0.62], [1.0, 0.31]],
}
VALUES = {name: index + 1 for index, name in enumerate(ANALYTICS_METRICS)}


def _report(values: dict, order: list[str] | None = None) -> dict:
    names = order or list(values)
    return {
        "columnHeaders": [
            {"name": name, "columnType": "METRIC", "dataType": "INTEGER"} for name in names
        ],
        "rows": [[values[name] for name in names]],
    }


class FakeAnalytics(FakePublishingAdapter):
    """Synthetic Analytics responses; records every request."""

    def __init__(self) -> None:
        super().__init__()
        self.existence: str | Exception = "exists"
        self.values = dict(VALUES)
        self.order = list(reversed(ANALYTICS_METRICS))  # Never assume column order.
        self.retention: dict = RETENTION
        self.fail_ends: set[date] = set()
        self.requests: list[tuple] = []

    def video_existence(self, remote_id):
        self.calls.append("existence")
        if isinstance(self.existence, Exception):
            raise self.existence
        return self.existence

    def analytics_report(self, remote_id, start, end, metrics):
        self.requests.append(("report", remote_id, start, end, tuple(metrics)))
        if end in self.fail_ends:
            raise YouTubeObservationBlocked("youtube_request_failed")
        names = [name for name in self.order if name in self.values]
        return _report(self.values, names)

    def analytics_retention(self, remote_id, start, end):
        self.requests.append(("retention", remote_id, start, end))
        return self.retention


@pytest.fixture
def analytics(world):  # noqa: F811 - the imported fixture
    """A P11-type receipt (API-published, reconciled) and a service on the fake adapter."""

    repo, storage, _fake, service, clock, _artifact_id = world
    _package, publication, _public_at = _published(world)
    receipt = service.reconcile_scheduled_publication("r-1", "s-1", publication.id)
    fake = FakeAnalytics()
    return repo, PublishingService(repo, storage, fake, clock), fake, clock, receipt


def _count(repo, sql, *args) -> int:
    return repo.connection.execute(sql, args).fetchone()[0]


def _live_analytics(repo, receipt_id) -> int:
    return _count(
        repo,
        "SELECT COUNT(*) FROM performance_snapshots WHERE receipt_id = ? "
        "AND provider_purged_at IS NULL",
        receipt_id,
    )


# --- Pacific-time day windows -------------------------------------------------------------------


def test_pacific_dates_follow_the_us_daylight_saving_rule() -> None:
    assert pacific_date(datetime(2026, 3, 8, 9, 59, tzinfo=UTC)) == date(2026, 3, 8)
    assert pacific_midnight_utc(date(2026, 10, 18)) == datetime(2026, 10, 18, 7, tzinfo=UTC)
    assert pacific_midnight_utc(date(2026, 12, 1)) == datetime(2026, 12, 1, 8, tzinfo=UTC)
    # 06:59 UTC on 17 October is still 16 October in Pacific time (PDT).
    assert pacific_date(datetime(2026, 10, 17, 6, 59, tzinfo=UTC)) == date(2026, 10, 16)
    assert checkpoint_window("2026-10-16T17:45:28Z", "24h") == (
        date(2026, 10, 16),
        date(2026, 10, 17),
    )
    assert checkpoint_window("2026-10-16T17:45:28Z", "28d")[1] == date(2026, 11, 13)
    assert checkpoint_window("2026-10-05", "7d") == (date(2026, 10, 5), date(2026, 10, 12))
    assert window_due_at(date(2026, 10, 17)) == datetime(2026, 10, 18, 7, tzinfo=UTC)


# --- Migration 32 -------------------------------------------------------------------------------


def test_migration_32_is_additive_and_preserves_every_row(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:31])
    path = tmp_path / "v31.sqlite"
    repo = AtlasRepository(path)
    storage = LocalMediaStorage(tmp_path / "media")
    _artifact(repo, storage)
    fake = FakePublishingAdapter()
    _public(PublishingService(repo, storage, fake), fake, "manual", "manual")
    before_schema = _schema(repo.connection)
    repo.close()
    before_rows = _fingerprint(path)
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS)
    upgraded = AtlasRepository(path)
    try:
        connection = upgraded.connection
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 32
        after_rows = _fingerprint(path)
        assert {k: v for k, v in after_rows.items() if k not in {"schema_migrations"}} == {
            **{k: v for k, v in before_rows.items() if k != "schema_migrations"},
            "analytics_video_checks": after_rows["analytics_video_checks"],
        }
        assert after_rows["analytics_video_checks"][0] == 0
        after_schema = _schema(connection)
        assert {k: v for k, v in after_schema.items() if k in before_schema} == before_schema
        assert set(after_schema) - set(before_schema) == {
            ("table", "analytics_video_checks"),
            ("index", "idx_analytics_video_checks_receipt"),
            ("trigger", "analytics_video_checks_immutable_update"),
            ("trigger", "analytics_video_checks_immutable_delete"),
        }
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        upgraded.close()


def test_failed_migration_32_rolls_back_to_31(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:31])
    path = tmp_path / "atomic.sqlite"
    repo = AtlasRepository(path)
    try:
        schema_before = _schema(repo.connection)
        broken = MIGRATIONS[:31] + ((32, MIGRATION_32[1] + ("INVALID SQL",)),)
        with pytest.raises(sqlite3.DatabaseError):
            repo.apply_migrations(broken)
        connection = repo.connection
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 31
        assert _schema(connection) == schema_before
    finally:
        repo.close()


def test_repository_open_applies_migration_32_but_live_cli_refuses_below_head(
    tmp_path, monkeypatch, capsys
) -> None:
    """Deployment boundary: any AtlasRepository open (e.g. maintenance) applies pending 32."""

    for name in ("ATLAS_DB_PATH", "ATLAS_MEDIA_STORAGE_ROOT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:31])
    db = tmp_path / "v31.sqlite"
    AtlasRepository(db).close()
    (tmp_path / "media").mkdir()
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS)
    before = database_sha256(db)
    code = publishing_cli.main(
        [
            "approve",
            "p",
            "--package-digest",
            "0" * 64,
            "--decision-id",
            "d",
            "--founder-actor",
            "f",
            "--db",
            str(db),
            "--media",
            str(tmp_path / "media"),
            "--expect-db-sha256",
            before,
            "--dry-run",
        ]
    )
    assert code == 2 and "migration 31, this code at 32" in capsys.readouterr().err
    assert database_sha256(db) == before
    opened = AtlasRepository(db)  # Opening the repository is what applies the migration.
    try:
        assert (
            opened.connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
            == 32
        )
    finally:
        opened.close()


def test_existence_checks_are_append_only_except_provider_purge(analytics) -> None:
    repo, service, _fake, _clock, receipt = analytics
    service.verify_analytics_video("c-1", receipt.id)
    for statement in (
        "UPDATE analytics_video_checks SET outcome = 'missing'",
        "UPDATE analytics_video_checks SET checked_at = 'x'",
        "DELETE FROM analytics_video_checks",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="immutable"), repo.connection:
            repo.connection.execute(statement)
    with pytest.raises(sqlite3.IntegrityError), repo.connection:
        repo.connection.execute(
            "INSERT INTO analytics_video_checks VALUES ('c-2', ?, 'now', 'gone', 'now', NULL)",
            (receipt.id,),
        )
    repo._purge_analytics_video_check("c-1")
    assert repo.latest_analytics_video_check(receipt.id)["outcome"] is None


# --- Disabled by default ------------------------------------------------------------------------


def test_analytics_is_disabled_by_default() -> None:
    assert youtube_consent.ANALYTICS_ENABLED is False
    with pytest.raises(YouTubeObservationBlocked, match="analytics_disabled"):
        YouTubeAnalyticsAdapter.from_client_config(Path("c.json"), Path("."), None)


@pytest.mark.parametrize(
    "command", [["analytics-check", "r-1", "--check-id", "c-1"], ["collect-analytics", "r-1"]]
)
def test_disabled_cli_commands_refuse_before_any_work(
    cli_world, capsys, command  # noqa: F811
) -> None:
    db, media, _metadata, root = cli_world
    before = database_sha256(db)
    code = publishing_cli.main(
        [
            *command,
            "--client-config",
            str(root / "c.json"),
            "--consent-state",
            str(root / "s.json"),
            "--db",
            str(db),
            "--media",
            str(media),
            "--expect-db-sha256",
            before,
            "--backup-root",
            str(root / "backups"),
        ]
    )
    assert code == 2 and "Analytics is disabled" in capsys.readouterr().err
    assert database_sha256(db) == before and not (root / "backups").exists()


def test_disabled_authorization_refuses_before_any_consent_or_api(tmp_path) -> None:
    store = FakeStore()

    class NoCalls:
        def authenticated_channel_ids(self, credentials):
            pytest.fail("No API call while Analytics is disabled.")

    code = authorize_analytics(
        tmp_path / "client.json",
        tmp_path / "result.json",
        tmp_path / "consent.json",
        store=store,
        channel_client=NoCalls(),
    )
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert code == 2 and result["error_category"] == "analytics_disabled"
    assert store.saved == [] and result["stored"] is False


def test_disabled_governance_behaves_exactly_as_before(tmp_path) -> None:
    stores = {KEYRING_ACCOUNT: FakeStore("ro"), UPLOAD_KEYRING_ACCOUNT: FakeStore("up")}
    governance = governance_for(None, tmp_path, stores=stores)
    governance.registry.mark_reconfirmed("readonly", CLOCK)
    assert set(governance.registry.status(CLOCK)["authorizations"]) == {"readonly", "upload"}
    assert governance.active_kinds() == ["readonly", "upload"]
    assert governance.present_kinds() == ["readonly", "upload"]

    class NoData:
        def purge_all_youtube_api_data(self):
            return {}

        def purge_stale_youtube_api_data(self, cutoff):  # The pre-Analytics signature.
            return {}

    governance.repository = NoData()
    governance.handle_definitive("upload")
    assert governance.registry.last_reconfirmed("readonly") == CLOCK  # Others untouched.
    assert governance.startup()["stale_purged"] == {}


def test_revocation_covers_a_stored_analytics_credential_even_when_disabled(tmp_path) -> None:
    stores = {
        KEYRING_ACCOUNT: FakeStore("ro"),
        UPLOAD_KEYRING_ACCOUNT: FakeStore("up"),
        ANALYTICS_KEYRING_ACCOUNT: FakeStore("an"),
    }

    class NoData:
        def purge_all_youtube_api_data(self):
            return {}

    governance = governance_for(NoData(), tmp_path, stores=stores)
    result = governance.revoke()
    assert set(result["authorizations"]) == {"readonly", "upload", "analytics"}
    assert all(store.token is None for store in stores.values())


# --- Video-existence evidence and retention -----------------------------------------------------


@pytest.mark.parametrize("outcome", ["exists", "missing", "inaccessible"])
def test_existence_check_records_its_outcome(analytics, outcome) -> None:
    repo, service, fake, _clock, receipt = analytics
    fake.existence = outcome
    check = service.verify_analytics_video("c-1", receipt.id)
    assert (check["id"], check["outcome"]) == ("c-1", outcome)


def test_transient_or_authorization_failure_records_no_existence_check(analytics) -> None:
    repo, service, fake, _clock, receipt = analytics
    fake.existence = YouTubeObservationBlocked("authorization_unusable")
    with pytest.raises(YouTubeObservationBlocked):
        service.verify_analytics_video("c-1", receipt.id)
    assert repo.latest_analytics_video_check(receipt.id) is None


def test_missing_or_inaccessible_video_deletes_its_analytics_at_once(analytics) -> None:
    repo, service, fake, clock, receipt = analytics
    clock.now = datetime(2026, 11, 2, 12, tzinfo=UTC)
    service.verify_analytics_video("c-1", receipt.id)
    assert service.collect_analytics(receipt.id)
    assert _live_analytics(repo, receipt.id) == 3
    fake.existence = "missing"
    service.verify_analytics_video("c-2", receipt.id)
    assert _live_analytics(repo, receipt.id) == 0
    with pytest.raises(ValueError, match="still exists"):
        service.collect_analytics(receipt.id)


def _collected(analytics):
    repo, service, _fake, clock, receipt = analytics
    clock.now = datetime(2026, 11, 2, 12, tzinfo=UTC)
    service.verify_analytics_video("c-1", receipt.id)
    service.collect_analytics(receipt.id)
    return repo, service, clock, receipt


@pytest.mark.parametrize(
    ("authorized_days_ago", "check_days_ago", "kept"),
    [
        (5, 5, True),  # Authorization and existence both re-verified within 30 days.
        (40, 5, False),  # Authorization not re-verified.
        (None, 5, False),  # Never authorized, or Analytics disabled since.
        (5, 40, False),  # Existence not re-checked.
    ],
)
def test_analytics_retention_beyond_30_days_needs_fresh_authorization_and_existence(
    analytics, authorized_days_ago, check_days_ago, kept
) -> None:
    from dataclasses import replace

    repo, service, clock, receipt = _collected(analytics)
    fake = analytics[2]
    later = clock.now + timedelta(days=60)  # Snapshots collected long ago.
    clock.now = later - timedelta(days=5)
    # A P11-type (API) identity is kept only by a passed status observation (existing rule).
    fake.remote = replace(fake.remote, remote_id="od-video-1", observed_at=clock.now.isoformat())
    assert service.observe_status("s-2", receipt.publication_id).verification == "passed"
    clock.now = later - timedelta(days=check_days_ago)
    service.verify_analytics_video("c-2", receipt.id)
    authorized = (
        None if authorized_days_ago is None else later - timedelta(days=authorized_days_ago)
    )
    kwargs = {} if authorized is None else {"analytics_authorized_at": authorized}
    repo.purge_stale_youtube_api_data(later - timedelta(days=30), **kwargs)
    assert (_live_analytics(repo, receipt.id) == 3) is kept


def test_governance_passes_the_analytics_authorization_time_only_once_authorized(
    analytics, tmp_path
) -> None:
    repo, _service, clock, receipt = _collected(analytics)
    governance = governance_for(repo, tmp_path)
    governance.clock = lambda: clock.now + timedelta(days=1)
    governance.registry.mark_reconfirmed("analytics", clock.now)
    governance.enforce_stale_data()
    assert _live_analytics(repo, receipt.id) == 3  # Fresh: kept.
    governance.registry.clear("analytics")  # e.g. Analytics turned off and not re-verified.
    governance.enforce_stale_data()
    assert _live_analytics(repo, receipt.id) == 0  # Expiry still enforced.


def test_existence_checks_follow_the_30_day_rule(analytics) -> None:
    repo, _service, clock, receipt = _collected(analytics)
    counts = repo.purge_stale_youtube_api_data(clock.now + timedelta(days=1))
    assert counts["analytics_video_checks"] == 1
    assert repo.latest_analytics_video_check(receipt.id)["outcome"] is None
    assert _live_analytics(repo, receipt.id) == 0


def test_delete_data_clears_existence_checks_and_analytics(analytics, tmp_path) -> None:
    repo, _service, _clock, receipt = _collected(analytics)
    result = governance_for(repo, tmp_path).delete_data()
    assert result["purged"]["analytics_video_checks"] == 1
    assert repo.latest_analytics_video_check(receipt.id)["outcome"] is None
    assert _live_analytics(repo, receipt.id) == 0


def test_retrospective_receipts_support_existence_checks(tmp_path) -> None:
    """P8/P9-type founder-attested identities are checked the same way (never observed)."""

    from dataclasses import replace as dataclass_replace
    from hashlib import sha256

    from project_atlas.publishing_retrospective import p8_release, record_release
    from tests.test_publishing_retrospective import _chain, _production

    repo = AtlasRepository(tmp_path / "retro.sqlite")
    storage = LocalMediaStorage(tmp_path / "media")
    try:
        content = b"synthetic p8 final mp4"
        _chain(repo, storage, "p8", "production-8-attempt-2-artifact-2", content, 700)
        _production(repo, "production-8-attempt-2", "p8-plan", "production-8-attempt-2-artifact-2")
        release = dataclass_replace(p8_release(), artifact_sha256=sha256(content).hexdigest())
        record_release(repo, tmp_path / "media", release)
        receipt_id = repo.connection.execute("SELECT id FROM publication_receipts").fetchone()[0]
        fake = FakeAnalytics()
        service = PublishingService(repo, storage, fake, lambda: datetime(2026, 11, 1, tzinfo=UTC))
        assert service.verify_analytics_video("c-1", receipt_id)["outcome"] == "exists"
        assert "existence" in fake.calls
    finally:
        repo.close()


def test_purged_identity_cannot_be_checked_or_collected(analytics) -> None:
    repo, service, _fake, _clock, receipt = analytics
    repo.purge_publication_api_data(receipt.publication_id)
    for call in (
        lambda: service.verify_analytics_video("c-1", receipt.id),
        lambda: service.collect_analytics(receipt.id),
    ):
        with pytest.raises(ValueError, match="Purged provider binding"):
            call()


# --- Collection ---------------------------------------------------------------------------------


def test_collection_records_due_checkpoints_by_returned_column_name(analytics) -> None:
    repo, service, fake, clock, receipt = analytics
    clock.now = datetime(2026, 10, 31, 12, tzinfo=UTC)  # 24h and 72h due; 7d due 1 November.
    service.verify_analytics_video("c-1", receipt.id)
    snapshots = service.collect_analytics(receipt.id)
    assert [item.checkpoint for item in snapshots] == ["24h", "72h"]
    first = snapshots[0]
    assert {name: value["value"] for name, value in first.metrics.items()} == VALUES
    assert first.requested_coverage == {
        "metrics": list(ANALYTICS_METRICS),
        "startDate": "2026-10-24",
        "endDate": "2026-10-25",
        "timezone": "America/Los_Angeles",
    }
    assert first.api_context["schema"] == "youtube-analytics-reports-v1"
    assert first.retention["availability"] == "available"
    assert [item.maturity for item in snapshots] == ["mature", "mature"]
    assert fake.requests[0] == (
        "report",
        "od-video-1",
        date(2026, 10, 24),
        date(2026, 10, 25),
        ANALYTICS_METRICS,
    )


def test_missing_metric_or_retention_is_partial_never_mature(analytics) -> None:
    repo, service, fake, clock, receipt = analytics
    clock.now = datetime(2026, 10, 31, 12, tzinfo=UTC)
    service.verify_analytics_video("c-1", receipt.id)
    del fake.values["subscribersLost"]
    fake.retention = {"columnHeaders": RETENTION["columnHeaders"], "rows": []}
    snapshot = service.collect_analytics(receipt.id)[0]
    assert snapshot.maturity == "partial"
    assert snapshot.metrics["subscribersLost"]["availability"] == "not_returned"
    assert snapshot.metrics["subscribersLost"]["reason"] == "column-not-returned"
    assert snapshot.retention == {
        "availability": "unavailable",
        "reason": "no-retention-rows",
        "points": None,
    }


def test_immature_attempts_are_recollected_and_a_mature_one_is_never_repeated(analytics) -> None:
    repo, service, fake, clock, receipt = analytics
    clock.now = datetime(2026, 10, 27, 12, tzinfo=UTC)  # 24h due, but within the data lag.
    service.verify_analytics_video("c-1", receipt.id)
    [first] = service.collect_analytics(receipt.id)
    assert (first.id, first.maturity) == (f"analytics-{receipt.id}-24h-1", "immature")
    clock.now = datetime(2026, 10, 29, 8, tzinfo=UTC)  # 24h past the lag; 72h now due.
    second, third = service.collect_analytics(receipt.id)
    assert (second.id, second.maturity) == (f"analytics-{receipt.id}-24h-2", "mature")
    assert (third.id, third.maturity) == (f"analytics-{receipt.id}-72h-1", "immature")
    clock.now = datetime(2026, 10, 29, 9, tzinfo=UTC)
    requests = len(fake.requests)
    [fourth] = service.collect_analytics(receipt.id)  # The mature 24h is never repeated.
    assert fourth.id == f"analytics-{receipt.id}-72h-2"
    assert [request[3] for request in fake.requests[requests:]] == [date(2026, 10, 27)] * 2


def test_a_failed_request_records_nothing_for_that_checkpoint(analytics) -> None:
    repo, service, fake, clock, receipt = analytics
    clock.now = datetime(2026, 10, 31, 12, tzinfo=UTC)
    service.verify_analytics_video("c-1", receipt.id)
    fake.fail_ends = {date(2026, 10, 27)}  # The 72h window.
    with pytest.raises(YouTubeObservationBlocked):
        service.collect_analytics(receipt.id)
    assert [row["id"] for row in repo.analytics_snapshot_attempts(receipt.id, "72h")] == []
    assert len(repo.analytics_snapshot_attempts(receipt.id, "24h")) == 1
    fake.fail_ends = set()
    [retry] = service.collect_analytics(receipt.id)
    assert retry.id == f"analytics-{receipt.id}-72h-1"


@pytest.mark.parametrize("state", ["none", "stale", "missing"])
def test_collection_needs_a_fresh_existence_check(analytics, state) -> None:
    repo, service, fake, clock, receipt = analytics
    clock.now = datetime(2026, 10, 31, 12, tzinfo=UTC)
    if state == "stale":
        service.verify_analytics_video("c-1", receipt.id)
        clock.now += timedelta(days=31)
    elif state == "missing":
        fake.existence = "missing"
        service.verify_analytics_video("c-1", receipt.id)
    with pytest.raises(ValueError, match="still exists"):
        service.collect_analytics(receipt.id)
    assert not [request for request in fake.requests if request[0] == "report"]


def test_malformed_reports_record_nothing() -> None:
    with pytest.raises(ValueError, match="column headers"):
        parse_metrics_report({"rows": [[1]]}, ANALYTICS_METRICS)
    with pytest.raises(ValueError, match="do not match"):
        parse_metrics_report(
            {"columnHeaders": [{"name": "views"}], "rows": [[1, 2]]}, ANALYTICS_METRICS
        )
    metrics, availability, reasons, _columns = parse_metrics_report(
        {"columnHeaders": [{"name": "views"}], "rows": []}, ("views",)
    )
    assert metrics == {} and reasons == {"views": "no-report-rows"}
    assert (
        maturity(
            datetime(2026, 12, 1, tzinfo=UTC),
            datetime(2026, 11, 1, tzinfo=UTC),
            availability,
            {"availability": "available"},
        )
        == "partial"
    )


# --- Learning records ---------------------------------------------------------------------------


def test_learning_on_analytics_snapshots_stays_qualitative(analytics) -> None:
    repo, service, _fake, clock, receipt = analytics
    clock.now = datetime(2026, 10, 31, 12, tzinfo=UTC)
    service.verify_analytics_video("c-1", receipt.id)
    snapshot = service.collect_analytics(receipt.id)[0]
    for text in ("Retention fell 12% after the hook", "Views were 3", "a 40 % drop"):
        with pytest.raises(ValueError, match="qualitative"):
            service.assess(
                "a-1", [snapshot.id], "hook", text, "x", "low", [], "y", "observation", "f"
            )
    assessment = service.assess(
        "a-2",
        [snapshot.id],
        "hook pacing in production-11-flow",
        "P11 kept viewers through the hook, per the cited snapshot",
        "A qualitative reading of YouTube's reported retention",
        "low",
        ["single video"],
        "Keep the hook pacing for P12",
        "observation",
        "founder",
    )
    assert assessment.id == "a-2"
    # Documented limit: prose like this is not detectable; founder review covers it.
    assert (
        service.assess(
            "a-3",
            [snapshot.id],
            "hook",
            "roughly double the earlier views",
            "x",
            "low",
            [],
            "y",
            "observation",
            "founder",
        ).id
        == "a-3"
    )


# --- Enabled-state authorization behaviour ------------------------------------------------------


def _three_stores():
    return {
        KEYRING_ACCOUNT: FakeStore("ro"),
        UPLOAD_KEYRING_ACCOUNT: FakeStore("up"),
        ANALYTICS_KEYRING_ACCOUNT: FakeStore("an"),
    }


class KindInner:
    def __init__(self, kind, error=None) -> None:
        self.kind, self.error = kind, error

    def acquire(self):
        if self.error:
            raise PreflightBlocked(self.error)
        scopes = youtube_consent.ALL_AUTHORIZATIONS[self.kind][1]
        return Credentials(scopes=tuple(scopes), granted_scopes=tuple(scopes))


def _enabled_governance(monkeypatch, tmp_path, failing, error):
    monkeypatch.setattr(youtube_consent, "ANALYTICS_ENABLED", True)

    class NoData:
        def purge_all_youtube_api_data(self):
            return {}

        def purge_stale_youtube_api_data(self, cutoff, analytics_authorized_at=None):
            return {}

    stores = _three_stores()
    governance = governance_for(NoData(), tmp_path, stores=stores)
    for kind in ("readonly", "analytics"):
        governance.registry.mark_reconfirmed(kind, CLOCK)  # Fresh: not due.
    original = governance.reconfirm
    governance.reconfirm = lambda kind, inner: original(
        kind, inner, CountingChannels([TARGET_CHANNEL])
    )
    used = []

    def inner_for(kind):
        used.append(kind)
        return KindInner(kind, error if kind == failing else None)

    return governance, stores, used, inner_for


def test_enabled_definitive_failure_rechecks_every_other_authorization_now(
    monkeypatch, tmp_path
) -> None:
    governance, stores, used, inner_for = _enabled_governance(
        monkeypatch, tmp_path, "upload", "authorization_revoked"
    )
    report = governance.maintain(inner_for)
    assert report["reconfirmation"] == {
        "readonly": "reconfirmed",
        "upload": "authorization_revoked",
        "analytics": "reconfirmed",
    }
    assert sorted(used) == ["analytics", "readonly", "upload"]
    assert stores[UPLOAD_KEYRING_ACCOUNT].token is None
    assert stores[KEYRING_ACCOUNT].token == "ro" and stores[ANALYTICS_KEYRING_ACCOUNT].token == "an"


def test_enabled_transient_failure_rechecks_nothing_else(monkeypatch, tmp_path) -> None:
    governance, stores, used, inner_for = _enabled_governance(
        monkeypatch, tmp_path, "upload", "authorization_check_transient"
    )
    report = governance.maintain(inner_for)
    assert report["reconfirmation"] == {
        "readonly": "not_due",
        "upload": "authorization_check_transient",
        "analytics": "not_due",
    }
    assert used == ["upload"] and all(store.token for store in stores.values())


# --- The real Analytics adapter (fake HTTP client) ----------------------------------------------


class AnalyticsClient:
    def __init__(self, item="default") -> None:
        self.params: list[dict] = []
        self.item = item

    def authenticated_channel_ids(self, credentials):
        return [TARGET_CHANNEL]

    def video_resource(self, credentials, remote_id):
        if self.item != "default":
            return self.item
        return {
            "id": remote_id,
            "snippet": {"channelId": TARGET_CHANNEL},
            "status": {"privacyStatus": "public", "uploadStatus": "processed"},
        }

    def report(self, credentials, params):
        self.params.append(params)
        return _report({"views": 7})


def _adapter(client, scopes=ANALYTICS_SCOPES):
    credentials = Credentials(scopes=tuple(scopes), granted_scopes=tuple(scopes))
    return YouTubeAnalyticsAdapter(Provider(credentials), client)


def test_adapter_sends_exact_reports_query_parameters() -> None:
    client = AnalyticsClient()
    adapter = _adapter(client)
    adapter.analytics_report("vid", date(2026, 10, 16), date(2026, 10, 17), ANALYTICS_METRICS)
    adapter.analytics_retention("vid", date(2026, 10, 16), date(2026, 10, 17))
    assert client.params == [
        {
            "ids": "channel==MINE",
            "startDate": "2026-10-16",
            "endDate": "2026-10-17",
            "metrics": ",".join(ANALYTICS_METRICS),
            "filters": "video==vid",
        },
        {
            "ids": "channel==MINE",
            "startDate": "2026-10-16",
            "endDate": "2026-10-17",
            "dimensions": "elapsedVideoTimeRatio",
            "metrics": "audienceWatchRatio",
            "filters": "video==vid",
        },
    ]
    assert "subscribersLost" in ANALYTICS_METRICS and "estimatedRevenue" not in ANALYTICS_METRICS


@pytest.mark.parametrize(
    ("item", "outcome"),
    [
        ("default", "exists"),
        (None, "missing"),
        (
            {
                "id": "vid",
                "snippet": {"channelId": "UC-someone-else"},
                "status": {"privacyStatus": "public"},
            },
            "inaccessible",
        ),
        (
            {
                "id": "vid",
                "snippet": {"channelId": TARGET_CHANNEL},
                "status": {"privacyStatus": "private", "uploadStatus": "deleted"},
            },
            "inaccessible",
        ),
    ],
)
def test_adapter_maps_video_existence(item, outcome) -> None:
    assert _adapter(AnalyticsClient(item)).video_existence("vid") == outcome


def test_adapter_refuses_a_broader_or_narrower_grant() -> None:
    for scopes in (
        (YOUTUBE_READONLY_SCOPE,),
        (*ANALYTICS_SCOPES, "https://www.googleapis.com/auth/youtube.upload"),
    ):
        with pytest.raises(YouTubeObservationBlocked):
            _adapter(AnalyticsClient(), scopes).video_existence("vid")


# --- CLI, enabled, with a fake adapter ----------------------------------------------------------


def test_cli_analytics_commands_rehearse_then_run_live_with_backup(
    cli_world, capsys, monkeypatch  # noqa: F811
) -> None:
    from project_atlas import youtube_adapter

    db, media, _metadata, root = cli_world
    publication_id = _cli_publication(db, media)
    repo = AtlasRepository(db)
    try:
        observer = FakePublishingAdapter()
        now = datetime.now(UTC).replace(microsecond=0)
        from dataclasses import replace

        observer.remote = replace(
            observer.remote,
            privacy="public",
            public_at=(now + timedelta(seconds=30)).isoformat(),
            observed_at=(now + timedelta(seconds=60)).isoformat(),
        )
        service = PublishingService(repo, LocalMediaStorage(media), observer)
        receipt = service.reconcile_scheduled_publication("r-1", "s-1", publication_id)
    finally:
        repo.close()
    monkeypatch.setattr(youtube_consent, "ANALYTICS_ENABLED", True)
    fake = FakeAnalytics()
    monkeypatch.setattr(
        youtube_adapter.YouTubeAnalyticsAdapter, "from_client_config", lambda *a, **k: fake
    )
    common = [
        "--client-config",
        root / "c.json",
        "--consent-state",
        root / "s.json",
        "--db",
        db,
        "--media",
        media,
    ]
    code, report = _cli(
        capsys,
        "analytics-check",
        receipt.id,
        "--check-id",
        "c-1",
        *common,
        "--expect-db-sha256",
        database_sha256(db),
        "--dry-run",
    )
    assert code == 0 and "video_existence" in report["rehearsal"]["stopped_at"], report
    assert fake.calls == []
    code, report = _cli(
        capsys,
        "analytics-check",
        receipt.id,
        "--check-id",
        "c-1",
        *common,
        "--expect-db-sha256",
        database_sha256(db),
        "--backup-root",
        root / "backups",
    )
    assert code == 0 and report["live"]["result"]["outcome"] == "exists", report
    assert report["backup"]["integrity"] == "ok"
    code, report = _cli(
        capsys,
        "collect-analytics",
        receipt.id,
        *common,
        "--expect-db-sha256",
        database_sha256(db),
        "--backup-root",
        root / "backups-2",
    )
    assert code == 0 and report["live"]["result"] == {"collected": []}, report  # None due yet.
