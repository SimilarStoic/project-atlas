"""SQLite persistence for Atlas discovery through content-piece and script foundations."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
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
class ResearchPack:
    """A versioned research snapshot owned by one Opportunity."""

    id: str
    opportunity_id: str
    version: int
    summary: str
    as_of_date: str | None
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


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


Migration = tuple[int, tuple[str, ...]]
EDITORIAL_ANGLE_CLAIM_ROLES = frozenset({"core", "supporting"})


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
)


class AtlasRepository:
    """A small application/repository boundary over SQLite."""

    def __init__(self, database_path: Path | str | None = None) -> None:
        self.database_path = Path(database_path or default_database_path())
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
            }
            for item in self.list_opportunities()
        ]

    def create_research_pack(
        self,
        research_pack_id: str,
        opportunity_id: str,
        version: int,
        summary: str,
        as_of_date: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResearchPack:
        """Create an immutable, versioned research snapshot for an Opportunity."""

        stamp = now()
        with self.connection:
            self.connection.execute(
                "INSERT INTO research_packs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    research_pack_id,
                    opportunity_id,
                    version,
                    summary,
                    as_of_date,
                    json.dumps(metadata or {}),
                    stamp,
                    stamp,
                ),
            )
        return self.get_research_pack(research_pack_id)

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
                "INSERT INTO editorial_angles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
        ):
            raise ValueError(
                "EditorialAngle Opportunity and ResearchPack provenance are immutable."
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

        stamp = now()
        with self.connection:
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
                "INSERT OR IGNORE INTO research_packs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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

    @staticmethod
    def _research_pack(row: sqlite3.Row) -> ResearchPack:
        return ResearchPack(
            row["id"],
            row["opportunity_id"],
            row["version"],
            row["summary"],
            row["as_of_date"],
            json.loads(row["metadata_json"]),
            row["created_at"],
            row["updated_at"],
        )

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
