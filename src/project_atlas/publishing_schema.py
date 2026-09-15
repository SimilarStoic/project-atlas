"""Additive, provider-neutral persistence for the offline controlled-publishing pilot."""

_PURGE_FIELDS = {
    "publication_operation_events": ("provider_evidence_json", "provider_evidence_digest"),
    "platform_publications": ("remote_id", "binding_digest"),
    "publication_status_snapshots": (
        "privacy",
        "processing",
        "verification",
        "api_locked",
        "observed_at",
        "observation_digest",
        "provider_payload_json",
        "provider_payload_digest",
    ),
    "publication_receipts": ("public_at", "first_public_observed_at", "receipt_digest"),
    "performance_snapshots": (
        "due_at",
        "collected_at",
        "returned_coverage_json",
        "metrics_json",
        "retention_json",
        "maturity",
        "api_context_json",
        "observation_digest",
        "provider_payload_json",
        "provider_payload_digest",
    ),
}


def _immutable(table: str, columns: tuple[str, ...], *, purgeable: bool = False) -> tuple[str, str]:
    """Generate explicit source-defined triggers; purge only designated provider fields."""

    stable = " AND ".join(f"NEW.{column} IS OLD.{column}" for column in columns)
    provider_fields = _PURGE_FIELDS.get(table, ())
    cleared = " AND ".join(f"NEW.{field} IS NULL" for field in provider_fields)
    purge = (
        "OLD.provider_purged_at IS NULL AND NEW.provider_purged_at IS NOT NULL AND "
        f"{cleared} AND {stable}"
    )
    if table == "platform_publications":
        purge += " AND OLD.identity_source = 'api'"
    allowed = purge if purgeable else "0"
    return (
        f"CREATE TRIGGER {table}_immutable_update BEFORE UPDATE ON {table} "
        f"WHEN NOT ({allowed}) BEGIN SELECT RAISE(ABORT, '{table} is immutable'); END",
        f"CREATE TRIGGER {table}_immutable_delete BEFORE DELETE ON {table} "
        f"BEGIN SELECT RAISE(ABORT, '{table} is immutable'); END",
    )


_TABLES = (
    (
        "publishing_packages",
        (
            "id",
            "pilot_key",
            "pilot_slot",
            "version",
            "predecessor_id",
            "final_media_artifact_id",
            "artifact_digest",
            "platform",
            "channel_id",
            "pilot_week",
            "manifest_json",
            "package_digest",
            "created_at",
        ),
        False,
    ),
    (
        "publication_gate_decisions",
        (
            "id",
            "package_id",
            "package_digest",
            "sequence",
            "decision",
            "founder_actor",
            "transfer_route",
            "release_route",
            "timing_json",
            "comment",
            "created_at",
        ),
        False,
    ),
    (
        "publication_operations",
        (
            "id",
            "operation_key",
            "package_id",
            "gate_decision_id",
            "action_kind",
            "execution_mode",
            "intent_json",
            "intent_digest",
            "created_at",
        ),
        False,
    ),
    (
        "publication_operation_events",
        ("id", "operation_id", "sequence", "kind", "actor", "evidence_json", "created_at"),
        True,
    ),
    (
        "platform_publications",
        (
            "id",
            "package_id",
            "upload_operation_id",
            "platform",
            "channel_id",
            "identified_at",
            "identity_source",
        ),
        True,
    ),
    (
        "publication_status_snapshots",
        (
            "id",
            "publication_id",
            "adapter_version",
        ),
        True,
    ),
    (
        "publication_receipts",
        (
            "id",
            "publication_id",
            "package_id",
            "gate_decision_id",
            "release_operation_id",
            "public_status_id",
            "execution_mode",
            "channel_id",
            "pilot_week",
            "timestamp_source",
            "timestamp_precision",
            "created_at",
        ),
        True,
    ),
    (
        "performance_snapshots",
        (
            "id",
            "receipt_id",
            "checkpoint",
            "requested_coverage_json",
        ),
        True,
    ),
    (
        "learning_assessments",
        (
            "id",
            "predecessor_id",
            "feature",
            "outcome",
            "interpretation",
            "confidence",
            "confounds_json",
            "recommendation",
            "evidence_tier",
            "producer",
            "assessment_digest",
            "created_at",
        ),
        False,
    ),
    ("learning_assessment_evidence", ("assessment_id", "performance_snapshot_id"), False),
    (
        "learning_applications",
        (
            "id",
            "assessment_id",
            "opportunity_id",
            "hook_option_id",
            "script_id",
            "visual_plan_id",
            "final_media_input_snapshot_id",
            "decision_reference",
            "context_json",
            "change_digest",
            "founder_reference",
            "actor",
            "created_at",
        ),
        False,
    ),
)


