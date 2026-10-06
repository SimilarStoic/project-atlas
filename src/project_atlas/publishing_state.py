"""Offline publishing records and guarded SQLite transitions, without provider clients."""

from __future__ import annotations

import json
import sqlite3
from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from math import isfinite
from typing import Any

TARGET_CHANNEL = "UC1cX-OTF9-LZeNo5TaFgrgQ"
RAW_METRICS = frozenset(
    {
        "views",
        "engagedViews",
        "estimatedMinutesWatched",
        "averageViewDuration",
        "averageViewPercentage",
        "likes",
        "comments",
        "shares",
        "subscribersGained",
    }
)
_FORBIDDEN_KEY_PARTS = (
    "authorization",
    "apikey",
    "accesstoken",
    "refreshtoken",
    "secret",
    "sessionuri",
    "sessionurl",
    "resumableurl",
    "cookie",
)


def stamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    """Stable UTF-8 identity: sorted keys, compact separators, no ASCII escaping or NaN."""

    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def pilot_timing(value: dict[str, Any]) -> tuple[str, datetime, datetime]:
    """Validate frozen London timing; return derived ISO week and execution bounds."""

    if not isinstance(value, dict) or value.get("timezone") != "Europe/London":
        raise ValueError("Pilot timing must identify Europe/London explicitly.")

    def last_sunday(year: int, month: int) -> int:
        _, last_day = monthrange(year, month)
        weekday = datetime(year, month, last_day).weekday()
        return last_day - ((weekday + 1) % 7)

    def london_offset(moment_utc: datetime) -> timedelta:
        year = moment_utc.year
        spring = datetime(year, 3, last_sunday(year, 3), 1, tzinfo=UTC)
        autumn = datetime(year, 10, last_sunday(year, 10), 1, tzinfo=UTC)
        return timedelta(hours=1) if spring <= moment_utc < autumn else timedelta(0)

    def read(name: str) -> datetime:
        try:
            moment = datetime.fromisoformat(value[name])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Pilot timing needs exact timezone-aware bounds.") from exc
        if moment.tzinfo is None or moment.utcoffset() != london_offset(moment.astimezone(UTC)):
            raise ValueError("Pilot timing offset must match Europe/London at that instant.")
        return moment

    if value.get("mode") == "exact" and set(value) == {"timezone", "mode", "at"}:
        start = read("at")
        if start.second or start.microsecond:
            raise ValueError("Exact pilot publication time has minute precision.")
        end = start + timedelta(minutes=1)
    elif value.get("mode") == "window" and set(value) == {"timezone", "mode", "start", "end"}:
        start, end = read("start"), read("end")
        if start >= end:
            raise ValueError("Manual window must have positive bounded duration.")
    else:
        raise ValueError("Pilot timing must be exact or a bounded manual window.")
    if start.isocalendar()[:2] != (end - timedelta(microseconds=1)).isocalendar()[:2]:
        raise ValueError("Pilot publication window must stay within one London ISO week.")
    year, week, _ = start.isocalendar()
    return f"{year}-W{week:02d}", start.astimezone(UTC), end.astimezone(UTC)


# Evidence-only packages: frozen, permanent never-release policy. The schema predates it, so
# such a package (and its approval) carries release_route "manual" purely as a legacy-schema
# compatibility sentinel; it never authorizes a release of any kind.
NEVER_RELEASE_POLICY = "never_release"
NEVER_RELEASE_TIMING = {"mode": "never_release"}
NEVER_RELEASE_WEEK = "never-release"
NEVER_RELEASE_ROUTE_SENTINEL = "manual"


def is_never_release(manifest: dict[str, Any]) -> bool:
    return isinstance(manifest, dict) and manifest.get("release_policy") == NEVER_RELEASE_POLICY


def package_release_week(manifest: dict[str, Any]) -> str:
    """Validate the release proposition and derive the persisted pilot week."""

    timing = manifest.get("publication_timing")
    if "release_policy" in manifest:
        if (
            manifest["release_policy"] != NEVER_RELEASE_POLICY
            or manifest.get("release_route") != NEVER_RELEASE_ROUTE_SENTINEL
            or timing != NEVER_RELEASE_TIMING
            or manifest.get("private_first") is not True
        ):
            raise ValueError(
                "A never-release package needs exactly release_policy never_release, the "
                "compatibility release_route manual, never_release timing and private_first."
            )
        return NEVER_RELEASE_WEEK
    if isinstance(timing, dict) and timing.get("mode") == NEVER_RELEASE_TIMING["mode"]:
        raise ValueError("never_release timing is only valid on a never-release package.")
    pilot_week, _, _ = pilot_timing(timing)
    return pilot_week


def timing_is_open(value: dict[str, Any], now: datetime) -> bool:
    if now.tzinfo is None:
        raise ValueError("Execution clock must be timezone-aware.")
    _, start, end = pilot_timing(value)
    return start <= now.astimezone(UTC) < end


_AVAILABILITY = {"available", "unavailable", "immature", "not_returned"}


def _metric_observations(
    requested: dict[str, Any],
    values: dict[str, int | float | None],
    states: dict[str, str],
    reasons: dict[str, str] | None,
) -> dict[str, dict[str, Any]]:
    names = requested.get("metrics")
    if not isinstance(names, list) or any(name not in RAW_METRICS for name in names):
        raise ValueError("Requested scalar metric coverage must name supported raw metrics.")
    if len(set(names)) != len(names) or not values.keys() <= RAW_METRICS:
        raise ValueError("Scalar metric names must be unique and raw/provider-supported.")
    observations = {}
    for name in sorted(set(names) | set(values)):
        present = name in values
        value = values.get(name)
        state = states.get(name, "available" if present and value is not None else "not_returned")
        reason = (reasons or {}).get(name)
        if state not in _AVAILABILITY:
            raise ValueError("Metric availability state is invalid.")
        if state == "available":
            if (
                not present
                or isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
            ):
                raise ValueError("Available metric needs its finite raw numeric value.")
        elif value is not None or not reason:
            if state == "not_returned" and not reason:
                reason = "provider-returned-null" if present else "requested-but-absent"
            else:
                raise ValueError("Unavailable metric needs NULL value and explicit reason.")
        observations[name] = {
            "value": value,
            "availability": state,
            "reason": reason,
            "unit": None,
            "requested": name in names,
        }
    return observations


