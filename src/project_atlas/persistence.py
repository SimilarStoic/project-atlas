"""SQLite persistence for Atlas Subjects and Opportunities only."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from project_atlas.demo_data import OPPORTUNITIES


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


Migration = tuple[int, tuple[str, ...]]


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
