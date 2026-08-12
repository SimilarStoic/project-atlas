"""Tests for Atlas persistence through the v0.5 content-piece and script foundation."""

import sqlite3
from dataclasses import replace

from project_atlas.persistence import MIGRATIONS, AtlasRepository


def test_fresh_database_migrates_and_seeds_discovery_research_angles_and_scripts(tmp_path) -> None:
    """Fresh startup applies all migrations and creates the scoped seed data."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        assert [
            row["version"]
            for row in repository.connection.execute("SELECT version FROM schema_migrations")
        ] == [1, 2, 3, 4]
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
        assert len(repository.list_editorial_angles_for_opportunity("uk-isa-rules")) == 2
        assert len(repository.list_content_pieces_for_opportunity("uk-isa-rules")) == 1
        assert (
            len(repository.list_scripts_for_content_piece("content-piece-isa-deadline-video-v1"))
            == 1
        )
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert reopened.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[0] == 1
        assert reopened.connection.execute("SELECT COUNT(*) FROM claims").fetchone()[0] == 3
        assert reopened.connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 2
        assert reopened.connection.execute("SELECT COUNT(*) FROM claim_evidence").fetchone()[0] == 4
        assert (
            reopened.connection.execute("SELECT COUNT(*) FROM editorial_angles").fetchone()[0] == 2
        )
        assert (
            reopened.connection.execute("SELECT COUNT(*) FROM editorial_angle_claims").fetchone()[0]
            == 5
        )
        assert reopened.connection.execute("SELECT COUNT(*) FROM content_pieces").fetchone()[0] == 1
        assert reopened.connection.execute("SELECT COUNT(*) FROM scripts").fetchone()[0] == 1
    finally:
        reopened.close()


def test_existing_v04_database_migrates_to_v05_without_rewriting_discovery_data(tmp_path) -> None:
    """The new migration applies cleanly to a database already recorded at v0.4."""

    database = tmp_path / "atlas-v04.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for statement in MIGRATIONS[0][1]:
            connection.execute(statement)
        connection.execute("INSERT INTO schema_migrations VALUES (1, '2026-08-11T00:00:00+00:00')")
        for statement in MIGRATIONS[1][1]:
            connection.execute(statement)
        connection.execute("INSERT INTO schema_migrations VALUES (2, '2026-08-12T00:00:00+00:00')")
        for statement in MIGRATIONS[2][1]:
            connection.execute(statement)
        connection.execute("INSERT INTO schema_migrations VALUES (3, '2026-08-12T00:00:00+00:00')")
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
        ] == [1, 2, 3, 4]
        assert repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='content_pieces'"
        ).fetchone()
    finally:
        repository.close()


def test_failed_migration_is_atomic_and_not_recorded(tmp_path) -> None:
    """A broken later statement rolls back the entire migration transaction."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        failing_migration = (
            (
                5,
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
                "SELECT version FROM schema_migrations WHERE version = 5"
            ).fetchone()
            is None
        )
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
            repository.connection.execute("DELETE FROM scripts")
            repository.connection.execute("DELETE FROM content_pieces")
            repository.connection.execute("DELETE FROM editorial_angle_claims")
            repository.connection.execute("DELETE FROM editorial_angles")
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

        assert (
            repository.connection.execute(
                "SELECT COUNT(*) FROM sources WHERE url = ?", (source_url,)
            ).fetchone()[0]
            == 1
        )
        assert repository.get_claim(allowance_claim.id).verification_notes == "Preserve this edit."
        assert {source.id for _, source in repository.evidence_for_claim(allowance_claim.id)} == {
            existing_source.id
        }
        assert len(repository.evidence_for_claim("claim-isa-transfer-v1")) == 2
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert (
            reopened.connection.execute(
                "SELECT COUNT(*) FROM sources WHERE url = ?", (source_url,)
            ).fetchone()[0]
            == 1
        )
        tax_year_sources = reopened.evidence_for_claim("claim-isa-tax-year-v1")
        assert {source.id for _, source in tax_year_sources} == {"pre-existing-source-id"}
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


