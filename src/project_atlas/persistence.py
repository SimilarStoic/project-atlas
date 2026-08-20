"""SQLite persistence for Atlas discovery through asset-spec and asset foundations."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from project_atlas.demo_data import OPPORTUNITIES, content_payload


def now() -> str:
    """Return a UTC timestamp for application writes."""

    return datetime.now(UTC).replace(microsecond=0).isoformat()


def default_database_path() -> Path:
    """Return the configured local database location."""

    return Path(os.environ.get("ATLAS_DB_PATH", "data/atlas.db"))


@dataclass(frozen=True)
class Subject:
    id: str
    slug: str
    name: str
    description: str
    active: bool
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Opportunity:
    id: str
    title: str
    summary: str
    why_now: str
    score: int
    status: str
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class IdeaGateReviewSnapshot:
    """An immutable human-visible Opportunity representation prepared for Idea Gate review."""

    id: str
    opportunity_id: str
    payload_schema_version: int
    review_payload: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class IdeaGateDecision:
    """An immutable founder decision about one exact Idea Gate review snapshot."""

    id: str
    review_snapshot_id: str
    outcome: str
    founder_actor: str
    founder_comment: str | None
    founder_direction: str | None
    created_at: str


@dataclass(frozen=True)
class ResearchPack:
    """A versioned research snapshot owned by one Opportunity."""

    id: str
    opportunity_id: str
    idea_gate_decision_id: str | None
    version: int
    summary: str
    as_of_date: str | None
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ResearchReadinessAssessment:
    """An immutable readiness record over one exact frozen ResearchPack evidence state."""

    id: str
    research_pack_id: str
    schema_version: int
    frozen_evidence_state: dict[str, Any]
    outcome: str
    findings: dict[str, Any]
    policy_version: str
    producer_kind: str
    producer_identifier: str
    producer_implementation_version: str
    created_at: str


@dataclass(frozen=True)
class Claim:
    """A version-specific editorial or research statement."""

    id: str
    research_pack_id: str
    text: str
    claim_type: str
    risk_level: str
    freshness_type: str
    verification_status: str
    verification_notes: str
    reviewed_at: str | None
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Source:
    """A reusable Atlas-wide source, identified by its exact URL."""

    id: str
    source_type: str
    title: str
    publisher: str
    author: str | None
    url: str
    publication_date: str | None
    accessed_at: str
    jurisdiction: str | None
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ClaimEvidence:
    """The provenance relationship between a Claim and a Source."""

    claim_id: str
    source_id: str
    stance: str
    reference: str | None
    notes: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class EditorialAngle:
    """A durable editorial proposition grounded in one ResearchPack."""

    id: str
    opportunity_id: str
    research_pack_id: str
    research_readiness_assessment_id: str | None
    working_title: str
    thesis: str
    audience_promise: str
    framing: str
    key_takeaways: list[str]
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class EditorialAngleClaim:
    """A Claim's role in an EditorialAngle."""

    editorial_angle_id: str
    claim_id: str
    role: str
    created_at: str


@dataclass(frozen=True)
class ContentPiece:
    """A concrete deliverable derived from one EditorialAngle."""

    id: str
    opportunity_id: str
    editorial_angle_id: str
    format_key: str
    working_title: str
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Script:
    """An immutable complete narration version for one ContentPiece."""

    id: str
    content_piece_id: str
    version: int
    narration_text: str
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ScriptClaimSet:
    """One closed, immutable Claim-provenance declaration for an exact Script."""

    id: str
    script_id: str
    created_at: str


@dataclass(frozen=True)
class ScriptClaimLink:
    """One immutable Claim identity membership in a closed ScriptClaimSet."""

    script_claim_set_id: str
    claim_id: str
    created_at: str


@dataclass(frozen=True)
class TitleOption:
    """An immutable title alternative owned by one ContentPiece."""

    id: str
    content_piece_id: str
    text: str
    metadata: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class HookOption:
    """An immutable hook alternative owned by one ContentPiece."""

    id: str
    content_piece_id: str
    text: str
    metadata: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class EditorialPackageSnapshot:
    """One frozen editorial proposition composed from exact ContentPiece records."""

    id: str
    content_piece_id: str
    title_option_id: str
    hook_option_id: str
    script_id: str
    created_at: str


@dataclass(frozen=True)
class EditorialReadinessAssessment:
    """An immutable deterministic readiness assessment of one exact editorial package."""

    id: str
    editorial_package_snapshot_id: str
    schema_version: int
    evaluator_id: str
    evaluator_version: str
    outcome: str
    findings: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class EditorialGateDecision:
    """An immutable human decision over one exact Ready editorial proposition."""

    id: str
    editorial_package_snapshot_id: str
    editorial_readiness_assessment_id: str
    outcome: str
    actor: str
    comment: str | None
    created_at: str


@dataclass(frozen=True)
class VisualPlan:
    """A visual translation plan for one immutable Script version."""

    id: str
    content_piece_id: str
    script_id: str
    visual_direction: str
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class VisualPlanGateProvenance:
    """The exact approved Editorial Gate decision that initiated one VisualPlan."""

    visual_plan_id: str
    editorial_gate_decision_id: str
    created_at: str


@dataclass(frozen=True)
class Scene:
    """An ordered, non-authoritative visual locator within one VisualPlan."""

    id: str
    visual_plan_id: str
    sequence: int
    narration_excerpt: str
    visual_intent: str
    hamster_action: str | None
    on_screen_text: str | None
    transition_note: str | None
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AssetSpec:
    """A durable, provider-neutral asset requirement owned by one Scene."""

    id: str
    scene_id: str
    asset_type: str
    purpose: str
    description: str
    generation_prompt: str
    continuity_key: str | None
    character_profile_id: str | None
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Asset:
    """An immutable registered asset version produced for one AssetSpec."""

    id: str
    asset_spec_id: str
    generation_execution_id: str | None
    version: int
    storage_path: str
    media_type: str
    source_kind: str
    content_digest: str | None
    metadata: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class VisualStyleProfile:
    """An immutable, versioned visual-language configuration for generation."""

    id: str
    style_key: str
    version: int
    name: str
    description: str
    generation_guidance: str
    rules: dict[str, Any]
    metadata: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class CharacterProfile:
    """An immutable, versioned canonical identity for recurring characters."""

    id: str
    character_key: str
    version: int
    name: str
    identity_description: str
    generation_guidance: str
    metadata: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class CharacterReferenceSet:
    """An immutable ordered visual-reference basis for one CharacterProfile."""

    id: str
    character_profile_id: str
    version: int
    created_at: str


@dataclass(frozen=True)
class CharacterReferenceSetMember:
    """One immutable Asset member of a CharacterReferenceSet."""

    character_reference_set_id: str
    asset_id: str
    position: int
    created_at: str


Migration = tuple[int, tuple[str, ...]]
EDITORIAL_ANGLE_CLAIM_ROLES = frozenset({"core", "supporting"})
GENERATION_EXECUTION_OUTCOMES = frozenset({"succeeded", "failed"})
IDEA_GATE_DECISION_OUTCOMES = frozenset({"Proceed", "Reject", "Steer"})
RESEARCH_READINESS_OUTCOMES = frozenset({"Ready", "NeedsMoreResearch", "Blocked"})
EDITORIAL_READINESS_OUTCOMES = frozenset({"Ready", "NotReady"})
EDITORIAL_GATE_DECISION_OUTCOMES = frozenset({"Approve", "Revise", "Reject"})
EDITORIAL_READINESS_ASSESSMENT_SCHEMA_VERSION = 1
EDITORIAL_READINESS_EVALUATOR_ID = "deterministic-editorial-readiness"
EDITORIAL_READINESS_EVALUATOR_VERSION = "v1"


@dataclass(frozen=True)
class GenerationExecution:
    """An immutable terminal generator attempt against one AssetSpec snapshot."""

    id: str
    asset_spec_id: str
    visual_style_profile_id: str | None
    character_profile_id: str | None
    character_reference_set_id: str | None
    asset_spec_snapshot: dict[str, Any]
    generation_input: dict[str, Any]
    generator_key: str
    provider_key: str | None
    model_key: str | None
    provider_request_id: str | None
    outcome: str
    error_code: str | None
    error_message: str | None
    response_metadata: dict[str, Any]
    created_at: str