def _retention_observation(value: dict[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {"availability": "not_returned", "reason": "no-retention-series", "points": None}
    if not isinstance(value, dict) or value.get("availability") not in _AVAILABILITY:
        raise ValueError("Retention requires an explicit availability state.")
    state, points, reason = value["availability"], value.get("points"), value.get("reason")
    if state != "available":
        if points is not None or not isinstance(reason, str) or not reason:
            raise ValueError("Missing retention requires no points and an explicit reason.")
        return {"availability": state, "reason": reason, "points": None}
    if not isinstance(points, list) or not points:
        raise ValueError("Available retention needs a nonempty raw series.")
    normalized = []
    for point in points:
        if not isinstance(point, dict) or set(point) != {
            "elapsedVideoTimeRatio",
            "audienceWatchRatio",
        }:
            raise ValueError("Retention point needs both exact raw platform axes.")
        elapsed, ratio = point["elapsedVideoTimeRatio"], point["audienceWatchRatio"]
        if (
            any(
                isinstance(x, bool) or not isinstance(x, (int, float)) or not isfinite(x)
                for x in (elapsed, ratio)
            )
            or not 0 <= elapsed <= 1
            or ratio < 0
        ):
            raise ValueError("Retention raw values are invalid.")
        normalized.append(point)
    normalized.sort(key=lambda point: point["elapsedVideoTimeRatio"])
    if len({point["elapsedVideoTimeRatio"] for point in normalized}) != len(normalized):
        raise ValueError("Duplicate retention elapsed positions are invalid.")
    return {"availability": "available", "reason": None, "points": normalized}


def safe_evidence(value: Any) -> None:
    """Reject raw secret/session material in ordinary authored provenance."""

    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("Publishing provenance keys must be text.")
            normalized_key = "".join(char for char in key.lower() if char.isalnum())
            if any(part in normalized_key for part in _FORBIDDEN_KEY_PARTS):
                raise ValueError("Secret/session fields are forbidden in publishing provenance.")
            safe_evidence(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            safe_evidence(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if (
            "bearer " in lowered
            or "upload_session=" in lowered
            or ("://" in lowered and ("session" in lowered or "upload" in lowered))
        ):
            raise ValueError("Raw authorization/session material is forbidden in provenance.")


@dataclass(frozen=True)
class PublishingPackage:
    id: str
    pilot_key: str
    pilot_slot: int
    version: int
    predecessor_id: str | None
    final_media_artifact_id: str
    artifact_digest: str
    platform: str
    channel_id: str
    pilot_week: str
    manifest: dict[str, Any]
    package_digest: str
    created_at: str


@dataclass(frozen=True)
class PublicationGateDecision:
    id: str
    package_id: str
    package_digest: str
    sequence: int
    decision: str
    founder_actor: str
    transfer_route: str | None
    release_route: str | None
    timing: dict[str, Any]
    comment: str | None
    created_at: str


@dataclass(frozen=True)
class PublicationOperationEvent:
    id: str
    operation_id: str
    sequence: int
    kind: str
    actor: str
    evidence: dict[str, Any]
    provider_evidence: dict[str, Any] | None
    provider_purged_at: str | None
    created_at: str


@dataclass(frozen=True)
class PublicationOperation:
    id: str
    operation_key: str
    package_id: str
    gate_decision_id: str
    action_kind: str
    execution_mode: str
    intent: dict[str, Any]
    intent_digest: str
    created_at: str
    outcome: str  # Derived from the ordered, immutable event journal.


@dataclass(frozen=True)
class PlatformPublication:
    id: str
    package_id: str
    upload_operation_id: str
    platform: str
    channel_id: str
    remote_id: str | None
    binding_digest: str | None
    identified_at: str
    identity_source: str
    provider_purged_at: str | None


@dataclass(frozen=True)
class PublicationStatusSnapshot:
    id: str
    publication_id: str
    privacy: str | None
    processing: str | None
    verification: str | None
    api_locked: bool | None
    observed_at: str | None
    adapter_version: str
    observation_digest: str | None
    provider_payload: dict[str, Any] | None
    provider_purged_at: str | None


@dataclass(frozen=True)
class PublicationReceipt:
    id: str
    publication_id: str
    package_id: str
    gate_decision_id: str
    release_operation_id: str
    public_status_id: str
    execution_mode: str
    channel_id: str
    pilot_week: str
    public_at: str | None
    timestamp_source: str
    timestamp_precision: str
    first_public_observed_at: str | None
    receipt_digest: str | None
    created_at: str
    provider_purged_at: str | None


@dataclass(frozen=True)
class PerformanceSnapshot:
    id: str
    receipt_id: str
    checkpoint: str
    due_at: str | None
    collected_at: str | None
    requested_coverage: dict[str, Any]
    returned_coverage: dict[str, Any] | None
    metrics: dict[str, dict[str, Any]] | None
    retention: dict[str, Any] | None
    maturity: str | None
    api_context: dict[str, Any] | None
    observation_digest: str | None
    provider_payload: dict[str, Any] | None
    provider_purged_at: str | None


@dataclass(frozen=True)
class LearningAssessment:
    id: str
    predecessor_id: str | None
    feature: str
    outcome: str
    interpretation: str
    confidence: str
    confounds: list[str]
    recommendation: str
    evidence_tier: str
    producer: str
    assessment_digest: str
    created_at: str
    evidence_snapshot_ids: tuple[str, ...]
    publication_ids: tuple[str, ...]


@dataclass(frozen=True)
class LearningApplication:
    id: str
    assessment_id: str
    target_kind: str
    target_id: str
    decision_reference: str
    context: dict[str, Any]
    change_digest: str
    founder_reference: str | None
    actor: str
    created_at: str


def _required_text(*values: str) -> None:
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError("Publishing identifiers and authored facts must be non-empty text.")


class PublishingRepositoryMixin:
    """Only guarded publishing transitions; AtlasRepository supplies connection/artifact reads."""

    connection: sqlite3.Connection

    def get_publishing_package(self, package_id: str) -> PublishingPackage:
        row = self.connection.execute(
            "SELECT * FROM publishing_packages WHERE id = ?", (package_id,)
        ).fetchone()
        if row is None:
            raise KeyError(package_id)
        return PublishingPackage(
            row["id"],
            row["pilot_key"],
            row["pilot_slot"],
            row["version"],
            row["predecessor_id"],
            row["final_media_artifact_id"],
            row["artifact_digest"],
            row["platform"],
            row["channel_id"],
            row["pilot_week"],
            json.loads(row["manifest_json"]),
            row["package_digest"],
            row["created_at"],
        )

    def list_publishing_packages(self, pilot_key: str) -> list[PublishingPackage]:
        rows = self.connection.execute(
            "SELECT id FROM publishing_packages WHERE pilot_key = ? ORDER BY pilot_slot, version",
            (pilot_key,),
        )
        return [self.get_publishing_package(row["id"]) for row in rows]

    def final_media_artifact_is_packaged(self, artifact_id: str) -> bool:
        """True once any publishing package references this final-media artifact."""

        return (
            self.connection.execute(
                "SELECT 1 FROM publishing_packages WHERE final_media_artifact_id = ? LIMIT 1",
                (artifact_id,),
            ).fetchone()
            is not None
        )

    def create_publishing_package(
        self,
        package_id: str,
        pilot_key: str,
        pilot_slot: int,
        version: int,
        artifact_id: str,
        artifact_digest: str,
        channel_id: str,
        manifest: dict[str, Any],
        predecessor_id: str | None = None,
    ) -> PublishingPackage:
        _required_text(package_id, pilot_key, artifact_id, artifact_digest, channel_id)
        if channel_id != TARGET_CHANNEL or not 1 <= pilot_slot <= 3 or version < 1:
            raise ValueError("Package target channel, pilot slot or version is invalid.")
        artifact = self.get_final_media_artifact(artifact_id)
        if artifact.content_digest != artifact_digest:
            raise ValueError("FinalMediaArtifact digest mismatch.")
        if predecessor_id is not None:
            predecessor = self.get_publishing_package(predecessor_id)
            if (predecessor.pilot_key, predecessor.pilot_slot, predecessor.version + 1) != (
                pilot_key,
                pilot_slot,
                version,
            ):
                raise ValueError("Package predecessor must be the previous exact pilot version.")
        elif version != 1:
            raise ValueError("A later package version needs an explicit predecessor.")
        if not isinstance(manifest, dict):
            raise ValueError("Package manifest must be a frozen object.")
        safe_evidence(manifest)
        pilot_week = package_release_week(manifest)
        if manifest.get("pilot_slot") != pilot_slot or manifest.get("release_route") not in {
            "api",
            "manual",
        }:
            raise ValueError("Pilot slot and release route must be frozen in the package.")
        if not is_never_release(manifest) and (manifest["release_route"] == "api") != (
            manifest["publication_timing"]["mode"] == "exact"
        ):
            raise ValueError("API release needs exact time; manual release needs a bounded window.")
        identity = {
            "schema": "publishing-package-v1",
            "pilot_key": pilot_key,
            "pilot_slot": pilot_slot,
            "version": version,
            "predecessor_id": predecessor_id,
            "artifact_id": artifact_id,
            "artifact_digest": artifact_digest,
            "platform": "youtube",
            "channel_id": channel_id,
            "manifest": manifest,
        }
        with self.connection:
            self.connection.execute(
                "INSERT INTO publishing_packages VALUES "
                "(?, ?, ?, ?, ?, ?, ?, 'youtube', ?, ?, ?, ?, ?)",
                (
                    package_id,
                    pilot_key,
                    pilot_slot,
                    version,
                    predecessor_id,
                    artifact_id,
                    artifact_digest,
                    channel_id,
                    pilot_week,
                    canonical_json(manifest),
                    digest(identity),
                    stamp(),
                ),
            )
        return self.get_publishing_package(package_id)

    def get_publication_gate_decision(self, decision_id: str) -> PublicationGateDecision:
        row = self.connection.execute(
            "SELECT * FROM publication_gate_decisions WHERE id = ?", (decision_id,)
        ).fetchone()
        if row is None:
            raise KeyError(decision_id)
        return PublicationGateDecision(
            row["id"],
            row["package_id"],
            row["package_digest"],
            row["sequence"],
            row["decision"],
            row["founder_actor"],
            row["transfer_route"],
            row["release_route"],
            json.loads(row["timing_json"]),
            row["comment"],
            row["created_at"],
        )

    def record_publication_gate_decision(
        self,
        decision_id: str,
        package_id: str,
        package_digest: str,
        founder_actor: str,
        decision: str,
        transfer_route: str | None,
        release_route: str | None,
        timing: dict[str, Any],
        comment: str | None = None,
    ) -> PublicationGateDecision:
        package = self.get_publishing_package(package_id)
        _required_text(decision_id, founder_actor)
        if package.package_digest != package_digest or decision not in {
            "approve",
            "reject",
            "revoke",
        }:
            raise ValueError(
                "Founder decision must bind the exact package digest and allowed outcome."
            )
        if decision == "approve" and (
            transfer_route not in {"api", "manual"} or release_route not in {"api", "manual"}
        ):
            raise ValueError("Approval requires exact transfer and release routes.")
        if not isinstance(timing, dict) or not timing:
            raise ValueError("Founder timing/window must be frozen.")
        safe_evidence(timing)
        if decision == "approve" and (
            timing != package.manifest["publication_timing"]
            or release_route != package.manifest["release_route"]
            or transfer_route != package.manifest["transfer_route"]
        ):
            raise ValueError("Founder approval must match the exact frozen package proposition.")
        with self.connection:
            sequence = self.connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 FROM publication_gate_decisions "
                "WHERE package_id = ?",
                (package_id,),
            ).fetchone()[0]
            if decision == "revoke" and self.effective_publication_approval(package_id) is None:
                raise ValueError("Only an effective approval may be revoked.")
            self.connection.execute(
                "INSERT INTO publication_gate_decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    decision_id,
                    package_id,
                    package_digest,
                    sequence,
                    decision,
                    founder_actor,
                    transfer_route,
                    release_route,
                    canonical_json(timing),
                    comment,
                    stamp(),
                ),
            )
        return self.get_publication_gate_decision(decision_id)

    def effective_publication_approval(self, package_id: str) -> PublicationGateDecision | None:
        package = self.get_publishing_package(package_id)
        row = self.connection.execute(
            "SELECT id FROM publication_gate_decisions WHERE package_id = ? "
            "ORDER BY sequence DESC LIMIT 1",
            (package_id,),
        ).fetchone()
        if row is None:
            return None
        decision = self.get_publication_gate_decision(row["id"])
        return (
            decision
            if decision.decision == "approve" and decision.package_digest == package.package_digest
            else None
        )

    def get_publication_operation_events(
        self, operation_id: str
    ) -> list[PublicationOperationEvent]:
        rows = self.connection.execute(
            "SELECT * FROM publication_operation_events WHERE operation_id = ? ORDER BY sequence",
            (operation_id,),
        )
        return [
            PublicationOperationEvent(
                row["id"],
                row["operation_id"],
                row["sequence"],
                row["kind"],
                row["actor"],
                json.loads(row["evidence_json"]),
                (
                    json.loads(row["provider_evidence_json"])
                    if row["provider_evidence_json"] is not None
                    else None
                ),
                row["provider_purged_at"],
                row["created_at"],
            )
            for row in rows
        ]

    def get_publication_operation(self, operation_id: str) -> PublicationOperation:
        row = self.connection.execute(
            "SELECT * FROM publication_operations WHERE id = ?", (operation_id,)
        ).fetchone()
        if row is None:
            raise KeyError(operation_id)
        events = self.get_publication_operation_events(operation_id)
        if not events:
            raise ValueError("Operation lacks its durable reservation event.")
        last = events[-1]
        outcome = {"succeeded": "succeeded", "failed": "failed", "outcome_unknown": "unknown"}.get(
            last.kind, "pending"
        )
        if last.kind == "reconciled":
            outcome = last.evidence["resolution"]
        return PublicationOperation(
            row["id"],
            row["operation_key"],
            row["package_id"],
            row["gate_decision_id"],
            row["action_kind"],
            row["execution_mode"],
            json.loads(row["intent_json"]),
            row["intent_digest"],
            row["created_at"],
            outcome,
        )

    def reserve_publication_operation(
        self,
        package_id: str,
        action_kind: str,
        execution_mode: str,
        intent: dict[str, Any],
        now: datetime | None = None,
    ) -> PublicationOperation:
        # Serialize the read/check/reserve sequence across SQLite connections. The
        # unique key protects duplicate intent; this lock also protects slot conflicts.
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            result = self._reserve_publication_operation_locked(
                package_id,
                action_kind,
                execution_mode,
                intent,
                now,
            )
        except BaseException:
            self.connection.rollback()
            raise
        self.connection.commit()
        return result

    def _reserve_publication_operation_locked(
        self,
        package_id: str,
        action_kind: str,
        execution_mode: str,
        intent: dict[str, Any],
        now: datetime | None,
    ) -> PublicationOperation:
        package = self.get_publishing_package(package_id)
        if action_kind == "release" and is_never_release(package.manifest):
            # Checked first: the stored manual route is only a compatibility sentinel.
            raise ValueError("A never-release package can never be released.")
        approval = self.effective_publication_approval(package_id)
        if approval is None or action_kind not in {"upload", "release"}:
            raise ValueError(
                "Exact effective founder authority is required for an external operation."
            )
        route = approval.transfer_route if action_kind == "upload" else approval.release_route
        if execution_mode != route or not isinstance(intent, dict):
            raise ValueError("Operation execution mode or intent differs from founder authority.")
        safe_evidence(intent)
        identity = {
            "schema": "publication-operation-v1",
            "package_digest": package.package_digest,
            "gate_decision_id": approval.id,
            "action_kind": action_kind,
            "execution_mode": execution_mode,
            "intent": intent,
        }
        key = digest(identity)
        operation_id = f"publication-operation-{key}"
        existing = self.connection.execute(
            "SELECT id FROM publication_operations WHERE operation_key = ?", (key,)
        ).fetchone()
        if existing:
            return self.get_publication_operation(existing["id"])
        if action_kind == "release" and (
            intent.get("pilot_slot") != package.pilot_slot
            or intent.get("timing") != approval.timing
            or now is None
            or not timing_is_open(approval.timing, now)
        ):
            raise ValueError("New public release requires the exact active approved slot.")
        if action_kind == "upload":
            rows = self.connection.execute(
                "SELECT id FROM publication_operations WHERE action_kind = 'upload' "
                "AND package_id IN (SELECT id FROM publishing_packages "
                "WHERE pilot_key = ? AND pilot_slot = ?)",
                (package.pilot_key, package.pilot_slot),
            )
            for row in rows:
                predecessor = self.get_publication_operation(row["id"])
                if predecessor.outcome != "failed":
                    raise ValueError(
                        "An unresolved or successful predecessor blocks another upload."
                    )
        if action_kind == "release":
            rows = self.connection.execute(
                "SELECT o.id FROM publication_operations o JOIN publishing_packages p "
                "ON p.id = o.package_id WHERE o.action_kind = 'release' "
                "AND p.channel_id = ? AND p.pilot_week = ?",
                (package.channel_id, package.pilot_week),
            )
            for row in rows:
                if self.get_publication_operation(row["id"]).outcome != "failed":
                    raise ValueError("This channel's pilot week is reserved or consumed.")
        self.connection.execute(
            "INSERT INTO publication_operations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                operation_id,
                key,
                package_id,
                approval.id,
                action_kind,
                execution_mode,
                canonical_json(intent),
                digest(intent),
                stamp(),
            ),
        )
        self.connection.execute(
            "INSERT INTO publication_operation_events VALUES "
            "(?, ?, 1, 'reserved', 'Conveyor', '{}', ?, NULL, NULL, NULL)",
            (f"{operation_id}:1", operation_id, stamp()),
        )
        return self.get_publication_operation(operation_id)

    def append_publication_operation_event(
        self,
        operation_id: str,
        kind: str,
        actor: str,
        evidence: dict[str, Any],
        provider_evidence: dict[str, Any] | None = None,
    ) -> PublicationOperationEvent:
        operation = self.get_publication_operation(operation_id)
        _required_text(actor)
        if not isinstance(evidence, dict):
            raise ValueError("Operation evidence must be an authored object.")
        safe_evidence(evidence)
        if provider_evidence is not None:
            safe_evidence(provider_evidence)
        last = self.get_publication_operation_events(operation_id)[-1]
        allowed = {
            "reserved": {"dispatch_started", "failed"},
            "dispatch_started": {
                "progress",
                "remote_identity_observed",
                "succeeded",
                "failed",
                "outcome_unknown",
            },
            "progress": {
                "progress",
                "remote_identity_observed",
                "succeeded",
                "failed",
                "outcome_unknown",
            },
            "remote_identity_observed": {"succeeded", "failed", "outcome_unknown"},
            "outcome_unknown": {"reconciled"},
            "failed": set(),
            "succeeded": set(),
            "reconciled": set(),
        }
        if kind not in allowed[last.kind]:
            raise ValueError("Invalid or duplicate publishing operation transition.")
        if kind == "reconciled" and evidence.get("resolution") not in {"succeeded", "failed"}:
            raise ValueError("Reconciliation requires a definitive resolution.")
        if kind == "dispatch_started" and operation.outcome != "pending":
            raise ValueError("Only a pending reservation may dispatch.")
        sequence = last.sequence + 1
        with self.connection:
            self.connection.execute(
                "INSERT INTO publication_operation_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (
                    f"{operation_id}:{sequence}",
                    operation_id,
                    sequence,
                    kind,
                    actor,
                    canonical_json(evidence),
                    stamp(),
                    canonical_json(provider_evidence) if provider_evidence is not None else None,
                    digest(provider_evidence) if provider_evidence is not None else None,
                ),
            )
        return self.get_publication_operation_events(operation_id)[-1]

    def assert_release_week_clear(self, operation_id: str) -> None:
        operation = self.get_publication_operation(operation_id)
        package = self.get_publishing_package(operation.package_id)
        if operation.action_kind != "release" or (
            operation.intent.get("pilot_slot") != package.pilot_slot
            or operation.intent.get("timing") != package.manifest["publication_timing"]
        ):
            raise ValueError("Release intent must match the approved pilot slot and timing.")
        conflict = self.release_week_conflict(package, operation_id)
        if conflict:
            raise ValueError(conflict)

    def release_week_conflict(
        self, package: PublishingPackage, exclude_operation_id: str | None = None
    ) -> str | None:
        """The single channel-week public-release rule, shared by releases and public uploads.

        A non-failed release, a non-failed public/unlisted upload, or a public receipt in the
        package's channel pilot week consumes that week.
        """

        if is_never_release(package.manifest):
            return None  # Never-release packages neither consume nor contend for a release week.
        rows = self.connection.execute(
            "SELECT o.id FROM publication_operations o JOIN publishing_packages p "
            "ON p.id = o.package_id WHERE o.id <> ? AND p.channel_id = ? AND p.pilot_week = ? "
            "AND p.pilot_week <> ? AND o.action_kind IN ('release', 'upload')",
            (
                exclude_operation_id or "",
                package.channel_id,
                package.pilot_week,
                NEVER_RELEASE_WEEK,
            ),
        )
        for row in rows:
            operation = self.get_publication_operation(row["id"])
            public = operation.action_kind == "release" or operation.intent.get("privacy") in {
                "public",
                "unlisted",
            }
            if public and operation.outcome != "failed":
                return "Another public item reserves or consumed this channel pilot week."
        receipt = self.connection.execute(
            "SELECT id FROM publication_receipts WHERE channel_id = ? AND pilot_week = ? "
            "AND release_operation_id <> ?",
            (package.channel_id, package.pilot_week, exclude_operation_id or ""),
        ).fetchone()
        if receipt is not None:
            return "Another public receipt consumed this channel pilot week."
        return None

    def bind_platform_publication(
        self,
        publication_id: str,
        package_id: str,
        upload_operation_id: str,
        channel_id: str,
        remote_id: str,
        binding_evidence: dict[str, Any],
        identity_source: str = "api",
    ) -> PlatformPublication:
        package = self.get_publishing_package(package_id)
        upload = self.get_publication_operation(upload_operation_id)
        _required_text(publication_id, remote_id)
        if (
            channel_id != package.channel_id
            or upload.action_kind != "upload"
            or upload.package_id != package_id
            or upload.outcome != "succeeded"
        ):
            raise ValueError("Remote identity needs the succeeded exact upload and target channel.")
        safe_evidence(binding_evidence)
        if identity_source not in {"api", "founder_manual"}:
            raise ValueError("Remote identity source must be explicit.")
        evidence_digest = digest(
            {
                "remote_id": remote_id,
                "channel_id": channel_id,
                "package_digest": package.package_digest,
                "operation_key": upload.operation_key,
                "evidence": binding_evidence,
            }
        )
        with self.connection:
            self.connection.execute(
                "INSERT INTO platform_publications VALUES "
                "(?, ?, ?, 'youtube', ?, ?, ?, ?, ?, NULL)",
                (
                    publication_id,
                    package_id,
                    upload_operation_id,
                    channel_id,
                    remote_id,
                    evidence_digest,
                    stamp(),
                    identity_source,
                ),
            )
        return self.get_platform_publication(publication_id)

    def get_platform_publication(self, publication_id: str) -> PlatformPublication:
        row = self.connection.execute(
            "SELECT * FROM platform_publications WHERE id = ?", (publication_id,)
        ).fetchone()
        if row is None:
            raise KeyError(publication_id)
        return PlatformPublication(*tuple(row))

    def append_publication_status(
        self,
        status_id: str,
        publication_id: str,
        privacy: str | None,
        processing: str | None,
        verification: str,
        api_locked: bool,
        adapter_version: str,
        observed_at: str,
        provider_payload: dict[str, Any] | None = None,
    ) -> PublicationStatusSnapshot:
        self.get_platform_publication(publication_id)
        _required_text(status_id, adapter_version, observed_at)
        if verification not in {"passed", "failed", "unknown"}:
            raise ValueError("Status verification outcome is invalid.")
        if provider_payload is not None:
            safe_evidence(provider_payload)
        facts = {
            "publication_id": publication_id,
            "privacy": privacy,
            "processing": processing,
            "verification": verification,
            "api_locked": bool(api_locked),
            "observed_at": observed_at,
            "adapter_version": adapter_version,
        }
        with self.connection:
            self.connection.execute(
                "INSERT INTO publication_status_snapshots VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (
                    status_id,
                    publication_id,
                    privacy,
                    processing,
                    verification,
                    int(api_locked),
                    observed_at,
                    adapter_version,
                    digest(facts),
                    canonical_json(provider_payload) if provider_payload is not None else None,
                    digest(provider_payload) if provider_payload is not None else None,
                ),
            )
        return self.get_publication_status(status_id)

    def get_publication_status(self, status_id: str) -> PublicationStatusSnapshot:
        row = self.connection.execute(
            "SELECT * FROM publication_status_snapshots WHERE id = ?", (status_id,)
        ).fetchone()
        if row is None:
            raise KeyError(status_id)
        return PublicationStatusSnapshot(
            row["id"],
            row["publication_id"],
            row["privacy"],
            row["processing"],
            row["verification"],
            bool(row["api_locked"]) if row["api_locked"] is not None else None,
            row["observed_at"],
            row["adapter_version"],
            row["observation_digest"],
            (
                json.loads(row["provider_payload_json"])
                if row["provider_payload_json"] is not None
                else None
            ),
            row["provider_purged_at"],
        )

    def create_publication_receipt(
        self,
        receipt_id: str,
        publication_id: str,
        release_operation_id: str,
        public_status_id: str,
        public_at: str,
        timestamp_source: str,
        timestamp_precision: str,
    ) -> PublicationReceipt:
        publication = self.get_platform_publication(publication_id)
        package = self.get_publishing_package(publication.package_id)
        if is_never_release(package.manifest):
            raise ValueError("A never-release package can never have a public receipt.")
        release = self.get_publication_operation(release_operation_id)
        status = self.get_publication_status(public_status_id)
        # A later revocation prevents NEW actions, not truthful receipt lineage
        # for a release already dispatched under its original exact approval.
        approval = self.get_publication_gate_decision(release.gate_decision_id)
        _required_text(receipt_id, public_at, timestamp_source, timestamp_precision)
        if (
            approval.decision != "approve"
            or approval.package_id != package.id
            or approval.package_digest != package.package_digest
            or approval.release_route != release.execution_mode
            or release.package_id != package.id
            or release.action_kind != "release"
            or release.outcome != "succeeded"
            or status.publication_id != publication_id
            or status.privacy != "public"
            or status.processing != "succeeded"
            or status.verification != "passed"
            or status.api_locked
        ):
            raise ValueError(
                "Receipt requires exact authority, release and independently verified public state."
            )
        try:
            public_time = datetime.fromisoformat(public_at)
            private_time = datetime.fromisoformat(publication.identified_at)
            observed_time = datetime.fromisoformat(status.observed_at)
            if any(item.tzinfo is None for item in (public_time, private_time, observed_time)):
                raise ValueError("Public timing needs timezone-aware timestamps.")
        except ValueError as exc:
            raise ValueError("Public timing needs valid timezone-aware timestamps.") from exc
        if public_time <= private_time or public_time > observed_time:
            raise ValueError("Private identification time or future time cannot be public time.")
        facts = {
            "publication_id": publication_id,
            "package_digest": package.package_digest,
            "gate_decision_id": approval.id,
            "release_operation_key": release.operation_key,
            "public_status_digest": status.observation_digest,
            "public_at": public_at,
            "timestamp_source": timestamp_source,
            "timestamp_precision": timestamp_precision,
            "first_public_observed_at": status.observed_at,
            "execution_mode": release.execution_mode,
        }
        with self.connection:
            self.connection.execute(
                "INSERT INTO publication_receipts VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    receipt_id,
                    publication_id,
                    package.id,
                    approval.id,
                    release_operation_id,
                    public_status_id,
                    release.execution_mode,
                    package.channel_id,
                    package.pilot_week,
                    public_at,
                    timestamp_source,
                    timestamp_precision,
                    status.observed_at,
                    digest(facts),
                    stamp(),
                    None,
                ),
            )
        return self.get_publication_receipt(receipt_id)

    def get_publication_receipt(self, receipt_id: str) -> PublicationReceipt:
        row = self.connection.execute(
            "SELECT * FROM publication_receipts WHERE id = ?", (receipt_id,)
        ).fetchone()
        if row is None:
            raise KeyError(receipt_id)
        return PublicationReceipt(*tuple(row))

    def append_performance_snapshot(
        self,
        snapshot_id: str,
        receipt_id: str,
        checkpoint: str,
        due_at: str,
        collected_at: str,
        requested_coverage: dict[str, Any],
        returned_coverage: dict[str, Any] | None,
        metrics: dict[str, int | float | None],
        availability: dict[str, str],
        maturity: str,
        api_context: dict[str, Any],
        provider_payload: dict[str, Any] | None = None,
        retention: dict[str, Any] | None = None,
        missing_reasons: dict[str, str] | None = None,
    ) -> PerformanceSnapshot:
        self.get_publication_receipt(receipt_id)
        if checkpoint not in {"24h", "72h", "7d", "28d"} or maturity not in {
            "immature",
            "partial",
            "mature",
        }:
            raise ValueError("Performance checkpoint/maturity is invalid.")
        _required_text(snapshot_id, due_at, collected_at)
        if not isinstance(metrics, dict) or not isinstance(availability, dict):
            raise ValueError("Raw scalar metrics and availability must be objects.")
        observations = _metric_observations(
            requested_coverage, metrics, availability, missing_reasons
        )
        retention_observation = _retention_observation(retention)
        for item in (
            requested_coverage,
            returned_coverage,
            availability,
            missing_reasons,
            retention_observation,
            api_context,
            provider_payload,
        ):
            if item is not None:
                safe_evidence(item)
        facts = {
            "receipt_id": receipt_id,
            "checkpoint": checkpoint,
            "due_at": due_at,
            "collected_at": collected_at,
            "requested_coverage": requested_coverage,
            "returned_coverage": returned_coverage,
            "metrics": observations,
            "retention": retention_observation,
            "maturity": maturity,
            "api_context": api_context,
        }
        with self.connection:
            self.connection.execute(
                "INSERT INTO performance_snapshots VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (
                    snapshot_id,
                    receipt_id,
                    checkpoint,
                    due_at,
                    collected_at,
                    canonical_json(requested_coverage),
                    canonical_json(returned_coverage) if returned_coverage is not None else None,
                    canonical_json(observations),
                    canonical_json(retention_observation),
                    maturity,
                    canonical_json(api_context),
                    digest(facts),
                    canonical_json(provider_payload) if provider_payload is not None else None,
                    digest(provider_payload) if provider_payload is not None else None,
                ),
            )
        return self.get_performance_snapshot(snapshot_id)

    def get_performance_snapshot(self, snapshot_id: str) -> PerformanceSnapshot:
        row = self.connection.execute(
            "SELECT * FROM performance_snapshots WHERE id = ?", (snapshot_id,)
        ).fetchone()
        if row is None:
            raise KeyError(snapshot_id)
        return PerformanceSnapshot(
            row["id"],
            row["receipt_id"],
            row["checkpoint"],
            row["due_at"],
            row["collected_at"],
            json.loads(row["requested_coverage_json"]),
            (
                json.loads(row["returned_coverage_json"])
                if row["returned_coverage_json"] is not None
                else None
            ),
            json.loads(row["metrics_json"]) if row["metrics_json"] is not None else None,
            json.loads(row["retention_json"]) if row["retention_json"] is not None else None,
            row["maturity"],
            json.loads(row["api_context_json"]) if row["api_context_json"] is not None else None,
            row["observation_digest"],
            (
                json.loads(row["provider_payload_json"])
                if row["provider_payload_json"] is not None
                else None
            ),
            row["provider_purged_at"],
        )

    def purge_provider_snapshot_payload(self, table: str, snapshot_id: str) -> None:
        """Purge all API-origin fields of one snapshot, not only its raw payload."""

        if table not in {"publication_status_snapshots", "performance_snapshots"}:
            raise ValueError("Only designated provider snapshots may be purged.")
        columns = (
            "privacy, processing, verification, api_locked, observed_at, observation_digest, "
            "provider_payload_json, provider_payload_digest"
            if table == "publication_status_snapshots"
            else "due_at, collected_at, returned_coverage_json, metrics_json, retention_json, "
            "maturity, api_context_json, observation_digest, provider_payload_json, "
            "provider_payload_digest"
        )
        with self.connection:
            row = self.connection.execute(
                f"SELECT provider_purged_at FROM {table} WHERE id = ?", (snapshot_id,)
            ).fetchone()
            if row is None:
                raise KeyError(snapshot_id)
            if row["provider_purged_at"] is None:
                assignments = ", ".join(f"{column.strip()} = NULL" for column in columns.split(","))
                self.connection.execute(
                    f"UPDATE {table} SET {assignments}, provider_purged_at = ? WHERE id = ?",
                    (stamp(), snapshot_id),
                )

    def purge_publication_api_data(self, publication_id: str) -> None:
        """Remove provider-origin responses/hashes but retain authored FK/approval lineage."""

        publication = self.get_platform_publication(publication_id)
        with self.connection:
            receipts = self.connection.execute(
                "SELECT id FROM publication_receipts WHERE publication_id = ?",
                (publication_id,),
            ).fetchall()
            for receipt in receipts:
                self.connection.execute(
                    "UPDATE performance_snapshots SET due_at = NULL, collected_at = NULL, "
                    "returned_coverage_json = NULL, metrics_json = NULL, retention_json = NULL, "
                    "maturity = NULL, api_context_json = NULL, observation_digest = NULL, "
                    "provider_payload_json = NULL, provider_payload_digest = NULL, "
                    "provider_purged_at = ? WHERE receipt_id = ? AND provider_purged_at IS NULL",
                    (stamp(), receipt["id"]),
                )
            self.connection.execute(
                "UPDATE publication_receipts SET public_at = NULL, "
                "first_public_observed_at = NULL, receipt_digest = NULL, "
                "provider_purged_at = ? WHERE publication_id = ? AND provider_purged_at IS NULL",
                (stamp(), publication_id),
            )
            self.connection.execute(
                "UPDATE publication_status_snapshots SET privacy = NULL, processing = NULL, "
                "verification = NULL, api_locked = NULL, observed_at = NULL, "
                "observation_digest = NULL, provider_payload_json = NULL, "
                "provider_payload_digest = NULL, provider_purged_at = ? "
                "WHERE publication_id = ? AND provider_purged_at IS NULL",
                (stamp(), publication_id),
            )
            operations = self.connection.execute(
                "SELECT upload_operation_id FROM platform_publications WHERE id = ?",
                (publication_id,),
            ).fetchone()
            release_ids = self.connection.execute(
                "SELECT release_operation_id FROM publication_receipts WHERE publication_id = ?",
                (publication_id,),
            ).fetchall()
            for operation_id in [
                operations["upload_operation_id"],
                *[row["release_operation_id"] for row in release_ids],
            ]:
                self._clear_provider_operation_evidence(operation_id)
            if publication.identity_source == "api" and publication.provider_purged_at is None:
                self.connection.execute(
                    "UPDATE platform_publications SET remote_id = NULL, binding_digest = NULL, "
                    "provider_purged_at = ? WHERE id = ?",
                    (stamp(), publication_id),
                )

    def _clear_provider_operation_evidence(self, operation_id: str) -> None:
        self.connection.execute(
            "UPDATE publication_operation_events SET provider_evidence_json = NULL, "
            "provider_evidence_digest = NULL, provider_purged_at = ? "
            "WHERE operation_id = ? AND provider_evidence_json IS NOT NULL "
            "AND provider_purged_at IS NULL",
            (stamp(), operation_id),
        )

    def purge_all_youtube_api_data(self) -> dict[str, int]:
        """Delete every stored YouTube API-origin field via the existing purge rules.

        Conveyor-authored records (packages, approvals, intents, founder-attested identities,
        operation journals) remain; only provider-origin values and hashes are removed.
        """

        publications = [
            row["id"]
            for row in self.connection.execute(
                "SELECT id FROM platform_publications ORDER BY id"
            ).fetchall()
        ]
        for publication_id in publications:
            self.purge_publication_api_data(publication_id)
        operations = [
            row["operation_id"]
            for row in self.connection.execute(
                "SELECT DISTINCT operation_id FROM publication_operation_events "
                "WHERE provider_evidence_json IS NOT NULL AND provider_purged_at IS NULL"
            ).fetchall()
        ]
        for operation_id in operations:
            self.purge_provider_operation_evidence(operation_id)
        return {"publications": len(publications), "operations": len(operations)}

    def purge_stale_youtube_api_data(self, cutoff: datetime) -> dict[str, int]:
        """Delete YouTube API payloads not refreshed since ``cutoff`` (30-day rule).

        A publication's API identity counts as refreshed by a verified status observation
        newer than the cutoff; observation is the refresh path, deletion the default.
        """

        def older(value: str | None) -> bool:
            try:
                moment = datetime.fromisoformat(value) if value else None
            except ValueError:
                moment = None
            return moment is None or moment < cutoff

        counts = {
            "status_snapshots": 0,
            "performance_snapshots": 0,
            "operations": 0,
            "publications": 0,
        }
        for row in self.connection.execute(
            "SELECT id, observed_at FROM publication_status_snapshots "
            "WHERE provider_purged_at IS NULL"
        ).fetchall():
            if older(row["observed_at"]):
                self.purge_provider_snapshot_payload("publication_status_snapshots", row["id"])
                counts["status_snapshots"] += 1
        for row in self.connection.execute(
            "SELECT id, collected_at FROM performance_snapshots WHERE provider_purged_at IS NULL"
        ).fetchall():
            if older(row["collected_at"]):
                self.purge_provider_snapshot_payload("performance_snapshots", row["id"])
                counts["performance_snapshots"] += 1
        stale_operations = {
            row["operation_id"]
            for row in self.connection.execute(
                "SELECT operation_id, created_at FROM publication_operation_events "
                "WHERE provider_evidence_json IS NOT NULL AND provider_purged_at IS NULL"
            ).fetchall()
            if older(row["created_at"])
        }
        for operation_id in sorted(stale_operations):
            self.purge_provider_operation_evidence(operation_id)
            counts["operations"] += 1
        for row in self.connection.execute(
            "SELECT id, identified_at FROM platform_publications WHERE identity_source = 'api' "
            "AND remote_id IS NOT NULL AND provider_purged_at IS NULL"
        ).fetchall():
            fresh = self.connection.execute(
                "SELECT observed_at FROM publication_status_snapshots WHERE publication_id = ? "
                "AND verification = 'passed' AND provider_purged_at IS NULL",
                (row["id"],),
            ).fetchall()
            if older(row["identified_at"]) and all(older(item["observed_at"]) for item in fresh):
                self.purge_publication_api_data(row["id"])
                counts["publications"] += 1
        return counts

    def purge_provider_operation_evidence(self, operation_id: str) -> None:
        """Allow deletion even for a dispatched API operation with no bound publication."""

        self.get_publication_operation(operation_id)
        with self.connection:
            self._clear_provider_operation_evidence(operation_id)

    def create_learning_assessment(
        self,
        assessment_id: str,
        snapshot_ids: list[str],
        feature: str,
        outcome: str,
        interpretation: str,
        confidence: str,
        confounds: list[str],
        recommendation: str,
        evidence_tier: str,
        producer: str,
        predecessor_id: str | None = None,
    ) -> LearningAssessment:
        _required_text(assessment_id, feature, outcome, interpretation, recommendation, producer)
        if not snapshot_ids or len(set(snapshot_ids)) != len(snapshot_ids):
            raise ValueError("Learning needs distinct exact supporting observations.")
        snapshots = [self.get_performance_snapshot(item) for item in snapshot_ids]
        receipts = [self.get_publication_receipt(item.receipt_id) for item in snapshots]
        publication_ids = sorted({item.publication_id for item in receipts})
        if evidence_tier in {"repeated", "consequential_review"} and len(publication_ids) < 3:
            raise ValueError("A one-item assessment cannot change routine strategy.")
        if evidence_tier == "consequential_review" and len(publication_ids) < 5:
            raise ValueError("Consequential strategy review needs stronger comparable evidence.")
        if predecessor_id is not None:
            self.get_learning_assessment(predecessor_id)
        if not isinstance(confounds, list):
            raise ValueError("Confounds must be a frozen list.")
        facts = {
            "snapshot_ids": sorted(snapshot_ids),
            "publication_ids": publication_ids,
            "predecessor_id": predecessor_id,
            "feature": feature,
            "outcome": outcome,
            "interpretation": interpretation,
            "confidence": confidence,
            "confounds": confounds,
            "recommendation": recommendation,
            "evidence_tier": evidence_tier,
            "producer": producer,
        }
        with self.connection:
            self.connection.execute(
                "INSERT INTO learning_assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    assessment_id,
                    predecessor_id,
                    feature,
                    outcome,
                    interpretation,
                    confidence,
                    canonical_json(confounds),
                    recommendation,
                    evidence_tier,
                    producer,
                    digest(facts),
                    stamp(),
                ),
            )
            self.connection.executemany(
                "INSERT INTO learning_assessment_evidence VALUES (?, ?)",
                [(assessment_id, item) for item in sorted(snapshot_ids)],
            )
        return self.get_learning_assessment(assessment_id)

    def get_learning_assessment(self, assessment_id: str) -> LearningAssessment:
        row = self.connection.execute(
            "SELECT * FROM learning_assessments WHERE id = ?", (assessment_id,)
        ).fetchone()
        if row is None:
            raise KeyError(assessment_id)
        evidence = tuple(
            item[0]
            for item in self.connection.execute(
                "SELECT performance_snapshot_id FROM learning_assessment_evidence "
                "WHERE assessment_id = ? ORDER BY performance_snapshot_id",
                (assessment_id,),
            )
        )
        publications = tuple(
            item[0]
            for item in self.connection.execute(
                "SELECT DISTINCT r.publication_id FROM learning_assessment_evidence e "
                "JOIN performance_snapshots p ON p.id = e.performance_snapshot_id "
                "JOIN publication_receipts r ON r.id = p.receipt_id WHERE e.assessment_id = ? "
                "ORDER BY r.publication_id",
                (assessment_id,),
            )
        )
        return LearningAssessment(
            row["id"],
            row["predecessor_id"],
            row["feature"],
            row["outcome"],
            row["interpretation"],
            row["confidence"],
            json.loads(row["confounds_json"]),
            row["recommendation"],
            row["evidence_tier"],
            row["producer"],
            row["assessment_digest"],
            row["created_at"],
            evidence,
            publications,
        )

    def record_learning_application(
        self,
        application_id: str,
        assessment_id: str,
        target_kind: str,
        target_id: str,
        decision_reference: str,
        context: dict[str, Any],
        actor: str,
        founder_reference: str | None = None,
    ) -> LearningApplication:
        assessment = self.get_learning_assessment(assessment_id)
        targets = {
            "opportunity": "opportunity_id",
            "hook": "hook_option_id",
            "script": "script_id",
            "visual_plan": "visual_plan_id",
            "final_media_input": "final_media_input_snapshot_id",
        }
        if target_kind not in targets:
            raise ValueError("Learning target must be an existing typed content record.")
        _required_text(application_id, target_id, decision_reference, actor)
        if assessment.evidence_tier == "consequential_review" and not founder_reference:
            raise ValueError("Consequential learning application requires founder authority.")
        safe_evidence(context)
        columns = {
            key: target_id if key == targets[target_kind] else None for key in targets.values()
        }
        change_hash = digest(
            {
                "assessment_id": assessment_id,
                "target_kind": target_kind,
                "target_id": target_id,
                "decision_reference": decision_reference,
                "context": context,
            }
        )
        with self.connection:
            self.connection.execute(
                "INSERT INTO learning_applications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    application_id,
                    assessment_id,
                    columns["opportunity_id"],
                    columns["hook_option_id"],
                    columns["script_id"],
                    columns["visual_plan_id"],
                    columns["final_media_input_snapshot_id"],
                    decision_reference,
                    canonical_json(context),
                    change_hash,
                    founder_reference,
                    actor,
                    stamp(),
                ),
            )
        return LearningApplication(
            application_id,
            assessment_id,
            target_kind,
            target_id,
            decision_reference,
            context,
            change_hash,
            founder_reference,
            actor,
            self.connection.execute(
                "SELECT created_at FROM learning_applications WHERE id = ?", (application_id,)
            ).fetchone()[0],
        )