def test_editorial_angle_provenance_is_immutable_while_normal_edits_persist(
    tmp_path,
) -> None:
    """Angles retain provenance while normal editorial detail remains editable."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        pack = repository.get_research_pack("research-pack-isa-deadline-v1")
        angle = repository.create_editorial_angle(
            "editorial-angle-isa-test-v1",
            "uk-isa-rules",
            pack.id,
            "A test editorial proposition.",
            "The test thesis is grounded in the ISA research pack.",
            "Understand the decision context from the available research.",
            "A test framing for repository coverage.",
            ["First intended takeaway.", "Second intended takeaway."],
        )
        next_pack = repository.create_research_pack(
            "research-pack-isa-deadline-v2", "uk-isa-rules", 2, "A later ISA snapshot."
        )
        for provenance_change in (
            replace(angle, opportunity_id="credit-utilisation"),
            replace(angle, research_pack_id=next_pack.id),
        ):
            try:
                repository.update_editorial_angle(provenance_change)
            except ValueError as error:
                assert "provenance are immutable" in str(error)
            else:
                raise AssertionError("An EditorialAngle update changed historical provenance.")
        updated = repository.update_editorial_angle(
            replace(
                angle,
                working_title="A revised test editorial proposition.",
                thesis="The revised test thesis persists after restart.",
                audience_promise="A revised audience promise.",
                framing="A revised framing.",
                key_takeaways=["Revised intended takeaway."],
                metadata={"edited": True},
            )
        )
        assert updated.thesis == "The revised test thesis persists after restart."
        assert updated.opportunity_id == "uk-isa-rules"
        assert updated.research_pack_id == pack.id
        assert len(repository.list_editorial_angles_for_opportunity("uk-isa-rules")) == 3
        assert len(repository.list_editorial_angles_for_research_pack(pack.id)) == 3
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        persisted = reopened.get_editorial_angle("editorial-angle-isa-test-v1")
        assert persisted.working_title == "A revised test editorial proposition."
        assert persisted.thesis == "The revised test thesis persists after restart."
        assert persisted.audience_promise == "A revised audience promise."
        assert persisted.framing == "A revised framing."
        assert persisted.key_takeaways == ["Revised intended takeaway."]
        assert persisted.metadata == {"edited": True}
        assert persisted.opportunity_id == "uk-isa-rules"
        assert persisted.research_pack_id == "research-pack-isa-deadline-v1"
    finally:
        reopened.close()


def test_editorial_angle_rejects_research_pack_from_another_opportunity(tmp_path) -> None:
    """The Angle's Opportunity and ResearchPack must agree in the repository layer."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        other_pack = repository.create_research_pack(
            "research-pack-credit-v1", "credit-utilisation", 1, "Credit test pack."
        )
        try:
            repository.create_editorial_angle(
                "editorial-angle-invalid-pack-v1",
                "uk-isa-rules",
                other_pack.id,
                "Invalid angle.",
                "Invalid thesis.",
                "Invalid promise.",
                "Invalid framing.",
                ["Invalid takeaway."],
            )
        except ValueError as error:
            assert "same Opportunity" in str(error)
        else:
            raise AssertionError(
                "An EditorialAngle accepted a ResearchPack from another Opportunity."
            )
    finally:
        repository.close()


