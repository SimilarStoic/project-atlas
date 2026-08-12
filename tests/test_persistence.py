"""Tests for Atlas persistence through the v0.3 research-evidence foundation."""

import sqlite3
from dataclasses import replace

from project_atlas.persistence import MIGRATIONS, AtlasRepository


def test_fresh_database_migrates_and_seeds_discovery_and_one_research_pack(tmp_path) -> None:
    """Fresh startup applies both migrations and creates only the scoped seed data."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        assert [
            row["version"]
            for row in repository.connection.execute("SELECT version FROM schema_migrations")
        ] == [1, 2]
        assert len(repository.discover_payload()) == 6
        assert repository.get_subject("subject-isa").name == "ISA"
        assert len(repository.list_research_packs("uk-isa-rules")) == 1
        payload = repository.latest_research_pack_payload("uk-isa-rules")
        assert payload is not None
        assert len(payload["claims"]) == 3
        assert payload["source_count"] == 2
        assert payload["claims"][2]["evidence"][0]["stance"] in {
            "contextualises",
            "supports",
        }
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert reopened.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[0] == 1
        assert reopened.connection.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 3
        assert reopened.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 2
        assert reopened.connection.execute("SELECT COUNT(*) FROM claim_evidence").fetchone()[0] == 4
    finally:
        reopened.close()


def test_existing_v02_database_migrates_to_v03_without_rewriting_discovery_data(tmp_path) -> None:
    """The new migration applies cleanly to a database already recorded at v0.2."""

    database = tmp_path / "atlas-v02.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for statement in MIGRATIONS[0][1]:
            connection.execute(statement)
        connection.execute(
            "INSERT INTO schema_migrations VALUES (1, '2026-08-11T00:00:00+00:00')"
        )
        connection.execute(
            "INSERT INTO opportunities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "existing-opportunity",
                "Existing opportunity",
                "Existing summary",
                "Existing why now",
                50,
                "proposed",
                "{}",
                "2026-08-11T00:00:00+00:00",
                "2026-08-11T00:00:00+00:00",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    repository = AtlasRepository(database)
    try:
        assert repository.get_opportunity("existing-opportunity").title == "Existing opportunity"
        assert [
            row["version"]
            for row in repository.connection.execute("SELECT version FROM schema_migrations")
        ] == [1, 2]
        assert repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='research_packs'"
        ).fetchone()
    finally:
        repository.close()


def test_failed_migration_is_atomic_and_not_recorded(tmp_path) -> None:
    """A broken later statement rolls back the entire migration transaction."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        failing_migration = (
            (
                3,
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

        assert repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='should_not_survive'"
        ).fetchone() is None
        assert repository.connection.execute(
            "SELECT version FROM schema_migrations WHERE version = 3"
        ).fetchone() is None
    finally:
        repository.close()


