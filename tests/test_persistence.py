"""Tests for the scoped Subjects and Opportunities persistence layer."""

import sqlite3
from dataclasses import replace

from project_atlas.persistence import AtlasRepository


def test_migrations_seed_and_relationships_are_idempotent(tmp_path) -> None:
    """A new database migrates once and seeds the six existing Discover fixtures once."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        assert [
            row["version"]
            for row in repository.connection.execute("SELECT version FROM schema_migrations")
        ] == [1]
        assert len(repository.discover_payload()) == 6
        assert repository.get_subject("subject-isa").name == "ISA"
        assert (
            repository.opportunity_subjects("salary-sacrifice")[0][0].id
            == "subject-salary-sacrifice"
        )
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert (
            reopened.connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1
        )
        assert reopened.connection.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0] == 6
        assert (
            reopened.connection.execute("SELECT COUNT(*) FROM opportunity_subjects").fetchone()[0]
            == 7
        )
    finally:
        reopened.close()


def test_updates_and_new_relationships_survive_reopen_without_seed_overwrite(tmp_path) -> None:
    """Existing local changes survive a later application startup."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        opportunity = repository.get_opportunity("uk-isa-rules")
        repository.update_opportunity(replace(opportunity, status="founder_review", score=99))
        repository.create_subject(
            "subject-savings", "savings", "Savings", "Money set aside for future use."
        )
        repository.associate_subject("uk-isa-rules", "subject-savings", "supporting")
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        changed = reopened.get_opportunity("uk-isa-rules")
        assert changed.status == "founder_review"
        assert changed.score == 99
        assert {subject.id for subject, _ in reopened.opportunity_subjects(changed.id)} == {
            "subject-isa",
            "subject-savings",
        }
        assert reopened.discover_payload()[0]["id"] == "uk-isa-rules"
    finally:
        reopened.close()


def test_failed_migration_is_atomic_and_not_recorded(tmp_path) -> None:
    """A broken later statement rolls back the entire migration."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        failing_migration = (
            (
                2,
                (
                    "CREATE TABLE should_not_survive (id TEXT PRIMARY KEY)",
                    "THIS IS NOT VALID SQL",
                ),
            ),
        )
        try:
            repository.apply_migrations(failing_migration)
        except sqlite3.DatabaseError:
            pass
        else:
            raise AssertionError("The intentionally invalid migration did not fail.")

        assert (
            repository.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='should_not_survive'"
            ).fetchone()
            is None
        )
        assert (
            repository.connection.execute(
                "SELECT version FROM schema_migrations WHERE version = 2"
            ).fetchone()
            is None
        )
    finally:
        repository.close()


def test_discover_serializes_opportunity_without_legacy_display_pillar(tmp_path) -> None:
    """Display-only Pillar metadata is optional for valid Opportunities."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        repository.create_opportunity(
            "opportunity-unclassified",
            "A new editorial opportunity",
            "A valid Opportunity with no legacy display metadata.",
            "A local test case.",
            1,
            "proposed",
            {
                "suggested_angle": "A test angle.",
                "evidence_quality": "Not assessed",
                "risk": "Not assessed",
                "portfolio_relevance": "Not assessed",
                "visual_potential": "Not assessed",
            },
        )
        payload = next(
            item
            for item in repository.discover_payload()
            if item["id"] == "opportunity-unclassified"
        )
        assert payload["pillar"] == "Not yet classified"
    finally:
        repository.close()