def test_editorial_angle_claims_are_reusable_idempotent_and_same_pack_only(tmp_path) -> None:
    """Claim roles persist without duplicate pairs and cannot cross ResearchPack boundaries."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        first_angle = repository.get_editorial_angle("editorial-angle-isa-decision-tree-v1")
        second_angle = repository.get_editorial_angle("editorial-angle-isa-transfer-process-v1")
        allowance_claim = repository.get_claim("claim-isa-allowance-v1")
        transfer_claim = repository.get_claim("claim-isa-transfer-v1")

        assert len(repository.claims_for_editorial_angle(first_angle.id)) == 3
        assert len(repository.claims_for_editorial_angle(second_angle.id)) == 2
        assert {
            angle.id
            for angle in repository.list_editorial_angles_for_research_pack(
                first_angle.research_pack_id
            )
        } >= {first_angle.id, second_angle.id}

        relationship = repository.link_claim_to_editorial_angle(
            first_angle.id, allowance_claim.id, "supporting"
        )
        assert relationship.role == "core"
        assert (
            repository.update_editorial_angle_claim_role(
                first_angle.id, allowance_claim.id, "supporting"
            ).role
            == "supporting"
        )
        assert len(repository.claims_for_editorial_angle(first_angle.id)) == 3
        try:
            repository.update_editorial_angle_claim_role(
                first_angle.id, allowance_claim.id, "primary"
            )
        except ValueError as error:
            assert "core or supporting" in str(error)
        else:
            raise AssertionError("An unrecognised EditorialAngleClaim role was accepted.")
        assert {
            claim.id for _, claim in repository.claims_for_editorial_angle(second_angle.id)
        } >= {allowance_claim.id, transfer_claim.id}

        other_pack = repository.create_research_pack(
            "research-pack-credit-v1", "credit-utilisation", 1, "Credit test pack."
        )
        other_claim = repository.create_claim(
            "claim-credit-v1",
            other_pack.id,
            "A claim from another research pack.",
            "factual",
            "low",
            "stable",
            "unreviewed",
            "Test-only claim.",
        )
        try:
            repository.link_claim_to_editorial_angle(first_angle.id, other_claim.id, "supporting")
        except ValueError as error:
            assert "ResearchPack" in str(error)
        else:
            raise AssertionError("An EditorialAngle accepted a Claim from another ResearchPack.")
    finally:
        repository.close()


def test_editorial_angle_seed_restores_missing_links_without_overwriting_edits(tmp_path) -> None:
    """Restart seeding restores a missing link while preserving Angle, Claim, and role edits."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        angle = repository.get_editorial_angle("editorial-angle-isa-decision-tree-v1")
        repository.update_editorial_angle(
            replace(angle, audience_promise="Founder-edited promise that must persist.")
        )
        repository.update_editorial_angle_claim_role(angle.id, "claim-isa-transfer-v1", "core")
        claim = repository.get_claim("claim-isa-allowance-v1")
        repository.update_claim(replace(claim, verification_notes="Founder-edited claim note."))
        with repository.connection:
            repository.connection.execute(
                "DELETE FROM editorial_angle_claims WHERE editorial_angle_id = ? AND claim_id = ?",
                ("editorial-angle-isa-transfer-process-v1", "claim-isa-allowance-v1"),
            )
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        angle = reopened.get_editorial_angle("editorial-angle-isa-decision-tree-v1")
        assert angle.audience_promise == "Founder-edited promise that must persist."
        assert len(reopened.list_editorial_angles_for_opportunity("uk-isa-rules")) == 2
        assert reopened.get_editorial_angle_claim(angle.id, "claim-isa-transfer-v1").role == "core"
        assert (
            reopened.get_editorial_angle_claim(
                "editorial-angle-isa-transfer-process-v1", "claim-isa-allowance-v1"
            ).role
            == "supporting"
        )
        assert reopened.get_claim("claim-isa-allowance-v1").verification_notes == (
            "Founder-edited claim note."
        )
        payload = reopened.editorial_angle_payload(angle.id)
        assert payload["working_title"] == "The 15-minute ISA decision tree before the deadline."
        assert {claim["role"] for claim in payload["claims"]} == {"core"}
    finally:
        reopened.close()


