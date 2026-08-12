"""Tests for Atlas persistence through the v0.7 asset-spec and asset foundation."""

import sqlite3
from dataclasses import replace

from project_atlas.generation import (
    AssetStorageFailure,
    GeneratedArtifact,
    GenerationFailure,
    GenerationInput,
    GenerationService,
    LocalAssetStorage,
    OpenAIImageGenerator,
    UnsupportedGenerationType,
)
from project_atlas.persistence import MIGRATIONS, AtlasRepository


class FakeImageGenerator:
    """Deterministic provider-neutral generator used only by v0.8 tests."""

    generator_key = "fake-image"

    def __init__(self, *, failure: GenerationFailure | None = None) -> None:
        self.failure = failure
        self.inputs: list[object] = []

    def supports(self, asset_type: str) -> bool:
        return asset_type in {"environment", "character", "graphic", "prop"}

    def generate(self, generation_input: object) -> GeneratedArtifact:
        self.inputs.append(generation_input)
        if self.failure:
            raise self.failure
        return GeneratedArtifact(
            b"deterministic png bytes",
            "image/png",
            provider_key="fake-provider",
            model_key="fake-model-v1",
            provider_request_id="request-fake-1",
            response_metadata={"test": True},
        )


def test_fresh_database_migrates_and_seeds_discovery_through_asset_specs(tmp_path) -> None:
    """Fresh startup applies all migrations and creates the scoped seed data."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        assert [
            row["version"]
            for row in repository.connection.execute("SELECT version FROM schema_migrations")
        ] == [1, 2, 3, 4, 5, 6, 7]
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
        assert (
            len(
                repository.list_visual_plans_for_content_piece(
                    "content-piece-isa-deadline-video-v1"
                )
            )
            == 1
        )
        assert len(repository.list_scenes_for_visual_plan("visual-plan-isa-deadline-video-v1")) == 3
        assert len(repository.list_asset_specs_for_scene("scene-isa-deadline-video-v1-01")) == 2
        assert repository.connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 0
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM generation_executions").fetchone()[
                0
            ]
            == 0
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
        assert reopened.connection.execute("SELECT COUNT(*) FROM visual_plans").fetchone()[0] == 1
        assert reopened.connection.execute("SELECT COUNT(*) FROM scenes").fetchone()[0] == 3
        assert reopened.connection.execute("SELECT COUNT(*) FROM asset_specs").fetchone()[0] == 5
        assert reopened.connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 0
        assert (
            reopened.connection.execute("SELECT COUNT(*) FROM generation_executions").fetchone()[0]
            == 0
        )
    finally:
        reopened.close()


def test_existing_v07_database_migrates_to_v08_without_rewriting_existing_assets(tmp_path) -> None:
    """Migration 7 adds nullable execution provenance without rebuilding Assets."""

    database = tmp_path / "atlas-v06.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for version, statements in MIGRATIONS[:6]:
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, '2026-08-12T00:00:00+00:00')", (version,)
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
        connection.execute(
            "INSERT INTO asset_specs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "existing-asset-spec",
                "scene-existing",
                "graphic",
                "Existing purpose",
                "Existing description",
                "Existing prompt",
                None,
                "{}",
                "2026-08-12T00:00:00+00:00",
                "2026-08-12T00:00:00+00:00",
            ),
        )
        connection.execute(
            "INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "existing-manual-asset",
                "existing-asset-spec",
                1,
                "existing.png",
                "image/png",
                "manual",
                "{}",
                "2026-08-12T00:00:00+00:00",
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
        ] == [1, 2, 3, 4, 5, 6, 7]
        assert repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='generation_executions'"
        ).fetchone()
        assert repository.get_asset("existing-manual-asset").generation_execution_id is None
    finally:
        repository.close()


def test_failed_migration_is_atomic_and_not_recorded(tmp_path) -> None:
    """A broken later statement rolls back the entire migration transaction."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        failing_migration = (
            (
                8,
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
                "SELECT version FROM schema_migrations WHERE version = 8"
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
            repository.connection.execute("DELETE FROM assets")
            repository.connection.execute("DELETE FROM asset_specs")
            repository.connection.execute("DELETE FROM scenes")
            repository.connection.execute("DELETE FROM visual_plans")
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
            repository.connection.execute("DELETE FROM assets")
            repository.connection.execute("DELETE FROM asset_specs")
            repository.connection.execute("DELETE FROM scenes")
            repository.connection.execute("DELETE FROM visual_plans")
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
            repository.connection.execute("DELETE FROM assets")
            repository.connection.execute("DELETE FROM asset_specs")
            repository.connection.execute("DELETE FROM scenes")
            repository.connection.execute("DELETE FROM visual_plans")
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


def test_visual_plans_retain_provenance_while_normal_edits_persist(tmp_path) -> None:
    """VisualPlans remain tied to one ContentPiece and exact Script version."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        plan = repository.create_visual_plan(
            "visual-plan-isa-test-v1",
            "content-piece-isa-deadline-video-v1",
            "script-isa-deadline-video-v1",
            "A test visual direction.",
        )
        repository.create_visual_plan(
            "visual-plan-isa-test-v2",
            "content-piece-isa-deadline-video-v1",
            "script-isa-deadline-video-v1",
            "A second test visual direction.",
        )
        other_piece = repository.create_content_piece(
            "content-piece-isa-visual-plan-test-v1",
            "uk-isa-rules",
            "editorial-angle-isa-decision-tree-v1",
            "video",
            "A VisualPlan validation test ContentPiece.",
        )
        other_script = repository.create_script(
            "script-isa-visual-plan-test-v1",
            other_piece.id,
            1,
            "A separate test narration.",
        )
        try:
            repository.create_visual_plan(
                "visual-plan-isa-mismatch-v1",
                "content-piece-isa-deadline-video-v1",
                other_script.id,
                "Invalid cross-ContentPiece VisualPlan.",
            )
        except ValueError as error:
            assert "same ContentPiece" in str(error)
        else:
            raise AssertionError("A VisualPlan accepted a Script from another ContentPiece.")
        for provenance_change in (
            replace(plan, content_piece_id=other_piece.id),
            replace(plan, script_id=other_script.id),
        ):
            try:
                repository.update_visual_plan(provenance_change)
            except ValueError as error:
                assert "provenance are immutable" in str(error)
            else:
                raise AssertionError("A VisualPlan update changed historical provenance.")
        updated = repository.update_visual_plan(
            replace(
                plan,
                visual_direction="A revised test visual direction.",
                metadata={"edited": True},
            )
        )
        assert updated.visual_direction == "A revised test visual direction."
        assert (
            len(
                repository.list_visual_plans_for_content_piece(
                    "content-piece-isa-deadline-video-v1"
                )
            )
            == 3
        )
        assert len(repository.list_visual_plans_for_script("script-isa-deadline-video-v1")) == 3
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        persisted = reopened.get_visual_plan("visual-plan-isa-test-v1")
        assert persisted.visual_direction == "A revised test visual direction."
        assert persisted.metadata == {"edited": True}
        assert persisted.content_piece_id == "content-piece-isa-deadline-video-v1"
        assert persisted.script_id == "script-isa-deadline-video-v1"
    finally:
        reopened.close()


def test_scenes_are_ordered_editable_and_owned_by_one_visual_plan(tmp_path) -> None:
    """Scenes order per plan, retain their owner, and support nullable direction detail."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        plan = repository.create_visual_plan(
            "visual-plan-isa-scene-test-v1",
            "content-piece-isa-deadline-video-v1",
            "script-isa-deadline-video-v1",
            "A scene ordering test direction.",
        )
        other_plan = repository.create_visual_plan(
            "visual-plan-isa-scene-test-v2",
            "content-piece-isa-deadline-video-v1",
            "script-isa-deadline-video-v1",
            "A second scene ordering test direction.",
        )
        second_scene = repository.create_scene(
            "scene-isa-scene-test-v1-02",
            plan.id,
            2,
            "Second narration locator.",
            "Second visual intent.",
        )
        first_scene = repository.create_scene(
            "scene-isa-scene-test-v1-01",
            plan.id,
            1,
            "First narration locator.",
            "First visual intent.",
            "The hamster freezes in reaction.",
            "Supporting text only.",
            "Move to the second scene.",
        )
        assert [scene.id for scene in repository.list_scenes_for_visual_plan(plan.id)] == [
            first_scene.id,
            second_scene.id,
        ]
        assert second_scene.hamster_action is None
        assert second_scene.on_screen_text is None
        assert second_scene.transition_note is None
        try:
            repository.update_scene(
                replace(
                    second_scene,
                    sequence=1,
                    visual_intent="This collision must not persist.",
                )
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("A Scene sequence collision was accepted during update.")
        unchanged_second_scene = repository.get_scene(second_scene.id)
        assert unchanged_second_scene.sequence == 2
        assert unchanged_second_scene.visual_intent == "Second visual intent."
        try:
            repository.create_scene(
                "scene-isa-scene-test-v1-duplicate",
                plan.id,
                1,
                "Duplicate narration locator.",
                "Duplicate visual intent.",
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("A duplicate Scene sequence was accepted within one VisualPlan.")
        same_sequence_elsewhere = repository.create_scene(
            "scene-isa-scene-test-v2-01",
            other_plan.id,
            1,
            "Other plan narration locator.",
            "Other plan visual intent.",
        )
        assert repository.list_scenes_for_visual_plan(other_plan.id) == [same_sequence_elsewhere]
        try:
            repository.update_scene(replace(first_scene, visual_plan_id=other_plan.id))
        except ValueError as error:
            assert "provenance is immutable" in str(error)
        else:
            raise AssertionError("A Scene update changed VisualPlan provenance.")
        updated = repository.update_scene(
            replace(
                second_scene,
                sequence=3,
                narration_excerpt="Revised narration locator.",
                visual_intent="Revised visual intent.",
                hamster_action="The hamster stuffs its cheeks.",
                on_screen_text="Still supporting.",
                transition_note="End the visual sequence.",
                metadata={"edited": True},
            )
        )
        assert [scene.sequence for scene in repository.list_scenes_for_visual_plan(plan.id)] == [
            1,
            3,
        ]
        assert updated.sequence == 3
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        persisted = reopened.get_scene("scene-isa-scene-test-v1-02")
        assert persisted.narration_excerpt == "Revised narration locator."
        assert persisted.visual_intent == "Revised visual intent."
        assert persisted.hamster_action == "The hamster stuffs its cheeks."
        assert persisted.on_screen_text == "Still supporting."
        assert persisted.transition_note == "End the visual sequence."
        assert persisted.metadata == {"edited": True}
    finally:
        reopened.close()


def test_visual_plan_seed_is_idempotent_and_restores_missing_structure(tmp_path) -> None:
    """VisualPlan startup restores missing seed rows without overwriting valid earlier edits."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        content_piece = repository.get_content_piece("content-piece-isa-deadline-video-v1")
        repository.update_content_piece(
            replace(content_piece, working_title="Founder-edited ContentPiece title.")
        )
        visual_plan = repository.get_visual_plan("visual-plan-isa-deadline-video-v1")
        repository.update_visual_plan(
            replace(visual_plan, visual_direction="Founder-edited VisualPlan direction.")
        )
        edited_scene = repository.get_scene("scene-isa-deadline-video-v1-01")
        repository.update_scene(replace(edited_scene, visual_intent="Founder-edited Scene intent."))
        original_narration = repository.get_script("script-isa-deadline-video-v1").narration_text
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert reopened.get_content_piece("content-piece-isa-deadline-video-v1").working_title == (
            "Founder-edited ContentPiece title."
        )
        assert reopened.get_visual_plan("visual-plan-isa-deadline-video-v1").visual_direction == (
            "Founder-edited VisualPlan direction."
        )
        assert reopened.get_scene("scene-isa-deadline-video-v1-01").visual_intent == (
            "Founder-edited Scene intent."
        )
        assert (
            reopened.get_script("script-isa-deadline-video-v1").narration_text == original_narration
        )
        with reopened.connection:
            reopened.connection.execute(
                "DELETE FROM asset_specs WHERE scene_id = ?", ("scene-isa-deadline-video-v1-03",)
            )
            reopened.connection.execute(
                "DELETE FROM scenes WHERE id = ?", ("scene-isa-deadline-video-v1-03",)
            )
    finally:
        reopened.close()

    reopened = AtlasRepository(database)
    try:
        assert len(reopened.list_scenes_for_visual_plan("visual-plan-isa-deadline-video-v1")) == 3
        assert reopened.get_scene("scene-isa-deadline-video-v1-01").visual_intent == (
            "Founder-edited Scene intent."
        )
        with reopened.connection:
            reopened.connection.execute("DELETE FROM assets")
            reopened.connection.execute("DELETE FROM asset_specs")
            reopened.connection.execute(
                "DELETE FROM scenes WHERE visual_plan_id = ?",
                ("visual-plan-isa-deadline-video-v1",),
            )
            reopened.connection.execute(
                "DELETE FROM visual_plans WHERE id = ?",
                ("visual-plan-isa-deadline-video-v1",),
            )
    finally:
        reopened.close()

    restored = AtlasRepository(database)
    try:
        assert (
            len(restored.list_visual_plans_for_content_piece("content-piece-isa-deadline-video-v1"))
            == 1
        )
        assert len(restored.list_scenes_for_visual_plan("visual-plan-isa-deadline-video-v1")) == 3
        assert restored.get_content_piece("content-piece-isa-deadline-video-v1").working_title == (
            "Founder-edited ContentPiece title."
        )
        assert (
            restored.get_script("script-isa-deadline-video-v1").narration_text == original_narration
        )
        assert len(restored.list_editorial_angles_for_opportunity("uk-isa-rules")) == 2
        assert len(restored.list_claims("research-pack-isa-deadline-v1")) == 3
    finally:
        restored.close()


def test_asset_specs_retain_scene_provenance_while_normal_edits_persist(tmp_path) -> None:
    """Asset requirements remain owned by their original Scene across normal edits."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        first_scene = repository.get_scene("scene-isa-deadline-video-v1-01")
        other_scene = repository.get_scene("scene-isa-deadline-video-v1-02")
        required_text = {
            "asset_type": "prop",
            "purpose": "Give the hamster a practical decision prop.",
            "description": "A labelled envelope used in the ISA decision scene.",
            "generation_prompt": "Illustrated labelled envelope for a calm UK ISA decision scene.",
        }
        for field_name in required_text:
            for invalid_value in ("", "   "):
                values = {**required_text, field_name: invalid_value}
                try:
                    repository.create_asset_spec(
                        f"asset-spec-isa-invalid-{field_name}-{len(invalid_value)}",
                        first_scene.id,
                        values["asset_type"],
                        values["purpose"],
                        values["description"],
                        values["generation_prompt"],
                    )
                except ValueError as error:
                    assert "must not be empty or whitespace-only" in str(error)
                else:
                    raise AssertionError("An AssetSpec accepted invalid required text.")
        first_spec = repository.create_asset_spec(
            "asset-spec-isa-test-v1",
            first_scene.id,
            required_text["asset_type"],
            required_text["purpose"],
            required_text["description"],
            required_text["generation_prompt"],
            "isa-envelope-prop",
        )
        second_spec = repository.create_asset_spec(
            "asset-spec-isa-test-v2",
            first_scene.id,
            "graphic",
            "Reinforce a practical branch.",
            "A simple supporting decision graphic.",
            "Simple illustrated decision graphic that supports the narration.",
        )
        assert repository.get_asset_spec(first_spec.id) == first_spec
        assert [
            asset_spec.id for asset_spec in repository.list_asset_specs_for_scene(first_scene.id)
        ][-2:] == [first_spec.id, second_spec.id]
        try:
            repository.update_asset_spec(replace(first_spec, scene_id=other_scene.id))
        except ValueError as error:
            assert "provenance is immutable" in str(error)
        else:
            raise AssertionError("An AssetSpec update changed Scene provenance.")
        for field_name in required_text:
            for invalid_value in ("", "   "):
                try:
                    repository.update_asset_spec(replace(first_spec, **{field_name: invalid_value}))
                except ValueError as error:
                    assert "must not be empty or whitespace-only" in str(error)
                else:
                    raise AssertionError("An AssetSpec update accepted invalid required text.")
        assert repository.get_asset_spec(first_spec.id) == first_spec
        updated = repository.update_asset_spec(
            replace(
                first_spec,
                asset_type="illustration",
                purpose="Clarify the viewer's practical ISA decision.",
                description="A revised labelled envelope used in the ISA decision scene.",
                generation_prompt="Revised provider-neutral envelope illustration prompt.",
                continuity_key=None,
                metadata={"edited": True},
            )
        )
        assert updated.scene_id == first_scene.id
        assert updated.continuity_key is None
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        persisted = reopened.get_asset_spec("asset-spec-isa-test-v1")
        assert persisted.scene_id == "scene-isa-deadline-video-v1-01"
        assert persisted.asset_type == "illustration"
        assert persisted.purpose == "Clarify the viewer's practical ISA decision."
        assert persisted.metadata == {"edited": True}
    finally:
        reopened.close()


def test_assets_are_immutable_versions_scoped_to_one_asset_spec(tmp_path) -> None:
    """Asset records remain distinct immutable versions without a current-state flag."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        asset_spec = repository.create_asset_spec(
            "asset-spec-isa-asset-test-v1",
            "scene-isa-deadline-video-v1-01",
            "prop",
            "Support a practical decision.",
            "A test envelope prop.",
            "Provider-neutral envelope prop prompt.",
        )
        other_spec = repository.create_asset_spec(
            "asset-spec-isa-asset-test-v2",
            "scene-isa-deadline-video-v1-02",
            "graphic",
            "Support a decision check.",
            "A test calendar graphic.",
            "Provider-neutral calendar graphic prompt.",
        )
        version_one = repository.create_asset(
            "asset-isa-test-v1",
            asset_spec.id,
            1,
            "assets/isa-envelope-v1.png",
            "image/png",
            "manual",
            {"colour": "blue"},
        )
        version_two = repository.create_asset(
            "asset-isa-test-v2",
            asset_spec.id,
            2,
            "assets/isa-envelope-v2.png",
            "image/png",
            "generated",
        )
        other_version_one = repository.create_asset(
            "asset-isa-other-test-v1",
            other_spec.id,
            1,
            "assets/isa-calendar-v1.svg",
            "image/svg+xml",
            "manual",
        )
        assert repository.get_asset(version_one.id) == version_one
        assert repository.list_assets_for_asset_spec(asset_spec.id) == [version_one, version_two]
        assert repository.list_assets_for_asset_spec(other_spec.id) == [other_version_one]
        try:
            repository.create_asset(
                "asset-isa-test-duplicate-v1",
                asset_spec.id,
                1,
                "assets/duplicate.png",
                "image/png",
                "manual",
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("An AssetSpec accepted a duplicate Asset version.")
        for invalid_version in (0, -1, "1"):
            try:
                repository.create_asset(
                    f"asset-isa-invalid-version-{invalid_version}",
                    asset_spec.id,
                    invalid_version,
                    "assets/invalid.png",
                    "image/png",
                    "manual",
                )
            except ValueError:
                pass
            else:
                raise AssertionError("An Asset accepted a non-positive or non-integer version.")
        assert not hasattr(repository, "update_asset")
        try:
            repository.create_asset(
                "asset-isa-missing-spec-v1",
                "missing-asset-spec",
                1,
                "assets/missing.png",
                "image/png",
                "manual",
            )
        except KeyError as error:
            assert error.args == ("missing-asset-spec",)
        else:
            raise AssertionError("An Asset was created without an AssetSpec.")
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert [
            (asset.id, asset.version, asset.storage_path)
            for asset in reopened.list_assets_for_asset_spec("asset-spec-isa-asset-test-v1")
        ] == [
            ("asset-isa-test-v1", 1, "assets/isa-envelope-v1.png"),
            ("asset-isa-test-v2", 2, "assets/isa-envelope-v2.png"),
        ]
    finally:
        reopened.close()


def test_asset_spec_seed_is_idempotent_and_restores_missing_requirements(tmp_path) -> None:
    """Startup restores only missing AssetSpecs and never creates seeded Asset outputs."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        edited_spec = repository.get_asset_spec("asset-spec-isa-scene-01-kitchen-background-v1")
        repository.update_asset_spec(
            replace(edited_spec, purpose="Founder-edited kitchen environment purpose.")
        )
        edited_scene = repository.get_scene("scene-isa-deadline-video-v1-01")
        repository.update_scene(replace(edited_scene, visual_intent="Founder-edited Scene intent."))
        with repository.connection:
            repository.connection.execute(
                "DELETE FROM asset_specs WHERE id = ?",
                ("asset-spec-isa-scene-03-decision-tree-v1",),
            )
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert reopened.connection.execute("SELECT COUNT(*) FROM asset_specs").fetchone()[0] == 5
        assert reopened.connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 0
        assert reopened.get_asset_spec("asset-spec-isa-scene-01-kitchen-background-v1").purpose == (
            "Founder-edited kitchen environment purpose."
        )
        assert reopened.get_scene("scene-isa-deadline-video-v1-01").visual_intent == (
            "Founder-edited Scene intent."
        )
        assert reopened.get_asset_spec("asset-spec-isa-scene-03-decision-tree-v1").asset_type == (
            "graphic"
        )
        assert reopened.get_opportunity("uk-isa-rules").title
        assert reopened.get_research_pack("research-pack-isa-deadline-v1").version == 1
        assert reopened.get_editorial_angle("editorial-angle-isa-decision-tree-v1").id
        assert reopened.get_content_piece("content-piece-isa-deadline-video-v1").id
        assert reopened.get_script("script-isa-deadline-video-v1").version == 1
        assert reopened.get_visual_plan("visual-plan-isa-deadline-video-v1").id
    finally:
        reopened.close()


def test_generation_execution_failure_is_immutable_and_validated(tmp_path) -> None:
    """Failed terminal attempts retain validated immutable provenance without an Asset."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-01-kitchen-background-v1")
        snapshot = {
            "schema_version": 1,
            "asset_spec_id": asset_spec.id,
            "scene_id": asset_spec.scene_id,
        }
        generation_input = {"schema_version": 1, "asset_type": "environment", "prompt": "Test"}
        failed = repository.create_failed_generation_execution(
            "generation-execution-failure-v1",
            asset_spec.id,
            snapshot,
            generation_input,
            " test-generator ",
            provider_key="test-provider",
            error_code="provider_rejected",
            error_message="The provider rejected this deterministic test.",
            response_metadata={"status": 400},
        )
        assert failed.generator_key == "test-generator"
        assert failed.outcome == "failed"
        assert repository.get_asset_for_generation_execution(failed.id) is None
        assert repository.list_generation_executions_for_asset_spec(asset_spec.id) == [failed]
        assert not hasattr(repository, "update_generation_execution")
        for invalid_outcome in ("queued", "", "succeeded "):
            try:
                (
                    repository.create_failed_generation_execution(
                        f"invalid-outcome-{invalid_outcome or 'empty'}",
                        asset_spec.id,
                        snapshot,
                        generation_input,
                        "test-generator",
                        response_metadata={},
                    )
                    if invalid_outcome == "failed"
                    else repository._insert_generation_execution(
                        f"invalid-outcome-{invalid_outcome or 'empty'}",
                        asset_spec.id,
                        snapshot,
                        generation_input,
                        "test-generator",
                        invalid_outcome,
                        None,
                        None,
                        None,
                        None,
                        None,
                        {},
                    )
                )
            except ValueError:
                pass
            else:
                raise AssertionError("An invalid GenerationExecution outcome was accepted.")
        for invalid_generator_key in ("", "   "):
            try:
                repository.create_failed_generation_execution(
                    f"invalid-generator-{len(invalid_generator_key)}",
                    asset_spec.id,
                    snapshot,
                    generation_input,
                    invalid_generator_key,
                )
            except ValueError:
                pass
            else:
                raise AssertionError("An empty GenerationExecution generator key was accepted.")
    finally:
        repository.close()


def test_generation_service_persists_one_asset_and_frozen_provenance(tmp_path) -> None:
    """One successful synchronous generation creates one linked immutable Asset."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    generator = FakeImageGenerator()
    storage_root = tmp_path / "assets"
    service = GenerationService(repository, generator, LocalAssetStorage(storage_root))
    try:
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-01-kitchen-background-v1")
        result = service.generate_asset_spec(asset_spec.id)
        assert result.execution.outcome == "succeeded"
        assert result.asset is not None
        assert result.asset.asset_spec_id == result.execution.asset_spec_id == asset_spec.id
        assert result.asset.generation_execution_id == result.execution.id
        assert result.asset.version == 1
        stored = storage_root / result.asset.storage_path
        assert stored.read_bytes() == b"deterministic png bytes"
        repository.update_asset_spec(
            replace(asset_spec, generation_prompt="Founder-edited prompt after execution.")
        )
        persisted = repository.get_generation_execution(result.execution.id)
        assert persisted.asset_spec_snapshot["generation_prompt"] == asset_spec.generation_prompt
        assert persisted.generation_input["prompt"] == asset_spec.generation_prompt
        second = service.generate_asset_spec(asset_spec.id)
        assert second.asset is not None
        assert second.asset.version == 2
        assert repository.get_asset_for_generation_execution(second.execution.id) == second.asset
        try:
            with repository.connection:
                repository.connection.execute(
                    "UPDATE assets SET generation_execution_id = ? WHERE id = ?",
                    (result.execution.id, second.asset.id),
                )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("One GenerationExecution linked to multiple Assets.")
        manual = repository.create_asset(
            "manual-asset-after-generation-v1",
            asset_spec.id,
            3,
            "manual.png",
            "image/png",
            "manual",
        )
        assert manual.generation_execution_id is None
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert reopened.get_asset_for_generation_execution(result.execution.id) is not None
        assert reopened.get_generation_execution(result.execution.id).outcome == "succeeded"
    finally:
        reopened.close()


def test_seeded_character_asset_spec_generates_with_same_spec_provenance(tmp_path) -> None:
    """The recurring persisted hamster is an executable still-image AssetSpec."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        assert asset_spec.asset_type == "character"
        result = GenerationService(
            repository, FakeImageGenerator(), LocalAssetStorage(tmp_path / "assets")
        ).generate_asset_spec(asset_spec.id)
        assert result.execution.outcome == "succeeded"
        assert result.asset is not None
        assert result.execution.asset_spec_id == asset_spec.id
        assert result.asset.asset_spec_id == asset_spec.id
        assert result.asset.generation_execution_id == result.execution.id
        assert len(repository.list_generation_executions_for_asset_spec(asset_spec.id)) == 1
        assert repository.get_asset_for_generation_execution(result.execution.id) == result.asset
    finally:
        repository.close()


def test_generation_service_records_generator_and_storage_failures_without_assets(tmp_path) -> None:
    """Expected invoked-boundary failures are durable failures, never fake success."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    asset_spec_id = "asset-spec-isa-scene-01-kitchen-background-v1"
    try:
        generator_failure = GenerationService(
            repository,
            FakeImageGenerator(
                failure=GenerationFailure(
                    "Provider rejected the request.",
                    error_code="rejected",
                    provider_key="fake-provider",
                    model_key="fake-model-v1",
                )
            ),
            LocalAssetStorage(tmp_path / "assets"),
        ).generate_asset_spec(asset_spec_id)
        assert generator_failure.execution.outcome == "failed"
        assert generator_failure.asset is None
        assert generator_failure.execution.error_code == "rejected"
        blocked_root = tmp_path / "blocked-root"
        blocked_root.write_text("not a directory")
        storage_failure = GenerationService(
            repository, FakeImageGenerator(), LocalAssetStorage(blocked_root)
        ).generate_asset_spec(asset_spec_id)
        assert storage_failure.execution.outcome == "failed"
        assert storage_failure.execution.error_code == "storage_failure"
        assert storage_failure.asset is None
        assert repository.connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 0
    finally:
        repository.close()


def test_generation_service_rejects_unsupported_asset_types_before_history(tmp_path) -> None:
    """Open-ended future AssetSpec types cannot create execution history prematurely."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        unsupported = repository.create_asset_spec(
            "asset-spec-unsupported-audio-v1",
            "scene-isa-deadline-video-v1-01",
            "audio",
            "Future audio requirement.",
            "A future audio asset.",
            "Generate future audio.",
        )
        service = GenerationService(
            repository, FakeImageGenerator(), LocalAssetStorage(tmp_path / "assets")
        )
        try:
            service.generate_asset_spec(unsupported.id)
        except UnsupportedGenerationType:
            pass
        else:
            raise AssertionError("An unsupported AssetSpec type crossed the generator boundary.")
        assert repository.list_generation_executions_for_asset_spec(unsupported.id) == []
    finally:
        repository.close()


def test_local_asset_storage_preserves_immutable_paths_and_rejects_traversal(tmp_path) -> None:
    """Storage writes under its root and never overwrites a pre-existing immutable file."""

    storage = LocalAssetStorage(tmp_path / "assets")
    stored = storage.write("asset-spec-safe-v1", "asset-safe-v1", b"first", "image/png")
    assert stored.read_bytes() == b"first"
    try:
        storage.write("asset-spec-safe-v1", "asset-safe-v1", b"second", "image/png")
    except AssetStorageFailure as error:
        assert "already exists" in str(error)
    else:
        raise AssertionError("Atlas storage overwrote an immutable Asset file.")
    assert stored.read_bytes() == b"first"
    try:
        storage.write("..", "asset-safe-v2", b"escape", "image/png")
    except AssetStorageFailure as error:
        assert "safe path components" in str(error)
    else:
        raise AssertionError("Atlas storage allowed traversal outside its configured root.")


def test_generation_service_removes_new_file_when_database_persistence_fails(tmp_path) -> None:
    """A database failure compensates by removing only the newly written artifact file."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    storage_root = tmp_path / "assets"
    service = GenerationService(repository, FakeImageGenerator(), LocalAssetStorage(storage_root))
    original = repository.record_successful_generation

    def fail_persistence(*args: object, **kwargs: object) -> object:
        raise sqlite3.DatabaseError("deterministic persistence failure")

    repository.record_successful_generation = fail_persistence  # type: ignore[method-assign]
    try:
        try:
            service.generate_asset_spec("asset-spec-isa-scene-01-kitchen-background-v1")
        except sqlite3.DatabaseError:
            pass
        else:
            raise AssertionError(
                "A database failure was silently converted into generation success."
            )
        assert list(storage_root.rglob("*.png")) == []
    finally:
        repository.record_successful_generation = original  # type: ignore[method-assign]
        repository.close()


def test_openai_adapter_requires_configured_key_without_network() -> None:
    """The concrete adapter fails clearly before any request when no secret is configured."""

    generator = OpenAIImageGenerator(api_key="")
    try:
        generator.generate(GenerationInput("environment", "Test prompt", None, {}))
    except GenerationFailure as error:
        assert error.error_code == "missing_api_key"
        assert error.provider_key == "openai"
    else:
        raise AssertionError("OpenAI image generation ran without a configured API key.")
