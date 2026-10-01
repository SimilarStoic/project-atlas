"""Migration 28: authoritative, append-only production lifecycle records."""

from __future__ import annotations


def _immutable(table: str) -> tuple[str, str]:
    return (
        f"CREATE TRIGGER {table}_immutable_update BEFORE UPDATE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{table} is immutable'); END",
        f"CREATE TRIGGER {table}_immutable_delete BEFORE DELETE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{table} is immutable'); END",
    )


MIGRATION_28 = (
    28,
    (
        """
        CREATE TABLE production_runs (
          id TEXT PRIMARY KEY,
          visual_plan_id TEXT NOT NULL,
          request_json TEXT NOT NULL,
          request_digest TEXT NOT NULL CHECK (length(request_digest) = 64),
          created_at TEXT NOT NULL,
          FOREIGN KEY (visual_plan_id) REFERENCES visual_plans(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE production_run_events (
          id TEXT PRIMARY KEY,
          production_run_id TEXT NOT NULL,
          sequence INTEGER NOT NULL CHECK (sequence > 0),
          status TEXT NOT NULL CHECK (status IN (
            'created',
            'acquiring',
            'acquisition_review_pending',
            'assembling',
            'narrating',
            'rendering',
            'qa_review_pending',
            'private_founder_review_ready',
            'founder_accepted',
            'founder_rejected',
            'failed'
          )),
          stage TEXT NOT NULL,
          evidence_json TEXT NOT NULL,
          error_code TEXT NULL,
          error_message TEXT NULL,
          created_at TEXT NOT NULL,
          UNIQUE (production_run_id, sequence),
          FOREIGN KEY (production_run_id) REFERENCES production_runs(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE production_run_evidence (
          id TEXT PRIMARY KEY,
          production_run_id TEXT NOT NULL,
          evidence_type TEXT NOT NULL,
          generation_execution_id TEXT NULL,
          asset_id TEXT NULL,
          world_revision_id TEXT NULL,
          resolved_state_id TEXT NULL,
          narration_generation_execution_id TEXT NULL,
          narration_asset_id TEXT NULL,
          final_media_input_snapshot_id TEXT NULL,
          render_execution_id TEXT NULL,
          final_media_artifact_id TEXT NULL,
          payload_json TEXT NOT NULL,
          payload_digest TEXT NOT NULL CHECK (length(payload_digest) = 64),
          created_at TEXT NOT NULL,
          FOREIGN KEY (production_run_id) REFERENCES production_runs(id) ON DELETE RESTRICT,
          FOREIGN KEY (generation_execution_id)
            REFERENCES generation_executions(id) ON DELETE RESTRICT,
          FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE RESTRICT,
          FOREIGN KEY (world_revision_id)
            REFERENCES persistent_scene_world_revisions(id) ON DELETE RESTRICT,
          FOREIGN KEY (resolved_state_id)
            REFERENCES persistent_scene_resolved_states(id) ON DELETE RESTRICT,
          FOREIGN KEY (narration_generation_execution_id)
            REFERENCES narration_generation_executions(id) ON DELETE RESTRICT,
          FOREIGN KEY (narration_asset_id) REFERENCES narration_assets(id) ON DELETE RESTRICT,
          FOREIGN KEY (final_media_input_snapshot_id)
            REFERENCES final_media_input_snapshots(id) ON DELETE RESTRICT,
          FOREIGN KEY (render_execution_id) REFERENCES render_executions(id) ON DELETE RESTRICT,
          FOREIGN KEY (final_media_artifact_id)
            REFERENCES final_media_artifacts(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE production_qa_reviews (
          id TEXT PRIMARY KEY,
          production_run_id TEXT NOT NULL,
          scope TEXT NOT NULL CHECK (scope IN ('acquisition', 'cell', 'whole_video')),
          outcome TEXT NOT NULL CHECK (outcome IN ('passed', 'failed')),
          reviewer_kind TEXT NOT NULL CHECK (reviewer_kind IN ('automated', 'human')),
          profile_json TEXT NOT NULL,
          evidence_json TEXT NOT NULL,
          final_media_artifact_id TEXT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (production_run_id) REFERENCES production_runs(id) ON DELETE RESTRICT,
          FOREIGN KEY (final_media_artifact_id)
            REFERENCES final_media_artifacts(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE production_founder_reviews (
          id TEXT PRIMARY KEY,
          production_run_id TEXT NOT NULL UNIQUE,
          outcome TEXT NOT NULL CHECK (outcome IN ('accepted', 'rejected')),
          founder_actor TEXT NOT NULL,
          decision_reference TEXT NOT NULL,
          notes TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (production_run_id) REFERENCES production_runs(id) ON DELETE RESTRICT
        )
        """,
        "CREATE INDEX idx_production_run_events ON production_run_events "
        "(production_run_id, sequence)",
        "CREATE INDEX idx_production_run_evidence ON production_run_evidence "
        "(production_run_id, evidence_type, created_at, id)",
        "CREATE INDEX idx_production_qa_reviews ON production_qa_reviews "
        "(production_run_id, scope, created_at, id)",
        *_immutable("production_runs"),
        *_immutable("production_run_events"),
        *_immutable("production_run_evidence"),
        *_immutable("production_qa_reviews"),
        *_immutable("production_founder_reviews"),
    ),
)