def test_content_pieces_retain_provenance_while_normal_edits_persist(tmp_path) -> None:
    """ContentPieces may be edited normally but cannot move away from their Angle provenance."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        angle = repository.get_editorial_angle("editorial-angle-isa-decision-tree-v1")
        content_piece = repository.create_content_piece(
            "content-piece-isa-test-v1",
            "uk-isa-rules",
            angle.id,
            "video",
            "A test ContentPiece.",
        )
        repository.create_content_piece(
            "content-piece-isa-test-v2",
            "uk-isa-rules",
            angle.id,
            "article",
            "A second test ContentPiece.",
        )
        other_angle = repository.get_editorial_angle("editorial-angle-isa-transfer-process-v1")
        try:
            repository.create_content_piece(
                "content-piece-invalid-v1",
                "credit-utilisation",
                angle.id,
                "video",
                "Invalid ContentPiece.",
            )
        except ValueError as error:
            assert "same Opportunity" in str(error)
        else:
            raise AssertionError("A ContentPiece accepted an Angle from another Opportunity.")
        for provenance_change in (
            replace(content_piece, opportunity_id="credit-utilisation"),
            replace(content_piece, editorial_angle_id=other_angle.id),
        ):
            try:
                repository.update_content_piece(provenance_change)
            except ValueError as error:
                assert "provenance are immutable" in str(error)
            else:
                raise AssertionError("A ContentPiece update changed historical provenance.")
        updated = repository.update_content_piece(
            replace(
                content_piece,
                format_key="short_video",
                working_title="A revised test ContentPiece.",
                metadata={"edited": True},
            )
        )
        assert updated.format_key == "short_video"
        assert len(repository.list_content_pieces_for_opportunity("uk-isa-rules")) == 3
        assert len(repository.list_content_pieces_for_editorial_angle(angle.id)) == 3
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        persisted = reopened.get_content_piece("content-piece-isa-test-v1")
        assert persisted.working_title == "A revised test ContentPiece."
        assert persisted.format_key == "short_video"
        assert persisted.metadata == {"edited": True}
        assert persisted.opportunity_id == "uk-isa-rules"
        assert persisted.editorial_angle_id == "editorial-angle-isa-decision-tree-v1"
    finally:
        reopened.close()


def test_script_versions_are_immutable_and_latest_after_reopen(tmp_path) -> None:
    """Scripts remain distinct immutable narration versions for one ContentPiece."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        content_piece = repository.create_content_piece(
            "content-piece-isa-script-test-v1",
            "uk-isa-rules",
            "editorial-angle-isa-decision-tree-v1",
            "video",
            "A script versioning test ContentPiece.",
        )
        script_v1 = repository.create_script(
            "script-isa-test-v1", content_piece.id, 1, "Original narration version one."
        )
        script_v2 = repository.create_script(
            "script-isa-test-v2", content_piece.id, 2, "Revised narration version two."
        )
        try:
            repository.create_script(
                "script-isa-test-duplicate-v2", content_piece.id, 2, "Duplicate version."
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("A duplicate ContentPiece/Script version was accepted.")
        assert [
            script.version for script in repository.list_scripts_for_content_piece(content_piece.id)
        ] == [
            1,
            2,
        ]
        assert repository.latest_script_for_content_piece(content_piece.id) == script_v2
        assert (
            repository.get_script(script_v1.id).narration_text == "Original narration version one."
        )
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert reopened.get_script("script-isa-test-v1").narration_text == (
            "Original narration version one."
        )
        assert (
            reopened.latest_script_for_content_piece("content-piece-isa-script-test-v1").version
            == 2
        )
    finally:
        reopened.close()


def test_content_piece_seed_does_not_overwrite_existing_script_v1_narration(tmp_path) -> None:
    """Startup preserves persisted historical narration for the seeded Script v1."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        replacement_narration = "Persisted historical Script v1 narration."
        with repository.connection:
            repository.connection.execute(
                "UPDATE scripts SET narration_text = ? WHERE id = ?",
                (replacement_narration, "script-isa-deadline-video-v1"),
            )
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert reopened.get_script("script-isa-deadline-video-v1").narration_text == (
            replacement_narration
        )
        assert (
            len(reopened.list_scripts_for_content_piece("content-piece-isa-deadline-video-v1")) == 1
        )
    finally:
        reopened.close()


def test_content_piece_seed_restores_missing_script_v1_without_overwriting_piece(tmp_path) -> None:
    """Startup restores only the missing seeded Script while retaining ContentPiece edits."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        content_piece = repository.get_content_piece("content-piece-isa-deadline-video-v1")
        repository.update_content_piece(
            replace(content_piece, working_title="Founder-edited ContentPiece title.")
        )
        seeded_narration = repository.get_script("script-isa-deadline-video-v1").narration_text
        with repository.connection:
            repository.connection.execute(
                "DELETE FROM scripts WHERE id = ?", ("script-isa-deadline-video-v1",)
            )
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert reopened.get_content_piece("content-piece-isa-deadline-video-v1").working_title == (
            "Founder-edited ContentPiece title."
        )
        assert (
            reopened.get_script("script-isa-deadline-video-v1").narration_text == seeded_narration
        )
        assert (
            len(reopened.list_scripts_for_content_piece("content-piece-isa-deadline-video-v1")) == 1
        )
    finally:
        reopened.close()


def test_content_piece_seed_restores_missing_piece_and_script_without_touching_earlier_data(
    tmp_path,
) -> None:
    """Startup restores the seeded v0.5 pair while retaining v0.2-v0.4 records."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        expected_opportunities = repository.discover_payload()
        expected_angle_ids = [
            angle.id for angle in repository.list_editorial_angles_for_opportunity("uk-isa-rules")
        ]
        expected_claim_ids = [
            claim.id for claim in repository.list_claims("research-pack-isa-deadline-v1")
        ]
        seeded_narration = repository.get_script("script-isa-deadline-video-v1").narration_text
        with repository.connection:
            repository.connection.execute(
                "DELETE FROM scripts WHERE id = ?", ("script-isa-deadline-video-v1",)
            )
            repository.connection.execute(
                "DELETE FROM content_pieces WHERE id = ?",
                ("content-piece-isa-deadline-video-v1",),
            )
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert len(reopened.list_content_pieces_for_opportunity("uk-isa-rules")) == 1
        assert reopened.get_content_piece(
            "content-piece-isa-deadline-video-v1"
        ).editorial_angle_id == ("editorial-angle-isa-decision-tree-v1")
        assert (
            reopened.get_script("script-isa-deadline-video-v1").narration_text == seeded_narration
        )
        assert (
            len(reopened.list_scripts_for_content_piece("content-piece-isa-deadline-video-v1")) == 1
        )
        assert reopened.discover_payload() == expected_opportunities
        assert len(reopened.list_editorial_angles_for_opportunity("uk-isa-rules")) == 2
        assert [
            angle.id for angle in reopened.list_editorial_angles_for_opportunity("uk-isa-rules")
        ] == expected_angle_ids
        assert [
            claim.id for claim in reopened.list_claims("research-pack-isa-deadline-v1")
        ] == expected_claim_ids
    finally:
        reopened.close()