MIGRATION_25: tuple[int, tuple[str, ...]] = (
    25,
    (
        """
        CREATE TABLE publishing_packages (
          id TEXT PRIMARY KEY, pilot_key TEXT NOT NULL, pilot_slot INTEGER NOT NULL
            CHECK (pilot_slot BETWEEN 1 AND 3), version INTEGER NOT NULL CHECK (version >= 1),
          predecessor_id TEXT NULL, final_media_artifact_id TEXT NOT NULL,
          artifact_digest TEXT NOT NULL CHECK (length(artifact_digest) = 64),
          platform TEXT NOT NULL CHECK (platform = 'youtube'),
          channel_id TEXT NOT NULL CHECK (length(trim(channel_id)) > 0),
          pilot_week TEXT NOT NULL,
          manifest_json TEXT NOT NULL, package_digest TEXT NOT NULL
            CHECK (length(package_digest) = 64), created_at TEXT NOT NULL,
          UNIQUE (pilot_key, pilot_slot, version),
          FOREIGN KEY (predecessor_id) REFERENCES publishing_packages(id) ON DELETE RESTRICT,
          FOREIGN KEY (final_media_artifact_id)
            REFERENCES final_media_artifacts(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE publication_gate_decisions (
          id TEXT PRIMARY KEY, package_id TEXT NOT NULL, package_digest TEXT NOT NULL
            CHECK (length(package_digest) = 64), sequence INTEGER NOT NULL CHECK (sequence >= 1),
          decision TEXT NOT NULL CHECK (decision IN ('approve', 'reject', 'revoke')),
          founder_actor TEXT NOT NULL CHECK (length(trim(founder_actor)) > 0),
          transfer_route TEXT NULL CHECK (transfer_route IN ('api', 'manual')),
          release_route TEXT NULL CHECK (release_route IN ('api', 'manual')),
          timing_json TEXT NOT NULL, comment TEXT NULL, created_at TEXT NOT NULL,
          UNIQUE (package_id, sequence), UNIQUE (id, package_id),
          CHECK (decision <> 'approve' OR
            (transfer_route IS NOT NULL AND release_route IS NOT NULL)),
          FOREIGN KEY (package_id) REFERENCES publishing_packages(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TRIGGER publication_gate_exact_digest BEFORE INSERT ON publication_gate_decisions
        WHEN NEW.package_digest <> (SELECT package_digest FROM publishing_packages
                                    WHERE id = NEW.package_id)
        BEGIN SELECT RAISE(ABORT, 'gate package digest mismatch'); END
        """,
        """
        CREATE TABLE publication_operations (
          id TEXT PRIMARY KEY, operation_key TEXT NOT NULL UNIQUE, package_id TEXT NOT NULL,
          gate_decision_id TEXT NOT NULL, action_kind TEXT NOT NULL
            CHECK (action_kind IN ('upload', 'release')),
          execution_mode TEXT NOT NULL CHECK (execution_mode IN ('api', 'manual')),
          intent_json TEXT NOT NULL, intent_digest TEXT NOT NULL CHECK (length(intent_digest) = 64),
          created_at TEXT NOT NULL,
          FOREIGN KEY (package_id) REFERENCES publishing_packages(id) ON DELETE RESTRICT,
          FOREIGN KEY (gate_decision_id, package_id)
            REFERENCES publication_gate_decisions(id, package_id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE publication_operation_events (
          id TEXT PRIMARY KEY, operation_id TEXT NOT NULL, sequence INTEGER NOT NULL
            CHECK (sequence >= 1), kind TEXT NOT NULL CHECK (kind IN
            ('reserved', 'dispatch_started', 'progress', 'remote_identity_observed',
             'succeeded', 'failed', 'outcome_unknown', 'reconciled')),
          actor TEXT NOT NULL, evidence_json TEXT NOT NULL, created_at TEXT NOT NULL,
          provider_evidence_json TEXT NULL, provider_evidence_digest TEXT NULL,
          provider_purged_at TEXT NULL,
          CHECK ((provider_evidence_json IS NULL) = (provider_evidence_digest IS NULL)),
          UNIQUE (operation_id, sequence),
          FOREIGN KEY (operation_id) REFERENCES publication_operations(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE platform_publications (
          id TEXT PRIMARY KEY, package_id TEXT NOT NULL, upload_operation_id TEXT NOT NULL UNIQUE,
          platform TEXT NOT NULL CHECK (platform = 'youtube'), channel_id TEXT NOT NULL,
          remote_id TEXT NULL CHECK (remote_id IS NULL OR length(trim(remote_id)) > 0),
          binding_digest TEXT NULL CHECK (binding_digest IS NULL OR length(binding_digest) = 64),
          identified_at TEXT NOT NULL, identity_source TEXT NOT NULL
            CHECK (identity_source IN ('api', 'founder_manual')),
          provider_purged_at TEXT NULL, UNIQUE (platform, channel_id, remote_id),
          CHECK ((remote_id IS NULL) = (binding_digest IS NULL)),
          FOREIGN KEY (package_id) REFERENCES publishing_packages(id) ON DELETE RESTRICT,
          FOREIGN KEY (upload_operation_id) REFERENCES publication_operations(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE publication_status_snapshots (
          id TEXT PRIMARY KEY, publication_id TEXT NOT NULL,
          privacy TEXT NULL CHECK (privacy IN ('private', 'unlisted', 'public')),
          processing TEXT NULL CHECK (processing IN ('pending', 'succeeded', 'failed')),
          verification TEXT NULL CHECK (verification IN ('unknown', 'passed', 'failed')),
          api_locked INTEGER NULL CHECK (api_locked IN (0, 1)),
          observed_at TEXT NULL, adapter_version TEXT NOT NULL,
          observation_digest TEXT NULL
            CHECK (observation_digest IS NULL OR length(observation_digest) = 64),
          provider_payload_json TEXT NULL, provider_payload_digest TEXT NULL
            CHECK (provider_payload_digest IS NULL OR length(provider_payload_digest) = 64),
          provider_purged_at TEXT NULL,
          CHECK ((provider_payload_json IS NULL) = (provider_payload_digest IS NULL)),
          FOREIGN KEY (publication_id) REFERENCES platform_publications(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE publication_receipts (
          id TEXT PRIMARY KEY, publication_id TEXT NOT NULL UNIQUE, package_id TEXT NOT NULL,
          gate_decision_id TEXT NOT NULL, release_operation_id TEXT NOT NULL UNIQUE,
          public_status_id TEXT NOT NULL UNIQUE,
          execution_mode TEXT NOT NULL CHECK (execution_mode IN ('api', 'manual')),
          channel_id TEXT NOT NULL, pilot_week TEXT NOT NULL,
          public_at TEXT NULL, timestamp_source TEXT NOT NULL,
          timestamp_precision TEXT NOT NULL, first_public_observed_at TEXT NULL,
          receipt_digest TEXT NULL CHECK (receipt_digest IS NULL OR length(receipt_digest) = 64),
          created_at TEXT NOT NULL, provider_purged_at TEXT NULL,
          UNIQUE (channel_id, pilot_week),
          CHECK ((public_at IS NULL) = (receipt_digest IS NULL)),
          FOREIGN KEY (publication_id) REFERENCES platform_publications(id) ON DELETE RESTRICT,
          FOREIGN KEY (package_id) REFERENCES publishing_packages(id) ON DELETE RESTRICT,
          FOREIGN KEY (gate_decision_id, package_id)
            REFERENCES publication_gate_decisions(id, package_id) ON DELETE RESTRICT,
          FOREIGN KEY (release_operation_id)
            REFERENCES publication_operations(id) ON DELETE RESTRICT,
          FOREIGN KEY (public_status_id)
            REFERENCES publication_status_snapshots(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TRIGGER publication_receipt_public_state BEFORE INSERT ON publication_receipts
        WHEN NOT EXISTS (
          SELECT 1 FROM publication_status_snapshots s
          WHERE s.id = NEW.public_status_id AND s.publication_id = NEW.publication_id
            AND s.privacy = 'public' AND s.processing = 'succeeded'
            AND s.verification = 'passed' AND s.api_locked = 0
        )
        BEGIN SELECT RAISE(ABORT, 'receipt requires verified public observation'); END
        """,
        """
        CREATE TRIGGER publication_receipt_weekly_limit BEFORE INSERT ON publication_receipts
        WHEN EXISTS (SELECT 1 FROM publication_receipts r WHERE r.channel_id = NEW.channel_id
                     AND r.pilot_week = NEW.pilot_week)
        BEGIN SELECT RAISE(ABORT, 'channel pilot week already consumed'); END
        """,
        """
        CREATE TABLE performance_snapshots (
          id TEXT PRIMARY KEY, receipt_id TEXT NOT NULL,
          checkpoint TEXT NOT NULL CHECK (checkpoint IN ('24h', '72h', '7d', '28d')),
          due_at TEXT NULL, collected_at TEXT NULL,
          requested_coverage_json TEXT NOT NULL, returned_coverage_json TEXT NULL,
          metrics_json TEXT NULL, retention_json TEXT NULL,
          maturity TEXT NULL CHECK (maturity IN ('immature', 'partial', 'mature')),
          api_context_json TEXT NULL, observation_digest TEXT NULL
            CHECK (observation_digest IS NULL OR length(observation_digest) = 64),
          provider_payload_json TEXT NULL, provider_payload_digest TEXT NULL
            CHECK (provider_payload_digest IS NULL OR length(provider_payload_digest) = 64),
          provider_purged_at TEXT NULL,
          CHECK ((provider_payload_json IS NULL) = (provider_payload_digest IS NULL)),
          FOREIGN KEY (receipt_id) REFERENCES publication_receipts(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE learning_assessments (
          id TEXT PRIMARY KEY, predecessor_id TEXT NULL,
          feature TEXT NOT NULL, outcome TEXT NOT NULL, interpretation TEXT NOT NULL,
          confidence TEXT NOT NULL CHECK (confidence IN ('low', 'medium', 'high')),
          confounds_json TEXT NOT NULL, recommendation TEXT NOT NULL,
          evidence_tier TEXT NOT NULL CHECK (evidence_tier IN
            ('observation', 'hypothesis', 'repeated', 'consequential_review')),
          producer TEXT NOT NULL, assessment_digest TEXT NOT NULL
            CHECK (length(assessment_digest) = 64), created_at TEXT NOT NULL,
          FOREIGN KEY (predecessor_id) REFERENCES learning_assessments(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE learning_assessment_evidence (
          assessment_id TEXT NOT NULL, performance_snapshot_id TEXT NOT NULL,
          PRIMARY KEY (assessment_id, performance_snapshot_id),
          FOREIGN KEY (assessment_id) REFERENCES learning_assessments(id) ON DELETE RESTRICT,
          FOREIGN KEY (performance_snapshot_id)
            REFERENCES performance_snapshots(id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE learning_applications (
          id TEXT PRIMARY KEY, assessment_id TEXT NOT NULL,
          opportunity_id TEXT NULL, hook_option_id TEXT NULL, script_id TEXT NULL,
          visual_plan_id TEXT NULL, final_media_input_snapshot_id TEXT NULL,
          decision_reference TEXT NOT NULL, context_json TEXT NOT NULL,
          change_digest TEXT NOT NULL CHECK (length(change_digest) = 64),
          founder_reference TEXT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL,
          CHECK ((opportunity_id IS NOT NULL) + (hook_option_id IS NOT NULL) +
                 (script_id IS NOT NULL) + (visual_plan_id IS NOT NULL) +
                 (final_media_input_snapshot_id IS NOT NULL) = 1),
          UNIQUE (assessment_id, decision_reference, change_digest),
          FOREIGN KEY (assessment_id) REFERENCES learning_assessments(id) ON DELETE RESTRICT,
          FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE RESTRICT,
          FOREIGN KEY (hook_option_id) REFERENCES hook_options(id) ON DELETE RESTRICT,
          FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE RESTRICT,
          FOREIGN KEY (visual_plan_id) REFERENCES visual_plans(id) ON DELETE RESTRICT,
          FOREIGN KEY (final_media_input_snapshot_id)
            REFERENCES final_media_input_snapshots(id) ON DELETE RESTRICT
        )
        """,
        "CREATE INDEX idx_publishing_packages_artifact "
        "ON publishing_packages(final_media_artifact_id)",
        "CREATE INDEX idx_publication_operations_package "
        "ON publication_operations(package_id, action_kind)",
        "CREATE INDEX idx_publication_operation_events_operation "
        "ON publication_operation_events(operation_id, sequence)",
        "CREATE INDEX idx_publication_status_publication "
        "ON publication_status_snapshots(publication_id, observed_at)",
        "CREATE INDEX idx_performance_receipt "
        "ON performance_snapshots(receipt_id, checkpoint, collected_at)",
        "CREATE INDEX idx_learning_evidence_snapshot "
        "ON learning_assessment_evidence(performance_snapshot_id)",
    )
    + tuple(
        statement
        for table, columns, purgeable in _TABLES
        for statement in _immutable(table, columns, purgeable=purgeable)
    ),
)
