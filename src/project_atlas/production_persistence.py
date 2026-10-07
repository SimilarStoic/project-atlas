"""Append-only persistence for canonical v2 production lifecycle state."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


_TRANSITIONS = {
    None: {"created"},
    "created": {"acquiring", "failed"},
    "acquiring": {"acquisition_review_pending", "failed"},
    "acquisition_review_pending": {"assembling", "failed"},
    "assembling": {"narrating", "failed"},
    # Narration then its completeness verification are successive stages of narrating.
    "narrating": {"narrating", "rendering", "failed"},
    "rendering": {"qa_review_pending", "failed"},
    # A bounded post-narration retime re-renders approved inputs before human QA; a
    # founder-authorized narration retake re-narrates before re-rendering.
    "qa_review_pending": {"private_founder_review_ready", "failed", "rendering", "narrating"},
    "private_founder_review_ready": {"founder_accepted", "founder_rejected"},
    "founder_accepted": set(),
    "founder_rejected": set(),
    "failed": {"acquiring", "assembling", "narrating", "rendering"},
}


@dataclass(frozen=True)
class ProductionRun:
    id: str
    visual_plan_id: str
    request: dict[str, Any]
    request_digest: str
    created_at: str


@dataclass(frozen=True)
class ProductionRunEvent:
    id: str
    production_run_id: str
    sequence: int
    status: str
    stage: str
    evidence: dict[str, Any]
    error_code: str | None
    error_message: str | None
    created_at: str


@dataclass(frozen=True)
class ProductionEvidence:
    id: str
    production_run_id: str
    evidence_type: str
    generation_execution_id: str | None
    asset_id: str | None
    world_revision_id: str | None
    resolved_state_id: str | None
    narration_generation_execution_id: str | None
    narration_asset_id: str | None
    final_media_input_snapshot_id: str | None
    render_execution_id: str | None
    final_media_artifact_id: str | None
    payload: dict[str, Any]
    payload_digest: str
    created_at: str


@dataclass(frozen=True)
class ProductionQAReview:
    id: str
    production_run_id: str
    scope: str
    outcome: str
    reviewer_kind: str
    profile: dict[str, Any]
    evidence: dict[str, Any]
    final_media_artifact_id: str | None
    created_at: str


@dataclass(frozen=True)
class ProductionFounderReview:
    id: str
    production_run_id: str
    outcome: str
    founder_actor: str
    decision_reference: str
    notes: str
    created_at: str


class ProductionRepositoryMixin:
    """Narrow lifecycle records layered over existing canonical artifacts."""

    connection: Any

    def create_production_run(
        self, run_id: str, visual_plan_id: str, request: dict[str, Any]
    ) -> ProductionRun:
        self._require_gate_authorized_visual_plan(visual_plan_id)
        if not isinstance(run_id, str) or not run_id.strip() or not isinstance(request, dict):
            raise ValueError("ProductionRun requires an ID and object request.")
        frozen = _canonical(request)
        with self.connection:
            self.connection.execute(
                "INSERT INTO production_runs VALUES (?, ?, ?, ?, ?)",
                (
                    run_id.strip(),
                    visual_plan_id,
                    frozen,
                    sha256(frozen.encode()).hexdigest(),
                    _now(),
                ),
            )
        run = self.get_production_run(run_id.strip())
        self.append_production_run_event(
            run.id, "created", "request", {"request_digest": run.request_digest}
        )
        return run

    def get_production_run(self, run_id: str) -> ProductionRun:
        row = self.connection.execute(
            "SELECT * FROM production_runs WHERE id=?", (run_id,)
        ).fetchone()
        if row is None:
            raise KeyError(run_id)
        return ProductionRun(
            row["id"],
            row["visual_plan_id"],
            json.loads(row["request_json"]),
            row["request_digest"],
            row["created_at"],
        )

    def append_production_run_event(
        self,
        run_id: str,
        status: str,
        stage: str,
        evidence: dict[str, Any] | None = None,
        *,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ProductionRunEvent:
        self.get_production_run(run_id)
        if not stage.strip() or not isinstance(evidence or {}, dict):
            raise ValueError("Production event requires a stage and object evidence.")
        if status == "failed" and (not error_code or error_message is None):
            raise ValueError("Failed production event requires bounded error details.")
        if status != "failed" and (error_code is not None or error_message is not None):
            raise ValueError("Only failed production events may carry errors.")
        latest = self.latest_production_run_event(run_id)
        prior_status = latest.status if latest else None
        if status not in _TRANSITIONS.get(prior_status, set()):
            raise ValueError(
                f"Production status transition {prior_status!r} -> {status!r} is not allowed."
            )
        sequence = 1 if latest is None else latest.sequence + 1
        event_id = f"{run_id}:event:{sequence}"
        with self.connection:
            self.connection.execute(
                "INSERT INTO production_run_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    run_id,
                    sequence,
                    status,
                    stage.strip(),
                    _canonical(evidence or {}),
                    error_code,
                    error_message[:1000] if error_message is not None else None,
                    _now(),
                ),
            )
        return self.latest_production_run_event(run_id)  # type: ignore[return-value]

    def latest_production_run_event(self, run_id: str) -> ProductionRunEvent | None:
        row = self.connection.execute(
            "SELECT * FROM production_run_events WHERE production_run_id=? "
            "ORDER BY sequence DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return ProductionRunEvent(
            row["id"],
            row["production_run_id"],
            row["sequence"],
            row["status"],
            row["stage"],
            json.loads(row["evidence_json"]),
            row["error_code"],
            row["error_message"],
            row["created_at"],
        )

    def list_production_run_events(self, run_id: str) -> list[ProductionRunEvent]:
        self.get_production_run(run_id)
        rows = self.connection.execute(
            "SELECT * FROM production_run_events WHERE production_run_id=? ORDER BY sequence",
            (run_id,),
        )
        return [
            ProductionRunEvent(
                row["id"],
                row["production_run_id"],
                row["sequence"],
                row["status"],
                row["stage"],
                json.loads(row["evidence_json"]),
                row["error_code"],
                row["error_message"],
                row["created_at"],
            )
            for row in rows
        ]

    def create_production_evidence(
        self,
        evidence_id: str,
        run_id: str,
        evidence_type: str,
        payload: dict[str, Any],
        **references: str | None,
    ) -> ProductionEvidence:
        self.get_production_run(run_id)
        allowed = {
            "generation_execution_id",
            "asset_id",
            "world_revision_id",
            "resolved_state_id",
            "narration_generation_execution_id",
            "narration_asset_id",
            "final_media_input_snapshot_id",
            "render_execution_id",
            "final_media_artifact_id",
        }
        if set(references) - allowed:
            raise ValueError("Production evidence contains an unsupported reference.")
        if not evidence_id.strip() or not evidence_type.strip() or not isinstance(payload, dict):
            raise ValueError("Production evidence requires IDs, type, and object payload.")
        frozen = _canonical(payload)
        values = [references.get(name) for name in allowed]
        ordered_names = (
            "generation_execution_id",
            "asset_id",
            "world_revision_id",
            "resolved_state_id",
            "narration_generation_execution_id",
            "narration_asset_id",
            "final_media_input_snapshot_id",
            "render_execution_id",
            "final_media_artifact_id",
        )
        values = [references.get(name) for name in ordered_names]
        with self.connection:
            self.connection.execute(
                "INSERT INTO production_run_evidence VALUES "
                "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    evidence_id.strip(),
                    run_id,
                    evidence_type.strip(),
                    *values,
                    frozen,
                    sha256(frozen.encode()).hexdigest(),
                    _now(),
                ),
            )
        return self.get_production_evidence(evidence_id.strip())

    def get_production_evidence(self, evidence_id: str) -> ProductionEvidence:
        row = self.connection.execute(
            "SELECT * FROM production_run_evidence WHERE id=?", (evidence_id,)
        ).fetchone()
        if row is None:
            raise KeyError(evidence_id)
        return ProductionEvidence(
            row["id"],
            row["production_run_id"],
            row["evidence_type"],
            row["generation_execution_id"],
            row["asset_id"],
            row["world_revision_id"],
            row["resolved_state_id"],
            row["narration_generation_execution_id"],
            row["narration_asset_id"],
            row["final_media_input_snapshot_id"],
            row["render_execution_id"],
            row["final_media_artifact_id"],
            json.loads(row["payload_json"]),
            row["payload_digest"],
            row["created_at"],
        )

    def list_production_evidence(
        self, run_id: str, evidence_type: str | None = None
    ) -> list[ProductionEvidence]:
        self.get_production_run(run_id)
        sql = "SELECT id FROM production_run_evidence WHERE production_run_id=?"
        params: tuple[Any, ...] = (run_id,)
        if evidence_type is not None:
            sql += " AND evidence_type=?"
            params += (evidence_type,)
        sql += " ORDER BY created_at, id"
        return [
            self.get_production_evidence(row["id"]) for row in self.connection.execute(sql, params)
        ]

    def create_production_qa_review(
        self,
        review_id: str,
        run_id: str,
        scope: str,
        outcome: str,
        reviewer_kind: str,
        profile: dict[str, Any],
        evidence: dict[str, Any],
        artifact_id: str | None = None,
    ) -> ProductionQAReview:
        self.get_production_run(run_id)
        if not all(isinstance(value, dict) for value in (profile, evidence)):
            raise ValueError("QA profile and evidence must be objects.")
        with self.connection:
            self.connection.execute(
                "INSERT INTO production_qa_reviews VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    review_id,
                    run_id,
                    scope,
                    outcome,
                    reviewer_kind,
                    _canonical(profile),
                    _canonical(evidence),
                    artifact_id,
                    _now(),
                ),
            )
        return self.get_production_qa_review(review_id)

    def get_production_qa_review(self, review_id: str) -> ProductionQAReview:
        row = self.connection.execute(
            "SELECT * FROM production_qa_reviews WHERE id=?", (review_id,)
        ).fetchone()
        if row is None:
            raise KeyError(review_id)
        return ProductionQAReview(
            row["id"],
            row["production_run_id"],
            row["scope"],
            row["outcome"],
            row["reviewer_kind"],
            json.loads(row["profile_json"]),
            json.loads(row["evidence_json"]),
            row["final_media_artifact_id"],
            row["created_at"],
        )

    def list_production_qa_reviews(self, run_id: str) -> list[ProductionQAReview]:
        self.get_production_run(run_id)
        return [
            self.get_production_qa_review(row["id"])
            for row in self.connection.execute(
                "SELECT id FROM production_qa_reviews WHERE production_run_id=? "
                "ORDER BY created_at, id",
                (run_id,),
            )
        ]

    def create_production_founder_review(
        self,
        review_id: str,
        run_id: str,
        outcome: str,
        founder_actor: str,
        decision_reference: str,
        notes: str,
    ) -> ProductionFounderReview:
        latest = self.latest_production_run_event(run_id)
        if latest is None or latest.status != "private_founder_review_ready":
            raise ValueError("Founder review requires a private-founder-review-ready production.")
        with self.connection:
            self.connection.execute(
                "INSERT INTO production_founder_reviews VALUES (?, ?, ?, ?, ?, ?, ?)",
                (review_id, run_id, outcome, founder_actor, decision_reference, notes, _now()),
            )
        self.append_production_run_event(
            run_id,
            f"founder_{outcome}",
            "founder_review",
            {"founder_review_id": review_id},
        )
        return self.get_production_founder_review(review_id)

    def get_production_founder_review(self, review_id: str) -> ProductionFounderReview:
        row = self.connection.execute(
            "SELECT * FROM production_founder_reviews WHERE id=?", (review_id,)
        ).fetchone()
        if row is None:
            raise KeyError(review_id)
        return ProductionFounderReview(
            row["id"],
            row["production_run_id"],
            row["outcome"],
            row["founder_actor"],
            row["decision_reference"],
            row["notes"],
            row["created_at"],
        )
