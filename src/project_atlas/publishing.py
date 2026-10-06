"""Bounded publishing orchestration with separately gated adapter capabilities."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any, Protocol

from project_atlas.media import LocalMediaStorage
from project_atlas.persistence import AtlasRepository
from project_atlas.publishing_state import (
    TARGET_CHANNEL,
    LearningAssessment,
    PerformanceSnapshot,
    PlatformPublication,
    PublicationOperation,
    PublicationReceipt,
    PublicationStatusSnapshot,
    PublishingPackage,
    is_never_release,
    timing_is_open,
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
        self._target(package.channel_id)
        self._authority(package, package.manifest["transfer_route"], "upload")
        if attempt < 1:
            raise ValueError("Technical attempt number must be positive.")
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
        self._target(package.channel_id)
        self._authority(package, "api", "upload")
        if self.repository.get_publication_operation_events(operation_id)[-1].kind != "reserved":
            raise ValueError("Dispatched/uncertain upload must be inspected, not begun again.")
        if operation.intent.get("privacy", "private") != "private":
            # Re-check immediately before dispatch: the approved window can close.
            self._public_upload_governance(package, operation.id)
        self.storage.read_verified(
            self.repository.get_final_media_artifact(package.final_media_artifact_id).storage_path,
            package.artifact_digest,
        )
        self.repository.append_publication_operation_event(
            operation_id, "dispatch_started", "Conveyor", {"action": "private-transfer"}
        )
        try:
            result = self.adapter.begin_private_transfer(package, operation)
            return self._record_transfer(
                self.repository.get_publication_operation(operation_id),
                result,
            )
        except Exception:
            if self.repository.get_publication_operation(operation_id).outcome == "pending":
                self.repository.append_publication_operation_event(
                    operation_id,
                    "outcome_unknown",
                    "Conveyor",
                    {"reason": "client-exception-after-dispatch"},
                )
            raise

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
            return self._record_transfer(operation, result)
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
        self._target(publication.channel_id)
        package = self.repository.get_publishing_package(publication.package_id)
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