MIGRATIONS: tuple[Migration, ...] = (
    (
        1,
        (
            """
        CREATE TABLE subjects (
          id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
          description TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
            """
        CREATE TABLE opportunities (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, summary TEXT NOT NULL, why_now TEXT NOT NULL,
          score INTEGER NOT NULL, status TEXT NOT NULL, metadata_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )
        """,
            """
        CREATE TABLE opportunity_subjects (
          opportunity_id TEXT NOT NULL, subject_id TEXT NOT NULL, relationship_type TEXT NOT NULL,
          created_at TEXT NOT NULL, PRIMARY KEY (opportunity_id, subject_id, relationship_type),
          FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
          FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        )
        """,
            "CREATE INDEX idx_opportunities_status_score ON opportunities (status, score DESC)",
            """
        CREATE INDEX idx_opportunity_subjects_subject
          ON opportunity_subjects (subject_id, opportunity_id)
        """,
        ),
    ),
    (
        2,
        (
            """
        CREATE TABLE research_packs (
          id TEXT PRIMARY KEY,
          opportunity_id TEXT NOT NULL,
          version INTEGER NOT NULL,
          summary TEXT NOT NULL,
          as_of_date TEXT NULL,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          UNIQUE (opportunity_id, version),
          FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE TABLE claims (
          id TEXT PRIMARY KEY,
          research_pack_id TEXT NOT NULL,
          text TEXT NOT NULL,
          claim_type TEXT NOT NULL,
          risk_level TEXT NOT NULL,
          freshness_type TEXT NOT NULL,
          verification_status TEXT NOT NULL,
          verification_notes TEXT NOT NULL,
          reviewed_at TEXT NULL,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY (research_pack_id) REFERENCES research_packs(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE TABLE sources (
          id TEXT PRIMARY KEY,
          source_type TEXT NOT NULL,
          title TEXT NOT NULL,
          publisher TEXT NOT NULL,
          author TEXT NULL,
          url TEXT NOT NULL UNIQUE,
          publication_date TEXT NULL,
          accessed_at TEXT NOT NULL,
          jurisdiction TEXT NULL,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """,
            """
        CREATE TABLE claim_evidence (
          claim_id TEXT NOT NULL,
          source_id TEXT NOT NULL,
          stance TEXT NOT NULL,
          reference TEXT NULL,
          notes TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          PRIMARY KEY (claim_id, source_id),
          FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE RESTRICT,
          FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE RESTRICT
        )
        """,
            "CREATE INDEX idx_claims_research_pack ON claims (research_pack_id)",
            "CREATE INDEX idx_claim_evidence_source ON claim_evidence (source_id, claim_id)",
        ),
    ),
    (
        3,
        (
            """
        CREATE TABLE editorial_angles (
          id TEXT PRIMARY KEY,
          opportunity_id TEXT NOT NULL,
          research_pack_id TEXT NOT NULL,
          working_title TEXT NOT NULL,
          thesis TEXT NOT NULL,
          audience_promise TEXT NOT NULL,
          framing TEXT NOT NULL,
          key_takeaways_json TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE RESTRICT,
          FOREIGN KEY (research_pack_id) REFERENCES research_packs(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE TABLE editorial_angle_claims (
          editorial_angle_id TEXT NOT NULL,
          claim_id TEXT NOT NULL,
          role TEXT NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY (editorial_angle_id, claim_id),
          FOREIGN KEY (editorial_angle_id) REFERENCES editorial_angles(id) ON DELETE RESTRICT,
          FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE RESTRICT
        )
        """,
            "CREATE INDEX idx_editorial_angles_opportunity ON editorial_angles (opportunity_id)",
            "CREATE INDEX idx_editorial_angles_research_pack "
            "ON editorial_angles (research_pack_id)",
            "CREATE INDEX idx_editorial_angle_claims_claim ON editorial_angle_claims (claim_id)",
        ),
    ),
    (
        4,
        (
            """
        CREATE TABLE content_pieces (
          id TEXT PRIMARY KEY,
          opportunity_id TEXT NOT NULL,
          editorial_angle_id TEXT NOT NULL,
          format_key TEXT NOT NULL,
          working_title TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE RESTRICT,
          FOREIGN KEY (editorial_angle_id) REFERENCES editorial_angles(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE TABLE scripts (
          id TEXT PRIMARY KEY,
          content_piece_id TEXT NOT NULL,
          version INTEGER NOT NULL,
          narration_text TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          UNIQUE (content_piece_id, version),
          FOREIGN KEY (content_piece_id) REFERENCES content_pieces(id) ON DELETE RESTRICT
        )
        """,
            "CREATE INDEX idx_content_pieces_opportunity ON content_pieces (opportunity_id)",
            "CREATE INDEX idx_content_pieces_editorial_angle "
            "ON content_pieces (editorial_angle_id)",
        ),
    ),
    (
        5,
        (
            """
        CREATE TABLE visual_plans (
          id TEXT PRIMARY KEY,
          content_piece_id TEXT NOT NULL,
          script_id TEXT NOT NULL,
          visual_direction TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY (content_piece_id) REFERENCES content_pieces(id) ON DELETE RESTRICT,
          FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE TABLE scenes (
          id TEXT PRIMARY KEY,
          visual_plan_id TEXT NOT NULL,
          sequence INTEGER NOT NULL,
          narration_excerpt TEXT NOT NULL,
          visual_intent TEXT NOT NULL,
          hamster_action TEXT NULL,
          on_screen_text TEXT NULL,
          transition_note TEXT NULL,
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          UNIQUE (visual_plan_id, sequence),
          FOREIGN KEY (visual_plan_id) REFERENCES visual_plans(id) ON DELETE RESTRICT
        )
        """,
            "CREATE INDEX idx_visual_plans_content_piece ON visual_plans (content_piece_id)",
            "CREATE INDEX idx_visual_plans_script ON visual_plans (script_id)",
        ),
    ),
    (
        6,
        (
            """
        CREATE TABLE asset_specs (
          id TEXT PRIMARY KEY,
          scene_id TEXT NOT NULL,
          asset_type TEXT NOT NULL,
          purpose TEXT NOT NULL,
          description TEXT NOT NULL,
          generation_prompt TEXT NOT NULL,
          continuity_key TEXT NULL,
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY (scene_id) REFERENCES scenes(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE TABLE assets (
          id TEXT PRIMARY KEY,
          asset_spec_id TEXT NOT NULL,
          version INTEGER NOT NULL,
          storage_path TEXT NOT NULL,
          media_type TEXT NOT NULL,
          source_kind TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          UNIQUE (asset_spec_id, version),
          FOREIGN KEY (asset_spec_id) REFERENCES asset_specs(id) ON DELETE RESTRICT
        )
        """,
            "CREATE INDEX idx_asset_specs_scene ON asset_specs (scene_id)",
        ),
    ),
    (
        7,
        (
            """
        CREATE TABLE generation_executions (
          id TEXT PRIMARY KEY,
          asset_spec_id TEXT NOT NULL,
          asset_spec_snapshot_json TEXT NOT NULL,
          generation_input_json TEXT NOT NULL,
          generator_key TEXT NOT NULL,
          provider_key TEXT NULL,
          model_key TEXT NULL,
          provider_request_id TEXT NULL,
          outcome TEXT NOT NULL CHECK (outcome IN ('succeeded', 'failed')),
          error_code TEXT NULL,
          error_message TEXT NULL,
          response_metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (asset_spec_id) REFERENCES asset_specs(id) ON DELETE RESTRICT
        )
        """,
            """
        ALTER TABLE assets
        ADD COLUMN generation_execution_id TEXT NULL
        REFERENCES generation_executions(id) ON DELETE RESTRICT
        """,
            """
        CREATE INDEX idx_generation_executions_asset_spec_created
          ON generation_executions (asset_spec_id, created_at)
        """,
            """
        CREATE UNIQUE INDEX idx_assets_generation_execution
          ON assets (generation_execution_id)
          WHERE generation_execution_id IS NOT NULL
        """,
        ),
    ),
    (
        8,
        (
            """
        CREATE TABLE visual_style_profiles (
          id TEXT PRIMARY KEY,
          style_key TEXT NOT NULL,
          version INTEGER NOT NULL,
          name TEXT NOT NULL,
          description TEXT NOT NULL,
          generation_guidance TEXT NOT NULL,
          rules_json TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          UNIQUE (style_key, version)
        )
        """,
            """
        ALTER TABLE generation_executions
        ADD COLUMN visual_style_profile_id TEXT NULL
        REFERENCES visual_style_profiles(id) ON DELETE RESTRICT
        """,
            """
        CREATE INDEX idx_generation_executions_visual_style_profile
          ON generation_executions (visual_style_profile_id)
        """,
        ),
    ),
    (
        9,
        (
            """
        CREATE TABLE character_profiles (
          id TEXT PRIMARY KEY,
          character_key TEXT NOT NULL,
          version INTEGER NOT NULL,
          name TEXT NOT NULL,
          identity_description TEXT NOT NULL,
          generation_guidance TEXT NOT NULL,
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          UNIQUE (character_key, version)
        )
        """,
            """
        ALTER TABLE asset_specs
        ADD COLUMN character_profile_id TEXT NULL
        REFERENCES character_profiles(id) ON DELETE RESTRICT
        """,
            """
        ALTER TABLE generation_executions
        ADD COLUMN character_profile_id TEXT NULL
        REFERENCES character_profiles(id) ON DELETE RESTRICT
        """,
            """
        CREATE INDEX idx_asset_specs_character_profile
          ON asset_specs (character_profile_id)
        """,
            """
        CREATE INDEX idx_generation_executions_character_profile
          ON generation_executions (character_profile_id)
        """,
        ),
    ),
    (
        10,
        (
            """
        ALTER TABLE assets
        ADD COLUMN content_digest TEXT NULL
        """,
            """
        CREATE TABLE character_reference_sets (
          id TEXT PRIMARY KEY,
          character_profile_id TEXT NOT NULL,
          version INTEGER NOT NULL,
          created_at TEXT NOT NULL,
          UNIQUE (character_profile_id, version),
          FOREIGN KEY (character_profile_id) REFERENCES character_profiles(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE TABLE character_reference_set_members (
          character_reference_set_id TEXT NOT NULL,
          asset_id TEXT NOT NULL,
          position INTEGER NOT NULL CHECK (position >= 1),
          created_at TEXT NOT NULL,
          PRIMARY KEY (character_reference_set_id, asset_id),
          UNIQUE (character_reference_set_id, position),
          FOREIGN KEY (character_reference_set_id) REFERENCES character_reference_sets(id)
            ON DELETE RESTRICT,
          FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE INDEX idx_character_reference_sets_profile_version
          ON character_reference_sets (character_profile_id, version)
        """,
            """
        CREATE INDEX idx_character_reference_set_members_asset
          ON character_reference_set_members (asset_id)
        """,
        ),
    ),
    (
        11,
        (
            """
        ALTER TABLE generation_executions
        ADD COLUMN character_reference_set_id TEXT NULL
        REFERENCES character_reference_sets(id) ON DELETE RESTRICT
        """,
            """
        CREATE INDEX idx_generation_executions_character_reference_set
          ON generation_executions (character_reference_set_id)
        """,
        ),
    ),
    (
        12,
        (
            """
        CREATE TABLE idea_gate_review_snapshots (
          id TEXT PRIMARY KEY,
          opportunity_id TEXT NOT NULL,
          payload_schema_version INTEGER NOT NULL CHECK (payload_schema_version >= 1),
          review_payload_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE TABLE idea_gate_decisions (
          id TEXT PRIMARY KEY,
          review_snapshot_id TEXT NOT NULL UNIQUE,
          outcome TEXT NOT NULL CHECK (outcome IN ('Proceed', 'Reject', 'Steer')),
          founder_actor TEXT NOT NULL,
          founder_comment TEXT NULL,
          founder_direction TEXT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (review_snapshot_id) REFERENCES idea_gate_review_snapshots(id)
            ON DELETE RESTRICT
        )
        """,
            """
        CREATE INDEX idx_idea_gate_review_snapshots_opportunity_created
          ON idea_gate_review_snapshots (opportunity_id, created_at, id)
        """,
            """
        CREATE INDEX idx_idea_gate_decisions_snapshot_created
          ON idea_gate_decisions (review_snapshot_id, created_at, id)
        """,
        ),
    ),
    (
        13,
        (
            """
        ALTER TABLE research_packs
        ADD COLUMN idea_gate_decision_id TEXT NULL
        REFERENCES idea_gate_decisions(id) ON DELETE RESTRICT
        """,
            """
        CREATE INDEX idx_research_packs_idea_gate_decision
          ON research_packs (idea_gate_decision_id, opportunity_id, version)
        """,
        ),
    ),
    (
        14,
        (
            """
        CREATE TABLE research_readiness_assessments (
          id TEXT PRIMARY KEY,
          research_pack_id TEXT NOT NULL,
          assessment_schema_version INTEGER NOT NULL CHECK (assessment_schema_version >= 1),
          frozen_evidence_state_json TEXT NOT NULL,
          outcome TEXT NOT NULL CHECK (outcome IN ('Ready', 'NeedsMoreResearch', 'Blocked')),
          findings_json TEXT NOT NULL,
          policy_version TEXT NOT NULL,
          producer_kind TEXT NOT NULL,
          producer_identifier TEXT NOT NULL,
          producer_implementation_version TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (research_pack_id) REFERENCES research_packs(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE INDEX idx_research_readiness_assessments_pack_created
          ON research_readiness_assessments (research_pack_id, created_at, id)
        """,
        ),
    ),
    (
        15,
        (
            """
        ALTER TABLE editorial_angles
        ADD COLUMN research_readiness_assessment_id TEXT NULL
        REFERENCES research_readiness_assessments(id) ON DELETE RESTRICT
        """,
            """
        CREATE INDEX idx_editorial_angles_research_readiness_assessment
          ON editorial_angles (research_readiness_assessment_id, created_at, id)
        """,
        ),
    ),
    (
        16,
        (
            """
        CREATE TABLE title_options (
          id TEXT PRIMARY KEY,
          content_piece_id TEXT NOT NULL,
          text TEXT NOT NULL CHECK (length(trim(text)) > 0),
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (content_piece_id) REFERENCES content_pieces(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE TABLE hook_options (
          id TEXT PRIMARY KEY,
          content_piece_id TEXT NOT NULL,
          text TEXT NOT NULL CHECK (length(trim(text)) > 0),
          metadata_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (content_piece_id) REFERENCES content_pieces(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE TABLE editorial_package_snapshots (
          id TEXT PRIMARY KEY,
          content_piece_id TEXT NOT NULL,
          title_option_id TEXT NOT NULL,
          hook_option_id TEXT NOT NULL,
          script_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (content_piece_id) REFERENCES content_pieces(id) ON DELETE RESTRICT,
          FOREIGN KEY (title_option_id) REFERENCES title_options(id) ON DELETE RESTRICT,
          FOREIGN KEY (hook_option_id) REFERENCES hook_options(id) ON DELETE RESTRICT,
          FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE RESTRICT
        )
        """,
            "CREATE INDEX idx_title_options_content_piece_created "
            "ON title_options (content_piece_id, created_at, id)",
            "CREATE INDEX idx_hook_options_content_piece_created "
            "ON hook_options (content_piece_id, created_at, id)",
            "CREATE INDEX idx_editorial_package_snapshots_content_piece_created "
            "ON editorial_package_snapshots (content_piece_id, created_at, id)",
            "CREATE INDEX idx_editorial_package_snapshots_title_option "
            "ON editorial_package_snapshots (title_option_id)",
            "CREATE INDEX idx_editorial_package_snapshots_hook_option "
            "ON editorial_package_snapshots (hook_option_id)",
            "CREATE INDEX idx_editorial_package_snapshots_script "
            "ON editorial_package_snapshots (script_id)",
        ),
    ),
    (
        17,
        (
            """
        CREATE TABLE script_claim_sets (
          id TEXT PRIMARY KEY,
          script_id TEXT NOT NULL UNIQUE,
          created_at TEXT NOT NULL,
          FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE TABLE script_claim_links (
          script_claim_set_id TEXT NOT NULL,
          claim_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY (script_claim_set_id, claim_id),
          FOREIGN KEY (script_claim_set_id) REFERENCES script_claim_sets(id) ON DELETE RESTRICT,
          FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE RESTRICT
        )
        """,
            "CREATE INDEX idx_script_claim_links_claim "
            "ON script_claim_links (claim_id, script_claim_set_id)",
        ),
    ),
    (
        18,
        (
            """
        CREATE TABLE editorial_readiness_assessments (
          id TEXT PRIMARY KEY,
          editorial_package_snapshot_id TEXT NOT NULL,
          assessment_schema_version INTEGER NOT NULL CHECK (assessment_schema_version >= 1),
          evaluator_id TEXT NOT NULL,
          evaluator_version TEXT NOT NULL,
          outcome TEXT NOT NULL CHECK (outcome IN ('Ready', 'NotReady')),
          findings_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (editorial_package_snapshot_id)
            REFERENCES editorial_package_snapshots(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE INDEX idx_editorial_readiness_assessments_package_created
          ON editorial_readiness_assessments (editorial_package_snapshot_id, created_at, id)
        """,
        ),
    ),
    (
        19,
        (
            """
        CREATE TABLE editorial_gate_decisions (
          id TEXT PRIMARY KEY,
          editorial_package_snapshot_id TEXT NOT NULL,
          editorial_readiness_assessment_id TEXT NOT NULL,
          outcome TEXT NOT NULL CHECK (outcome IN ('Approve', 'Revise', 'Reject')),
          actor TEXT NOT NULL CHECK (length(trim(actor)) > 0),
          comment TEXT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (editorial_package_snapshot_id)
            REFERENCES editorial_package_snapshots(id) ON DELETE RESTRICT,
          FOREIGN KEY (editorial_readiness_assessment_id)
            REFERENCES editorial_readiness_assessments(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE INDEX idx_editorial_gate_decisions_package_created
          ON editorial_gate_decisions (editorial_package_snapshot_id, created_at, id)
        """,
            """
        CREATE INDEX idx_editorial_gate_decisions_assessment
          ON editorial_gate_decisions (editorial_readiness_assessment_id)
        """,
            """
        CREATE TABLE visual_plan_gate_provenance (
          visual_plan_id TEXT PRIMARY KEY,
          editorial_gate_decision_id TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY (visual_plan_id) REFERENCES visual_plans(id) ON DELETE RESTRICT,
          FOREIGN KEY (editorial_gate_decision_id)
            REFERENCES editorial_gate_decisions(id) ON DELETE RESTRICT
        )
        """,
            """
        CREATE INDEX idx_visual_plan_gate_provenance_decision
          ON visual_plan_gate_provenance (editorial_gate_decision_id)
        """,
        ),
    ),
)


class AtlasRepository:
    """A small application/repository boundary over SQLite."""

    def __init__(
        self,
        database_path: Path | str | None = None,
        asset_storage_root: Path | str | None = None,
    ) -> None:
        self.database_path = Path(database_path or default_database_path())
        self.asset_storage_root = Path(
            asset_storage_root or os.environ.get("ATLAS_ASSET_STORAGE_ROOT", "data/assets")
        ).resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.apply_migrations()
        self.seed_demo_data()

    def close(self) -> None:
        self.connection.close()

    def apply_migrations(self, migrations: tuple[Migration, ...] | None = None) -> None:
        """Apply one explicit transaction per migration."""

        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        applied = {
            row["version"]
            for row in self.connection.execute("SELECT version FROM schema_migrations")
        }
        for version, statements in migrations or MIGRATIONS:
            if version not in applied:
                try:
                    self.connection.execute("BEGIN")
                    for statement in statements:
                        self.connection.execute(statement)
                    self.connection.execute(
                        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                        (version, now()),
                    )
                    self.connection.execute("COMMIT")
                except sqlite3.DatabaseError:
                    self.connection.rollback()
                    raise

    def create_subject(self, subject_id: str, slug: str, name: str, description: str) -> Subject:
        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO subjects VALUES (?, ?, ?, ?, 1, '{}', ?, ?)",
                (subject_id, slug, name, description, stamp, stamp),
            )
        return self.get_subject(subject_id)

    def get_subject(self, subject_id: str) -> Subject:
        row = self.connection.execute(
            "SELECT * FROM subjects WHERE id = ?", (subject_id,)
        ).fetchone()
        if row is None:
            raise KeyError(subject_id)
        return self._subject(row)

    def list_subjects(self) -> list[Subject]:
        return [
            self._subject(row)
            for row in self.connection.execute("SELECT * FROM subjects ORDER BY name")
        ]

    def create_opportunity(
        self,
        opportunity_id: str,
        title: str,
        summary: str,
        why_now: str,
        score: int,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> Opportunity:
        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO opportunities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    opportunity_id,
                    title,
                    summary,
                    why_now,
                    score,
                    status,
                    json.dumps(metadata or {}),
                    stamp,
                    stamp,
                ),
            )
        return self.get_opportunity(opportunity_id)

    def get_opportunity(self, opportunity_id: str) -> Opportunity:
        row = self.connection.execute(
            "SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)
        ).fetchone()
        if row is None:
            raise KeyError(opportunity_id)
        return self._opportunity(row)

    def list_opportunities(self) -> list[Opportunity]:
        rows = self.connection.execute(
            "SELECT * FROM opportunities ORDER BY score DESC, created_at"
        )
        return [self._opportunity(row) for row in rows]

    def update_opportunity(self, opportunity: Opportunity) -> Opportunity:
        with self.connection:
            result = self.connection.execute(
                "UPDATE opportunities SET title=?, summary=?, why_now=?, score=?, status=?, "
                "metadata_json=?, updated_at=? WHERE id=?",
                (
                    opportunity.title,
                    opportunity.summary,
                    opportunity.why_now,
                    opportunity.score,
                    opportunity.status,
                    json.dumps(opportunity.metadata),
                    now(),
                    opportunity.id,
                ),
            )
        if result.rowcount != 1:
            raise KeyError(opportunity.id)
        return self.get_opportunity(opportunity.id)

    def associate_subject(
        self, opportunity_id: str, subject_id: str, relationship_type: str = "primary"
    ) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO opportunity_subjects VALUES (?, ?, ?, ?)",
                (opportunity_id, subject_id, relationship_type, now()),
            )

    def opportunity_subjects(self, opportunity_id: str) -> list[tuple[Subject, str]]:
        rows = self.connection.execute(
            "SELECT subjects.*, opportunity_subjects.relationship_type FROM opportunity_subjects "
            "JOIN subjects ON subjects.id=opportunity_subjects.subject_id "
            "WHERE opportunity_subjects.opportunity_id=? ORDER BY relationship_type, name",
            (opportunity_id,),
        )
        return [(self._subject(row), row["relationship_type"]) for row in rows]

    def discover_payload(self) -> list[dict[str, Any]]:
        """Adapt persistence to the existing display API; no Pillar model is created."""

        return [
            {
                "id": item.id,
                "topic": item.title,
                "score": item.score,
                "why_now": item.why_now,
                "viewer_benefit": item.summary,
                "suggested_angle": item.metadata["suggested_angle"],
                "evidence_quality": item.metadata["evidence_quality"],
                "risk": item.metadata["risk"],
                "portfolio_relevance": item.metadata["portfolio_relevance"],
                "visual_potential": item.metadata["visual_potential"],
                "pillar": item.metadata.get("legacy_display_pillar", "Not yet classified"),
                "subjects": [
                    {
                        "id": subject.id,
                        "slug": subject.slug,
                        "name": subject.name,
                        "relationship_role": relationship_type,
                    }
                    for subject, relationship_type in self.opportunity_subjects(item.id)
                ],
            }
            for item in self.list_opportunities()
        ]

    def create_idea_gate_review_snapshot(
        self, snapshot_id: str, opportunity_id: str
    ) -> IdeaGateReviewSnapshot:
        """Freeze exactly the current Discover review material for one mutable Opportunity."""

        if not isinstance(snapshot_id, str) or not snapshot_id.strip():
            raise ValueError("Idea Gate review snapshot ID must be non-empty text.")
        opportunity = self.get_opportunity(opportunity_id)
        review_payload = self._idea_gate_review_payload(opportunity)
        with self.connection:
            self.connection.execute(
                "INSERT INTO idea_gate_review_snapshots "
                "(id, opportunity_id, payload_schema_version, review_payload_json, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    snapshot_id.strip(),
                    opportunity.id,
                    1,
                    json.dumps(review_payload, sort_keys=True),
                    now(),
                ),
            )
        return self.get_idea_gate_review_snapshot(snapshot_id.strip())

    def get_idea_gate_review_snapshot(self, snapshot_id: str) -> IdeaGateReviewSnapshot:
        row = self.connection.execute(
            "SELECT * FROM idea_gate_review_snapshots WHERE id = ?", (snapshot_id,)
        ).fetchone()
        if row is None:
            raise KeyError(snapshot_id)
        return self._idea_gate_review_snapshot(row)

    def list_idea_gate_review_snapshots(self, opportunity_id: str) -> list[IdeaGateReviewSnapshot]:
        """Return immutable review cycles in chronological creation order."""

        self.get_opportunity(opportunity_id)
        rows = self.connection.execute(
            "SELECT * FROM idea_gate_review_snapshots WHERE opportunity_id = ? "
            "ORDER BY created_at, id",
            (opportunity_id,),
        )
        return [self._idea_gate_review_snapshot(row) for row in rows]

    def record_idea_gate_decision(
        self,
        decision_id: str,
        review_snapshot_id: str,
        outcome: str,
        founder_actor: str = "founder",
        founder_comment: str | None = None,
        founder_direction: str | None = None,
    ) -> IdeaGateDecision:
        """Append one founder decision to one immutable Idea Gate review snapshot."""

        if not isinstance(decision_id, str) or not decision_id.strip():
            raise ValueError("Idea Gate decision ID must be non-empty text.")
        self.get_idea_gate_review_snapshot(review_snapshot_id)
        if self.get_idea_gate_decision_for_snapshot(review_snapshot_id) is not None:
            raise ValueError("An Idea Gate review snapshot may have only one decision.")
        self._validate_idea_gate_decision(
            outcome, founder_actor, founder_comment, founder_direction
        )
        try:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO idea_gate_decisions "
                    "(id, review_snapshot_id, outcome, founder_actor, founder_comment, "
                    "founder_direction, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        decision_id.strip(),
                        review_snapshot_id,
                        outcome,
                        founder_actor.strip(),
                        self._normalized_optional_text(founder_comment),
                        self._normalized_optional_text(founder_direction),
                        now(),
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise ValueError("An Idea Gate review snapshot may have only one decision.") from error
        return self.get_idea_gate_decision(decision_id.strip())

    def get_idea_gate_decision(self, decision_id: str) -> IdeaGateDecision:
        row = self.connection.execute(
            "SELECT * FROM idea_gate_decisions WHERE id = ?", (decision_id,)
        ).fetchone()
        if row is None:
            raise KeyError(decision_id)
        return self._idea_gate_decision(row)

    def get_idea_gate_decision_for_snapshot(
        self, review_snapshot_id: str
    ) -> IdeaGateDecision | None:
        row = self.connection.execute(
            "SELECT * FROM idea_gate_decisions WHERE review_snapshot_id = ?", (review_snapshot_id,)
        ).fetchone()
        return self._idea_gate_decision(row) if row else None

    def idea_gate_review_snapshot_payload(self, snapshot_id: str) -> dict[str, Any]:
        snapshot = self.get_idea_gate_review_snapshot(snapshot_id)
        return {
            "id": snapshot.id,
            "opportunity_id": snapshot.opportunity_id,
            "payload_schema_version": snapshot.payload_schema_version,
            "review_payload": snapshot.review_payload,
            "created_at": snapshot.created_at,
        }

    def idea_gate_decision_payload(self, decision_id: str) -> dict[str, Any]:
        decision = self.get_idea_gate_decision(decision_id)
        return self._idea_gate_decision_payload(decision)

    def idea_gate_history_payload(self, opportunity_id: str) -> dict[str, Any]:
        """Return complete additive review history without persisting a current decision."""

        snapshots = self.list_idea_gate_review_snapshots(opportunity_id)
        return {
            "opportunity_id": opportunity_id,
            "history": [
                {
                    "snapshot": self.idea_gate_review_snapshot_payload(snapshot.id),
                    "decision": (
                        self._idea_gate_decision_payload(decision)
                        if (decision := self.get_idea_gate_decision_for_snapshot(snapshot.id))
                        else None
                    ),
                }
                for snapshot in snapshots
            ],
        }

    def create_research_pack(
        self,
        research_pack_id: str,
        opportunity_id: str,
        version: int,
        summary: str,
        as_of_date: str | None = None,
        metadata: dict[str, Any] | None = None,
        idea_gate_decision_id: str | None = None,
    ) -> ResearchPack:
        """Create an immutable, versioned ResearchPack with optional Idea Gate provenance."""

        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO research_packs "
                "(id, opportunity_id, version, summary, as_of_date, metadata_json, created_at, "
                "updated_at, idea_gate_decision_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    research_pack_id,
                    opportunity_id,
                    version,
                    summary,
                    as_of_date,
                    json.dumps(metadata or {}),
                    stamp,
                    stamp,
                    idea_gate_decision_id,
                ),
            )
        return self.get_research_pack(research_pack_id)

    def create_research_pack_under_idea_gate_authorization(
        self,
        research_pack_id: str,
        opportunity_id: str,
        version: int,
        summary: str,
        idea_gate_decision_id: str,
        as_of_date: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResearchPack:
        """Deliberately create one ResearchPack under explicit qualifying Idea Gate authority."""

        decision = self.get_idea_gate_decision(idea_gate_decision_id)
        snapshot = self.get_idea_gate_review_snapshot(decision.review_snapshot_id)
        if decision.outcome not in {"Proceed", "Steer"}:
            raise ValueError("Only Proceed or Steer may authorize ResearchPack creation.")
        if snapshot.opportunity_id != opportunity_id:
            raise ValueError(
                "The Idea Gate decision snapshot must belong to the ResearchPack Opportunity."
            )
        return self.create_research_pack(
            research_pack_id,
            opportunity_id,
            version,
            summary,
            as_of_date,
            metadata,
            idea_gate_decision_id=decision.id,
        )

    def get_research_pack(self, research_pack_id: str) -> ResearchPack:
        row = self.connection.execute(
            "SELECT * FROM research_packs WHERE id = ?", (research_pack_id,)
        ).fetchone()
        if row is None:
            raise KeyError(research_pack_id)
        return self._research_pack(row)

    def list_research_packs(self, opportunity_id: str) -> list[ResearchPack]:
        rows = self.connection.execute(
            "SELECT * FROM research_packs WHERE opportunity_id = ? ORDER BY version",
            (opportunity_id,),
        )
        return [self._research_pack(row) for row in rows]

    def latest_research_pack(self, opportunity_id: str) -> ResearchPack | None:
        row = self.connection.execute(
            "SELECT * FROM research_packs WHERE opportunity_id = ? "
            "ORDER BY version DESC LIMIT 1",
            (opportunity_id,),
        ).fetchone()
        return self._research_pack(row) if row else None

    def build_research_readiness_evidence_state(self, research_pack_id: str) -> dict[str, Any]:
        """Freeze the canonical current evidence graph for one ResearchPack.

        Claims are scoped to the pack. Sources are scoped only through ClaimEvidence
        attached to those Claims, so global Sources with no relevant evidence link are
        intentionally excluded.
        """

        pack = self.get_research_pack(research_pack_id)
        claims = sorted(self.list_claims(pack.id), key=lambda claim: claim.id)
        evidence_links: list[ClaimEvidence] = []
        sources: dict[str, Source] = {}
        for claim in claims:
            for relationship, source in self.evidence_for_claim(claim.id):
                evidence_links.append(relationship)
                sources[source.id] = source
        return {
            "schema_version": 1,
            "research_pack": {
                "id": pack.id,
                "version": pack.version,
                "summary": pack.summary,
                "as_of_date": pack.as_of_date,
            },
            "claims": [
                {
                    "id": claim.id,
                    "text": claim.text,
                    "claim_type": claim.claim_type,
                    "risk_level": claim.risk_level,
                    "freshness_type": claim.freshness_type,
                    "verification_status": claim.verification_status,
                    "verification_notes": claim.verification_notes,
                    "reviewed_at": claim.reviewed_at,
                }
                for claim in claims
            ],
            "sources": [
                {
                    "id": source.id,
                    "source_type": source.source_type,
                    "title": source.title,
                    "publisher": source.publisher,
                    "url": source.url,
                    "publication_date": source.publication_date,
                    "accessed_at": source.accessed_at,
                    "jurisdiction": source.jurisdiction,
                }
                for source in sorted(sources.values(), key=lambda source: source.id)
            ],
            "claim_evidence": [
                {
                    "claim_id": relationship.claim_id,
                    "source_id": relationship.source_id,
                    "stance": relationship.stance,
                    "reference": relationship.reference,
                    "notes": relationship.notes,
                }
                for relationship in sorted(
                    evidence_links,
                    key=lambda relationship: (relationship.claim_id, relationship.source_id),
                )
            ],
        }

    def create_research_readiness_assessment(
        self,
        assessment_id: str,
        research_pack_id: str,
        outcome: str,
        findings: dict[str, Any],
        policy_version: str,
        producer_kind: str,
        producer_identifier: str,
        producer_implementation_version: str,
    ) -> ResearchReadinessAssessment:
        """Append one immutable, server-frozen readiness assessment."""

        if not isinstance(assessment_id, str) or not assessment_id.strip():
            raise ValueError("Research readiness assessment ID must be non-empty text.")
        self.get_research_pack(research_pack_id)
        if self.connection.execute(
            "SELECT 1 FROM research_readiness_assessments WHERE id = ?", (assessment_id.strip(),)
        ).fetchone():
            raise ValueError("Research readiness assessment ID already exists.")
        self._validate_research_readiness_assessment(
            outcome,
            findings,
            policy_version,
            producer_kind,
            producer_identifier,
            producer_implementation_version,
        )
        frozen_evidence_state = self.build_research_readiness_evidence_state(research_pack_id)
        with self.connection:
            self.connection.execute(
                "INSERT INTO research_readiness_assessments "
                "(id, research_pack_id, assessment_schema_version, frozen_evidence_state_json, "
                "outcome, findings_json, policy_version, producer_kind, producer_identifier, "
                "producer_implementation_version, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    assessment_id.strip(),
                    research_pack_id,
                    1,
                    json.dumps(frozen_evidence_state, sort_keys=True, separators=(",", ":")),
                    outcome,
                    json.dumps(findings, sort_keys=True, separators=(",", ":")),
                    policy_version.strip(),
                    producer_kind.strip(),
                    producer_identifier.strip(),
                    producer_implementation_version.strip(),
                    now(),
                ),
            )
        return self.get_research_readiness_assessment(assessment_id.strip())

    def get_research_readiness_assessment(self, assessment_id: str) -> ResearchReadinessAssessment:
        row = self.connection.execute(
            "SELECT * FROM research_readiness_assessments WHERE id = ?", (assessment_id,)
        ).fetchone()
        if row is None:
            raise KeyError(assessment_id)
        return self._research_readiness_assessment(row)

    def list_research_readiness_assessments(
        self, research_pack_id: str
    ) -> list[ResearchReadinessAssessment]:
        """Return append-only readiness history in deterministic creation order."""

        self.get_research_pack(research_pack_id)
        rows = self.connection.execute(
            "SELECT * FROM research_readiness_assessments WHERE research_pack_id = ? "
            "ORDER BY created_at, id",
            (research_pack_id,),
        )
        return [self._research_readiness_assessment(row) for row in rows]

    def research_readiness_assessment_payload(self, assessment_id: str) -> dict[str, Any]:
        assessment = self.get_research_readiness_assessment(assessment_id)
        return self._research_readiness_assessment_payload(assessment)

    def research_readiness_history_payload(self, research_pack_id: str) -> dict[str, Any]:
        return {
            "research_pack_id": research_pack_id,
            "assessments": [
                self._research_readiness_assessment_payload(assessment)
                for assessment in self.list_research_readiness_assessments(research_pack_id)
            ],
        }

    def create_editorial_angle(
        self,
        editorial_angle_id: str,
        opportunity_id: str,
        research_pack_id: str,
        working_title: str,
        thesis: str,
        audience_promise: str,
        framing: str,
        key_takeaways: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> EditorialAngle:
        """Create an editorial proposition grounded in its Opportunity's ResearchPack."""

        self._validate_angle_research_pack(opportunity_id, research_pack_id)
        self._validate_editorial_angle_takeaways(key_takeaways)
        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO editorial_angles "
                "(id, opportunity_id, research_pack_id, working_title, thesis, audience_promise, "
                "framing, key_takeaways_json, metadata_json, created_at, updated_at, "
                "research_readiness_assessment_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                (
                    editorial_angle_id,
                    opportunity_id,
                    research_pack_id,
                    working_title,
                    thesis,
                    audience_promise,
                    framing,
                    json.dumps(key_takeaways),
                    json.dumps(metadata or {}),
                    stamp,
                    stamp,
                ),
            )
        return self.get_editorial_angle(editorial_angle_id)

    def create_editorial_angle_under_research_readiness(
        self,
        editorial_angle_id: str,
        opportunity_id: str,
        research_pack_id: str,
        research_readiness_assessment_id: str,
        working_title: str,
        thesis: str,
        audience_promise: str,
        framing: str,
        key_takeaways: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> EditorialAngle:
        """Deliberately create one Angle under an exact Ready readiness assessment."""

        self.get_opportunity(opportunity_id)
        research_pack = self.get_research_pack(research_pack_id)
        if research_pack.opportunity_id != opportunity_id:
            raise ValueError("An EditorialAngle must use a ResearchPack from the same Opportunity.")
        assessment = self.get_research_readiness_assessment(research_readiness_assessment_id)
        if assessment.outcome != "Ready":
            raise ValueError(
                "Only a Ready ResearchReadinessAssessment may authorize EditorialAngle creation."
            )
        if assessment.research_pack_id != research_pack.id:
            raise ValueError(
                "The ResearchReadinessAssessment must belong to the EditorialAngle ResearchPack."
            )
        self._validate_editorial_angle_takeaways(key_takeaways)
        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO editorial_angles "
                "(id, opportunity_id, research_pack_id, working_title, thesis, audience_promise, "
                "framing, key_takeaways_json, metadata_json, created_at, updated_at, "
                "research_readiness_assessment_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    editorial_angle_id,
                    opportunity_id,
                    research_pack_id,
                    working_title,
                    thesis,
                    audience_promise,
                    framing,
                    json.dumps(key_takeaways),
                    json.dumps(metadata or {}),
                    stamp,
                    stamp,
                    assessment.id,
                ),
            )
        return self.get_editorial_angle(editorial_angle_id)

    def get_editorial_angle(self, editorial_angle_id: str) -> EditorialAngle:
        row = self.connection.execute(
            "SELECT * FROM editorial_angles WHERE id = ?", (editorial_angle_id,)
        ).fetchone()
        if row is None:
            raise KeyError(editorial_angle_id)
        return self._editorial_angle(row)

    def list_editorial_angles_for_opportunity(self, opportunity_id: str) -> list[EditorialAngle]:
        """Return an Opportunity's angles in stable seed and creation order."""

        rows = self.connection.execute(
            "SELECT * FROM editorial_angles WHERE opportunity_id = ? ORDER BY created_at, id",
            (opportunity_id,),
        )
        return [self._editorial_angle(row) for row in rows]

    def list_editorial_angles_for_research_pack(
        self, research_pack_id: str
    ) -> list[EditorialAngle]:
        """Return all editorial propositions supported by one ResearchPack."""

        rows = self.connection.execute(
            "SELECT * FROM editorial_angles WHERE research_pack_id = ? ORDER BY created_at, id",
            (research_pack_id,),
        )
        return [self._editorial_angle(row) for row in rows]

    def update_editorial_angle(self, editorial_angle: EditorialAngle) -> EditorialAngle:
        """Persist normal edits without changing the Angle's historical provenance."""

        persisted_angle = self.get_editorial_angle(editorial_angle.id)
        if (
            editorial_angle.opportunity_id != persisted_angle.opportunity_id
            or editorial_angle.research_pack_id != persisted_angle.research_pack_id
            or (
                editorial_angle.research_readiness_assessment_id
                != persisted_angle.research_readiness_assessment_id
            )
        ):
            raise ValueError(
                "EditorialAngle Opportunity, ResearchPack and readiness provenance are immutable."
            )
        self._validate_editorial_angle_takeaways(editorial_angle.key_takeaways)
        with self.connection:
            result = self.connection.execute(
                "UPDATE editorial_angles SET working_title=?, "
                "thesis=?, audience_promise=?, framing=?, key_takeaways_json=?, metadata_json=?, "
                "updated_at=? WHERE id=?",
                (
                    editorial_angle.working_title,
                    editorial_angle.thesis,
                    editorial_angle.audience_promise,
                    editorial_angle.framing,
                    json.dumps(editorial_angle.key_takeaways),
                    json.dumps(editorial_angle.metadata),
                    now(),
                    editorial_angle.id,
                ),
            )
        if result.rowcount != 1:
            raise KeyError(editorial_angle.id)
        return self.get_editorial_angle(editorial_angle.id)

    def link_claim_to_editorial_angle(
        self, editorial_angle_id: str, claim_id: str, role: str
    ) -> EditorialAngleClaim:
        """Link a same-pack Claim once without overwriting an existing role."""

        self._validate_angle_claim_research_pack(editorial_angle_id, claim_id)
        self._validate_editorial_angle_claim_role(role)
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO editorial_angle_claims VALUES (?, ?, ?, ?)",
                (editorial_angle_id, claim_id, role, now()),
            )
        return self.get_editorial_angle_claim(editorial_angle_id, claim_id)

    def get_editorial_angle_claim(
        self, editorial_angle_id: str, claim_id: str
    ) -> EditorialAngleClaim:
        row = self.connection.execute(
            "SELECT * FROM editorial_angle_claims WHERE editorial_angle_id = ? AND claim_id = ?",
            (editorial_angle_id, claim_id),
        ).fetchone()
        if row is None:
            raise KeyError((editorial_angle_id, claim_id))
        return self._editorial_angle_claim(row)

    def update_editorial_angle_claim_role(
        self, editorial_angle_id: str, claim_id: str, role: str
    ) -> EditorialAngleClaim:
        """Update only an existing Claim's application-level role in an Angle."""

        self._validate_angle_claim_research_pack(editorial_angle_id, claim_id)
        self._validate_editorial_angle_claim_role(role)
        with self.connection:
            result = self.connection.execute(
                "UPDATE editorial_angle_claims SET role=? "
                "WHERE editorial_angle_id=? AND claim_id=?",
                (role, editorial_angle_id, claim_id),
            )
        if result.rowcount != 1:
            raise KeyError((editorial_angle_id, claim_id))
        return self.get_editorial_angle_claim(editorial_angle_id, claim_id)

    def claims_for_editorial_angle(
        self, editorial_angle_id: str
    ) -> list[tuple[EditorialAngleClaim, Claim]]:
        """Load Claims and their roles for a persistent EditorialAngle."""

        rows = self.connection.execute(
            "SELECT editorial_angle_claims.*, claims.research_pack_id, claims.text, "
            "claims.claim_type, claims.risk_level, claims.freshness_type, "
            "claims.verification_status, claims.verification_notes, claims.reviewed_at, "
            "claims.metadata_json AS claim_metadata_json, claims.created_at AS claim_created_at, "
            "claims.updated_at AS claim_updated_at FROM editorial_angle_claims "
            "JOIN claims ON claims.id = editorial_angle_claims.claim_id "
            "WHERE editorial_angle_claims.editorial_angle_id = ? "
            "ORDER BY editorial_angle_claims.created_at, claims.id",
            (editorial_angle_id,),
        )
        return [
            (
                self._editorial_angle_claim(row),
                Claim(
                    row["claim_id"],
                    row["research_pack_id"],
                    row["text"],
                    row["claim_type"],
                    row["risk_level"],
                    row["freshness_type"],
                    row["verification_status"],
                    row["verification_notes"],
                    row["reviewed_at"],
                    json.loads(row["claim_metadata_json"]),
                    row["claim_created_at"],
                    row["claim_updated_at"],
                ),
            )
            for row in rows
        ]

    def editorial_angle_payload(self, editorial_angle_id: str) -> dict[str, Any]:
        """Load one read-only angle with the persistent Claims that ground it."""

        angle = self.get_editorial_angle(editorial_angle_id)
        return {
            "id": angle.id,
            "opportunity_id": angle.opportunity_id,
            "research_pack_id": angle.research_pack_id,
            "research_readiness_assessment_id": angle.research_readiness_assessment_id,
            "working_title": angle.working_title,
            "thesis": angle.thesis,
            "audience_promise": angle.audience_promise,
            "framing": angle.framing,
            "key_takeaways": angle.key_takeaways,
            "claims": [
                {
                    "id": claim.id,
                    "text": claim.text,
                    "claim_type": claim.claim_type,
                    "role": relationship.role,
                }
                for relationship, claim in self.claims_for_editorial_angle(angle.id)
            ],
        }

    def create_content_piece(
        self,
        content_piece_id: str,
        opportunity_id: str,
        editorial_angle_id: str,
        format_key: str,
        working_title: str,
        metadata: dict[str, Any] | None = None,
    ) -> ContentPiece:
        """Create a concrete deliverable without detaching it from its Angle provenance."""

        self._validate_content_piece_editorial_angle(opportunity_id, editorial_angle_id)
        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO content_pieces VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    content_piece_id,
                    opportunity_id,
                    editorial_angle_id,
                    format_key,
                    working_title,
                    json.dumps(metadata or {}),
                    stamp,
                    stamp,
                ),
            )
        return self.get_content_piece(content_piece_id)

    def create_content_piece_under_editorial_angle_readiness(
        self,
        content_piece_id: str,
        opportunity_id: str,
        editorial_angle_id: str,
        format_key: str,
        working_title: str,
        metadata: dict[str, Any] | None = None,
    ) -> ContentPiece:
        """Deliberately create one ContentPiece from an exact Ready-authorized Angle."""

        self.get_opportunity(opportunity_id)
        editorial_angle = self.get_editorial_angle(editorial_angle_id)
        if editorial_angle.opportunity_id != opportunity_id:
            raise ValueError("A ContentPiece must use an EditorialAngle from the same Opportunity.")
        assessment_id = editorial_angle.research_readiness_assessment_id
        if assessment_id is None:
            raise ValueError(
                "A readiness-authorized ContentPiece requires EditorialAngle readiness provenance."
            )
        try:
            assessment = self.get_research_readiness_assessment(assessment_id)
        except KeyError as error:
            raise ValueError(
                "The EditorialAngle readiness provenance must reference an existing "
                "ResearchReadinessAssessment."
            ) from error
        if assessment.outcome != "Ready":
            raise ValueError(
                "Only a Ready ResearchReadinessAssessment may authorize ContentPiece creation."
            )
        if assessment.research_pack_id != editorial_angle.research_pack_id:
            raise ValueError(
                "The ResearchReadinessAssessment must belong to the EditorialAngle ResearchPack."
            )
        try:
            research_pack = self.get_research_pack(editorial_angle.research_pack_id)
        except KeyError as error:
            raise ValueError(
                "The EditorialAngle must reference an existing ResearchPack."
            ) from error
        if research_pack.opportunity_id != opportunity_id:
            raise ValueError(
                "The EditorialAngle ResearchPack must belong to the ContentPiece Opportunity."
            )
        return self.create_content_piece(
            content_piece_id,
            opportunity_id,
            editorial_angle_id,
            format_key,
            working_title,
            metadata,
        )

    def get_content_piece(self, content_piece_id: str) -> ContentPiece:
        row = self.connection.execute(
            "SELECT * FROM content_pieces WHERE id = ?", (content_piece_id,)
        ).fetchone()
        if row is None:
            raise KeyError(content_piece_id)
        return self._content_piece(row)

    def list_content_pieces_for_opportunity(self, opportunity_id: str) -> list[ContentPiece]:
        """Return an Opportunity's ContentPieces in stable creation order."""

        rows = self.connection.execute(
            "SELECT * FROM content_pieces WHERE opportunity_id = ? ORDER BY created_at, id",
            (opportunity_id,),
        )
        return [self._content_piece(row) for row in rows]

    def list_content_pieces_for_editorial_angle(
        self, editorial_angle_id: str
    ) -> list[ContentPiece]:
        """Return the deliverables derived from one EditorialAngle."""

        rows = self.connection.execute(
            "SELECT * FROM content_pieces WHERE editorial_angle_id = ? ORDER BY created_at, id",
            (editorial_angle_id,),
        )
        return [self._content_piece(row) for row in rows]

    def update_content_piece(self, content_piece: ContentPiece) -> ContentPiece:
        """Persist normal deliverable edits without changing historical provenance."""

        persisted_piece = self.get_content_piece(content_piece.id)
        if (
            content_piece.opportunity_id != persisted_piece.opportunity_id
            or content_piece.editorial_angle_id != persisted_piece.editorial_angle_id
        ):
            raise ValueError(
                "ContentPiece Opportunity and EditorialAngle provenance are immutable."
            )
        with self.connection:
            result = self.connection.execute(
                "UPDATE content_pieces SET format_key=?, working_title=?, metadata_json=?, "
                "updated_at=? WHERE id=?",
                (
                    content_piece.format_key,
                    content_piece.working_title,
                    json.dumps(content_piece.metadata),
                    now(),
                    content_piece.id,
                ),
            )
        if result.rowcount != 1:
            raise KeyError(content_piece.id)
        return self.get_content_piece(content_piece.id)

    def create_script(
        self,
        script_id: str,
        content_piece_id: str,
        version: int,
        narration_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> Script:
        """Create an immutable Script version for a ContentPiece."""

        with self.connection:
            self._insert_script(
                script_id, content_piece_id, narration_text, metadata, version=version
            )
        return self.get_script(script_id)

    def create_script_under_content_piece_readiness(
        self,
        script_id: str,
        content_piece_id: str,
        narration_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> Script:
        """Deliberately append one Script under exact Ready ContentPiece provenance."""

        self._validate_content_piece_readiness_lineage(content_piece_id)
        with self.connection:
            self._insert_script(script_id, content_piece_id, narration_text, metadata)
        return self.get_script(script_id)

    def get_script(self, script_id: str) -> Script:
        row = self.connection.execute("SELECT * FROM scripts WHERE id = ?", (script_id,)).fetchone()
        if row is None:
            raise KeyError(script_id)
        return self._script(row)

    def list_scripts_for_content_piece(self, content_piece_id: str) -> list[Script]:
        """Return immutable narration versions in ascending version order."""

        rows = self.connection.execute(
            "SELECT * FROM scripts WHERE content_piece_id = ? ORDER BY version", (content_piece_id,)
        )
        return [self._script(row) for row in rows]

    def latest_script_for_content_piece(self, content_piece_id: str) -> Script | None:
        """Return the highest-version Script without persisting a current-state flag."""

        row = self.connection.execute(
            "SELECT * FROM scripts WHERE content_piece_id = ? ORDER BY version DESC LIMIT 1",
            (content_piece_id,),
        ).fetchone()
        return self._script(row) if row else None

    def create_script_claim_set(
        self, script_claim_set_id: str, script_id: str, claim_ids: list[str]
    ) -> ScriptClaimSet:
        """Close one explicit, immutable Claim-provenance set for an eligible Script."""

        if not isinstance(script_claim_set_id, str) or not script_claim_set_id.strip():
            raise ValueError("ScriptClaimSet ID must be non-empty text.")
        if not isinstance(claim_ids, list) or any(
            not isinstance(claim_id, str) or not claim_id.strip() for claim_id in claim_ids
        ):
            raise ValueError("ScriptClaimSet claim_ids must be an array of non-empty text.")
        normalized_claim_ids = [claim_id.strip() for claim_id in claim_ids]
        if len(set(normalized_claim_ids)) != len(normalized_claim_ids):
            raise ValueError("ScriptClaimSet claim_ids must not contain duplicates.")

        script = self.get_script(script_id)
        if self.get_script_claim_set_for_script(script.id) is not None:
            raise ValueError("A Script may have only one closed ScriptClaimSet.")
        content_piece = self._validate_content_piece_readiness_lineage(script.content_piece_id)
        editorial_angle = self.get_editorial_angle(content_piece.editorial_angle_id)
        assessment = self.get_research_readiness_assessment(
            editorial_angle.research_readiness_assessment_id or ""
        )
        frozen_claims = self._frozen_claims_by_id(assessment)
        for claim_id in normalized_claim_ids:
            claim = self.get_claim(claim_id)
            if claim.research_pack_id != editorial_angle.research_pack_id:
                raise ValueError(
                    "A ScriptClaimSet Claim must belong to the EditorialAngle ResearchPack."
                )
            if claim.id not in frozen_claims:
                raise ValueError(
                    "A ScriptClaimSet Claim must appear in the exact Ready assessment "
                    "frozen evidence."
                )
            try:
                self.get_editorial_angle_claim(editorial_angle.id, claim.id)
            except KeyError as error:
                raise ValueError(
                    "A ScriptClaimSet Claim must be associated with the originating EditorialAngle."
                ) from error

        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO script_claim_sets VALUES (?, ?, ?)",
                (script_claim_set_id.strip(), script.id, stamp),
            )
            self.connection.executemany(
                "INSERT INTO script_claim_links VALUES (?, ?, ?)",
                [
                    (script_claim_set_id.strip(), claim_id, stamp)
                    for claim_id in normalized_claim_ids
                ],
            )
        return self.get_script_claim_set(script_claim_set_id.strip())

    def get_script_claim_set(self, script_claim_set_id: str) -> ScriptClaimSet:
        row = self.connection.execute(
            "SELECT * FROM script_claim_sets WHERE id = ?", (script_claim_set_id,)
        ).fetchone()
        if row is None:
            raise KeyError(script_claim_set_id)
        return self._script_claim_set(row)

    def get_script_claim_set_for_script(self, script_id: str) -> ScriptClaimSet | None:
        """Return a Script's closed provenance declaration, if one exists."""

        row = self.connection.execute(
            "SELECT * FROM script_claim_sets WHERE script_id = ?", (script_id,)
        ).fetchone()
        return self._script_claim_set(row) if row else None

    def list_script_claim_links(self, script_claim_set_id: str) -> list[ScriptClaimLink]:
        """Return immutable Claim memberships in deterministic identity order."""

        self.get_script_claim_set(script_claim_set_id)
        rows = self.connection.execute(
            "SELECT * FROM script_claim_links WHERE script_claim_set_id = ? ORDER BY claim_id",
            (script_claim_set_id,),
        )
        return [self._script_claim_link(row) for row in rows]

    def script_claim_set_payload(self, script_id: str) -> dict[str, Any] | None:
        """Resolve a Script's closed Claim identities against exact frozen readiness evidence."""

        self.get_script(script_id)
        claim_set = self.get_script_claim_set_for_script(script_id)
        if claim_set is None:
            return None
        claim_ids = [link.claim_id for link in self.list_script_claim_links(claim_set.id)]
        assessment = self._script_claim_set_readiness_assessment(claim_set)
        frozen_claims = self._frozen_claims_by_id(assessment)
        frozen_evidence = assessment.frozen_evidence_state
        linked_evidence = [
            evidence
            for evidence in frozen_evidence.get("claim_evidence", [])
            if isinstance(evidence, dict) and evidence.get("claim_id") in set(claim_ids)
        ]
        source_ids = {
            evidence["source_id"]
            for evidence in linked_evidence
            if isinstance(evidence.get("source_id"), str)
        }
        return {
            "id": claim_set.id,
            "script_id": claim_set.script_id,
            "created_at": claim_set.created_at,
            "claim_ids": claim_ids,
            "frozen_claims": [frozen_claims[claim_id] for claim_id in claim_ids],
            "frozen_claim_evidence": linked_evidence,
            "frozen_sources": [
                source
                for source in frozen_evidence.get("sources", [])
                if isinstance(source, dict) and source.get("id") in source_ids
            ],
        }

    def content_piece_payload(self, content_piece_id: str) -> dict[str, Any]:
        """Load a read-only ContentPiece with its latest immutable Script version."""

        content_piece = self.get_content_piece(content_piece_id)
        latest_script = self.latest_script_for_content_piece(content_piece.id)
        return {
            "id": content_piece.id,
            "opportunity_id": content_piece.opportunity_id,
            "editorial_angle_id": content_piece.editorial_angle_id,
            "format_key": content_piece.format_key,
            "working_title": content_piece.working_title,
            "latest_script": (
                {
                    "id": latest_script.id,
                    "version": latest_script.version,
                    "narration_text": latest_script.narration_text,
                }
                if latest_script
                else None
            ),
        }

    def create_title_option_under_content_piece_readiness(
        self,
        title_option_id: str,
        content_piece_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> TitleOption:
        """Append one immutable title alternative under exact Ready ContentPiece provenance."""

        self._validate_content_piece_readiness_lineage(content_piece_id)
        self._validate_editorial_option_text(text, "TitleOption")
        with self.connection:
            self.connection.execute(
                "INSERT INTO title_options VALUES (?, ?, ?, ?, ?)",
                (title_option_id, content_piece_id, text, json.dumps(metadata or {}), now()),
            )
        return self.get_title_option(title_option_id)

    def get_title_option(self, title_option_id: str) -> TitleOption:
        row = self.connection.execute(
            "SELECT * FROM title_options WHERE id = ?", (title_option_id,)
        ).fetchone()
        if row is None:
            raise KeyError(title_option_id)
        return self._title_option(row)

    def list_title_options_for_content_piece(self, content_piece_id: str) -> list[TitleOption]:
        """Return immutable title alternatives in stable creation order."""

        rows = self.connection.execute(
            "SELECT * FROM title_options WHERE content_piece_id = ? ORDER BY created_at, id",
            (content_piece_id,),
        )
        return [self._title_option(row) for row in rows]

    def create_hook_option_under_content_piece_readiness(
        self,
        hook_option_id: str,
        content_piece_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> HookOption:
        """Append one immutable hook alternative under exact Ready ContentPiece provenance."""

        self._validate_content_piece_readiness_lineage(content_piece_id)
        self._validate_editorial_option_text(text, "HookOption")
        with self.connection:
            self.connection.execute(
                "INSERT INTO hook_options VALUES (?, ?, ?, ?, ?)",
                (hook_option_id, content_piece_id, text, json.dumps(metadata or {}), now()),
            )
        return self.get_hook_option(hook_option_id)

    def get_hook_option(self, hook_option_id: str) -> HookOption:
        row = self.connection.execute(
            "SELECT * FROM hook_options WHERE id = ?", (hook_option_id,)
        ).fetchone()
        if row is None:
            raise KeyError(hook_option_id)
        return self._hook_option(row)

    def list_hook_options_for_content_piece(self, content_piece_id: str) -> list[HookOption]:
        """Return immutable hook alternatives in stable creation order."""

        rows = self.connection.execute(
            "SELECT * FROM hook_options WHERE content_piece_id = ? ORDER BY created_at, id",
            (content_piece_id,),
        )
        return [self._hook_option(row) for row in rows]

    def create_editorial_package_snapshot(
        self,
        snapshot_id: str,
        content_piece_id: str,
        title_option_id: str,
        hook_option_id: str,
        script_id: str,
    ) -> EditorialPackageSnapshot:
        """Freeze one explicit title, hook and Script proposition for an eligible ContentPiece."""

        self._validate_content_piece_readiness_lineage(content_piece_id)
        title_option = self.get_title_option(title_option_id)
        hook_option = self.get_hook_option(hook_option_id)
        script = self.get_script(script_id)
        if title_option.content_piece_id != content_piece_id:
            raise ValueError("A package TitleOption must belong to the same ContentPiece.")
        if hook_option.content_piece_id != content_piece_id:
            raise ValueError("A package HookOption must belong to the same ContentPiece.")
        if script.content_piece_id != content_piece_id:
            raise ValueError("A package Script must belong to the same ContentPiece.")
        with self.connection:
            self.connection.execute(
                "INSERT INTO editorial_package_snapshots VALUES (?, ?, ?, ?, ?, ?)",
                (snapshot_id, content_piece_id, title_option_id, hook_option_id, script_id, now()),
            )
        return self.get_editorial_package_snapshot(snapshot_id)

    def get_editorial_package_snapshot(self, snapshot_id: str) -> EditorialPackageSnapshot:
        row = self.connection.execute(
            "SELECT * FROM editorial_package_snapshots WHERE id = ?", (snapshot_id,)
        ).fetchone()
        if row is None:
            raise KeyError(snapshot_id)
        return self._editorial_package_snapshot(row)

    def list_editorial_package_snapshots_for_content_piece(
        self, content_piece_id: str
    ) -> list[EditorialPackageSnapshot]:
        """Return frozen editorial propositions in stable creation order."""

        rows = self.connection.execute(
            "SELECT * FROM editorial_package_snapshots WHERE content_piece_id = ? "
            "ORDER BY created_at, id",
            (content_piece_id,),
        )
        return [self._editorial_package_snapshot(row) for row in rows]

    def create_editorial_readiness_assessment(
        self,
        assessment_id: str,
        editorial_package_snapshot_id: str,
    ) -> EditorialReadinessAssessment:
        """Append one server-derived deterministic assessment of an exact package."""

        if not isinstance(assessment_id, str) or not assessment_id.strip():
            raise ValueError("Editorial readiness assessment ID must be non-empty text.")
        snapshot = self.get_editorial_package_snapshot(editorial_package_snapshot_id)
        if self.connection.execute(
            "SELECT 1 FROM editorial_readiness_assessments WHERE id = ?", (assessment_id.strip(),)
        ).fetchone():
            raise ValueError("Editorial readiness assessment ID already exists.")

        findings = self._evaluate_editorial_package_readiness(snapshot)
        outcome = "NotReady" if any(finding["blocking"] for finding in findings) else "Ready"
        with self.connection:
            self.connection.execute(
                "INSERT INTO editorial_readiness_assessments "
                "(id, editorial_package_snapshot_id, assessment_schema_version, evaluator_id, "
                "evaluator_version, outcome, findings_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    assessment_id.strip(),
                    snapshot.id,
                    EDITORIAL_READINESS_ASSESSMENT_SCHEMA_VERSION,
                    EDITORIAL_READINESS_EVALUATOR_ID,
                    EDITORIAL_READINESS_EVALUATOR_VERSION,
                    outcome,
                    json.dumps({"findings": findings}, sort_keys=True, separators=(",", ":")),
                    now(),
                ),
            )
        return self.get_editorial_readiness_assessment(assessment_id.strip())

    def get_editorial_readiness_assessment(
        self, assessment_id: str
    ) -> EditorialReadinessAssessment:
        row = self.connection.execute(
            "SELECT * FROM editorial_readiness_assessments WHERE id = ?", (assessment_id,)
        ).fetchone()
        if row is None:
            raise KeyError(assessment_id)
        return self._editorial_readiness_assessment(row)

    def list_editorial_readiness_assessments(
        self, editorial_package_snapshot_id: str
    ) -> list[EditorialReadinessAssessment]:
        """Return immutable package assessment history in deterministic creation order."""

        self.get_editorial_package_snapshot(editorial_package_snapshot_id)
        rows = self.connection.execute(
            "SELECT * FROM editorial_readiness_assessments "
            "WHERE editorial_package_snapshot_id = ? ORDER BY created_at, id",
            (editorial_package_snapshot_id,),
        )
        return [self._editorial_readiness_assessment(row) for row in rows]

    def editorial_readiness_assessment_payload(self, assessment_id: str) -> dict[str, Any]:
        return self._editorial_readiness_assessment_payload(
            self.get_editorial_readiness_assessment(assessment_id)
        )

    def editorial_readiness_assessment_history_payload(
        self, editorial_package_snapshot_id: str
    ) -> dict[str, Any]:
        return {
            "editorial_package_snapshot_id": editorial_package_snapshot_id,
            "assessments": [
                self._editorial_readiness_assessment_payload(assessment)
                for assessment in self.list_editorial_readiness_assessments(
                    editorial_package_snapshot_id
                )
            ],
        }

    def create_editorial_gate_decision(
        self,
        decision_id: str,
        editorial_package_snapshot_id: str,
        editorial_readiness_assessment_id: str,
        outcome: str,
        actor: str,
        comment: str | None = None,
    ) -> EditorialGateDecision:
        """Append one immutable human decision over one exact Ready editorial package."""

        if not isinstance(decision_id, str) or not decision_id.strip():
            raise ValueError("Editorial Gate decision ID must be non-empty text.")
        snapshot = self.get_editorial_package_snapshot(editorial_package_snapshot_id)
        assessment = self.get_editorial_readiness_assessment(editorial_readiness_assessment_id)
        self._validate_editorial_gate_decision_input(snapshot, assessment, outcome, actor, comment)
        with self.connection:
            self.connection.execute(
                "INSERT INTO editorial_gate_decisions "
                "(id, editorial_package_snapshot_id, editorial_readiness_assessment_id, outcome, "
                "actor, comment, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    decision_id.strip(),
                    snapshot.id,
                    assessment.id,
                    outcome,
                    actor.strip(),
                    comment,
                    now(),
                ),
            )
        return self.get_editorial_gate_decision(decision_id.strip())

    def get_editorial_gate_decision(self, decision_id: str) -> EditorialGateDecision:
        row = self.connection.execute(
            "SELECT * FROM editorial_gate_decisions WHERE id = ?", (decision_id,)
        ).fetchone()
        if row is None:
            raise KeyError(decision_id)
        return self._editorial_gate_decision(row)

    def list_editorial_gate_decisions(
        self, editorial_package_snapshot_id: str
    ) -> list[EditorialGateDecision]:
        """Return immutable Editorial Gate decision history for one exact package."""

        self.get_editorial_package_snapshot(editorial_package_snapshot_id)
        rows = self.connection.execute(
            "SELECT * FROM editorial_gate_decisions WHERE editorial_package_snapshot_id = ? "
            "ORDER BY created_at, id",
            (editorial_package_snapshot_id,),
        )
        return [self._editorial_gate_decision(row) for row in rows]

    def editorial_gate_decision_payload(self, decision_id: str) -> dict[str, Any]:
        return self._editorial_gate_decision_payload(self.get_editorial_gate_decision(decision_id))

    def editorial_gate_decision_history_payload(
        self, editorial_package_snapshot_id: str
    ) -> dict[str, Any]:
        return {
            "editorial_package_snapshot_id": editorial_package_snapshot_id,
            "decisions": [
                self._editorial_gate_decision_payload(decision)
                for decision in self.list_editorial_gate_decisions(editorial_package_snapshot_id)
            ],
        }

    def create_visual_plan_under_editorial_gate(
        self,
        visual_plan_id: str,
        editorial_gate_decision_id: str,
        visual_direction: str,
        metadata: dict[str, Any] | None = None,
    ) -> VisualPlan:
        """Create one VisualPlan from the exact package and Script an Approve decision reviewed."""

        decision = self.get_editorial_gate_decision(editorial_gate_decision_id)
        snapshot, _assessment = self._validate_editorial_gate_decision_lineage(decision)
        if decision.outcome != "Approve":
            raise ValueError("Only an Approve EditorialGateDecision may initiate a VisualPlan.")
        try:
            self._validate_editorial_package_snapshot_integrity(snapshot)
            script = self.get_script(snapshot.script_id)
        except KeyError as error:
            raise ValueError(
                "The Editorial Gate package provenance must resolve its ContentPiece and Script."
            ) from error
        if script.content_piece_id != snapshot.content_piece_id:
            raise ValueError(
                "The Editorial Gate package Script must belong to its exact ContentPiece."
            )
        stamp = now()
        with self.connection:
            self._insert_visual_plan(
                visual_plan_id,
                snapshot.content_piece_id,
                snapshot.script_id,
                visual_direction,
                metadata,
                stamp,
            )
            self.connection.execute(
                "INSERT INTO visual_plan_gate_provenance "
                "(visual_plan_id, editorial_gate_decision_id, created_at) VALUES (?, ?, ?)",
                (visual_plan_id, decision.id, stamp),
            )
        return self.get_visual_plan(visual_plan_id)

    def get_visual_plan_gate_provenance(
        self, visual_plan_id: str
    ) -> VisualPlanGateProvenance | None:
        """Return deliberate Editorial Gate lineage when a VisualPlan has it."""

        self.get_visual_plan(visual_plan_id)
        row = self.connection.execute(
            "SELECT * FROM visual_plan_gate_provenance WHERE visual_plan_id = ?", (visual_plan_id,)
        ).fetchone()
        return self._visual_plan_gate_provenance(row) if row else None

    def list_visual_plans_for_editorial_gate_decision(
        self, editorial_gate_decision_id: str
    ) -> list[VisualPlan]:
        """Return all independently initiated VisualPlans from one Approve decision."""

        self.get_editorial_gate_decision(editorial_gate_decision_id)
        rows = self.connection.execute(
            "SELECT visual_plans.* FROM visual_plans "
            "JOIN visual_plan_gate_provenance "
            "ON visual_plan_gate_provenance.visual_plan_id = visual_plans.id "
            "WHERE visual_plan_gate_provenance.editorial_gate_decision_id = ? "
            "ORDER BY visual_plans.created_at, visual_plans.id",
            (editorial_gate_decision_id,),
        )
        return [self._visual_plan(row) for row in rows]

    def visual_plan_gate_provenance_payload(self, visual_plan_id: str) -> dict[str, Any] | None:
        provenance = self.get_visual_plan_gate_provenance(visual_plan_id)
        return self._visual_plan_gate_provenance_payload(provenance) if provenance else None

    @staticmethod
    def title_option_payload(title_option: TitleOption) -> dict[str, Any]:
        return {
            "id": title_option.id,
            "content_piece_id": title_option.content_piece_id,
            "text": title_option.text,
            "metadata": title_option.metadata,
            "created_at": title_option.created_at,
        }

    @staticmethod
    def hook_option_payload(hook_option: HookOption) -> dict[str, Any]:
        return {
            "id": hook_option.id,
            "content_piece_id": hook_option.content_piece_id,
            "text": hook_option.text,
            "metadata": hook_option.metadata,
            "created_at": hook_option.created_at,
        }

    @staticmethod
    def editorial_package_snapshot_payload(
        snapshot: EditorialPackageSnapshot,
    ) -> dict[str, Any]:
        return {
            "id": snapshot.id,
            "content_piece_id": snapshot.content_piece_id,
            "title_option_id": snapshot.title_option_id,
            "hook_option_id": snapshot.hook_option_id,
            "script_id": snapshot.script_id,
            "created_at": snapshot.created_at,
        }

    @staticmethod
    def _editorial_readiness_assessment_payload(
        assessment: EditorialReadinessAssessment,
    ) -> dict[str, Any]:
        return {
            "id": assessment.id,
            "editorial_package_snapshot_id": assessment.editorial_package_snapshot_id,
            "schema_version": assessment.schema_version,
            "evaluator_id": assessment.evaluator_id,
            "evaluator_version": assessment.evaluator_version,
            "outcome": assessment.outcome,
            "findings": assessment.findings,
            "created_at": assessment.created_at,
        }

    @staticmethod
    def _editorial_gate_decision_payload(decision: EditorialGateDecision) -> dict[str, Any]:
        return {
            "id": decision.id,
            "editorial_package_snapshot_id": decision.editorial_package_snapshot_id,
            "editorial_readiness_assessment_id": decision.editorial_readiness_assessment_id,
            "outcome": decision.outcome,
            "actor": decision.actor,
            "comment": decision.comment,
            "created_at": decision.created_at,
        }

    @staticmethod
    def _visual_plan_gate_provenance_payload(
        provenance: VisualPlanGateProvenance,
    ) -> dict[str, Any]:
        return {
            "visual_plan_id": provenance.visual_plan_id,
            "editorial_gate_decision_id": provenance.editorial_gate_decision_id,
            "created_at": provenance.created_at,
        }

    def create_visual_plan(
        self,
        visual_plan_id: str,
        content_piece_id: str,
        script_id: str,
        visual_direction: str,
        metadata: dict[str, Any] | None = None,
    ) -> VisualPlan:
        """Create a visual plan without detaching it from its exact Script version."""

        self._validate_visual_plan_script(content_piece_id, script_id)
        with self.connection:
            self._insert_visual_plan(
                visual_plan_id,
                content_piece_id,
                script_id,
                visual_direction,
                metadata,
                now(),
            )
        return self.get_visual_plan(visual_plan_id)

    def get_visual_plan(self, visual_plan_id: str) -> VisualPlan:
        row = self.connection.execute(
            "SELECT * FROM visual_plans WHERE id = ?", (visual_plan_id,)
        ).fetchone()
        if row is None:
            raise KeyError(visual_plan_id)
        return self._visual_plan(row)

    def list_visual_plans_for_content_piece(self, content_piece_id: str) -> list[VisualPlan]:
        """Return a ContentPiece's visual plans in stable creation order."""

        rows = self.connection.execute(
            "SELECT * FROM visual_plans WHERE content_piece_id = ? ORDER BY created_at, id",
            (content_piece_id,),
        )
        return [self._visual_plan(row) for row in rows]

    def list_visual_plans_for_script(self, script_id: str) -> list[VisualPlan]:
        """Return all visual plans for one immutable Script version."""

        rows = self.connection.execute(
            "SELECT * FROM visual_plans WHERE script_id = ? ORDER BY created_at, id",
            (script_id,),
        )
        return [self._visual_plan(row) for row in rows]

    def update_visual_plan(self, visual_plan: VisualPlan) -> VisualPlan:
        """Persist normal visual-direction edits without changing Script provenance."""

        persisted_plan = self.get_visual_plan(visual_plan.id)
        if (
            visual_plan.content_piece_id != persisted_plan.content_piece_id
            or visual_plan.script_id != persisted_plan.script_id
        ):
            raise ValueError("VisualPlan ContentPiece and Script provenance are immutable.")
        with self.connection:
            result = self.connection.execute(
                "UPDATE visual_plans SET visual_direction=?, metadata_json=?, "
                "updated_at=? WHERE id=?",
                (
                    visual_plan.visual_direction,
                    json.dumps(visual_plan.metadata),
                    now(),
                    visual_plan.id,
                ),
            )
        if result.rowcount != 1:
            raise KeyError(visual_plan.id)
        return self.get_visual_plan(visual_plan.id)

    def create_scene(
        self,
        scene_id: str,
        visual_plan_id: str,
        sequence: int,
        narration_excerpt: str,
        visual_intent: str,
        hamster_action: str | None = None,
        on_screen_text: str | None = None,
        transition_note: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Scene:
        """Create one ordered Scene whose excerpt only locates Script narration."""

        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO scenes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    scene_id,
                    visual_plan_id,
                    sequence,
                    narration_excerpt,
                    visual_intent,
                    hamster_action,
                    on_screen_text,
                    transition_note,
                    json.dumps(metadata or {}),
                    stamp,
                    stamp,
                ),
            )
        return self.get_scene(scene_id)

    def get_scene(self, scene_id: str) -> Scene:
        row = self.connection.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,)).fetchone()
        if row is None:
            raise KeyError(scene_id)
        return self._scene(row)

    def list_scenes_for_visual_plan(self, visual_plan_id: str) -> list[Scene]:
        """Return one VisualPlan's scenes in their explicit sequence order."""

        rows = self.connection.execute(
            "SELECT * FROM scenes WHERE visual_plan_id = ? ORDER BY sequence", (visual_plan_id,)
        )
        return [self._scene(row) for row in rows]

    def update_scene(self, scene: Scene) -> Scene:
        """Persist normal scene edits without moving the Scene to another VisualPlan."""

        persisted_scene = self.get_scene(scene.id)
        if scene.visual_plan_id != persisted_scene.visual_plan_id:
            raise ValueError("Scene VisualPlan provenance is immutable.")
        with self.connection:
            result = self.connection.execute(
                "UPDATE scenes SET sequence=?, narration_excerpt=?, visual_intent=?, "
                "hamster_action=?, on_screen_text=?, transition_note=?, metadata_json=?, "
                "updated_at=? WHERE id=?",
                (
                    scene.sequence,
                    scene.narration_excerpt,
                    scene.visual_intent,
                    scene.hamster_action,
                    scene.on_screen_text,
                    scene.transition_note,
                    json.dumps(scene.metadata),
                    now(),
                    scene.id,
                ),
            )
        if result.rowcount != 1:
            raise KeyError(scene.id)
        return self.get_scene(scene.id)

    def visual_plan_payload(self, visual_plan_id: str) -> dict[str, Any]:
        """Load one visual plan with its ordered, non-authoritative Scene locators."""

        visual_plan = self.get_visual_plan(visual_plan_id)
        return {
            "id": visual_plan.id,
            "content_piece_id": visual_plan.content_piece_id,
            "script_id": visual_plan.script_id,
            "visual_direction": visual_plan.visual_direction,
            "scenes": [
                {
                    "id": scene.id,
                    "sequence": scene.sequence,
                    "narration_excerpt": scene.narration_excerpt,
                    "visual_intent": scene.visual_intent,
                    "hamster_action": scene.hamster_action,
                    "on_screen_text": scene.on_screen_text,
                    "transition_note": scene.transition_note,
                    "asset_specs": [
                        self.asset_spec_payload(asset_spec.id)
                        for asset_spec in self.list_asset_specs_for_scene(scene.id)
                    ],
                }
                for scene in self.list_scenes_for_visual_plan(visual_plan.id)
            ],
        }

    def create_visual_style_profile(
        self,
        profile_id: str,
        style_key: str,
        version: int,
        name: str,
        description: str,
        generation_guidance: str,
        rules: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> VisualStyleProfile:
        """Create one immutable version of an Atlas visual-style profile."""

        profile_metadata = {} if metadata is None else metadata
        self._validate_visual_style_profile(
            version, style_key, name, description, generation_guidance, rules, profile_metadata
        )
        with self.connection:
            self.connection.execute(
                "INSERT INTO visual_style_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    profile_id,
                    style_key.strip(),
                    version,
                    name.strip(),
                    description.strip(),
                    generation_guidance.strip(),
                    json.dumps(rules, sort_keys=True),
                    json.dumps(profile_metadata, sort_keys=True),
                    now(),
                ),
            )
        return self.get_visual_style_profile(profile_id)

    def get_visual_style_profile(self, profile_id: str) -> VisualStyleProfile:
        """Return one immutable visual-style profile."""

        row = self.connection.execute(
            "SELECT * FROM visual_style_profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        if row is None:
            raise KeyError(profile_id)
        return self._visual_style_profile(row)

    def list_visual_style_profiles(self) -> list[VisualStyleProfile]:
        """Return immutable profiles in stable style/version order."""

        rows = self.connection.execute(
            "SELECT * FROM visual_style_profiles ORDER BY style_key, version"
        )
        return [self._visual_style_profile(row) for row in rows]

    def create_character_profile(
        self,
        profile_id: str,
        character_key: str,
        version: int,
        name: str,
        identity_description: str,
        generation_guidance: str,
        metadata: dict[str, Any] | None = None,
    ) -> CharacterProfile:
        """Create one immutable version of an Atlas character identity profile."""

        profile_metadata = {} if metadata is None else metadata
        self._validate_character_profile(
            version,
            character_key,
            name,
            identity_description,
            generation_guidance,
            profile_metadata,
        )
        with self.connection:
            self.connection.execute(
                "INSERT INTO character_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    profile_id,
                    character_key.strip(),
                    version,
                    name.strip(),
                    identity_description.strip(),
                    generation_guidance.strip(),
                    json.dumps(profile_metadata, sort_keys=True),
                    now(),
                ),
            )
        return self.get_character_profile(profile_id)

    def get_character_profile(self, profile_id: str) -> CharacterProfile:
        """Return one immutable character identity profile."""

        row = self.connection.execute(
            "SELECT * FROM character_profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        if row is None:
            raise KeyError(profile_id)
        return self._character_profile(row)

    def list_character_profiles(self) -> list[CharacterProfile]:
        """Return immutable character profiles in stable key/version order."""

        rows = self.connection.execute(
            "SELECT * FROM character_profiles ORDER BY character_key, version"
        )
        return [self._character_profile(row) for row in rows]

    def create_asset_spec(
        self,
        asset_spec_id: str,
        scene_id: str,
        asset_type: str,
        purpose: str,
        description: str,
        generation_prompt: str,
        continuity_key: str | None = None,
        character_profile_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AssetSpec:
        """Create a provider-neutral asset requirement for one persisted Scene."""

        self.get_scene(scene_id)
        self._validate_asset_spec_text(asset_type, purpose, description, generation_prompt)
        self._validate_asset_spec_character_profile(asset_type, character_profile_id)
        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO asset_specs "
                "(id, scene_id, asset_type, purpose, description, generation_prompt, "
                "continuity_key, metadata_json, created_at, updated_at, character_profile_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    asset_spec_id,
                    scene_id,
                    asset_type,
                    purpose,
                    description,
                    generation_prompt,
                    continuity_key,
                    json.dumps(metadata or {}),
                    stamp,
                    stamp,
                    character_profile_id,
                ),
            )
        return self.get_asset_spec(asset_spec_id)

    def get_asset_spec(self, asset_spec_id: str) -> AssetSpec:
        row = self.connection.execute(
            "SELECT * FROM asset_specs WHERE id = ?", (asset_spec_id,)
        ).fetchone()
        if row is None:
            raise KeyError(asset_spec_id)
        return self._asset_spec(row)

    def list_asset_specs_for_scene(self, scene_id: str) -> list[AssetSpec]:
        """Return one Scene's asset requirements in stable creation order."""

        rows = self.connection.execute(
            "SELECT * FROM asset_specs WHERE scene_id = ? ORDER BY created_at, id", (scene_id,)
        )
        return [self._asset_spec(row) for row in rows]

    def update_asset_spec(self, asset_spec: AssetSpec) -> AssetSpec:
        """Persist requirement edits without changing the owning Scene provenance."""

        persisted_spec = self.get_asset_spec(asset_spec.id)
        if asset_spec.scene_id != persisted_spec.scene_id:
            raise ValueError("AssetSpec Scene provenance is immutable.")
        self._validate_asset_spec_text(
            asset_spec.asset_type,
            asset_spec.purpose,
            asset_spec.description,
            asset_spec.generation_prompt,
        )
        self._validate_asset_spec_character_profile(
            asset_spec.asset_type, asset_spec.character_profile_id
        )
        with self.connection:
            result = self.connection.execute(
                "UPDATE asset_specs SET asset_type=?, purpose=?, description=?, "
                "generation_prompt=?, continuity_key=?, metadata_json=?, character_profile_id=?, "
                "updated_at=? WHERE id=?",
                (
                    asset_spec.asset_type,
                    asset_spec.purpose,
                    asset_spec.description,
                    asset_spec.generation_prompt,
                    asset_spec.continuity_key,
                    json.dumps(asset_spec.metadata),
                    asset_spec.character_profile_id,
                    now(),
                    asset_spec.id,
                ),
            )
        if result.rowcount != 1:
            raise KeyError(asset_spec.id)
        return self.get_asset_spec(asset_spec.id)

    def create_asset(
        self,
        asset_id: str,
        asset_spec_id: str,
        version: int,
        storage_path: str,
        media_type: str,
        source_kind: str,
        metadata: dict[str, Any] | None = None,
        content_digest: str | None = None,
    ) -> Asset:
        """Register an immutable asset version for one AssetSpec."""

        self.get_asset_spec(asset_spec_id)
        self._validate_asset_version(version)
        self._validate_content_digest(content_digest)
        with self.connection:
            self.connection.execute(
                "INSERT INTO assets (id, asset_spec_id, version, storage_path, media_type, "
                "source_kind, metadata_json, created_at, generation_execution_id, content_digest) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)",
                (
                    asset_id,
                    asset_spec_id,
                    version,
                    storage_path,
                    media_type,
                    source_kind,
                    json.dumps(metadata or {}),
                    now(),
                    content_digest,
                ),
            )
        return self.get_asset(asset_id)

    def create_failed_generation_execution(
        self,
        execution_id: str,
        asset_spec_id: str,
        asset_spec_snapshot: dict[str, Any],
        generation_input: dict[str, Any],
        generator_key: str,
        *,
        visual_style_profile_id: str | None = None,
        character_profile_id: str | None = None,
        character_reference_set_id: str | None = None,
        provider_key: str | None = None,
        model_key: str | None = None,
        provider_request_id: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        response_metadata: dict[str, Any] | None = None,
    ) -> GenerationExecution:
        """Record one immutable failed generator attempt without creating an Asset."""

        with self.connection:
            self._insert_generation_execution(
                execution_id,
                asset_spec_id,
                asset_spec_snapshot,
                generation_input,
                generator_key,
                visual_style_profile_id,
                character_profile_id,
                "failed",
                provider_key,
                model_key,
                provider_request_id,
                error_code,
                error_message,
                response_metadata or {},
                character_reference_set_id,
            )
        return self.get_generation_execution(execution_id)

    def record_successful_generation(
        self,
        execution_id: str,
        asset_id: str,
        asset_spec_id: str,
        asset_spec_snapshot: dict[str, Any],
        generation_input: dict[str, Any],
        generator_key: str,
        storage_path: str,
        media_type: str,
        *,
        visual_style_profile_id: str | None = None,
        character_profile_id: str | None = None,
        character_reference_set_id: str | None = None,
        provider_key: str | None = None,
        model_key: str | None = None,
        provider_request_id: str | None = None,
        response_metadata: dict[str, Any] | None = None,
        content_digest: str | None = None,
    ) -> tuple[GenerationExecution, Asset]:
        """Atomically record a succeeded execution and its one immutable Asset."""

        self._validate_content_digest(content_digest)
        if content_digest is None:
            raise ValueError("Successful generated Assets must include a content digest.")
        with self.connection:
            self._insert_generation_execution(
                execution_id,
                asset_spec_id,
                asset_spec_snapshot,
                generation_input,
                generator_key,
                visual_style_profile_id,
                character_profile_id,
                "succeeded",
                provider_key,
                model_key,
                provider_request_id,
                None,
                None,
                response_metadata or {},
                character_reference_set_id,
            )
            version = self.connection.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM assets WHERE asset_spec_id = ?",
                (asset_spec_id,),
            ).fetchone()[0]
            self.connection.execute(
                "INSERT INTO assets (id, asset_spec_id, version, storage_path, media_type, "
                "source_kind, metadata_json, created_at, generation_execution_id, content_digest) "
                "VALUES (?, ?, ?, ?, ?, 'generated', '{}', ?, ?, ?)",
                (
                    asset_id,
                    asset_spec_id,
                    version,
                    storage_path,
                    media_type,
                    now(),
                    execution_id,
                    content_digest,
                ),
            )
        return self.get_generation_execution(execution_id), self.get_asset(asset_id)

    def get_generation_execution(self, execution_id: str) -> GenerationExecution:
        row = self.connection.execute(
            "SELECT * FROM generation_executions WHERE id = ?", (execution_id,)
        ).fetchone()
        if row is None:
            raise KeyError(execution_id)
        return self._generation_execution(row)

    def list_generation_executions_for_asset_spec(
        self, asset_spec_id: str
    ) -> list[GenerationExecution]:
        """Return immutable execution history in stable creation order."""

        rows = self.connection.execute(
            "SELECT * FROM generation_executions WHERE asset_spec_id = ? "
            "ORDER BY created_at, id",
            (asset_spec_id,),
        )
        return [self._generation_execution(row) for row in rows]

    def get_asset_for_generation_execution(self, execution_id: str) -> Asset | None:
        """Return the one Asset registered from an execution, if it succeeded."""

        row = self.connection.execute(
            "SELECT * FROM assets WHERE generation_execution_id = ?", (execution_id,)
        ).fetchone()
        return self._asset(row) if row else None

    def get_asset(self, asset_id: str) -> Asset:
        row = self.connection.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if row is None:
            raise KeyError(asset_id)
        return self._asset(row)

    def list_assets_for_asset_spec(self, asset_spec_id: str) -> list[Asset]:
        """Return immutable asset versions in ascending version order."""

        rows = self.connection.execute(
            "SELECT * FROM assets WHERE asset_spec_id = ? ORDER BY version", (asset_spec_id,)
        )
        return [self._asset(row) for row in rows]

    def managed_asset_path(self, asset_id: str) -> Path:
        """Resolve one generated Asset only when its stored file is safely managed by Atlas."""

        asset = self.get_asset(asset_id)
        if asset.source_kind != "generated":
            raise ValueError("Only Atlas-generated Assets have managed file content.")
        if asset.media_type not in {"image/png", "image/jpeg", "image/webp"}:
            raise ValueError("Asset media type is not safe for managed image serving.")
        if not isinstance(asset.storage_path, str) or not asset.storage_path:
            raise ValueError("Asset storage path is not a managed relative path.")
        candidate = (self.asset_storage_root / asset.storage_path).resolve()
        if self.asset_storage_root not in candidate.parents:
            raise ValueError("Asset storage path escaped the managed storage root.")
        if not candidate.is_file():
            raise ValueError("Managed Asset file does not exist.")
        return candidate

    def create_character_reference_set(
        self,
        reference_set_id: str,
        character_profile_id: str,
        asset_ids: list[str],
    ) -> CharacterReferenceSet:
        """Atomically record one immutable, ordered visual basis for a CharacterProfile."""

        if not isinstance(reference_set_id, str) or not reference_set_id.strip():
            raise ValueError("CharacterReferenceSet ID must be non-empty text.")
        if not isinstance(asset_ids, list) or not asset_ids:
            raise ValueError("A CharacterReferenceSet must include one or more Asset IDs.")
        if not all(isinstance(asset_id, str) and asset_id.strip() for asset_id in asset_ids):
            raise ValueError("CharacterReferenceSet Asset IDs must be non-empty text.")
        if len(set(asset_ids)) != len(asset_ids):
            raise ValueError("An Asset cannot appear more than once in one CharacterReferenceSet.")
        self.get_character_profile(character_profile_id)
        for asset_id in asset_ids:
            self._validate_character_reference_asset(asset_id, character_profile_id)
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            version = self.connection.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM character_reference_sets "
                "WHERE character_profile_id = ?",
                (character_profile_id,),
            ).fetchone()[0]
            self.connection.execute(
                "INSERT INTO character_reference_sets VALUES (?, ?, ?, ?)",
                (reference_set_id.strip(), character_profile_id, version, now()),
            )
            for position, asset_id in enumerate(asset_ids, start=1):
                self.connection.execute(
                    "INSERT INTO character_reference_set_members VALUES (?, ?, ?, ?)",
                    (reference_set_id.strip(), asset_id, position, now()),
                )
        return self.get_character_reference_set(reference_set_id)

    def get_character_reference_set(self, reference_set_id: str) -> CharacterReferenceSet:
        row = self.connection.execute(
            "SELECT * FROM character_reference_sets WHERE id = ?", (reference_set_id,)
        ).fetchone()
        if row is None:
            raise KeyError(reference_set_id)
        return self._character_reference_set(row)

    def list_character_reference_sets(
        self, character_profile_id: str
    ) -> list[CharacterReferenceSet]:
        """Return immutable visual-reference selections in version order."""

        self.get_character_profile(character_profile_id)
        rows = self.connection.execute(
            "SELECT * FROM character_reference_sets WHERE character_profile_id = ? "
            "ORDER BY version",
            (character_profile_id,),
        )
        return [self._character_reference_set(row) for row in rows]

    def get_latest_character_reference_set(
        self, character_profile_id: str
    ) -> CharacterReferenceSet | None:
        """Return the highest immutable reference-set version for one exact profile."""

        self.get_character_profile(character_profile_id)
        row = self.connection.execute(
            "SELECT * FROM character_reference_sets WHERE character_profile_id = ? "
            "ORDER BY version DESC LIMIT 1",
            (character_profile_id,),
        ).fetchone()
        return self._character_reference_set(row) if row else None

    def list_character_reference_set_members(
        self, reference_set_id: str
    ) -> list[CharacterReferenceSetMember]:
        """Return one immutable reference set's members in explicit position order."""

        self.get_character_reference_set(reference_set_id)
        rows = self.connection.execute(
            "SELECT * FROM character_reference_set_members WHERE character_reference_set_id = ? "
            "ORDER BY position",
            (reference_set_id,),
        )
        return [self._character_reference_set_member(row) for row in rows]

    def list_eligible_character_reference_assets(self, character_profile_id: str) -> list[Asset]:
        """Return existing generated character Assets that are eligible for visual selection."""

        self.get_character_profile(character_profile_id)
        rows = self.connection.execute(
            "SELECT assets.id FROM assets "
            "JOIN generation_executions "
            "ON generation_executions.id = assets.generation_execution_id "
            "WHERE assets.source_kind = 'generated' "
            "AND generation_executions.outcome = 'succeeded' "
            "AND generation_executions.character_profile_id = ? "
            "ORDER BY assets.created_at, assets.id",
            (character_profile_id,),
        )
        eligible = []
        for row in rows:
            try:
                eligible.append(
                    self._validate_character_reference_asset(row["id"], character_profile_id)
                )
            except ValueError:
                continue
        return eligible

    def character_reference_set_payload(self, reference_set_id: str) -> dict[str, Any]:
        """Load one immutable reference selection with concise Asset provenance."""

        reference_set = self.get_character_reference_set(reference_set_id)
        return {
            "id": reference_set.id,
            "version": reference_set.version,
            "created_at": reference_set.created_at,
            "character_profile": self.character_profile_summary(reference_set.character_profile_id),
            "members": [
                self._character_reference_member_payload(member)
                for member in self.list_character_reference_set_members(reference_set.id)
            ],
        }

    def character_reference_review_payload(self, character_profile_id: str) -> dict[str, Any]:
        """Load the narrow candidate and immutable-reference history required by the local UI."""

        return {
            "character_profile": self.character_profile_summary(character_profile_id),
            "eligible_assets": [
                self._character_reference_asset_payload(asset)
                for asset in self.list_eligible_character_reference_assets(character_profile_id)
            ],
            "reference_sets": [
                self.character_reference_set_payload(reference_set.id)
                for reference_set in self.list_character_reference_sets(character_profile_id)
            ],
        }

    def asset_spec_payload(self, asset_spec_id: str) -> dict[str, Any]:
        """Load one Scene asset requirement and its registered immutable outputs."""

        asset_spec = self.get_asset_spec(asset_spec_id)
        payload = {
            "id": asset_spec.id,
            "scene_id": asset_spec.scene_id,
            "asset_type": asset_spec.asset_type,
            "purpose": asset_spec.purpose,
            "description": asset_spec.description,
            "generation_prompt": asset_spec.generation_prompt,
            "continuity_key": asset_spec.continuity_key,
            "character_profile": self.character_profile_summary(asset_spec.character_profile_id),
            "assets": [],
            "generation_executions": [
                self.generation_execution_payload(execution.id)
                for execution in self.list_generation_executions_for_asset_spec(asset_spec.id)
            ],
        }
        for asset in self.list_assets_for_asset_spec(asset_spec.id):
            item = {
                "id": asset.id,
                "version": asset.version,
                "storage_path": asset.storage_path,
                "media_type": asset.media_type,
                "source_kind": asset.source_kind,
            }
            if asset.generation_execution_id is not None:
                item["generation_execution_id"] = asset.generation_execution_id
            payload["assets"].append(item)
        return payload

    def generation_execution_payload(self, execution_id: str) -> dict[str, Any]:
        """Load read-only execution provenance for the Content Workspace."""

        execution = self.get_generation_execution(execution_id)
        asset = self.get_asset_for_generation_execution(execution.id)
        return {
            "id": execution.id,
            "asset_spec_id": execution.asset_spec_id,
            "visual_style_profile_id": execution.visual_style_profile_id,
            "character_profile": self.character_profile_summary(execution.character_profile_id),
            "character_reference_set_id": execution.character_reference_set_id,
            "generator_key": execution.generator_key,
            "provider_key": execution.provider_key,
            "model_key": execution.model_key,
            "provider_request_id": execution.provider_request_id,
            "outcome": execution.outcome,
            "error_code": execution.error_code,
            "error_message": execution.error_message,
            "created_at": execution.created_at,
            "asset": (
                {"id": asset.id, "version": asset.version, "media_type": asset.media_type}
                if asset
                else None
            ),
        }

    def character_profile_summary(self, profile_id: str | None) -> dict[str, Any] | None:
        """Return concise immutable character identity detail for read-only display."""

        if profile_id is None:
            return None
        profile = self.get_character_profile(profile_id)
        return {
            "id": profile.id,
            "name": profile.name,
            "version": profile.version,
            "identity_description": profile.identity_description,
        }

    def _character_reference_asset_payload(self, asset: Asset) -> dict[str, Any]:
        execution = self.get_generation_execution(asset.generation_execution_id or "")
        return {
            "id": asset.id,
            "version": asset.version,
            "media_type": asset.media_type,
            "content_digest": asset.content_digest,
            "asset_spec_id": asset.asset_spec_id,
            "generation_execution": {
                "id": execution.id,
                "provider_key": execution.provider_key,
                "model_key": execution.model_key,
                "character_profile": self.character_profile_summary(execution.character_profile_id),
            },
        }

    def _character_reference_member_payload(
        self, member: CharacterReferenceSetMember
    ) -> dict[str, Any]:
        return {
            "position": member.position,
            "asset": self._character_reference_asset_payload(self.get_asset(member.asset_id)),
        }

    def _validate_character_reference_asset(
        self, asset_id: str, character_profile_id: str
    ) -> Asset:
        asset = self.get_asset(asset_id)
        if asset.source_kind != "generated" or asset.generation_execution_id is None:
            raise ValueError(
                "Character references must be generated Assets with execution provenance."
            )
        execution = self.get_generation_execution(asset.generation_execution_id)
        if execution.outcome != "succeeded":
            raise ValueError("Character references must originate from succeeded executions.")
        if execution.asset_spec_snapshot.get("asset_type") != "character":
            raise ValueError("Character references must originate from character AssetSpecs.")
        if execution.character_profile_id != character_profile_id:
            raise ValueError(
                "Character reference identity lineage must match its CharacterProfile."
            )
        self._validate_content_digest(asset.content_digest)
        if asset.content_digest is None:
            raise ValueError("Character references require an immutable content digest.")
        managed_path = self.managed_asset_path(asset.id)
        if sha256(managed_path.read_bytes()).hexdigest() != asset.content_digest:
            raise ValueError("Managed Asset bytes do not match the stored content digest.")
        return asset

    def load_verified_character_reference_asset(
        self, asset_id: str, character_profile_id: str
    ) -> tuple[Asset, bytes]:
        """Safely load exact verified managed bytes for provider-time reference use."""

        asset = self._validate_character_reference_asset(asset_id, character_profile_id)
        content = self.managed_asset_path(asset.id).read_bytes()
        if asset.content_digest is None or sha256(content).hexdigest() != asset.content_digest:
            raise ValueError("Managed Asset bytes do not match the stored content digest.")
        return asset, content

    def _validate_angle_research_pack(self, opportunity_id: str, research_pack_id: str) -> None:
        research_pack = self.get_research_pack(research_pack_id)
        if research_pack.opportunity_id != opportunity_id:
            raise ValueError("An EditorialAngle must use a ResearchPack from the same Opportunity.")

    def _validate_angle_claim_research_pack(self, editorial_angle_id: str, claim_id: str) -> None:
        editorial_angle = self.get_editorial_angle(editorial_angle_id)
        claim = self.get_claim(claim_id)
        if claim.research_pack_id != editorial_angle.research_pack_id:
            raise ValueError("An EditorialAngle Claim must belong to the Angle's ResearchPack.")

    def _validate_content_piece_editorial_angle(
        self, opportunity_id: str, editorial_angle_id: str
    ) -> None:
        editorial_angle = self.get_editorial_angle(editorial_angle_id)
        if editorial_angle.opportunity_id != opportunity_id:
            raise ValueError("A ContentPiece must use an EditorialAngle from the same Opportunity.")

    def _validate_content_piece_readiness_lineage(self, content_piece_id: str) -> ContentPiece:
        """Return a ContentPiece only when its stored initiation lineage remains exactly Ready."""

        content_piece = self.get_content_piece(content_piece_id)
        try:
            editorial_angle = self.get_editorial_angle(content_piece.editorial_angle_id)
        except KeyError as error:
            raise ValueError(
                "The ContentPiece provenance must reference an existing EditorialAngle."
            ) from error
        if editorial_angle.opportunity_id != content_piece.opportunity_id:
            raise ValueError(
                "The ContentPiece and EditorialAngle must belong to the same Opportunity."
            )
        assessment_id = editorial_angle.research_readiness_assessment_id
        if assessment_id is None:
            raise ValueError(
                "A readiness-authorized editorial record requires EditorialAngle "
                "readiness provenance."
            )
        try:
            assessment = self.get_research_readiness_assessment(assessment_id)
        except KeyError as error:
            raise ValueError(
                "The EditorialAngle readiness provenance must reference an existing "
                "ResearchReadinessAssessment."
            ) from error
        if assessment.outcome != "Ready":
            raise ValueError(
                "Only a Ready ResearchReadinessAssessment may authorize editorial record creation."
            )
        if assessment.research_pack_id != editorial_angle.research_pack_id:
            raise ValueError(
                "The ResearchReadinessAssessment must belong to the EditorialAngle ResearchPack."
            )
        try:
            research_pack = self.get_research_pack(editorial_angle.research_pack_id)
        except KeyError as error:
            raise ValueError(
                "The EditorialAngle must reference an existing ResearchPack."
            ) from error
        if research_pack.opportunity_id != content_piece.opportunity_id:
            raise ValueError(
                "The EditorialAngle ResearchPack must belong to the ContentPiece Opportunity."
            )
        return content_piece

    def _script_claim_set_readiness_assessment(
        self, script_claim_set: ScriptClaimSet
    ) -> ResearchReadinessAssessment:
        """Derive the exact historical readiness assessment for a closed Script claim set."""

        script = self.get_script(script_claim_set.script_id)
        content_piece = self._validate_content_piece_readiness_lineage(script.content_piece_id)
        editorial_angle = self.get_editorial_angle(content_piece.editorial_angle_id)
        assessment_id = editorial_angle.research_readiness_assessment_id
        if assessment_id is None:
            raise ValueError("A ScriptClaimSet requires EditorialAngle readiness provenance.")
        return self.get_research_readiness_assessment(assessment_id)

    def _evaluate_editorial_package_readiness(
        self, snapshot: EditorialPackageSnapshot
    ) -> list[dict[str, Any]]:
        """Evaluate only the approved deterministic package/provenance conditions."""

        self._validate_editorial_package_snapshot_integrity(snapshot)
        claim_set = self.get_script_claim_set_for_script(snapshot.script_id)
        if claim_set is None:
            return [
                {
                    "code": "SCRIPT_CLAIM_SET_MISSING",
                    "severity": "error",
                    "blocking": True,
                    "message": "The package Script does not have a closed claim provenance set.",
                }
            ]
        self._validate_script_claim_set_frozen_provenance(claim_set)
        return []

    def _validate_editorial_package_snapshot_integrity(
        self, snapshot: EditorialPackageSnapshot
    ) -> None:
        """Validate the exact immutable package components before assessment."""

        try:
            self._validate_content_piece_readiness_lineage(snapshot.content_piece_id)
            title_option = self.get_title_option(snapshot.title_option_id)
            hook_option = self.get_hook_option(snapshot.hook_option_id)
            script = self.get_script(snapshot.script_id)
        except KeyError as error:
            raise ValueError(
                "An EditorialPackageSnapshot must reference existing ContentPiece components."
            ) from error
        if title_option.content_piece_id != snapshot.content_piece_id:
            raise ValueError("A package TitleOption must belong to the same ContentPiece.")
        if hook_option.content_piece_id != snapshot.content_piece_id:
            raise ValueError("A package HookOption must belong to the same ContentPiece.")
        if script.content_piece_id != snapshot.content_piece_id:
            raise ValueError("A package Script must belong to the same ContentPiece.")

    @staticmethod
    def _validate_editorial_gate_decision_input(
        snapshot: EditorialPackageSnapshot,
        assessment: EditorialReadinessAssessment,
        outcome: str,
        actor: str,
        comment: str | None,
    ) -> None:
        if assessment.editorial_package_snapshot_id != snapshot.id:
            raise ValueError(
                "An EditorialGateDecision assessment must belong to the exact "
                "EditorialPackageSnapshot."
            )
        if assessment.outcome != "Ready":
            raise ValueError("Only a Ready EditorialReadinessAssessment may enter Editorial Gate.")
        if outcome not in EDITORIAL_GATE_DECISION_OUTCOMES:
            raise ValueError("EditorialGateDecision outcome must be Approve, Revise, or Reject.")
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError("EditorialGateDecision actor must be non-empty text.")
        if comment is not None and not isinstance(comment, str):
            raise ValueError("EditorialGateDecision comment must be text or null.")

    def _validate_editorial_gate_decision_lineage(
        self, decision: EditorialGateDecision
    ) -> tuple[EditorialPackageSnapshot, EditorialReadinessAssessment]:
        """Resolve an immutable decision only when its exact Ready input chain remains coherent."""

        try:
            snapshot = self.get_editorial_package_snapshot(decision.editorial_package_snapshot_id)
            assessment = self.get_editorial_readiness_assessment(
                decision.editorial_readiness_assessment_id
            )
        except KeyError as error:
            raise ValueError(
                "The EditorialGateDecision provenance must reference existing package and "
                "assessment records."
            ) from error
        self._validate_editorial_gate_decision_input(
            snapshot, assessment, decision.outcome, decision.actor, decision.comment
        )
        return snapshot, assessment

    def _validate_script_claim_set_frozen_provenance(self, claim_set: ScriptClaimSet) -> None:
        """Require a closed set's memberships to resolve only against frozen Ready evidence."""

        try:
            assessment = self._script_claim_set_readiness_assessment(claim_set)
        except KeyError as error:
            raise ValueError(
                "A ScriptClaimSet must resolve exact Ready assessment provenance."
            ) from error
        frozen_claims = self._frozen_claims_by_id(assessment)
        claim_ids = [link.claim_id for link in self.list_script_claim_links(claim_set.id)]
        missing_claim_ids = [claim_id for claim_id in claim_ids if claim_id not in frozen_claims]
        if missing_claim_ids:
            raise ValueError(
                "A ScriptClaimSet Claim must resolve in the exact Ready assessment frozen evidence."
            )

        frozen_evidence = assessment.frozen_evidence_state
        sources = frozen_evidence.get("sources")
        claim_evidence = frozen_evidence.get("claim_evidence")
        if not isinstance(sources, list) or not isinstance(claim_evidence, list):
            raise ValueError(
                "Research readiness frozen evidence must resolve Sources and ClaimEvidence."
            )
        source_ids = {
            source.get("id")
            for source in sources
            if isinstance(source, dict) and isinstance(source.get("id"), str)
        }
        linked_claim_ids = set(claim_ids)
        for evidence in claim_evidence:
            if not isinstance(evidence, dict):
                raise ValueError(
                    "Research readiness frozen ClaimEvidence must be structured records."
                )
            if evidence.get("claim_id") in linked_claim_ids:
                source_id = evidence.get("source_id")
                if not isinstance(source_id, str) or source_id not in source_ids:
                    raise ValueError(
                        "A ScriptClaimSet ClaimEvidence record must resolve its frozen Source."
                    )

    @staticmethod
    def _frozen_claims_by_id(
        assessment: ResearchReadinessAssessment,
    ) -> dict[str, dict[str, Any]]:
        """Return exact frozen Claim representations keyed by immutable Claim identity."""

        claims = assessment.frozen_evidence_state.get("claims")
        if not isinstance(claims, list):
            raise ValueError("Research readiness frozen evidence must contain Claims.")
        return {
            claim["id"]: claim
            for claim in claims
            if isinstance(claim, dict) and isinstance(claim.get("id"), str)
        }

    @staticmethod
    def _validate_editorial_option_text(text: str, record_name: str) -> None:
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{record_name} text must be non-empty text.")

    def _insert_script(
        self,
        script_id: str,
        content_piece_id: str,
        narration_text: str,
        metadata: dict[str, Any] | None,
        *,
        version: int | None = None,
    ) -> None:
        """Insert one Script, deriving a version from immutable history when requested."""

        stamp = now()
        if version is None:
            self.connection.execute(
                "INSERT INTO scripts (id, content_piece_id, version, narration_text, "
                "metadata_json, created_at, updated_at) "
                "SELECT ?, ?, COALESCE(MAX(version), 0) + 1, ?, ?, ?, ? "
                "FROM scripts WHERE content_piece_id = ?",
                (
                    script_id,
                    content_piece_id,
                    narration_text,
                    json.dumps(metadata or {}),
                    stamp,
                    stamp,
                    content_piece_id,
                ),
            )
            return
        self.connection.execute(
            "INSERT INTO scripts VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                script_id,
                content_piece_id,
                version,
                narration_text,
                json.dumps(metadata or {}),
                stamp,
                stamp,
            ),
        )

    def _validate_visual_plan_script(self, content_piece_id: str, script_id: str) -> None:
        script = self.get_script(script_id)
        if script.content_piece_id != content_piece_id:
            raise ValueError("A VisualPlan must use a Script from the same ContentPiece.")

    def _insert_visual_plan(
        self,
        visual_plan_id: str,
        content_piece_id: str,
        script_id: str,
        visual_direction: str,
        metadata: dict[str, Any] | None,
        stamp: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO visual_plans VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                visual_plan_id,
                content_piece_id,
                script_id,
                visual_direction,
                json.dumps(metadata or {}),
                stamp,
                stamp,
            ),
        )

    def _insert_generation_execution(
        self,
        execution_id: str,
        asset_spec_id: str,
        asset_spec_snapshot: dict[str, Any],
        generation_input: dict[str, Any],
        generator_key: str,
        visual_style_profile_id: str | None,
        character_profile_id: str | None,
        outcome: str,
        provider_key: str | None,
        model_key: str | None,
        provider_request_id: str | None,
        error_code: str | None,
        error_message: str | None,
        response_metadata: dict[str, Any],
        character_reference_set_id: str | None = None,
    ) -> None:
        self.get_asset_spec(asset_spec_id)
        self._validate_generation_execution(
            asset_spec_snapshot,
            generation_input,
            generator_key,
            outcome,
            provider_key,
            model_key,
            provider_request_id,
            error_code,
            error_message,
            response_metadata,
        )
        if asset_spec_snapshot.get("asset_spec_id") != asset_spec_id:
            raise ValueError("GenerationExecution snapshot must identify its persisted AssetSpec.")
        self._validate_generation_execution_provenance(
            generation_input,
            visual_style_profile_id,
            character_profile_id,
            character_reference_set_id,
        )
        self.connection.execute(
            "INSERT INTO generation_executions "
            "(id, asset_spec_id, asset_spec_snapshot_json, generation_input_json, generator_key, "
            "provider_key, model_key, provider_request_id, outcome, error_code, error_message, "
            "response_metadata_json, created_at, visual_style_profile_id, character_profile_id, "
            "character_reference_set_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                execution_id,
                asset_spec_id,
                json.dumps(asset_spec_snapshot, sort_keys=True),
                json.dumps(generation_input, sort_keys=True),
                generator_key.strip(),
                self._normalized_optional_identifier(provider_key),
                self._normalized_optional_identifier(model_key),
                self._normalized_optional_identifier(provider_request_id),
                outcome,
                self._normalized_optional_identifier(error_code),
                self._normalized_optional_identifier(error_message),
                json.dumps(response_metadata, sort_keys=True),
                now(),
                visual_style_profile_id,
                character_profile_id,
                character_reference_set_id,
            ),
        )

    @staticmethod
    def _validate_asset_version(version: int) -> None:
        if type(version) is not int or version < 1:
            raise ValueError("Asset version must be a positive integer.")

    @staticmethod
    def _validate_content_digest(content_digest: str | None) -> None:
        if content_digest is None:
            return
        if (
            not isinstance(content_digest, str)
            or len(content_digest) != 64
            or any(character not in "0123456789abcdef" for character in content_digest)
        ):
            raise ValueError("Asset content digest must be lowercase SHA-256 hexadecimal text.")

    @staticmethod
    def _normalized_optional_identifier(value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Optional generation identifiers must be null or non-empty text.")
        return value.strip()

    @staticmethod
    def _validate_generation_execution(
        asset_spec_snapshot: dict[str, Any],
        generation_input: dict[str, Any],
        generator_key: str,
        outcome: str,
        provider_key: str | None,
        model_key: str | None,
        provider_request_id: str | None,
        error_code: str | None,
        error_message: str | None,
        response_metadata: dict[str, Any],
    ) -> None:
        if not isinstance(generator_key, str) or not generator_key.strip():
            raise ValueError("GenerationExecution generator key must be non-empty text.")
        if outcome not in GENERATION_EXECUTION_OUTCOMES:
            raise ValueError("GenerationExecution outcome must be succeeded or failed.")
        if not isinstance(asset_spec_snapshot, dict):
            raise ValueError("GenerationExecution AssetSpec snapshot must be an object.")
        if not isinstance(generation_input, dict):
            raise ValueError("GenerationExecution generation input must be an object.")
        if not isinstance(response_metadata, dict):
            raise ValueError("GenerationExecution response metadata must be an object.")
        for value in (provider_key, model_key, provider_request_id, error_code, error_message):
            AtlasRepository._normalized_optional_identifier(value)

    def _validate_generation_execution_provenance(
        self,
        generation_input: dict[str, Any],
        visual_style_profile_id: str | None,
        character_profile_id: str | None,
        character_reference_set_id: str | None = None,
    ) -> None:
        schema_version = generation_input.get("schema_version")
        if schema_version not in {2, 3, 4}:
            if visual_style_profile_id is not None:
                raise ValueError("GenerationInput v1 cannot identify a VisualStyleProfile.")
            if character_profile_id is not None:
                raise ValueError("GenerationInput v1 cannot identify a CharacterProfile.")
            if character_reference_set_id is not None:
                raise ValueError("GenerationInput v1 cannot identify a CharacterReferenceSet.")
            return
        if visual_style_profile_id is None:
            raise ValueError("Styled GenerationInput must identify a VisualStyleProfile.")
        style = generation_input.get("style")
        if not isinstance(style, dict):
            raise ValueError("Styled GenerationInput style must be an object.")
        profile = self.get_visual_style_profile(visual_style_profile_id)
        if (
            style.get("profile_id") != profile.id
            or style.get("style_key") != profile.style_key
            or style.get("version") != profile.version
        ):
            raise ValueError("Styled GenerationInput style must match its VisualStyleProfile.")
        if schema_version == 2:
            if character_profile_id is not None:
                raise ValueError("GenerationInput v2 cannot identify a CharacterProfile.")
            if character_reference_set_id is not None:
                raise ValueError("GenerationInput v2 cannot identify a CharacterReferenceSet.")
            return
        character = generation_input.get("character")
        if character_profile_id is None:
            if character is not None:
                raise ValueError("GenerationInput v3 character must have CharacterProfile lineage.")
            if schema_version == 4:
                raise ValueError("GenerationInput v4 requires CharacterProfile lineage.")
            if character_reference_set_id is not None:
                raise ValueError("GenerationInput v3 cannot identify a CharacterReferenceSet.")
            return
        if not isinstance(character, dict):
            raise ValueError("GenerationInput v3 character must be an object.")
        character_profile = self.get_character_profile(character_profile_id)
        if (
            character.get("profile_id") != character_profile.id
            or character.get("character_key") != character_profile.character_key
            or character.get("version") != character_profile.version
            or character.get("name") != character_profile.name
            or character.get("identity_description") != character_profile.identity_description
            or character.get("generation_guidance") != character_profile.generation_guidance
        ):
            raise ValueError("GenerationInput v3 character must match its CharacterProfile.")
        if schema_version == 3:
            if character_reference_set_id is not None:
                raise ValueError("GenerationInput v3 cannot identify a CharacterReferenceSet.")
            return
        if character_reference_set_id is None:
            raise ValueError("GenerationInput v4 requires CharacterReferenceSet lineage.")
        references = generation_input.get("character_references")
        if not isinstance(references, dict):
            raise ValueError("GenerationInput v4 character references must be an object.")
        if references.get("intent") != "character_identity_grounding":
            raise ValueError("GenerationInput v4 character references require identity grounding.")
        reference_set = self.get_character_reference_set(character_reference_set_id)
        if (
            references.get("reference_set_id") != reference_set.id
            or references.get("reference_set_version") != reference_set.version
            or reference_set.character_profile_id != character_profile_id
        ):
            raise ValueError(
                "GenerationInput v4 references must match CharacterReferenceSet lineage."
            )
        reference_profile = references.get("character_profile")
        if not isinstance(reference_profile, dict) or (
            reference_profile.get("profile_id") != character_profile.id
            or reference_profile.get("character_key") != character_profile.character_key
            or reference_profile.get("version") != character_profile.version
        ):
            raise ValueError("GenerationInput v4 references must match its CharacterProfile.")
        members = references.get("members")
        set_members = self.list_character_reference_set_members(reference_set.id)
        if not isinstance(members, list) or len(members) != len(set_members):
            raise ValueError("GenerationInput v4 references must freeze every ordered member.")
        for frozen, member in zip(members, set_members, strict=True):
            if not isinstance(frozen, dict):
                raise ValueError("GenerationInput v4 reference members must be objects.")
            asset = self.get_asset(member.asset_id)
            if (
                frozen.get("asset_id") != asset.id
                or frozen.get("content_digest") != asset.content_digest
                or frozen.get("media_type") != asset.media_type
                or frozen.get("position") != member.position
            ):
                raise ValueError(
                    "GenerationInput v4 reference members must match frozen set Assets."
                )

    def _validate_asset_spec_character_profile(
        self, asset_type: str, character_profile_id: str | None
    ) -> None:
        if character_profile_id is None:
            return
        if asset_type != "character":
            raise ValueError("Only character AssetSpecs can identify a CharacterProfile.")
        self.get_character_profile(character_profile_id)

    @staticmethod
    def _validate_asset_spec_text(*values: str) -> None:
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError("AssetSpec required text fields must not be empty or whitespace-only.")

    @staticmethod
    def _validate_visual_style_profile(
        version: int,
        style_key: str,
        name: str,
        description: str,
        generation_guidance: str,
        rules: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        if type(version) is not int or version < 1:
            raise ValueError("VisualStyleProfile version must be a positive integer.")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (style_key, name, description, generation_guidance)
        ):
            raise ValueError(
                "VisualStyleProfile required text fields must not be empty or whitespace-only."
            )
        if not isinstance(rules, dict):
            raise ValueError("VisualStyleProfile rules must be an object.")
        if not isinstance(metadata, dict):
            raise ValueError("VisualStyleProfile metadata must be an object.")

    @staticmethod
    def _validate_character_profile(
        version: int,
        character_key: str,
        name: str,
        identity_description: str,
        generation_guidance: str,
        metadata: dict[str, Any],
    ) -> None:
        if type(version) is not int or version < 1:
            raise ValueError("CharacterProfile version must be a positive integer.")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (character_key, name, identity_description, generation_guidance)
        ):
            raise ValueError(
                "CharacterProfile required text fields must not be empty or whitespace-only."
            )
        if not isinstance(metadata, dict):
            raise ValueError("CharacterProfile metadata must be an object.")

    @staticmethod
    def _validate_editorial_angle_takeaways(key_takeaways: list[str]) -> None:
        if not key_takeaways or not all(isinstance(takeaway, str) for takeaway in key_takeaways):
            raise ValueError(
                "EditorialAngle key takeaways must be a non-empty ordered list of strings."
            )

    @staticmethod
    def _validate_editorial_angle_claim_role(role: str) -> None:
        if role not in EDITORIAL_ANGLE_CLAIM_ROLES:
            raise ValueError("EditorialAngle Claim role must be core or supporting.")

    def create_claim(
        self,
        claim_id: str,
        research_pack_id: str,
        text: str,
        claim_type: str,
        risk_level: str,
        freshness_type: str,
        verification_status: str,
        verification_notes: str,
        reviewed_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Claim:
        """Create a Claim that remains owned by its ResearchPack version."""

        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    claim_id,
                    research_pack_id,
                    text,
                    claim_type,
                    risk_level,
                    freshness_type,
                    verification_status,
                    verification_notes,
                    reviewed_at,
                    json.dumps(metadata or {}),
                    stamp,
                    stamp,
                ),
            )
        return self.get_claim(claim_id)

    def get_claim(self, claim_id: str) -> Claim:
        row = self.connection.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
        if row is None:
            raise KeyError(claim_id)
        return self._claim(row)

    def list_claims(self, research_pack_id: str) -> list[Claim]:
        rows = self.connection.execute(
            "SELECT * FROM claims WHERE research_pack_id = ? ORDER BY created_at, id",
            (research_pack_id,),
        )
        return [self._claim(row) for row in rows]

    def update_claim(self, claim: Claim) -> Claim:
        """Update Claim detail without moving it to a different ResearchPack."""

        with self.connection:
            result = self.connection.execute(
                "UPDATE claims SET text=?, claim_type=?, risk_level=?, freshness_type=?, "
                "verification_status=?, verification_notes=?, reviewed_at=?, metadata_json=?, "
                "updated_at=? WHERE id=?",
                (
                    claim.text,
                    claim.claim_type,
                    claim.risk_level,
                    claim.freshness_type,
                    claim.verification_status,
                    claim.verification_notes,
                    claim.reviewed_at,
                    json.dumps(claim.metadata),
                    now(),
                    claim.id,
                ),
            )
        if result.rowcount != 1:
            raise KeyError(claim.id)
        return self.get_claim(claim.id)

    def create_source(
        self,
        source_id: str,
        source_type: str,
        title: str,
        publisher: str,
        url: str,
        accessed_at: str,
        author: str | None = None,
        publication_date: str | None = None,
        jurisdiction: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Source:
        """Create a global Source or return the existing Source for an exact URL."""

        existing = self.get_source_by_url(url)
        if existing is not None:
            return existing
        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    source_id,
                    source_type,
                    title,
                    publisher,
                    author,
                    url,
                    publication_date,
                    accessed_at,
                    jurisdiction,
                    json.dumps(metadata or {}),
                    stamp,
                    stamp,
                ),
            )
        return self.get_source(source_id)

    def get_source(self, source_id: str) -> Source:
        row = self.connection.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
        if row is None:
            raise KeyError(source_id)
        return self._source(row)

    def get_source_by_url(self, url: str) -> Source | None:
        row = self.connection.execute("SELECT * FROM sources WHERE url = ?", (url,)).fetchone()
        return self._source(row) if row else None

    def link_claim_evidence(
        self,
        claim_id: str,
        source_id: str,
        stance: str,
        reference: str | None = None,
        notes: str = "",
    ) -> ClaimEvidence:
        """Link a Source to a Claim, updating only that explicit relationship if it exists."""

        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO claim_evidence VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(claim_id, source_id) DO UPDATE SET stance=excluded.stance, "
                "reference=excluded.reference, notes=excluded.notes, "
                "updated_at=excluded.updated_at",
                (claim_id, source_id, stance, reference, notes, stamp, stamp),
            )
        return self.get_claim_evidence(claim_id, source_id)

    def get_claim_evidence(self, claim_id: str, source_id: str) -> ClaimEvidence:
        row = self.connection.execute(
            "SELECT * FROM claim_evidence WHERE claim_id = ? AND source_id = ?",
            (claim_id, source_id),
        ).fetchone()
        if row is None:
            raise KeyError((claim_id, source_id))
        return self._claim_evidence(row)

    def evidence_for_claim(self, claim_id: str) -> list[tuple[ClaimEvidence, Source]]:
        rows = self.connection.execute(
            "SELECT claim_evidence.*, sources.source_type, sources.title, sources.publisher, "
            "sources.author, sources.url, sources.publication_date, sources.accessed_at, "
            "sources.jurisdiction, sources.metadata_json AS source_metadata_json, "
            "sources.created_at AS source_created_at, sources.updated_at AS source_updated_at "
            "FROM claim_evidence JOIN sources ON sources.id = claim_evidence.source_id "
            "WHERE claim_evidence.claim_id = ? ORDER BY sources.title",
            (claim_id,),
        )
        return [
            (
                self._claim_evidence(row),
                Source(
                    row["source_id"],
                    row["source_type"],
                    row["title"],
                    row["publisher"],
                    row["author"],
                    row["url"],
                    row["publication_date"],
                    row["accessed_at"],
                    row["jurisdiction"],
                    json.loads(row["source_metadata_json"]),
                    row["source_created_at"],
                    row["source_updated_at"],
                ),
            )
            for row in rows
        ]

    def claims_for_source(self, source_id: str) -> list[Claim]:
        rows = self.connection.execute(
            "SELECT claims.* FROM claims JOIN claim_evidence "
            "ON claim_evidence.claim_id = claims.id WHERE claim_evidence.source_id = ? "
            "ORDER BY claims.created_at, claims.id",
            (source_id,),
        )
        return [self._claim(row) for row in rows]

    def research_pack_payload(self, research_pack_id: str) -> dict[str, Any]:
        """Load a complete ResearchPack for the read-only Content Workspace API."""

        pack = self.get_research_pack(research_pack_id)
        provenance = None
        if pack.idea_gate_decision_id is not None:
            decision = self.get_idea_gate_decision(pack.idea_gate_decision_id)
            provenance = {
                "decision": self._idea_gate_decision_payload(decision),
                "snapshot": self.idea_gate_review_snapshot_payload(decision.review_snapshot_id),
            }
        claims = []
        for claim in self.list_claims(pack.id):
            evidence = []
            for relationship, source in self.evidence_for_claim(claim.id):
                evidence.append(
                    {
                        "stance": relationship.stance,
                        "reference": relationship.reference,
                        "notes": relationship.notes,
                        "source": {
                            "id": source.id,
                            "source_type": source.source_type,
                            "title": source.title,
                            "publisher": source.publisher,
                            "url": source.url,
                            "jurisdiction": source.jurisdiction,
                        },
                    }
                )
            claims.append(
                {
                    "id": claim.id,
                    "text": claim.text,
                    "claim_type": claim.claim_type,
                    "risk_level": claim.risk_level,
                    "freshness_type": claim.freshness_type,
                    "verification_status": claim.verification_status,
                    "verification_notes": claim.verification_notes,
                    "reviewed_at": claim.reviewed_at,
                    "evidence": evidence,
                }
            )
        return {
            "id": pack.id,
            "opportunity_id": pack.opportunity_id,
            "version": pack.version,
            "summary": pack.summary,
            "as_of_date": pack.as_of_date,
            "idea_gate_decision_id": pack.idea_gate_decision_id,
            "idea_gate_provenance": provenance,
            "claims": claims,
            "source_count": len(
                {item["source"]["id"] for claim in claims for item in claim["evidence"]}
            ),
        }

    def latest_research_pack_payload(self, opportunity_id: str) -> dict[str, Any] | None:
        """Load the current highest-version snapshot for an Opportunity."""

        pack = self.latest_research_pack(opportunity_id)
        return self.research_pack_payload(pack.id) if pack else None

    def seed_demo_data(self) -> None:
        subjects = (
            ("subject-isa", "isa", "ISA", "UK individual savings accounts."),
            (
                "subject-credit-utilisation",
                "credit-utilisation",
                "Credit utilisation",
                "Credit-card balance usage.",
            ),
            (
                "subject-salary-sacrifice",
                "salary-sacrifice",
                "Salary sacrifice",
                "Pay exchanged for benefits.",
            ),
            ("subject-income-tax", "income-tax", "Income tax", "Tax on individual earnings."),
            ("subject-ai-work", "ai-at-work", "AI at work", "Practical workplace use of AI."),
            (
                "subject-energy-infrastructure",
                "energy-infrastructure",
                "Energy infrastructure",
                "Power and grids.",
            ),
            (
                "subject-lifestyle-inflation",
                "lifestyle-inflation",
                "Lifestyle inflation",
                "Spending rising with income.",
            ),
        )
        relations = {
            "uk-isa-rules": ("subject-isa",),
            "credit-utilisation": ("subject-credit-utilisation",),
            "salary-sacrifice": ("subject-salary-sacrifice", "subject-income-tax"),
            "ai-workflow": ("subject-ai-work",),
            "energy-grid": ("subject-energy-infrastructure",),
            "lifestyle-inflation": ("subject-lifestyle-inflation",),
        }
        stamp = now()
        with self.connection:
            for subject in subjects:
                self.connection.execute(
                    "INSERT OR IGNORE INTO subjects VALUES (?, ?, ?, ?, 1, '{}', ?, ?)",
                    (*subject, stamp, stamp),
                )
            for fixture in OPPORTUNITIES:
                metadata = {
                    "suggested_angle": fixture.suggested_angle,
                    "evidence_quality": fixture.evidence_quality,
                    "risk": fixture.risk,
                    "portfolio_relevance": fixture.portfolio_relevance,
                    "visual_potential": fixture.visual_potential,
                    "legacy_display_pillar": fixture.pillar,
                }
                self.connection.execute(
                    "INSERT OR IGNORE INTO opportunities "
                    "VALUES (?, ?, ?, ?, ?, 'proposed', ?, ?, ?)",
                    (
                        fixture.id,
                        fixture.topic,
                        fixture.viewer_benefit,
                        fixture.why_now,
                        fixture.score,
                        json.dumps(metadata),
                        stamp,
                        stamp,
                    ),
                )
            for opportunity_id, subject_ids in relations.items():
                for index, subject_id in enumerate(subject_ids):
                    self.connection.execute(
                        "INSERT OR IGNORE INTO opportunity_subjects VALUES (?, ?, ?, ?)",
                        (
                            opportunity_id,
                            subject_id,
                            "primary" if index == 0 else "supporting",
                            stamp,
                        ),
                    )
        self.seed_research_data()
        self.seed_editorial_angle_data()
        self.seed_content_piece_data()
        self.seed_visual_plan_data()
        self.seed_visual_style_profile_data()
        self.seed_character_profile_data()
        self.seed_asset_spec_data()

    def seed_research_data(self) -> None:
        """Seed one read-only demonstration ResearchPack without overwriting local edits."""

        stamp = now()
        research_pack = (
            "research-pack-isa-deadline-v1",
            "uk-isa-rules",
            1,
            (
                "Research Pack v1 brings together the existing ISA allowance, transfer and "
                "tax-year timing material used by the Content Workspace demo. Its claims remain "
                "unreviewed until date-sensitive editorial wording receives human review."
            ),
            None,
            "{}",
            stamp,
            stamp,
        )
        claims = (
            (
                "claim-isa-tax-year-v1",
                "research-pack-isa-deadline-v1",
                "The ISA tax year runs from 6 April to 5 April.",
                "factual",
                "medium",
                "date_sensitive",
                "unreviewed",
                "Retain date-sensitive wording review before publication.",
                None,
                "{}",
                stamp,
                stamp,
            ),
            (
                "claim-isa-allowance-v1",
                "research-pack-isa-deadline-v1",
                "ISA subscriptions use the allowance available for the relevant tax year.",
                "factual",
                "medium",
                "current",
                "unreviewed",
                "The current allowance amount is intentionally not stated until reviewed.",
                None,
                "{}",
                stamp,
                stamp,
            ),
            (
                "claim-isa-transfer-v1",
                "research-pack-isa-deadline-v1",
                (
                    "An ISA transfer needs to follow the receiving provider's process to preserve "
                    "the tax wrapper."
                ),
                "factual",
                "medium",
                "date_sensitive",
                "in_review",
                "Transfer detail needs provider and current-rule wording review.",
                None,
                "{}",
                stamp,
                stamp,
            ),
        )
        sources = (
            (
                "source-govuk-individual-savings-accounts",
                "official_primary",
                "Individual Savings Accounts (ISAs)",
                "GOV.UK",
                None,
                "https://www.gov.uk/individual-savings-accounts",
                None,
                "2026-08-12",
                "United Kingdom",
                "{}",
                stamp,
                stamp,
            ),
            (
                "source-govuk-isa-manager-transfers",
                "official_primary",
                "Transfer an ISA if you're an ISA manager",
                "GOV.UK",
                None,
                "https://www.gov.uk/guidance/transfer-an-isa-if-youre-an-isa-manager",
                None,
                "2026-08-12",
                "United Kingdom",
                "{}",
                stamp,
                stamp,
            ),
        )
        evidence = (
            (
                "claim-isa-tax-year-v1",
                "source-govuk-individual-savings-accounts",
                "supports",
                "Overview",
                "Provides the tax-year framing used in the existing deadline-oriented demo.",
            ),
            (
                "claim-isa-allowance-v1",
                "source-govuk-individual-savings-accounts",
                "supports",
                "Overview",
                (
                    "Provides the general allowance context; the exact current figure remains "
                    "unreviewed."
                ),
            ),
            (
                "claim-isa-transfer-v1",
                "source-govuk-individual-savings-accounts",
                "contextualises",
                "Transferring an ISA",
                "Gives general transfer context for the viewer-facing explanation.",
            ),
            (
                "claim-isa-transfer-v1",
                "source-govuk-isa-manager-transfers",
                "supports",
                "Transfer process",
                "Supports the need to use a provider-led transfer process.",
            ),
        )
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO research_packs "
                "(id, opportunity_id, version, summary, as_of_date, metadata_json, created_at, "
                "updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                research_pack,
            )
            for claim in claims:
                self.connection.execute(
                    "INSERT OR IGNORE INTO claims VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    claim,
                )
            for source in sources:
                self.connection.execute(
                    "INSERT OR IGNORE INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    source,
                )
            persisted_source_ids = {
                source[0]: self.get_source_by_url(source[5]).id for source in sources
            }
            for claim_id, seed_source_id, stance, reference, notes in evidence:
                self.connection.execute(
                    "INSERT OR IGNORE INTO claim_evidence VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        claim_id,
                        persisted_source_ids[seed_source_id],
                        stance,
                        reference,
                        notes,
                        stamp,
                        stamp,
                    ),
                )

    def seed_editorial_angle_data(self) -> None:
        """Seed two distinct ISA editorial propositions without overwriting local edits."""

        stamp = now()
        angles = (
            (
                "editorial-angle-isa-decision-tree-v1",
                "uk-isa-rules",
                "research-pack-isa-deadline-v1",
                "The 15-minute ISA decision tree before the deadline.",
                (
                    "Before the ISA tax-year deadline, the useful question is whether a viewer "
                    "has unused allowance and can avoid losing a tax-efficient opportunity."
                ),
                (
                    "Understand the deadline context and the practical checks needed before "
                    "unused ISA allowance expires."
                ),
                "A time-bound decision tree for a UK professional considering an ISA contribution.",
                json.dumps(
                    [
                        "The ISA tax year runs from 6 April to 5 April.",
                        "Subscriptions use the allowance for the relevant tax year.",
                        "Transfers need the receiving provider's process to preserve the wrapper.",
                    ]
                ),
                "{}",
                stamp,
                stamp,
            ),
            (
                "editorial-angle-isa-transfer-process-v1",
                "uk-isa-rules",
                "research-pack-isa-deadline-v1",
                "Moving an ISA? The transfer process protects the wrapper.",
                (
                    "Moving an ISA is not simply moving money: using the receiving provider's "
                    "process is part of preserving its tax wrapper."
                ),
                (
                    "Recognise why the transfer route matters before moving ISA savings or "
                    "investments."
                ),
                "A practical mistake-avoidance framing for viewers considering an ISA transfer.",
                json.dumps(
                    [
                        "An ISA transfer needs to follow the receiving provider's process.",
                        "The process matters for preserving the ISA tax wrapper.",
                        "Allowance context is relevant before making new ISA subscriptions.",
                    ]
                ),
                "{}",
                stamp,
                stamp,
            ),
        )
        relationships = (
            ("editorial-angle-isa-decision-tree-v1", "claim-isa-tax-year-v1", "core"),
            ("editorial-angle-isa-decision-tree-v1", "claim-isa-allowance-v1", "core"),
            ("editorial-angle-isa-decision-tree-v1", "claim-isa-transfer-v1", "supporting"),
            ("editorial-angle-isa-transfer-process-v1", "claim-isa-transfer-v1", "core"),
            ("editorial-angle-isa-transfer-process-v1", "claim-isa-allowance-v1", "supporting"),
        )
        with self.connection:
            for angle in angles:
                self.connection.execute(
                    "INSERT OR IGNORE INTO editorial_angles "
                    "(id, opportunity_id, research_pack_id, working_title, thesis, "
                    "audience_promise, "
                    "framing, key_takeaways_json, metadata_json, created_at, updated_at, "
                    "research_readiness_assessment_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
                    angle,
                )
            for editorial_angle_id, claim_id, role in relationships:
                self.connection.execute(
                    "INSERT OR IGNORE INTO editorial_angle_claims VALUES (?, ?, ?, ?)",
                    (editorial_angle_id, claim_id, role, stamp),
                )

    def seed_content_piece_data(self) -> None:
        """Seed one persistent ISA deliverable and its immutable demo narration version."""

        stamp = now()
        demo_content = content_payload()
        content_piece = (
            "content-piece-isa-deadline-video-v1",
            "uk-isa-rules",
            "editorial-angle-isa-decision-tree-v1",
            "video",
            demo_content["title"],
            "{}",
            stamp,
            stamp,
        )
        script = (
            "script-isa-deadline-video-v1",
            "content-piece-isa-deadline-video-v1",
            1,
            demo_content["script"],
            "{}",
            stamp,
            stamp,
        )
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO content_pieces VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                content_piece,
            )
            self.connection.execute(
                "INSERT OR IGNORE INTO scripts VALUES (?, ?, ?, ?, ?, ?, ?)", script
            )

    def seed_visual_plan_data(self) -> None:
        """Seed the existing ISA scene-plan direction as one durable VisualPlan."""

        stamp = now()
        visual_plan = (
            "visual-plan-isa-deadline-video-v1",
            "content-piece-isa-deadline-video-v1",
            "script-isa-deadline-video-v1",
            (
                "Calm kitchen-table ISA decision tree with the sling-bag hamster, a tax-year "
                "calendar, four labelled envelopes and progressively introduced branches."
            ),
            "{}",
            stamp,
            stamp,
        )
        scenes = (
            (
                "scene-isa-deadline-video-v1-01",
                "visual-plan-isa-deadline-video-v1",
                1,
                "If you have spare cash before 5 April",
                "Establish the calm kitchen-table decision context before the deadline.",
                "The sling-bag hamster sorts four labelled envelopes at the table.",
                None,
                "Introduce a tax-year calendar beside the envelopes.",
                "{}",
                stamp,
                stamp,
            ),
            (
                "scene-isa-deadline-video-v1-02",
                "visual-plan-isa-deadline-video-v1",
                2,
                "the question is not simply 'should I invest?'",
                "Use the calendar to reinforce the decision context without replacing narration.",
                "The hamster pauses and checks the calendar.",
                "Should I invest?",
                "Begin building the decision tree one branch at a time.",
                "{}",
                stamp,
                stamp,
            ),
            (
                "scene-isa-deadline-video-v1-03",
                "visual-plan-isa-deadline-video-v1",
                3,
                "whether you are about to lose a tax-year opportunity you cannot get back",
                "Complete the visual decision tree to reinforce the time-limited opportunity.",
                "The hamster reacts to the completed decision-tree branches.",
                None,
                None,
                "{}",
                stamp,
                stamp,
            ),
        )
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO visual_plans VALUES (?, ?, ?, ?, ?, ?, ?)", visual_plan
            )
            for scene in scenes:
                self.connection.execute(
                    "INSERT OR IGNORE INTO scenes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    scene,
                )

    def seed_asset_spec_data(self) -> None:
        """Seed the existing ISA Scene requirements without registering generated Assets."""

        stamp = now()
        hamster_profile_id = "character-profile-similarstoic-hamster-core-v1"
        canonical_hamster_prompts = {
            "asset-spec-isa-scene-01-hamster-sorting-v1": (
                "Illustrated hamster calmly sorting four labelled envelopes at a kitchen table."
            ),
            "asset-spec-isa-scene-03-hamster-reaction-v1": (
                "Illustrated hamster reacting to a completed decision tree."
            ),
        }
        asset_specs = (
            (
                "asset-spec-isa-scene-01-kitchen-background-v1",
                "scene-isa-deadline-video-v1-01",
                "environment",
                "Establish the calm kitchen-table decision context.",
                (
                    "A simple, calm young-professional kitchen-table setting with minimal kitchen "
                    "and table cues and generous clear background space."
                ),
                (
                    "Simple calm young-professional kitchen-table background for a SimilarStoic "
                    "ISA decision scene, with a predominantly open light canvas, minimal kitchen "
                    "and table cues, and generous clear space for later foreground layers."
                ),
                "isa-kitchen-environment",
                None,
                "{}",
                stamp,
                stamp,
            ),
            (
                "asset-spec-isa-scene-01-hamster-sorting-v1",
                "scene-isa-deadline-video-v1-01",
                "character",
                "Illustrate the viewer sorting practical ISA options.",
                "The sling-bag hamster sorts four labelled envelopes at the kitchen table.",
                canonical_hamster_prompts["asset-spec-isa-scene-01-hamster-sorting-v1"],
                "similarstoic-hamster-core",
                hamster_profile_id,
                "{}",
                stamp,
                stamp,
            ),
            (
                "asset-spec-isa-scene-02-tax-year-calendar-v1",
                "scene-isa-deadline-video-v1-02",
                "graphic",
                "Reinforce the tax-year deadline context without replacing narration.",
                "A readable tax-year calendar that supports the ISA decision context.",
                (
                    "Clear illustrated tax-year calendar graphic for a UK ISA decision video, "
                    "supporting an audio-first explanation; calm, simple, legible and not "
                    "dependent on text for the essential argument."
                ),
                None,
                None,
                "{}",
                stamp,
                stamp,
            ),
            (
                "asset-spec-isa-scene-03-decision-tree-v1",
                "scene-isa-deadline-video-v1-03",
                "graphic",
                "Complete the visual decision tree for the time-limited ISA opportunity.",
                "A completed decision-tree graphic that reinforces the narrated practical checks.",
                (
                    "Illustrated decision-tree graphic for a UK ISA deadline video, with calm "
                    "clear branches that reinforce rather than replace the audio-first explanation."
                ),
                None,
                None,
                "{}",
                stamp,
                stamp,
            ),
            (
                "asset-spec-isa-scene-03-hamster-reaction-v1",
                "scene-isa-deadline-video-v1-03",
                "character",
                "Add a relatable reaction to the completed decision-tree branches.",
                "The sling-bag hamster reacts to the completed decision-tree branches.",
                canonical_hamster_prompts["asset-spec-isa-scene-03-hamster-reaction-v1"],
                "similarstoic-hamster-core",
                hamster_profile_id,
                "{}",
                stamp,
                stamp,
            ),
        )
        with self.connection:
            for asset_spec in asset_specs:
                self.connection.execute(
                    "INSERT OR IGNORE INTO asset_specs "
                    "(id, scene_id, asset_type, purpose, description, generation_prompt, "
                    "continuity_key, character_profile_id, metadata_json, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    asset_spec,
                )
            for asset_spec_id, generation_prompt in canonical_hamster_prompts.items():
                self.connection.execute(
                    "UPDATE asset_specs SET generation_prompt = ?, character_profile_id = ? "
                    "WHERE id = ?",
                    (generation_prompt, hamster_profile_id, asset_spec_id),
                )

    def seed_character_profile_data(self) -> None:
        """Seed the canonical hamster identity without overwriting accepted versions."""

        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO character_profiles " "VALUES (?, ?, ?, ?, ?, ?, '{}', ?)",
                (
                    "character-profile-similarstoic-hamster-core-v1",
                    "similarstoic-hamster-core",
                    1,
                    "SimilarStoic Hamster Core",
                    (
                        "A recognisable classic hamster with a recurring consistent identity, "
                        "young-professional relatability and a small everyday sling/crossbody bag. "
                        "The hamster uses hamster-native behaviour to embody SimilarStoic money, "
                        "work, behaviour and life-strategy concepts, and is intended to remain "
                        "recognisably the same individual across character assets."
                    ),
                    (
                        "Depict the canonical SimilarStoic hamster consistently: a recognisable "
                        "classic hamster with a small everyday sling/crossbody bag, using "
                        "hamster-native behaviour to embody the requested concept."
                    ),
                    now(),
                ),
            )

    def seed_visual_style_profile_data(self) -> None:
        """Seed immutable SimilarStoic Core visual-language profile versions once."""

        rules = {
            "schema_version": 1,
            "global": {
                "background": "predominantly white or very light background",
                "composition": "sparse composition",
                "visual_ideas": "one dominant visual idea",
                "shapes": "clean simple shapes",
                "shading": "restrained shading",
                "colour": "restrained accent colour",
                "negative_space": "generous negative space",
                "detail": "minimal environmental detail and only necessary props",
                "avoid": [
                    "photorealism",
                    "cinematic or highly rendered imagery",
                    "detailed decorative clutter",
                    "dense information-heavy compositions",
                    (
                        "invented explanatory text, posters, labels, dashboards, "
                        "written information or signage unless explicitly required "
                        "by the AssetSpec"
                    ),
                ],
                "narration": (
                    "visuals reinforce narration and must not become necessary for understanding "
                    "the explanation"
                ),
            },
            "asset_types": {
                "environment": {
                    "role": "background setting layer only",
                    "layer_discipline": (
                        "leave clear space for later foreground composition and do not invent "
                        "sibling AssetSpec requirements"
                    ),
                    "prefer": [
                        "white or light open canvas",
                        "minimal setting cues",
                        "generous negative space",
                        "few essential objects",
                    ],
                    "avoid": [
                        "foreground characters unless they are part of the environment itself",
                        "standalone props",
                        "explanatory graphics",
                        "full explainer composition",
                        "dense signage",
                        "information boards",
                        "invented written material",
                        "multiple narrative events",
                        "unnecessary decorative props",
                        "fully furnished or detail-heavy rooms",
                    ],
                },
                "character": {
                    "role": "clear character pose, action or reaction",
                    "prefer": [
                        "character as dominant subject",
                        "plain or minimal background",
                        "clear silhouette and body language",
                        "very few competing props",
                    ],
                },
                "prop": {
                    "role": "one standalone object or small coherent object group",
                    "prefer": [
                        "simple isolated presentation",
                        "minimal background",
                        "no unrelated scene construction",
                    ],
                },
                "graphic": {
                    "role": "one clear explanatory graphic",
                    "prefer": [
                        "simple structure",
                        "minimal labels",
                        "only text explicitly required by the AssetSpec",
                        "high immediate readability",
                    ],
                },
            },
        }
        v2_rules = {
            "schema_version": 1,
            "global": {
                "background": "predominantly white or very light background",
                "composition": "sparse composition",
                "visual_ideas": "one dominant visual idea",
                "rendering_language": (
                    "visibly hand-drawn black or dark line illustration with natural stroke "
                    "variation, slightly uneven contours and simplified readable forms; keep "
                    "most of the scene white and unfilled, using no colour unless helpful and "
                    "then only one restrained flat block accent colour"
                ),
                "shapes": "simple deliberately imperfect geometry",
                "shading": "no soft or tonal shading",
                "colour": (
                    "no colour unless helpful; at most one restrained flat block accent colour"
                ),
                "negative_space": "generous negative space",
                "detail": "minimal environmental detail and only necessary props",
                "avoid": [
                    "mechanically perfect vector lines",
                    "perfectly uniform outlines",
                    "overly symmetrical object geometry",
                    "soft shaded colour",
                    "subtle colour variation",
                    "multiple shades of the same object",
                    "painterly fill treatment",
                    "airbrushed shading",
                    "textured colouring or fills",
                    "gradient shading",
                    "blended colour transitions",
                    "polished digital illustration finish",
                    "generic stock-illustration appearance",
                    "hyper-clean iconography",
                    "photorealism",
                    "realistic depth rendering",
                    "detailed decorative clutter",
                    "dense information-heavy compositions",
                    (
                        "invented explanatory text, posters, labels, dashboards, written "
                        "information or signage unless explicitly required by the AssetSpec"
                    ),
                ],
                "narration": (
                    "visuals reinforce narration and must not become necessary for understanding "
                    "the explanation"
                ),
            },
            "asset_types": {
                "environment": {
                    "role": "background setting layer only",
                    "layer_discipline": (
                        "leave clear space for later foreground composition and do not invent "
                        "sibling AssetSpec requirements"
                    ),
                    "prefer": [
                        "white or light open canvas",
                        "minimal setting cues",
                        "generous negative space",
                        "few essential objects",
                    ],
                    "avoid": [
                        "foreground characters unless they are part of the environment itself",
                        "standalone props",
                        "explanatory graphics",
                        "full explainer composition",
                        "dense signage",
                        "information boards",
                        "invented written material",
                        "multiple narrative events",
                        "unnecessary decorative props",
                        "fully furnished or detail-heavy rooms",
                    ],
                },
                "character": {
                    "role": "clear character pose, action or reaction",
                    "prefer": [
                        "character as dominant subject",
                        "plain or minimal background",
                        "clear silhouette and body language",
                        "very few competing props",
                    ],
                },
                "prop": {
                    "role": "one standalone object or small coherent object group",
                    "prefer": [
                        "simple isolated presentation",
                        "minimal background",
                        "no unrelated scene construction",
                    ],
                },
                "graphic": {
                    "role": "one clear explanatory graphic",
                    "prefer": [
                        "simple structure",
                        "minimal labels",
                        "only text explicitly required by the AssetSpec",
                        "high immediate readability",
                    ],
                },
            },
        }
        v3_rules = json.loads(json.dumps(v2_rules))
        v3_rules["global"]["rendering_language"] = (
            "visibly hand-drawn black or dark line illustration with natural stroke variation, "
            "slightly uneven contours and simple readable forms; use a crude amateur human-drawn "
            "grammar that feels like an average adult drew it from memory, rather than a polished "
            "professional illustration"
        )
        v3_rules["global"]["shapes"] = (
            "simple deliberately imperfect, blocky cartoon-like geometry; when depicting the "
            "canonical recurring hamster, use large distinctive hamster-like ears, long whiskers, "
            "and simple alert eyes"
        )
        v3_rules["global"]["colour"] = (
            "keep general scene colour restrained; for the canonical recurring SimilarStoic "
            "hamster only, the mostly white/light body may have warm tan/orange inner ears, "
            "nose and "
            "paws/hands/feet, and its signature sling/man-bag may use flat green, blue, orange, "
            "yellow, red and black with a dark-gray strap; this is not permission for arbitrary "
            "scene elements to become highly multicoloured"
        )
        v3_rules["global"]["detail"] = (
            "minimal environmental detail and only necessary props; the canonical recurring "
            "hamster uses minimal or no fur-detail rendering, and its signature bag must read "
            "as genuinely "
            "crossbody with physically correct strap/body interaction"
        )
        v3_rules["global"]["avoid"] = [
            *v2_rules["global"]["avoid"],
            "glossy mascot rendering",
            "highly polished AI-clean finish",
            "detailed fur rendering on the canonical recurring hamster",
        ]
        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO visual_style_profiles "
                "VALUES (?, ?, ?, ?, ?, ?, ?, '{}', ?)",
                (
                    "visual-style-profile-similarstoic-core-v1",
                    "similarstoic-core",
                    1,
                    "SimilarStoic Core",
                    "The sparse, hand-drawn editorial illustration direction for SimilarStoic.",
                    "Use a simple hand-drawn or line-drawn editorial illustration style.",
                    json.dumps(rules, sort_keys=True),
                    stamp,
                ),
            )
            self.connection.execute(
                "INSERT OR IGNORE INTO visual_style_profiles "
                "VALUES (?, ?, ?, ?, ?, ?, ?, '{}', ?)",
                (
                    "visual-style-profile-similarstoic-core-v3",
                    "similarstoic-core",
                    3,
                    "SimilarStoic Core",
                    (
                        "The founder-approved Phase 1 sparse, crude human-drawn visual baseline "
                        "for SimilarStoic."
                    ),
                    (
                        "Use a crude, visibly human hand-drawn editorial sketch with organic, "
                        "imperfect dark linework and simple readable forms. For the canonical "
                        "recurring hamster, preserve the founder-approved warm tan/orange accents "
                        "and signature flat multi-colour crossbody sling/man-bag within otherwise "
                        "restrained scene colour."
                    ),
                    json.dumps(v3_rules, sort_keys=True),
                    stamp,
                ),
            )
            self.connection.execute(
                "INSERT OR IGNORE INTO visual_style_profiles "
                "VALUES (?, ?, ?, ?, ?, ?, ?, '{}', ?)",
                (
                    "visual-style-profile-similarstoic-core-v2",
                    "similarstoic-core",
                    2,
                    "SimilarStoic Core",
                    (
                        "The sparse, visibly hand-drawn editorial sketch direction for "
                        "SimilarStoic."
                    ),
                    (
                        "Use a visibly hand-drawn editorial sketch with organic, imperfect "
                        "linework and simple readable forms."
                    ),
                    json.dumps(v2_rules, sort_keys=True),
                    stamp,
                ),
            )

    @staticmethod
    def _subject(row: sqlite3.Row) -> Subject:
        return Subject(
            row["id"],
            row["slug"],
            row["name"],
            row["description"],
            bool(row["active"]),
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

    @staticmethod
    def _opportunity(row: sqlite3.Row) -> Opportunity:
        return Opportunity(
            row["id"],
            row["title"],
            row["summary"],
            row["why_now"],
            row["score"],
            row["status"],
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

    def _idea_gate_review_payload(self, opportunity: Opportunity) -> dict[str, Any]:
        """Build the exact, intentionally limited Discover material shown at Idea Gate."""

        subjects = [
            {
                "id": subject.id,
                "slug": subject.slug,
                "name": subject.name,
                "relationship_role": relationship_type,
            }
            for subject, relationship_type in self.opportunity_subjects(opportunity.id)
        ]
        metadata = opportunity.metadata
        return {
            "opportunity": {
                "id": opportunity.id,
                "title": opportunity.title,
                "summary": opportunity.summary,
                "why_now": opportunity.why_now,
                "score": opportunity.score,
            },
            "subjects": subjects,
            "review_context": {
                "atlas_recommendation": metadata["suggested_angle"],
                "evidence_quality": metadata["evidence_quality"],
                "material_risk": metadata["risk"],
                "portfolio_relevance": metadata["portfolio_relevance"],
                "visual_potential": metadata["visual_potential"],
                "display_pillar": metadata.get("legacy_display_pillar", "Not yet classified"),
            },
        }

    @staticmethod
    def _normalized_optional_text(value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Idea Gate optional text must be text or null.")
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _validate_research_readiness_assessment(
        outcome: str,
        findings: dict[str, Any],
        policy_version: str,
        producer_kind: str,
        producer_identifier: str,
        producer_implementation_version: str,
    ) -> None:
        if not isinstance(outcome, str) or outcome not in RESEARCH_READINESS_OUTCOMES:
            raise ValueError(
                "Research readiness outcome must be Ready, NeedsMoreResearch or Blocked."
            )
        if not isinstance(findings, dict) or not findings:
            raise ValueError("Research readiness findings must be a non-empty JSON object.")
        if not any(
            (isinstance(value, str) and value.strip())
            or (isinstance(value, (list, dict)) and bool(value))
            for value in findings.values()
        ):
            raise ValueError("Research readiness findings must contain a meaningful reason.")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                policy_version,
                producer_kind,
                producer_identifier,
                producer_implementation_version,
            )
        ):
            raise ValueError(
                "Research readiness policy version and producer provenance must be non-empty text."
            )

    @staticmethod
    def _validate_idea_gate_decision(
        outcome: str,
        founder_actor: str,
        founder_comment: str | None,
        founder_direction: str | None,
    ) -> None:
        if outcome not in IDEA_GATE_DECISION_OUTCOMES:
            raise ValueError("Idea Gate outcome must be Proceed, Reject or Steer.")
        if not isinstance(founder_actor, str) or not founder_actor.strip():
            raise ValueError("Idea Gate founder actor must be non-empty text.")
        normalized_comment = AtlasRepository._normalized_optional_text(founder_comment)
        normalized_direction = AtlasRepository._normalized_optional_text(founder_direction)
        if outcome == "Steer" and normalized_direction is None:
            raise ValueError("Steer requires non-empty founder direction.")
        if outcome != "Steer" and normalized_direction is not None:
            raise ValueError("Founder direction is only valid for Steer.")
        if normalized_comment is not None and len(normalized_comment) > 10_000:
            raise ValueError("Idea Gate founder comment is too long.")
        if normalized_direction is not None and len(normalized_direction) > 10_000:
            raise ValueError("Idea Gate founder direction is too long.")

    @staticmethod
    def _idea_gate_review_snapshot(row: sqlite3.Row) -> IdeaGateReviewSnapshot:
        return IdeaGateReviewSnapshot(
            row["id"],
            row["opportunity_id"],
            row["payload_schema_version"],
            json.loads(row["review_payload_json"]),
            row["created_at"],
        )

    @staticmethod
    def _idea_gate_decision(row: sqlite3.Row) -> IdeaGateDecision:
        return IdeaGateDecision(
            row["id"],
            row["review_snapshot_id"],
            row["outcome"],
            row["founder_actor"],
            row["founder_comment"],
            row["founder_direction"],
            row["created_at"],
        )

    @staticmethod
    def _idea_gate_decision_payload(decision: IdeaGateDecision) -> dict[str, Any]:
        return {
            "id": decision.id,
            "review_snapshot_id": decision.review_snapshot_id,
            "outcome": decision.outcome,
            "founder_actor": decision.founder_actor,
            "founder_comment": decision.founder_comment,
            "founder_direction": decision.founder_direction,
            "created_at": decision.created_at,
        }

    @staticmethod
    def _research_pack(row: sqlite3.Row) -> ResearchPack:
        return ResearchPack(
            row["id"],
            row["opportunity_id"],
            row["idea_gate_decision_id"],
            row["version"],
            row["summary"],
            row["as_of_date"],
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

    @staticmethod
    def _research_readiness_assessment(row: sqlite3.Row) -> ResearchReadinessAssessment:
        return ResearchReadinessAssessment(
            row["id"],
            row["research_pack_id"],
            row["assessment_schema_version"],
            json.loads(row["frozen_evidence_state_json"]),
            row["outcome"],
            json.loads(row["findings_json"]),
            row["policy_version"],
            row["producer_kind"],
            row["producer_identifier"],
            row["producer_implementation_version"],
            row["created_at"],
        )

    @staticmethod
    def _research_readiness_assessment_payload(
        assessment: ResearchReadinessAssessment,
    ) -> dict[str, Any]:
        return {
            "id": assessment.id,
            "research_pack_id": assessment.research_pack_id,
            "schema_version": assessment.schema_version,
            "frozen_evidence_state": assessment.frozen_evidence_state,
            "outcome": assessment.outcome,
            "findings": assessment.findings,
            "policy_version": assessment.policy_version,
            "producer_kind": assessment.producer_kind,
            "producer_identifier": assessment.producer_identifier,
            "producer_implementation_version": assessment.producer_implementation_version,
            "created_at": assessment.created_at,
        }

    @staticmethod
    def _claim(row: sqlite3.Row) -> Claim:
        return Claim(
            row["id"],
            row["research_pack_id"],
            row["text"],
            row["claim_type"],
            row["risk_level"],
            row["freshness_type"],
            row["verification_status"],
            row["verification_notes"],
            row["reviewed_at"],
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

    @staticmethod
    def _source(row: sqlite3.Row) -> Source:
        return Source(
            row["id"],
            row["source_type"],
            row["title"],
            row["publisher"],
            row["author"],
            row["url"],
            row["publication_date"],
            row["accessed_at"],
            row["jurisdiction"],
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

    @staticmethod
    def _claim_evidence(row: sqlite3.Row) -> ClaimEvidence:
        return ClaimEvidence(
            row["claim_id"],
            row["source_id"],
            row["stance"],
            row["reference"],
            row["notes"],
            row["created_at"],
            row["updated_at"],
        )

    @staticmethod
    def _editorial_angle(row: sqlite3.Row) -> EditorialAngle:
        return EditorialAngle(
            row["id"],
            row["opportunity_id"],
            row["research_pack_id"],
            row["research_readiness_assessment_id"],
            row["working_title"],
            row["thesis"],
            row["audience_promise"],
            row["framing"],
            json.loads(row["key_takeaways_json"]),
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

    @staticmethod
    def _editorial_angle_claim(row: sqlite3.Row) -> EditorialAngleClaim:
        return EditorialAngleClaim(
            row["editorial_angle_id"], row["claim_id"], row["role"], row["created_at"]
        )

    @staticmethod
    def _content_piece(row: sqlite3.Row) -> ContentPiece:
        return ContentPiece(
            row["id"],
            row["opportunity_id"],
            row["editorial_angle_id"],
            row["format_key"],
            row["working_title"],
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

    @staticmethod
    def _script(row: sqlite3.Row) -> Script:
        return Script(
            row["id"],
            row["content_piece_id"],
            row["version"],
            row["narration_text"],
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

    @staticmethod
    def _script_claim_set(row: sqlite3.Row) -> ScriptClaimSet:
        return ScriptClaimSet(row["id"], row["script_id"], row["created_at"])

    @staticmethod
    def _script_claim_link(row: sqlite3.Row) -> ScriptClaimLink:
        return ScriptClaimLink(row["script_claim_set_id"], row["claim_id"], row["created_at"])

    @staticmethod
    def _title_option(row: sqlite3.Row) -> TitleOption:
        return TitleOption(
            row["id"],
            row["content_piece_id"],
            row["text"],
            json.loads(row["metadata_json"]),
            row["created_at"],
        )

    @staticmethod
    def _hook_option(row: sqlite3.Row) -> HookOption:
        return HookOption(
            row["id"],
            row["content_piece_id"],
            row["text"],
            json.loads(row["metadata_json"]),
            row["created_at"],
        )

    @staticmethod
    def _editorial_package_snapshot(row: sqlite3.Row) -> EditorialPackageSnapshot:
        return EditorialPackageSnapshot(
            row["id"],
            row["content_piece_id"],
            row["title_option_id"],
            row["hook_option_id"],
            row["script_id"],
            row["created_at"],
        )

    @staticmethod
    def _editorial_readiness_assessment(row: sqlite3.Row) -> EditorialReadinessAssessment:
        return EditorialReadinessAssessment(
            row["id"],
            row["editorial_package_snapshot_id"],
            row["assessment_schema_version"],
            row["evaluator_id"],
            row["evaluator_version"],
            row["outcome"],
            json.loads(row["findings_json"]),
            row["created_at"],
        )

    @staticmethod
    def _editorial_gate_decision(row: sqlite3.Row) -> EditorialGateDecision:
        return EditorialGateDecision(
            row["id"],
            row["editorial_package_snapshot_id"],
            row["editorial_readiness_assessment_id"],
            row["outcome"],
            row["actor"],
            row["comment"],
            row["created_at"],
        )

    @staticmethod
    def _visual_plan(row: sqlite3.Row) -> VisualPlan:
        return VisualPlan(
            row["id"],
            row["content_piece_id"],
            row["script_id"],
            row["visual_direction"],
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

    @staticmethod
    def _visual_plan_gate_provenance(row: sqlite3.Row) -> VisualPlanGateProvenance:
        return VisualPlanGateProvenance(
            row["visual_plan_id"], row["editorial_gate_decision_id"], row["created_at"]
        )

    @staticmethod
    def _scene(row: sqlite3.Row) -> Scene:
        return Scene(
            row["id"],
            row["visual_plan_id"],
            row["sequence"],
            row["narration_excerpt"],
            row["visual_intent"],
            row["hamster_action"],
            row["on_screen_text"],
            row["transition_note"],
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

    @staticmethod
    def _asset_spec(row: sqlite3.Row) -> AssetSpec:
        return AssetSpec(
            row["id"],
            row["scene_id"],
            row["asset_type"],
            row["purpose"],
            row["description"],
            row["generation_prompt"],
            row["continuity_key"],
            row["character_profile_id"],
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

    @staticmethod
    def _asset(row: sqlite3.Row) -> Asset:
        return Asset(
            row["id"],
            row["asset_spec_id"],
            row["generation_execution_id"],
            row["version"],
            row["storage_path"],
            row["media_type"],
            row["source_kind"],
            row["content_digest"],
            json.loads(row["metadata_json"]),
            row["created_at"],
        )

    @staticmethod
    def _character_reference_set(row: sqlite3.Row) -> CharacterReferenceSet:
        return CharacterReferenceSet(
            row["id"], row["character_profile_id"], row["version"], row["created_at"]
        )

    @staticmethod
    def _character_reference_set_member(row: sqlite3.Row) -> CharacterReferenceSetMember:
        return CharacterReferenceSetMember(
            row["character_reference_set_id"],
            row["asset_id"],
            row["position"],
            row["created_at"],
        )

    @staticmethod
    def _visual_style_profile(row: sqlite3.Row) -> VisualStyleProfile:
        return VisualStyleProfile(
            row["id"],
            row["style_key"],
            row["version"],
            row["name"],
            row["description"],
            row["generation_guidance"],
            json.loads(row["rules_json"]),
            json.loads(row["metadata_json"]),
            row["created_at"],
        )

    @staticmethod
    def _character_profile(row: sqlite3.Row) -> CharacterProfile:
        return CharacterProfile(
            row["id"],
            row["character_key"],
            row["version"],
            row["name"],
            row["identity_description"],
            row["generation_guidance"],
            json.loads(row["metadata_json"]),
            row["created_at"],
        )

    @staticmethod
    def _generation_execution(row: sqlite3.Row) -> GenerationExecution:
        return GenerationExecution(
            row["id"],
            row["asset_spec_id"],
            row["visual_style_profile_id"],
            row["character_profile_id"],
            row["character_reference_set_id"],
            json.loads(row["asset_spec_snapshot_json"]),
            json.loads(row["generation_input_json"]),
            row["generator_key"],
            row["provider_key"],
            row["model_key"],
            row["provider_request_id"],
            row["outcome"],
            row["error_code"],
            row["error_message"],
            json.loads(row["response_metadata_json"]),
            row["created_at"],
        )