def test_research_pack_versions_and_claim_updates_survive_reopen(tmp_path) -> None:
    """Packs version per Opportunity; Claims retain their ownership and editable detail."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        pack = repository.create_research_pack(
            "research-pack-isa-deadline-v2",
            "uk-isa-rules",
            2,
            "A later snapshot for test coverage.",
            "2026-08-12",
        )
        claim = repository.create_claim(
            "claim-isa-test-v2",
            pack.id,
            "A test claim.",
            "interpretive",
            "low",
            "stable",
            "in_review",
            "Needs editorial review.",
            "2026-08-12T10:00:00+00:00",
        )
        updated = repository.update_claim(
            replace(
                claim,
                verification_status="supported",
                verification_notes="Reviewed for test use.",
            )
        )
        assert updated.research_pack_id == pack.id
        assert repository.latest_research_pack("uk-isa-rules").version == 2
        try:
            repository.create_research_pack(
                "research-pack-duplicate-v2",
                "uk-isa-rules",
                2,
                "Duplicate version.",
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("A duplicate Opportunity/version pair was accepted.")
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        persisted = reopened.get_claim("claim-isa-test-v2")
        assert persisted.verification_status == "supported"
        assert persisted.verification_notes == "Reviewed for test use."
        assert persisted.reviewed_at == "2026-08-12T10:00:00+00:00"
    finally:
        reopened.close()


def test_sources_and_evidence_are_reusable_without_duplicate_pairs(tmp_path) -> None:
    """A Source links to Claims across packs while each Claim/Source pair stays unique."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        second_pack = repository.create_research_pack(
            "research-pack-credit-v1", "credit-utilisation", 1, "Credit test pack."
        )
        first_claim = repository.get_claim("claim-isa-tax-year-v1")
        second_claim = repository.create_claim(
            "claim-credit-test-v1",
            second_pack.id,
            "A test claim that reuses a source.",
            "illustrative",
            "low",
            "stable",
            "insufficient",
            "Test-only relationship.",
        )
        source = repository.get_source("source-govuk-individual-savings-accounts")
        reused = repository.create_source(
            "source-duplicate-id",
            "other",
            "Should not replace the source",
            "Test publisher",
            source.url,
            "2026-08-12",
        )
        assert reused.id == source.id
        repository.link_claim_evidence(
            second_claim.id, source.id, "contextualises", "Test section", "Reused source test."
        )
        relationship = repository.link_claim_evidence(
            second_claim.id, source.id, "supports", "Revised section", "Updated relationship."
        )
        assert relationship.stance == "supports"
        assert len(repository.evidence_for_claim(second_claim.id)) == 1
        assert {claim.id for claim in repository.claims_for_source(source.id)} >= {
            first_claim.id,
            second_claim.id,
        }
    finally:
        repository.close()


def test_seed_research_is_idempotent_and_does_not_overwrite_claim_edits(tmp_path) -> None:
    """Repeated startup preserves research changes rather than recreating seed records."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        claim = repository.get_claim("claim-isa-tax-year-v1")
        repository.update_claim(replace(claim, verification_notes="Founder review note."))
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert (
            reopened.get_claim("claim-isa-tax-year-v1").verification_notes == "Founder review note."
        )
        assert reopened.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[0] == 1
        assert reopened.connection.execute("SELECT COUNT(*) FROM claim_evidence").fetchone()[0] == 4
    finally:
        reopened.close()


def test_seed_reuses_existing_source_url_and_restores_missing_evidence(tmp_path) -> None:
    """Seed evidence resolves an existing Source by URL without replacing local Claim edits."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    source_url = "https://www.gov.uk/individual-savings-accounts"
    try:
        with repository.connection:
            repository.connection.execute("DELETE FROM claim_evidence")
            repository.connection.execute("DELETE FROM claims")
            repository.connection.execute("DELETE FROM research_packs")
            repository.connection.execute("DELETE FROM sources")
        existing_source = repository.create_source(
            "pre-existing-source-id",
            "other",
            "Existing source title",
            "Existing publisher",
            source_url,
            "2026-08-12",
        )

        repository.seed_research_data()
        allowance_claim = repository.get_claim("claim-isa-allowance-v1")
        repository.update_claim(replace(allowance_claim, verification_notes="Preserve this edit."))
        with repository.connection:
            repository.connection.execute(
                "DELETE FROM claim_evidence WHERE claim_id = ?",
                (allowance_claim.id,),
            )
        repository.seed_research_data()

        assert repository.connection.execute(
            "SELECT COUNT(*) FROM sources WHERE url = ?", (source_url,)
        ).fetchone()[0] == 1
        assert repository.get_claim(allowance_claim.id).verification_notes == "Preserve this edit."
        assert {source.id for _, source in repository.evidence_for_claim(allowance_claim.id)} == {
            existing_source.id
        }
        assert len(repository.evidence_for_claim("claim-isa-transfer-v1")) == 2
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert reopened.connection.execute(
            "SELECT COUNT(*) FROM sources WHERE url = ?", (source_url,)
        ).fetchone()[0] == 1
        tax_year_sources = reopened.evidence_for_claim("claim-isa-tax-year-v1")
        assert {source.id for _, source in tax_year_sources} == {
            "pre-existing-source-id"
        }
    finally:
        reopened.close()


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
