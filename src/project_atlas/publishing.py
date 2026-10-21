"""Bounded publishing orchestration with separately gated adapter capabilities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any, Protocol

from project_atlas import publishing_analytics as analytics
from project_atlas.media import LocalMediaStorage
from project_atlas.persistence import AtlasRepository
from project_atlas.publishing_credits import source_credits
from project_atlas.publishing_state import (
    ANALYTICS_SNAPSHOT_SCHEMA,
    CONFIRMATION_TTL,
    ON_DEMAND_SERIES,
    SCHEDULED_TRANSITION_SCHEMA,
    SCHEDULED_UPLOAD_SCHEMA,
    TARGET_CHANNEL,
    LearningAssessment,
    PerformanceSnapshot,
    PlatformPublication,
    PublicationOperation,
    PublicationReceipt,
    PublicationStatusSnapshot,
    PublishingPackage,
    is_never_release,
    is_on_demand,
    is_retrospective,
    publish_at_wire,
    timing_is_open,
    validate_publish_at,
)


@dataclass(frozen=True)
class TransferResult:
    """Provider-neutral, sanitized result; session_ref is an opaque protected-store reference."""

    classification: str  # succeeded, partial, transient, failed, unknown
    channel_id: str
    remote_id: str | None = None
    acknowledged_bytes: int | None = None
    session_ref: str | None = None
    reason: str | None = None
    # Sanitized provider facts (privacy/status/timestamps); never credentials or session URLs.
    evidence: dict[str, Any] | None = None


@dataclass(frozen=True)
class RemoteObservation:
    remote_id: str
    channel_id: str
    privacy: str | None
    processing: str | None
    metadata_matches: bool | None
    api_locked: bool
    observed_at: str
    public_at: str | None = None
    provider_payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class AggregateObservation:
    due_at: str
    collected_at: str
    requested_coverage: dict[str, Any]
    returned_coverage: dict[str, Any] | None
    metrics: dict[str, int | float | None]
    availability: dict[str, str]
    maturity: str
    api_context: dict[str, Any]
    provider_payload: dict[str, Any] | None = None
    retention: dict[str, Any] | None = None
    missing_reasons: dict[str, str] | None = None


def _same_instant(left: Any, right: Any) -> bool:
    """Two RFC 3339 timestamps denote the same instant (YouTube may add milliseconds)."""

    try:
        values = [
            datetime.fromisoformat(str(item).replace("Z", "+00:00")) for item in (left, right)
        ]
    except ValueError:
        return False
    return all(item.tzinfo is not None for item in values) and values[0] == values[1]


class PublishingAdapter(Protocol):
    """Narrow capability port; tests inject a deterministic fake, never a live client."""

    def authenticated_channel(self) -> str: ...

    def begin_private_transfer(
        self, package: PublishingPackage, operation: PublicationOperation
    ) -> TransferResult: ...

    def inspect_or_resume_transfer(self, operation: PublicationOperation) -> TransferResult: ...

    def observe_remote(
        self, remote_id: str, package: PublishingPackage | None = None
    ) -> RemoteObservation: ...

    def request_public_transition(
        self, publication: PlatformPublication, operation: PublicationOperation
    ) -> TransferResult: ...

    def aggregate_performance(
        self, receipt: PublicationReceipt, checkpoint: str
    ) -> AggregateObservation: ...


class PublishingService:
    """Explicit local commands and fail-closed reconciliation, without jobs or HTTP handlers."""

    def __init__(
        self,
        repository: AtlasRepository,
        storage: LocalMediaStorage,
        adapter: PublishingAdapter,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.adapter = adapter
        self.clock = clock or (lambda: datetime.now(UTC))

    def _target(self, expected: str) -> None:
        if expected != TARGET_CHANNEL or self.adapter.authenticated_channel() != expected:
            raise ValueError(
                "Authenticated publishing channel differs from the exact pilot target."
            )

    def _authority(self, package: PublishingPackage, mode: str, action: str) -> None:
        if action == "release" and is_never_release(package.manifest):
            # The stored manual route is a compatibility sentinel, never release authority.
            raise ValueError("A never-release package can never be released.")
        approval = self.repository.effective_publication_approval(package.id)
        route = (
            approval.transfer_route
            if approval and action == "upload"
            else (approval.release_route if approval else None)
        )
        if approval is None or approval.package_digest != package.package_digest or route != mode:
            raise ValueError("Exact effective founder approval and route are required.")

    def _historical_authority(
        self, package: PublishingPackage, operation: PublicationOperation
    ) -> None:
        """Verify original approved lineage for observation, not a new mutation."""

        approval = self.repository.get_publication_gate_decision(operation.gate_decision_id)
        route = (
            approval.transfer_route if operation.action_kind == "upload" else approval.release_route
        )
        if (
            approval.decision != "approve"
            or approval.package_id != package.id
            or approval.package_digest != package.package_digest
            or operation.package_id != package.id
            or route != operation.execution_mode
        ):
            raise ValueError("Operation lacks exact original founder authority.")

    def _public_upload_governance(
        self, package: PublishingPackage, exclude_operation_id: str | None = None
    ) -> None:
        """A public or unlisted videos.insert is a release: apply the existing release authority."""

        if is_never_release(package.manifest):
            raise ValueError(
                "This package is never-release: a public or unlisted upload is refused."
            )
        approval = self.repository.effective_publication_approval(package.id)
        if approval is None or approval.release_route != "api":
            raise ValueError(
                "A public or unlisted upload needs founder approval for an API public release."
            )
        if not timing_is_open(approval.timing, self.clock()):
            raise ValueError(
                "A public or unlisted upload is only allowed inside the approved publication time."
            )
        conflict = self.repository.release_week_conflict(package, exclude_operation_id)
        if conflict:
            raise ValueError(conflict)

    @staticmethod
    def _refuse_retrospective(package: PublishingPackage) -> None:
        """A founder-attested past release is a record only: no observation or new action."""

        if is_retrospective(package.manifest):
            raise ValueError(
                "A retrospective founder-attested package records a past external release; it "
                "authorizes no observation, upload, release or receipt."
            )

    @staticmethod
    def _refuse_never_release(package: PublishingPackage) -> None:
        """Every release, transition and receipt path stops here for a never-release package."""

        if is_never_release(package.manifest):
            raise ValueError("A never-release package can never be released.")

    def _expected(self, package: PublishingPackage, upload_operation_id: str) -> PublishingPackage:
        """Values the remote object must match: founder-confirmed upload values when present."""

        intent = self.repository.get_publication_operation(upload_operation_id).intent
        if "title" not in intent:
            return package
        return replace(
            package,
            manifest={
                **package.manifest,
                "title": intent["title"],
                "description": intent["description"],
            },
        )

    def prepare_package(
        self,
        package_id: str,
        pilot_key: str,
        pilot_slot: int,
        version: int,
        artifact_id: str,
        manifest: dict[str, Any],
        predecessor_id: str | None = None,
    ) -> PublishingPackage:
        artifact = self.repository.get_final_media_artifact(artifact_id)
        self.storage.read_verified(artifact.storage_path, artifact.content_digest)
        if pilot_key == ON_DEMAND_SERIES:
            manifest = self._on_demand_manifest(artifact_id, manifest)
        required = {
            "title",
            "description",
            "tags",
            "language",
            "caption_artifact",
            "cover_choice",
            "compliance",
            "audience",
            "private_first",
            "transfer_route",
            "release_route",
            "publication_timing",
            "pilot_slot",
        }
        if not isinstance(manifest, dict) or not required <= manifest.keys():
            raise ValueError("The exact external publication proposition is incomplete.")
        if manifest["pilot_slot"] != pilot_slot or manifest["private_first"] is not True:
            raise ValueError("Package manifest must freeze the exact private-first pilot slot.")
        if manifest["transfer_route"] not in {"api", "manual"} or manifest["release_route"] not in {
            "api",
            "manual",
        }:
            raise ValueError("Transfer and public-transition routes must be explicit.")
        return self.repository.create_publishing_package(
            package_id,
            pilot_key,
            pilot_slot,
            version,
            artifact_id,
            artifact.content_digest,
            TARGET_CHANNEL,
            manifest,
            predecessor_id,
        )

    def founder_accepted_run(self, artifact_id: str) -> str:
        """The production run whose current, founder-accepted render is exactly this artifact."""

        rows = self.repository.connection.execute(
            "SELECT DISTINCT production_run_id FROM production_run_evidence "
            "WHERE evidence_type = 'render' AND final_media_artifact_id = ?",
            (artifact_id,),
        ).fetchall()
        if len(rows) != 1:
            raise ValueError("The artifact is not the render of exactly one production run.")
        run_id = rows[0]["production_run_id"]
        latest = self.repository.latest_production_run_event(run_id)
        if latest is None or latest.status != "founder_accepted":
            raise ValueError(f"Production {run_id} is not founder-accepted.")
        renders = self.repository.list_production_evidence(run_id, "render")
        current = max(renders, key=lambda item: int(item.id.rsplit(":", 1)[1]))
        if current.final_media_artifact_id != artifact_id:
            raise ValueError("Only the production's current render can be published.")
        whole = sorted(
            (
                review
                for review in self.repository.list_production_qa_reviews(run_id)
                if review.scope == "whole_video"
            ),
            key=lambda review: (review.created_at, review.id),
        )
        if (
            not whole
            or whole[-1].outcome != "passed"
            or whole[-1].final_media_artifact_id != artifact_id
        ):
            raise ValueError("The current render has no passing whole-video review.")
        founder = self.repository.connection.execute(
            "SELECT outcome FROM production_founder_reviews WHERE production_run_id = ?",
            (run_id,),
        ).fetchall()
        if [row["outcome"] for row in founder] != ["accepted"]:
            raise ValueError("The production lacks exactly one founder acceptance.")
        return run_id

    def _on_demand_manifest(self, artifact_id: str, manifest: Any) -> dict[str, Any]:
        """Freeze the projected source credits; the description must carry them exactly."""

        if not isinstance(manifest, dict):
            raise ValueError("The exact external publication proposition is incomplete.")
        run_id = self.founder_accepted_run(artifact_id)
        credits = source_credits(self.repository, run_id)
        if "source_credits" in manifest and manifest["source_credits"] != credits:
            raise ValueError("Supplied source credits differ from the production's provenance.")
        description = manifest.get("description")
        if not isinstance(description, str) or credits["text"] not in description:
            raise ValueError("The description must include the projected source credits exactly.")
        return {**manifest, "source_credits": credits, "production_run_id": run_id}

    def approve_package(
        self, decision_id: str, package_id: str, founder_actor: str, comment: str | None = None
    ):
        package = self.repository.get_publishing_package(package_id)
        return self.repository.record_publication_gate_decision(
            decision_id,
            package_id,
            package.package_digest,
            founder_actor,
            "approve",
            package.manifest["transfer_route"],
            package.manifest["release_route"],
            package.manifest["publication_timing"],
            comment,
        )

    UPLOAD_PRIVACY = frozenset({"private", "unlisted", "public"})

    def reserve_upload(
        self, package_id: str, attempt: int = 1, upload: dict[str, Any] | None = None
    ) -> PublicationOperation:
        """Reserve one upload; ``upload`` freezes the founder-confirmed upload values.

        Confirmed values (title, description, privacy) are bound into the operation intent and
        sent exactly as confirmed; without them an upload stays the historical private-first
        package transfer.
        """

        package = self.repository.get_publishing_package(package_id)
        self._refuse_retrospective(package)
        self._target(package.channel_id)
        self._authority(package, package.manifest["transfer_route"], "upload")
        if attempt < 1:
            raise ValueError("Technical attempt number must be positive.")
        if is_on_demand(package.manifest):
            return self._reserve_scheduled_upload(package, attempt, upload)
        intent = {
            "schema": "private-transfer-v1",
            "package_digest": package.package_digest,
            "artifact_digest": package.artifact_digest,
            "channel_id": package.channel_id,
            "pilot_slot": package.pilot_slot,
            "attempt": attempt,
            "privacy": "private",
        }
        if upload is not None:
            actor = upload.get("founder_actor") if isinstance(upload, dict) else None
            if (
                not isinstance(upload, dict)
                or upload.get("founder_confirmed") is not True
                or not isinstance(actor, str)
                or not actor.strip()
                or not isinstance(upload.get("title"), str)
                or not isinstance(upload.get("description"), str)
                or upload.get("privacy") not in self.UPLOAD_PRIVACY
            ):
                raise ValueError(
                    "Upload requires explicit founder-confirmed title, description and privacy."
                )
            if upload["privacy"] != "private":
                self._public_upload_governance(package)
            intent.update(
                {
                    "schema": "confirmed-upload-v1",
                    "privacy": upload["privacy"],
                    "title": upload["title"],
                    "description": upload["description"],
                    "founder_confirmation": {
                        "actor": actor.strip(),
                        "confirmed_at": self.clock().replace(microsecond=0).isoformat(),
                    },
                }
            )
        return self.repository.reserve_publication_operation(
            package_id,
            "upload",
            package.manifest["transfer_route"],
            intent,
        )

    def _reserve_scheduled_upload(
        self, package: PublishingPackage, attempt: int, upload: dict[str, Any] | None
    ) -> PublicationOperation:
        """One founder confirmation = one scheduled videos.insert (private + publishAt)."""

        actor = upload.get("founder_actor") if isinstance(upload, dict) else None
        if (
            not isinstance(upload, dict)
            or upload.get("founder_confirmed") is not True
            or not isinstance(actor, str)
            or not actor.strip()
            or not isinstance(upload.get("title"), str)
            or not isinstance(upload.get("description"), str)
        ):
            raise ValueError(
                "A scheduled publication needs the founder-confirmed title, description and "
                "publication time."
            )
        if upload.get("privacy") != "private":
            raise ValueError(
                "A scheduled publication is uploaded private; YouTube makes it public at publishAt."
            )
        now = self.clock()
        publish_at = validate_publish_at(upload.get("publish_at"), now)
        credits = package.manifest["source_credits"]
        if credits["text"] not in upload["description"]:
            raise ValueError("The confirmed description must keep the source credits exactly.")
        confirmed_at = now.replace(microsecond=0)
        intent = {
            "schema": SCHEDULED_UPLOAD_SCHEMA,
            "package_digest": package.package_digest,
            "artifact_digest": package.artifact_digest,
            "channel_id": package.channel_id,
            "pilot_slot": package.pilot_slot,
            "attempt": attempt,
            "privacy": "private",
            "publish_at": publish_at_wire(publish_at),
            "title": upload["title"],
            "description": upload["description"],
            "source_credits_digest": credits["digest"],
            "founder_confirmation": {
                "actor": actor.strip(),
                "confirmed_at": confirmed_at.isoformat(),
                "expires_at": (confirmed_at + CONFIRMATION_TTL).isoformat(),
            },
        }
        return self.repository.reserve_publication_operation(
            package.id, "upload", package.manifest["transfer_route"], intent
        )

    def _scheduled_transition(self, upload: PublicationOperation) -> PublicationOperation | None:
        rows = self.repository.connection.execute(
            "SELECT id FROM publication_operations "
            "WHERE package_id = ? AND action_kind = 'release'",
            (upload.package_id,),
        ).fetchall()
        for row in rows:
            operation = self.repository.get_publication_operation(row["id"])
            if operation.intent.get("upload_operation_id") == upload.id:
                return operation
        return None

    def _record_scheduled_commitment(
        self, upload_operation_id: str, publication: PlatformPublication
    ) -> PublicationOperation:
        """Record YouTube's accepted schedule as a pending transition Conveyor never dispatches."""

        upload = self.repository.get_publication_operation(upload_operation_id)
        existing = self._scheduled_transition(upload)
        if existing is not None:
            return existing
        package = self.repository.get_publishing_package(upload.package_id)
        evidence = next(
            (
                event.provider_evidence or {}
                for event in self.repository.get_publication_operation_events(upload.id)
                if event.kind == "remote_identity_observed"
            ),
            {},
        )
        returned = evidence.get("returned_publish_at")
        provider = {
            "returned_publish_at": returned,
            "returned_privacy": evidence.get("returned_privacy"),
        }
        transition = self.repository.reserve_publication_operation(
            package.id,
            "release",
            "api",
            {
                "schema": SCHEDULED_TRANSITION_SCHEMA,
                "package_digest": package.package_digest,
                "upload_operation_id": upload.id,
                "publication_id": publication.id,
                "publish_at": upload.intent["publish_at"],
            },
            self.clock(),
        )
        # Without YouTube echoing the exact private schedule the public outcome is unknown, not
        # refused: the transition stays reserved (pending) for the founder to check in YouTube
        # Studio, and a receipt still needs an independently observed public state.
        if (
            _same_instant(returned, upload.intent["publish_at"])
            and evidence.get("returned_privacy") == "private"
        ):
            self.repository.append_publication_operation_event(
                transition.id,
                "progress",
                "YouTube",
                {
                    "kind": "scheduled-commitment-accepted",
                    "executor": "youtube-scheduled-publish",
                    "conveyor_dispatch": False,
                    "publish_at": upload.intent["publish_at"],
                },
                provider,
            )
        return self.repository.get_publication_operation(transition.id)

    def reconcile_scheduled_publication(
        self, receipt_id: str, status_id: str, publication_id: str
    ) -> PublicationReceipt:
        """Issue the receipt only once the exact video is independently observed public."""

        publication = self.repository.get_platform_publication(publication_id)
        if publication.remote_id is None:
            raise ValueError("Purged API identity cannot be reconciled as a new receipt.")
        package = self.repository.get_publishing_package(publication.package_id)
        if not is_on_demand(package.manifest):
            raise ValueError("Only on-demand scheduled publications reconcile here.")
        self._target(publication.channel_id)
        upload = self.repository.get_publication_operation(publication.upload_operation_id)
        transition = self._scheduled_transition(upload)
        if (
            transition is None
            and upload.intent.get("schema") == SCHEDULED_UPLOAD_SCHEMA
            and upload.outcome == "succeeded"
        ):
            # Recovery: the commitment was never recorded (a stop after the upload succeeded,
            # or an identity reconciled later). Recording it is idempotent and dispatches nothing.
            transition = self._record_scheduled_commitment(upload.id, publication)
        if (
            upload.intent.get("schema") == SCHEDULED_UPLOAD_SCHEMA
            and transition is not None
            and transition.outcome == "succeeded"
        ):
            return self._complete_scheduled_receipt(receipt_id, publication_id, transition)
        if (
            upload.intent.get("schema") != SCHEDULED_UPLOAD_SCHEMA
            or upload.outcome != "succeeded"
            or transition is None
            or transition.outcome != "pending"
        ):
            raise ValueError("No accepted, pending scheduled transition exists for this video.")
        publish_at = datetime.fromisoformat(upload.intent["publish_at"].replace("Z", "+00:00"))
        if self.clock() < publish_at:
            raise ValueError("The scheduled publication time has not arrived; nothing recorded.")
        observation = self.adapter.observe_remote(
            publication.remote_id, self._expected(package, publication.upload_operation_id)
        )
        if (
            observation.remote_id != publication.remote_id
            or observation.channel_id != publication.channel_id
            or observation.metadata_matches is not True
            or observation.privacy != "public"
            or observation.processing != "succeeded"
            or observation.api_locked
            or observation.public_at is None
        ):
            raise ValueError(
                "The exact video is not yet independently observed public; nothing recorded."
            )
        if not _same_instant(observation.public_at, upload.intent["publish_at"]) and (
            datetime.fromisoformat(observation.public_at.replace("Z", "+00:00")) < publish_at
        ):
            # Public before the schedule: not YouTube's scheduled transition (for example a
            # manual Studio publication). It needs founder review, not an automatic receipt.
            raise ValueError("The video became public before its scheduled time; nothing recorded.")
        public_time = datetime.fromisoformat(observation.public_at.replace("Z", "+00:00"))
        if public_time <= datetime.fromisoformat(publication.identified_at) or (
            public_time > datetime.fromisoformat(observation.observed_at.replace("Z", "+00:00"))
        ):
            # The receipt would refuse these times; refuse before writing anything.
            raise ValueError("The observed public time is inconsistent; nothing recorded.")
        status = self.repository.append_publication_status(
            status_id,
            publication_id,
            observation.privacy,
            observation.processing,
            "passed",
            False,
            "offline-adapter-v1",
            observation.observed_at,
            observation.provider_payload,
        )
        # Conveyor-authored lineage stays in the immutable evidence; YouTube's public time is
        # provider evidence, so the 30-day refresh-or-delete rule can purge it.
        self.repository.append_publication_operation_event(
            transition.id,
            "succeeded",
            "Conveyor",
            {"method": "independent-public-observation", "public_status_id": status.id},
            {"public_at": observation.public_at},
        )
        return self._complete_scheduled_receipt(
            receipt_id, publication_id, self.repository.get_publication_operation(transition.id)
        )

    def _complete_scheduled_receipt(
        self, receipt_id: str, publication_id: str, transition: PublicationOperation
    ) -> PublicationReceipt:
        """Create the receipt from the transition's recorded public observation.

        The status, the transition's success and the receipt are separate commits. A retry after
        a failure between them finishes from what the success event recorded: no new YouTube
        observation, status or event. A publication that already has its receipt is refused.

        YouTube's public time is read only from the event's purgeable provider evidence. Recovery
        refuses once that evidence is purged, and never uses a public time stored in the immutable
        Conveyor evidence by earlier code.
        """

        row = self.repository.connection.execute(
            "SELECT id FROM publication_receipts WHERE release_operation_id = ?",
            (transition.id,),
        ).fetchone()
        if row is not None:
            raise ValueError(
                f"This scheduled publication already has receipt {row['id']}; nothing recorded."
            )
        succeeded = self.repository.get_publication_operation_events(transition.id)[-1]
        observed = succeeded.evidence
        if (
            succeeded.kind != "succeeded"
            or observed.get("method") != "independent-public-observation"
            or not observed.get("public_status_id")
        ):
            raise ValueError("The succeeded transition lacks its recorded public observation.")
        if "public_at" in observed:
            raise ValueError(
                "This success event stores the public time in immutable evidence (earlier format); "
                "recovery refuses to use it. Nothing recorded."
            )
        if succeeded.provider_purged_at is not None:
            raise ValueError(
                "The recorded public time was purged under the 30-day rule; the receipt cannot be "
                "recovered from it. Nothing recorded."
            )
        public_at = (succeeded.provider_evidence or {}).get("public_at")
        if not public_at:
            raise ValueError("The succeeded transition lacks its recorded public time.")
        return self.repository.create_publication_receipt(
            receipt_id,
            publication_id,
            transition.id,
            observed["public_status_id"],
            public_at,
            "provider-public-state",
            "second",
        )

    def _record_transfer(
        self, operation: PublicationOperation, result: TransferResult
    ) -> PlatformPublication | None:
        package = self.repository.get_publishing_package(operation.package_id)
        self._target(package.channel_id)
        if result.channel_id != package.channel_id:
            self.repository.append_publication_operation_event(
                operation.id,
                "outcome_unknown",
                "Conveyor",
                {"reason": "wrong-channel-after-dispatch"},
                {"reported_channel_id": result.channel_id},
            )
            raise ValueError("Provider result identifies the wrong channel.")
        if result.classification == "partial":
            if result.acknowledged_bytes is None or result.acknowledged_bytes < 0:
                raise ValueError("Partial transfer lacks an authoritative acknowledged byte count.")
            if result.session_ref and (
                "://" in result.session_ref or "Bearer " in result.session_ref
            ):
                raise ValueError("Only an opaque protected-store session reference is permitted.")
            self.repository.append_publication_operation_event(
                operation.id,
                "progress",
                "Conveyor",
                {"kind": "transfer-progress"},
                {
                    "acknowledged_bytes": result.acknowledged_bytes,
                    "protected_session_ref": result.session_ref,
                },
            )
            return None
        if result.classification == "transient":
            self.repository.append_publication_operation_event(
                operation.id,
                "progress",
                "Conveyor",
                {"kind": "provider-transient"},
                {"reason": result.reason},
            )
            return None
        if result.classification == "unknown":
            self.repository.append_publication_operation_event(
                operation.id,
                "outcome_unknown",
                "Conveyor",
                {"reason": "provider-unknown"},
                {"reason": result.reason or "response-lost"},
            )
            return None
        if result.classification == "failed":
            self.repository.append_publication_operation_event(
                operation.id,
                "failed",
                "Conveyor",
                {"reason": "definitive-provider-failure"},
                {"reason": result.reason or "definitive"},
            )
            return None
        if result.classification != "succeeded" or not result.remote_id:
            raise ValueError("Transfer success needs a stable remote identity.")
        self.repository.append_publication_operation_event(
            operation.id,
            "remote_identity_observed",
            "Conveyor",
            {"method": "provider-result"},
            {
                **(result.evidence or {}),
                "remote_id": result.remote_id,
                "channel_id": result.channel_id,
            },
        )
        self.repository.append_publication_operation_event(
            operation.id,
            "succeeded",
            "Conveyor",
            {"method": "provider-result"},
        )
        return self.repository.bind_platform_publication(
            f"platform-publication-{operation.operation_key}",
            package.id,
            operation.id,
            result.channel_id,
            result.remote_id,
            {"method": "provider-result"},
        )

    def begin_api_upload(self, operation_id: str) -> PlatformPublication | None:
        operation = self.repository.get_publication_operation(operation_id)
        package = self.repository.get_publishing_package(operation.package_id)
        if operation.action_kind != "upload" or operation.execution_mode != "api":
            raise ValueError("This command requires a reserved API private-upload operation.")
        self._refuse_retrospective(package)
        self._target(package.channel_id)
        self._authority(package, "api", "upload")
        if self.repository.get_publication_operation_events(operation_id)[-1].kind != "reserved":
            raise ValueError("Dispatched/uncertain upload must be inspected, not begun again.")
        if operation.intent.get("privacy", "private") != "private":
            # Re-check immediately before dispatch: the approved window can close.
            self._public_upload_governance(package, operation.id)
        if is_on_demand(package.manifest):
            self._check_scheduled_dispatch(operation)
        self.storage.read_verified(
            self.repository.get_final_media_artifact(package.final_media_artifact_id).storage_path,
            package.artifact_digest,
        )
        self.repository.append_publication_operation_event(
            operation_id, "dispatch_started", "Conveyor", {"action": "private-transfer"}
        )
        try:
            result = self.adapter.begin_private_transfer(package, operation)
            publication = self._record_transfer(
                self.repository.get_publication_operation(operation_id),
                result,
            )
            if publication is not None and is_on_demand(package.manifest):
                self._record_scheduled_commitment(operation_id, publication)
            return publication
        except Exception:
            if self.repository.get_publication_operation(operation_id).outcome == "pending":
                self.repository.append_publication_operation_event(
                    operation_id,
                    "outcome_unknown",
                    "Conveyor",
                    {"reason": "client-exception-after-dispatch"},
                )
            raise

    def _check_scheduled_dispatch(self, operation: PublicationOperation) -> None:
        """Immediately before dispatch: the confirmation is unexpired and publishAt still valid.

        A refused scheduled reservation is closed as failed (nothing was sent), so a fresh
        founder confirmation can replace it.
        """

        intent = operation.intent
        now = self.clock()
        reason = None
        if intent.get("schema") != SCHEDULED_UPLOAD_SCHEMA:
            reason = "An on-demand upload needs a scheduled founder confirmation."
        else:
            expires = datetime.fromisoformat(intent["founder_confirmation"]["expires_at"])
            if now > expires:
                reason = "The founder confirmation expired before dispatch; confirm again."
            else:
                try:
                    validate_publish_at(intent["publish_at"].replace("Z", "+00:00"), now)
                except ValueError as exc:
                    reason = f"The scheduled time is no longer valid: {exc}"
        if reason is not None:
            self.repository.append_publication_operation_event(
                operation.id, "failed", "Conveyor", {"reason": "refused-before-dispatch"}
            )
            raise ValueError(reason + " Nothing was sent to YouTube.")

    def inspect_or_resume_upload(self, operation_id: str) -> PlatformPublication | None:
        operation = self.repository.get_publication_operation(operation_id)
        package = self.repository.get_publishing_package(operation.package_id)
        self._target(package.channel_id)
        self._authority(package, operation.execution_mode, "upload")
        if (
            operation.action_kind != "upload"
            or operation.execution_mode != "api"
            or operation.outcome != "pending"
            or self.repository.get_publication_operation_events(operation_id)[-1].kind
            not in {"dispatch_started", "progress"}
        ):
            raise ValueError("Only a known active session can be inspected/resumed automatically.")
        try:
            result = self.adapter.inspect_or_resume_transfer(operation)
            publication = self._record_transfer(operation, result)
            if publication is not None and is_on_demand(package.manifest):
                self._record_scheduled_commitment(operation_id, publication)
            return publication
        except Exception:
            if self.repository.get_publication_operation(operation_id).outcome == "pending":
                self.repository.append_publication_operation_event(
                    operation_id,
                    "outcome_unknown",
                    "Conveyor",
                    {"reason": "inspection-exception"},
                )
            raise

    def reconcile_upload_identity(
        self, operation_id: str, remote_id: str, actor: str
    ) -> PlatformPublication:
        operation = self.repository.get_publication_operation(operation_id)
        package = self.repository.get_publishing_package(operation.package_id)
        self._target(package.channel_id)
        self._historical_authority(package, operation)
        if operation.action_kind != "upload" or operation.outcome != "unknown":
            raise ValueError("Only an uncertain upload may use identity reconciliation.")
        observation = self.adapter.observe_remote(remote_id, self._expected(package, operation.id))
        if (
            observation.remote_id != remote_id
            or observation.channel_id != package.channel_id
            or observation.metadata_matches is not True
            or observation.privacy != operation.intent.get("privacy", "private")
        ):
            raise ValueError(
                "Identity recovery needs an exact independently observed remote object."
            )
        self.repository.append_publication_operation_event(
            operation_id,
            "reconciled",
            actor,
            {
                "resolution": "succeeded",
                "method": "authenticated-remote-observation",
            },
        )
        return self.repository.bind_platform_publication(
            f"platform-publication-{operation.operation_key}",
            package.id,
            operation.id,
            package.channel_id,
            remote_id,
            {"method": "reconciliation"},
            "founder_manual",  # The identity was supplied for explicit human reconciliation.
        )

    def complete_manual_private_upload(
        self, operation_id: str, remote_id: str, founder_actor: str
    ) -> PlatformPublication:
        operation = self.repository.get_publication_operation(operation_id)
        package = self.repository.get_publishing_package(operation.package_id)
        self._refuse_retrospective(package)
        self._target(package.channel_id)
        self._authority(package, "manual", "upload")
        if operation.action_kind != "upload" or operation.execution_mode != "manual":
            raise ValueError("Manual upload requires its approved reserved manual operation.")
        if operation.outcome != "pending":
            raise ValueError(
                "Completed/uncertain manual upload requires reconciliation, not repetition."
            )
        if self.repository.get_publication_operation_events(operation_id)[-1].kind == "reserved":
            self.repository.append_publication_operation_event(
                operation_id,
                "dispatch_started",
                founder_actor,
                {"action": "founder-Studio-private-upload"},
            )
        try:
            observation = self.adapter.observe_remote(remote_id, package)
        except Exception:
            self.repository.append_publication_operation_event(
                operation_id, "outcome_unknown", "Conveyor", {"reason": "manual-observation-lost"}
            )
            raise
        if (
            observation.remote_id != remote_id
            or observation.channel_id != package.channel_id
            or observation.metadata_matches is not True
            or observation.privacy != "private"
        ):
            self.repository.append_publication_operation_event(
                operation_id,
                "outcome_unknown",
                "Conveyor",
                {"reason": "manual-identity-unverified"},
            )
            raise ValueError("Manual transfer lacks independent exact remote verification.")
        self.repository.append_publication_operation_event(
            operation_id,
            "remote_identity_observed",
            founder_actor,
            {"remote_id": remote_id, "method": "founder-attested-Studio-action"},
        )
        self.repository.append_publication_operation_event(
            operation_id,
            "succeeded",
            "Conveyor",
            {"method": "independent-observation"},
        )
        return self.repository.bind_platform_publication(
            f"platform-publication-{operation.operation_key}",
            package.id,
            operation.id,
            package.channel_id,
            remote_id,
            {"method": "manual-attestation-plus-observation"},
            "founder_manual",
        )

    def observe_status(self, status_id: str, publication_id: str) -> PublicationStatusSnapshot:
        publication = self.repository.get_platform_publication(publication_id)
        if publication.remote_id is None:
            raise ValueError(
                "Purged API identity requires fresh authorized binding before observation."
            )
        package = self.repository.get_publishing_package(publication.package_id)
        self._refuse_retrospective(package)
        self._target(publication.channel_id)
        result = self.adapter.observe_remote(
            publication.remote_id, self._expected(package, publication.upload_operation_id)
        )
        if result.remote_id != publication.remote_id or result.channel_id != publication.channel_id:
            raise ValueError("Observed remote identity differs from bound lineage.")
        verification = (
            "passed"
            if result.metadata_matches is True
            else "failed" if result.metadata_matches is False else "unknown"
        )
        return self.repository.append_publication_status(
            status_id,
            publication_id,
            result.privacy,
            result.processing,
            verification,
            result.api_locked,
            "offline-adapter-v1",
            result.observed_at,
            result.provider_payload,
        )

    def reserve_release(self, publication_id: str) -> PublicationOperation:
        publication = self.repository.get_platform_publication(publication_id)
        package = self.repository.get_publishing_package(publication.package_id)
        self._refuse_retrospective(package)
        self._refuse_never_release(package)
        self._target(publication.channel_id)
        mode = package.manifest["release_route"]
        self._authority(package, mode, "release")
        if publication.remote_id is None:
            raise ValueError("Purged API identity cannot authorize a new public transition.")
        row = self.repository.connection.execute(
            "SELECT id FROM publication_status_snapshots WHERE publication_id = ? "
            "ORDER BY observed_at DESC, id DESC LIMIT 1",
            (publication_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Release needs a private-ready observation.")
        status = self.repository.get_publication_status(row["id"])
        if (
            status.privacy != "private"
            or status.processing != "succeeded"
            or status.verification != "passed"
            or status.api_locked
        ):
            raise ValueError("Remote object is not verified eligible private-ready.")
        intent = {
            "schema": "public-transition-v1",
            "package_digest": package.package_digest,
            "publication_id": publication_id,
            "channel_id": publication.channel_id,
            "pilot_slot": package.pilot_slot,
            "timing": package.manifest["publication_timing"],
        }
        return self.repository.reserve_publication_operation(
            package.id, "release", mode, intent, self.clock()
        )

    def begin_api_release(self, operation_id: str, publication_id: str) -> None:
        operation = self.repository.get_publication_operation(operation_id)
        publication = self.repository.get_platform_publication(publication_id)
        if publication.remote_id is None:
            raise ValueError("Purged API identity cannot be released without new authority.")
        package = self.repository.get_publishing_package(publication.package_id)
        self._refuse_retrospective(package)
        self._refuse_never_release(package)
        self._target(publication.channel_id)
        self._authority(package, "api", "release")
        if (
            operation.action_kind != "release"
            or operation.execution_mode != "api"
            or operation.package_id != package.id
            or self.repository.get_publication_operation_events(operation_id)[-1].kind != "reserved"
        ):
            raise ValueError("API release requires one exact untouched reserved operation.")
        # Re-check immediately before dispatch; a prior private-ready snapshot can stale.
        observed = self.adapter.observe_remote(
            publication.remote_id, self._expected(package, publication.upload_operation_id)
        )
        if (
            observed.remote_id != publication.remote_id
            or observed.channel_id != publication.channel_id
            or observed.privacy != "private"
            or observed.processing != "succeeded"
            or observed.metadata_matches is not True
            or observed.api_locked
        ):
            raise ValueError("Current remote state is not eligible for public transition.")
        if not timing_is_open(package.manifest["publication_timing"], self.clock()):
            raise ValueError("Approved exact publication time has expired or not begun.")
        self.repository.assert_release_week_clear(operation_id)
        self.repository.append_publication_operation_event(
            operation_id, "dispatch_started", "Conveyor", {"action": "approved-public-transition"}
        )
        try:
            result = self.adapter.request_public_transition(publication, operation)
            if (
                result.channel_id != publication.channel_id
                or result.remote_id != publication.remote_id
            ):
                raise ValueError("Release response identity is uncertain/wrong.")
            if result.classification == "succeeded":
                self.repository.append_publication_operation_event(
                    operation_id, "succeeded", "Conveyor", {"method": "provider-result"}
                )
            elif result.classification in {"unknown", "transient"}:
                self.repository.append_publication_operation_event(
                    operation_id,
                    "outcome_unknown",
                    "Conveyor",
                    {"reason": "provider-unknown"},
                    {"reason": result.reason},
                )
            elif result.classification == "failed":
                self.repository.append_publication_operation_event(
                    operation_id,
                    "failed",
                    "Conveyor",
                    {"reason": "definitive-provider-failure"},
                    {"reason": result.reason},
                )
            else:
                raise ValueError("Unexpected public-transition classification.")
        except Exception:
            if self.repository.get_publication_operation(operation_id).outcome == "pending":
                self.repository.append_publication_operation_event(
                    operation_id, "outcome_unknown", "Conveyor", {"reason": "release-response-lost"}
                )
            raise

    def reconcile_public_receipt(
        self,
        receipt_id: str,
        status_id: str,
        publication_id: str,
        release_operation_id: str,
        founder_actor: str | None = None,
    ) -> PublicationReceipt:
        release = self.repository.get_publication_operation(release_operation_id)
        publication = self.repository.get_platform_publication(publication_id)
        if publication.remote_id is None:
            raise ValueError("Purged API identity cannot be reconciled as a new receipt.")
        package = self.repository.get_publishing_package(publication.package_id)
        self._refuse_retrospective(package)
        self._refuse_never_release(package)
        self._target(publication.channel_id)
        self._historical_authority(package, release)
        if release.action_kind != "release" or release.package_id != package.id:
            raise ValueError("Receipt release intent differs from exact publication package.")
        if release.execution_mode == "manual":
            if not founder_actor:
                raise ValueError("Manual public transition needs founder action attestation.")
            if (
                self.repository.get_publication_operation_events(release_operation_id)[-1].kind
                == "reserved"
            ):
                self._authority(package, "manual", "release")
                if not timing_is_open(package.manifest["publication_timing"], self.clock()):
                    raise ValueError("Manual public window is not currently open.")
                self.repository.assert_release_week_clear(release_operation_id)
                self.repository.append_publication_operation_event(
                    release_operation_id,
                    "dispatch_started",
                    founder_actor,
                    {"action": "founder-Studio-private-to-public"},
                )
        try:
            observation = self.adapter.observe_remote(
                publication.remote_id, self._expected(package, publication.upload_operation_id)
            )
        except Exception:
            if (
                release.execution_mode == "manual"
                and self.repository.get_publication_operation(release_operation_id).outcome
                == "pending"
            ):
                self.repository.append_publication_operation_event(
                    release_operation_id,
                    "outcome_unknown",
                    "Conveyor",
                    {"reason": "manual-public-observation-lost"},
                )
            raise
        if (
            observation.remote_id != publication.remote_id
            or observation.channel_id != publication.channel_id
            or observation.metadata_matches is not True
            or observation.privacy != "public"
            or observation.processing != "succeeded"
            or observation.api_locked
            or observation.public_at is None
        ):
            if (
                release.execution_mode == "manual"
                and self.repository.get_publication_operation(release_operation_id).outcome
                == "pending"
            ):
                self.repository.append_publication_operation_event(
                    release_operation_id,
                    "outcome_unknown",
                    "Conveyor",
                    {"reason": "manual-public-state-unverified"},
                )
            raise ValueError(
                "Public receipt needs independent verified public observation and time."
            )
        state = self.repository.get_publication_operation(release_operation_id).outcome
        if state == "unknown":
            self.repository.append_publication_operation_event(
                release_operation_id,
                "reconciled",
                founder_actor or "Conveyor",
                {"resolution": "succeeded", "method": "public-remote-observation"},
            )
        elif state == "pending" and release.execution_mode == "manual":
            self.repository.append_publication_operation_event(
                release_operation_id,
                "succeeded",
                "Conveyor",
                {"method": "founder-attested-action-plus-public-observation"},
            )
        elif state != "succeeded":
            raise ValueError("Failed/unattempted release cannot generate a receipt.")
        status = self.repository.append_publication_status(
            status_id,
            publication_id,
            observation.privacy,
            observation.processing,
            "passed",
            False,
            "offline-adapter-v1",
            observation.observed_at,
            observation.provider_payload,
        )
        return self.repository.create_publication_receipt(
            receipt_id,
            publication_id,
            release_operation_id,
            status.id,
            observation.public_at,
            (
                "provider-public-state"
                if release.execution_mode == "api"
                else "manual-attestation-plus-public-observation"
            ),
            "second",
        )

    # --- YouTube Analytics (Option B; the adapter is only buildable while enabled) -------------

    def _analytics_target(self, receipt_id: str) -> tuple[PublicationReceipt, PlatformPublication]:
        receipt = self.repository.get_publication_receipt(receipt_id)
        publication = self.repository.get_platform_publication(receipt.publication_id)
        if receipt.public_at is None or publication.remote_id is None:
            raise ValueError("Purged provider binding cannot support Analytics; nothing recorded.")
        self._target(publication.channel_id)
        return receipt, publication

    def verify_analytics_video(self, check_id: str, receipt_id: str) -> dict[str, Any]:
        """Record whether the published video still exists (Analytics retention evidence).

        A missing or inaccessible video deletes its stored Analytics. Authorization and
        transient failures raise and record nothing.
        """

        _receipt, publication = self._analytics_target(receipt_id)
        outcome = self.adapter.video_existence(publication.remote_id)
        checked_at = self.clock().astimezone(UTC).replace(microsecond=0).isoformat()
        return self.repository.record_analytics_video_check(
            check_id, receipt_id, outcome, checked_at
        )

    def collect_analytics(self, receipt_id: str) -> list[PerformanceSnapshot]:
        """Collect every due, not-yet-mature checkpoint once, values exactly as reported.

        Refused unless the video's latest existence check is ``exists`` and fresh. Each attempt
        is a new snapshot; a checkpoint with a mature snapshot is never collected again. A failed
        request records nothing for that checkpoint.
        """

        receipt, publication = self._analytics_target(receipt_id)
        now = self.clock().astimezone(UTC)
        check = self.repository.latest_analytics_video_check(receipt_id)
        if (
            check is None
            or check["outcome"] != "exists"
            or datetime.fromisoformat(check["checked_at"]) < now - analytics.EXISTENCE_CHECK_MAX_AGE
        ):
            raise ValueError(
                "Confirm the video still exists (a fresh existence check) before collecting "
                "Analytics; nothing recorded."
            )
        collected = []
        for checkpoint in analytics.CHECKPOINTS:
            start, end = analytics.checkpoint_window(receipt.public_at, checkpoint)
            due_at = analytics.window_due_at(end)
            if now < due_at:
                continue
            attempts = self.repository.analytics_snapshot_attempts(receipt_id, checkpoint)
            if any(
                row["maturity"] == "mature" and row["provider_purged_at"] is None
                for row in attempts
            ):
                continue
            report = self.adapter.analytics_report(
                publication.remote_id, start, end, analytics.ANALYTICS_METRICS
            )
            retention_report = self.adapter.analytics_retention(publication.remote_id, start, end)
            metrics, availability, reasons, columns = analytics.parse_metrics_report(
                report, analytics.ANALYTICS_METRICS
            )
            retention = analytics.parse_retention_report(retention_report)
            collected.append(
                self.repository.append_performance_snapshot(
                    f"analytics-{receipt_id}-{checkpoint}-{len(attempts) + 1}",
                    receipt_id,
                    checkpoint,
                    due_at.isoformat(),
                    now.replace(microsecond=0).isoformat(),
                    {
                        "metrics": list(analytics.ANALYTICS_METRICS),
                        "startDate": start.isoformat(),
                        "endDate": end.isoformat(),
                        "timezone": analytics.REPORT_TIMEZONE,
                    },
                    {"columns": columns},
                    metrics,
                    availability,
                    analytics.maturity(now, due_at, availability, retention),
                    {
                        "schema": ANALYTICS_SNAPSHOT_SCHEMA,
                        "api": "youtubeAnalytics.reports.query",
                        "ids": "channel==MINE",
                    },
                    None,
                    retention,
                    reasons,
                )
            )
        return collected

    def collect_performance(
        self, snapshot_id: str, receipt_id: str, checkpoint: str
    ) -> PerformanceSnapshot:
        receipt = self.repository.get_publication_receipt(receipt_id)
        publication = self.repository.get_platform_publication(receipt.publication_id)
        if receipt.public_at is None or publication.remote_id is None:
            raise ValueError("Purged provider binding cannot support a new performance collection.")
        self._target(publication.channel_id)
        result = self.adapter.aggregate_performance(receipt, checkpoint)
        return self.repository.append_performance_snapshot(
            snapshot_id,
            receipt_id,
            checkpoint,
            result.due_at,
            result.collected_at,
            result.requested_coverage,
            result.returned_coverage,
            result.metrics,
            result.availability,
            result.maturity,
            result.api_context,
            result.provider_payload,
            result.retention,
            result.missing_reasons,
        )

    def assess(
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
    ) -> LearningAssessment:
        return self.repository.create_learning_assessment(
            assessment_id,
            snapshot_ids,
            feature,
            outcome,
            interpretation,
            confidence,
            confounds,
            recommendation,
            evidence_tier,
            producer,
        )
