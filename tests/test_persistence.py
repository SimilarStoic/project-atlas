"""Tests for Atlas persistence through the v0.7 asset-spec and asset foundation."""

import json
import sqlite3
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from project_atlas.generation import (
    AssetStorageFailure,
    GeneratedArtifact,
    GenerationFailure,
    GenerationInput,
    GenerationService,
    InvalidCharacterReferenceBootstrap,
    LocalAssetStorage,
    MissingCharacterReferenceSet,
    MissingProviderConfiguration,
    MissingVisualStyleProfile,
    OpenAIImageGenerator,
    PromptComposer,
    ReferenceImage,
    UnsupportedGenerationType,
    asset_spec_snapshot,
)
from project_atlas.persistence import MIGRATIONS, AtlasRepository, CharacterProfile


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


def generate_character_asset(repository: AtlasRepository, storage_root, asset_spec_id: str):
    """Generate one deterministic character Asset through the grounded production path."""

    asset_spec = repository.get_asset_spec(asset_spec_id)
    ensure_character_reference_set(repository, storage_root, asset_spec.character_profile_id)

    result = GenerationService(
        repository, FakeImageGenerator(), LocalAssetStorage(storage_root)
    ).generate_asset_spec(asset_spec_id)
    assert result.asset is not None
    return result


def ensure_character_reference_set(
    repository: AtlasRepository,
    storage_root,
    profile_id: str = "character-profile-similarstoic-hamster-core-v1",
) -> str:
    """Create v0.12-style historical character evidence for focused v0.13 tests."""

    existing = repository.get_latest_character_reference_set(profile_id)
    if existing is not None:
        return existing.id
    profile = repository.get_character_profile(profile_id)
    spec_id = f"asset-spec-test-reference-basis-{profile.id}"
    try:
        asset_spec = repository.get_asset_spec(spec_id)
    except KeyError:
        asset_spec = repository.create_asset_spec(
            spec_id,
            "scene-isa-deadline-video-v1-01",
            "character",
            "Historical canonical character-reference basis.",
            "A historical generated character reference used by v0.13 tests.",
            "Illustrate the canonical hamster reference basis.",
            character_profile_id=profile.id,
        )
    storage = LocalAssetStorage(storage_root)
    asset_id = f"asset-test-reference-basis-{profile.id}"
    stored = storage.write(asset_spec.id, asset_id, b"historical reference png bytes", "image/png")
    style = repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v2")
    input_payload = PromptComposer().compose(asset_spec, style, profile).payload()
    repository.record_successful_generation(
        f"generation-execution-test-reference-basis-{profile.id}",
        asset_id,
        asset_spec.id,
        asset_spec_snapshot(asset_spec),
        input_payload,
        "historical-test-generator",
        storage.relative_path(stored),
        "image/png",
        visual_style_profile_id=style.id,
        character_profile_id=profile.id,
        provider_key="historical-test-provider",
        model_key="historical-test-model",
        content_digest=sha256(b"historical reference png bytes").hexdigest(),
    )
    return repository.create_character_reference_set(
        f"character-reference-set-test-basis-{profile.id}", profile.id, [asset_id]
    ).id


def test_fresh_database_migrates_and_seeds_discovery_through_asset_specs(tmp_path) -> None:
    """Fresh startup applies all migrations and creates the scoped seed data."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        assert [
            row["version"]
            for row in repository.connection.execute("SELECT version FROM schema_migrations")
        ] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        decision_table_sql = repository.connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='idea_gate_decisions'"
        ).fetchone()["sql"]
        assert "UNIQUE" in decision_table_sql
        assert "Proceed', 'Reject', 'Steer" in decision_table_sql
        assert {
            row["name"]
            for row in repository.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND name LIKE 'idx_idea_gate_%'"
            )
        } == {
            "idx_idea_gate_review_snapshots_opportunity_created",
            "idx_idea_gate_decisions_snapshot_created",
        }
        readiness_table_sql = repository.connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' "
            "AND name='research_readiness_assessments'"
        ).fetchone()["sql"]
        assert "NeedsMoreResearch" in readiness_table_sql
        assert repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name='idx_research_readiness_assessments_pack_created'"
        ).fetchone()
        assert len(repository.discover_payload()) == 6
        assert repository.get_subject("subject-isa").name == "ISA"
        assert len(repository.list_research_packs("uk-isa-rules")) == 1
        assert repository.list_research_readiness_assessments("research-pack-isa-deadline-v1") == []
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
        assert [
            (profile.id, profile.version) for profile in repository.list_visual_style_profiles()
        ] == [
            ("visual-style-profile-similarstoic-core-v1", 1),
            ("visual-style-profile-similarstoic-core-v2", 2),
            ("visual-style-profile-similarstoic-core-v3", 3),
        ]
        assert [
            (profile.id, profile.version) for profile in repository.list_character_profiles()
        ] == [("character-profile-similarstoic-hamster-core-v1", 1)]
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


def test_research_readiness_assessments_freeze_exact_evidence_and_preserve_history(
    tmp_path,
) -> None:
    """Readiness records snapshot only their pack's linked evidence and never mutate."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        repository.create_opportunity(
            "readiness-opportunity",
            "Readiness opportunity",
            "A readiness test opportunity.",
            "It supports a frozen evidence test.",
            1,
            "proposed",
        )
        pack = repository.create_research_pack(
            "research-pack-readiness-v1",
            "readiness-opportunity",
            1,
            "A ResearchPack whose evidence state is frozen for readiness.",
            "2026-08-17",
        )
        claim_z = repository.create_claim(
            "claim-z-readiness",
            pack.id,
            "The later identifier must not control snapshot ordering.",
            "fact",
            "low",
            "current",
            "reviewed",
            "Initially reviewed.",
        )
        claim_a = repository.create_claim(
            "claim-a-readiness",
            pack.id,
            "The earlier identifier must appear first in a readiness snapshot.",
            "fact",
            "medium",
            "current",
            "reviewed",
            "Initially reviewed.",
            "2026-08-17T00:00:00+00:00",
        )
        linked_source_z = repository.create_source(
            "source-z-readiness",
            "report",
            "Linked source Z",
            "Atlas test publisher",
            "https://example.test/readiness/z",
            "2026-08-17T00:00:00+00:00",
        )
        linked_source_a = repository.create_source(
            "source-a-readiness",
            "report",
            "Linked source A",
            "Atlas test publisher",
            "https://example.test/readiness/a",
            "2026-08-17T00:00:00+00:00",
            publication_date="2026-08-01",
            jurisdiction="GB",
        )
        unrelated_source = repository.create_source(
            "source-unrelated-readiness",
            "report",
            "Unrelated source",
            "Atlas test publisher",
            "https://example.test/readiness/unrelated",
            "2026-08-17T00:00:00+00:00",
        )
        repository.create_opportunity(
            "unrelated-readiness-opportunity",
            "Unrelated readiness opportunity",
            "This must not enter another pack's snapshot.",
            "Isolation test.",
            1,
            "proposed",
        )
        unrelated_pack = repository.create_research_pack(
            "research-pack-unrelated-readiness-v1",
            "unrelated-readiness-opportunity",
            1,
            "An unrelated ResearchPack.",
        )
        unrelated_claim = repository.create_claim(
            "claim-unrelated-readiness",
            unrelated_pack.id,
            "This Claim must not enter the assessed pack.",
            "fact",
            "low",
            "current",
            "unreviewed",
            "Unrelated.",
        )
        repository.link_claim_evidence(claim_z.id, linked_source_z.id, "supports", "p. 8")
        repository.link_claim_evidence(claim_a.id, linked_source_a.id, "supports", "p. 2")

        assert repository.list_research_readiness_assessments(pack.id) == []
        frozen_before = repository.build_research_readiness_evidence_state(pack.id)
        assert [claim["id"] for claim in frozen_before["claims"]] == [claim_a.id, claim_z.id]
        assert unrelated_claim.id not in {claim["id"] for claim in frozen_before["claims"]}
        assert [source["id"] for source in frozen_before["sources"]] == [
            linked_source_a.id,
            linked_source_z.id,
        ]
        assert unrelated_source.id not in {source["id"] for source in frozen_before["sources"]}
        assert [
            (link["claim_id"], link["source_id"]) for link in frozen_before["claim_evidence"]
        ] == [(claim_a.id, linked_source_a.id), (claim_z.id, linked_source_z.id)]
        assert frozen_before == repository.build_research_readiness_evidence_state(pack.id)

        first = repository.create_research_readiness_assessment(
            "readiness-assessment-a",
            pack.id,
            "NeedsMoreResearch",
            {"summary": "One source needs corroboration.", "material_findings": [claim_a.id]},
            "readiness-policy-v1",
            "test",
            "persistence-test",
            "v1",
        )
        assert first.schema_version == 1
        assert first.frozen_evidence_state == frozen_before
        assert first.findings["material_findings"] == [claim_a.id]

        repository.update_claim(
            replace(claim_a, text="A later live Claim edit must not rewrite Assessment A.")
        )
        repository.link_claim_evidence(claim_z.id, linked_source_a.id, "context", "p. 10")
        late_source = repository.create_source(
            "source-late-readiness",
            "report",
            "A source added after Assessment A",
            "Atlas test publisher",
            "https://example.test/readiness/late",
            "2026-08-17T00:00:00+00:00",
        )
        repository.link_claim_evidence(claim_z.id, late_source.id, "supports", "p. 11")
        second = repository.create_research_readiness_assessment(
            "readiness-assessment-b",
            pack.id,
            "Ready",
            {"summary": "The current evidence is sufficient.", "material_findings": []},
            "readiness-policy-v1",
            "manual",
            "founder-review-fixture",
            "v1",
        )
        assert (
            repository.get_research_readiness_assessment(first.id).frozen_evidence_state
            == frozen_before
        )
        assert second.frozen_evidence_state["claims"][0]["text"] == (
            "A later live Claim edit must not rewrite Assessment A."
        )
        assert second.frozen_evidence_state != first.frozen_evidence_state
        assert late_source.id in {
            source["id"] for source in second.frozen_evidence_state["sources"]
        }
        assert [
            assessment.id for assessment in repository.list_research_readiness_assessments(pack.id)
        ] == [
            first.id,
            second.id,
        ]

        with pytest.raises(ValueError, match="outcome"):
            repository.create_research_readiness_assessment(
                "readiness-assessment-invalid",
                pack.id,
                "ready",
                {"summary": "No."},
                "v1",
                "test",
                "x",
                "v1",
            )
        with pytest.raises(ValueError, match="findings"):
            repository.create_research_readiness_assessment(
                "readiness-assessment-empty-findings",
                pack.id,
                "Blocked",
                {},
                "v1",
                "test",
                "x",
                "v1",
            )
        with pytest.raises(ValueError, match="meaningful"):
            repository.create_research_readiness_assessment(
                "readiness-assessment-null-findings",
                pack.id,
                "Blocked",
                {"summary": None},
                "v1",
                "test",
                "x",
                "v1",
            )
        with pytest.raises(ValueError, match="already exists"):
            repository.create_research_readiness_assessment(
                first.id, pack.id, "Blocked", {"summary": "No."}, "v1", "test", "x", "v1"
            )
        with pytest.raises(sqlite3.IntegrityError), repository.connection:
            repository.connection.execute(
                "INSERT INTO research_readiness_assessments "
                "(id, research_pack_id, assessment_schema_version, frozen_evidence_state_json, "
                "outcome, findings_json, policy_version, producer_kind, producer_identifier, "
                "producer_implementation_version, created_at) "
                "VALUES (?, ?, 1, '{}', ?, '{}', ?, ?, ?, ?, ?)",
                (
                    "readiness-assessment-db-invalid",
                    pack.id,
                    "Other",
                    "v1",
                    "test",
                    "x",
                    "v1",
                    "now",
                ),
            )
        with pytest.raises(sqlite3.IntegrityError), repository.connection:
            repository.connection.execute("DELETE FROM research_packs WHERE id = ?", (pack.id,))
    finally:
        repository.close()


def test_editorial_angle_readiness_initiation_preserves_exact_immutable_provenance(
    tmp_path,
) -> None:
    """v0.18 creates only explicitly Ready-assessed Angles without changing older behavior."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        repository.create_opportunity(
            "angle-opportunity-a", "A", "Summary", "Why now", 1, "proposed"
        )
        repository.create_opportunity(
            "angle-opportunity-b", "B", "Summary", "Why now", 1, "proposed"
        )
        pack_a = repository.create_research_pack(
            "angle-research-pack-a", "angle-opportunity-a", 1, "Pack A"
        )
        pack_b = repository.create_research_pack(
            "angle-research-pack-b", "angle-opportunity-b", 1, "Pack B"
        )

        def assessment(assessment_id: str, pack_id: str, outcome: str):
            return repository.create_research_readiness_assessment(
                assessment_id,
                pack_id,
                outcome,
                {"summary": f"{outcome} assessment."},
                "readiness-policy-v1",
                "test",
                "persistence-test",
                "v1",
            )

        needs_more = assessment("angle-needs-more", pack_a.id, "NeedsMoreResearch")
        blocked = assessment("angle-blocked", pack_a.id, "Blocked")
        ready_a = assessment("angle-ready-a", pack_a.id, "Ready")
        ready_b = assessment("angle-ready-b", pack_a.id, "Ready")
        ready_other_pack = assessment("angle-ready-other", pack_b.id, "Ready")
        assessment_count = repository.connection.execute(
            "SELECT COUNT(*) FROM research_readiness_assessments"
        ).fetchone()[0]
        original_status = repository.get_opportunity(pack_a.opportunity_id).status

        legacy = repository.create_editorial_angle(
            "angle-legacy",
            pack_a.opportunity_id,
            pack_a.id,
            "Legacy",
            "Thesis",
            "Promise",
            "Frame",
            ["One"],
        )
        assert legacy.research_readiness_assessment_id is None
        assert (
            repository.get_editorial_angle(
                "editorial-angle-isa-decision-tree-v1"
            ).research_readiness_assessment_id
            is None
        )

        arguments = (
            "angle-invalid",
            pack_a.opportunity_id,
            pack_a.id,
            "Title",
            "Thesis",
            "Promise",
            "Frame",
            ["One"],
        )
        with pytest.raises(ValueError, match="Ready"):
            repository.create_editorial_angle_under_research_readiness(
                arguments[0], arguments[1], arguments[2], needs_more.id, *arguments[3:]
            )
        with pytest.raises(ValueError, match="Ready"):
            repository.create_editorial_angle_under_research_readiness(
                arguments[0], arguments[1], arguments[2], blocked.id, *arguments[3:]
            )
        with pytest.raises(KeyError):
            repository.create_editorial_angle_under_research_readiness(
                arguments[0], arguments[1], arguments[2], "missing-assessment", *arguments[3:]
            )
        with pytest.raises(ValueError, match="ResearchPack"):
            repository.create_editorial_angle_under_research_readiness(
                arguments[0], pack_a.opportunity_id, pack_b.id, ready_other_pack.id, *arguments[3:]
            )
        with pytest.raises(ValueError, match="ResearchReadinessAssessment"):
            repository.create_editorial_angle_under_research_readiness(
                arguments[0], pack_a.opportunity_id, pack_a.id, ready_other_pack.id, *arguments[3:]
            )
        with pytest.raises(KeyError):
            repository.create_editorial_angle_under_research_readiness(
                arguments[0], "missing-opportunity", pack_a.id, ready_a.id, *arguments[3:]
            )
        with pytest.raises(KeyError):
            repository.create_editorial_angle_under_research_readiness(
                arguments[0], pack_a.opportunity_id, "missing-pack", ready_a.id, *arguments[3:]
            )

        first = repository.create_editorial_angle_under_research_readiness(
            "angle-ready-first", pack_a.opportunity_id, pack_a.id, ready_a.id, *arguments[3:]
        )
        second = repository.create_editorial_angle_under_research_readiness(
            "angle-ready-second", pack_a.opportunity_id, pack_a.id, ready_a.id, *arguments[3:]
        )
        later = repository.create_editorial_angle_under_research_readiness(
            "angle-ready-later", pack_a.opportunity_id, pack_a.id, ready_b.id, *arguments[3:]
        )
        assert first.research_readiness_assessment_id == ready_a.id
        assert second.research_readiness_assessment_id == ready_a.id
        assert later.research_readiness_assessment_id == ready_b.id
        assert (
            repository.editorial_angle_payload(first.id)["research_readiness_assessment_id"]
            == ready_a.id
        )
        assert (
            repository.connection.execute(
                "SELECT COUNT(*) FROM research_readiness_assessments"
            ).fetchone()[0]
            == assessment_count
        )

        updated = repository.update_editorial_angle(replace(first, thesis="Edited mutable thesis."))
        assert updated.research_readiness_assessment_id == ready_a.id
        with pytest.raises(ValueError, match="readiness provenance"):
            repository.update_editorial_angle(
                replace(updated, research_readiness_assessment_id=ready_b.id)
            )
        assert repository.get_opportunity(pack_a.opportunity_id).status == original_status

        claim = repository.create_claim(
            "angle-pack-a-claim",
            pack_a.id,
            "No frozen matching is required.",
            "fact",
            "low",
            "current",
            "reviewed",
            "",
        )
        repository.link_claim_to_editorial_angle(first.id, claim.id, "core")
        other_claim = repository.create_claim(
            "angle-pack-b-claim",
            pack_b.id,
            "Different pack.",
            "fact",
            "low",
            "current",
            "reviewed",
            "",
        )
        with pytest.raises(ValueError, match="Angle's ResearchPack"):
            repository.link_claim_to_editorial_angle(first.id, other_claim.id, "supporting")
    finally:
        repository.close()


def test_content_piece_readiness_initiation_preserves_exact_angle_lineage(tmp_path) -> None:
    """v0.19 creates ContentPieces only from exact Ready-authorized Angle provenance."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        opportunity_id = "content-piece-readiness-opportunity"
        other_opportunity_id = "content-piece-readiness-other-opportunity"
        repository.create_opportunity(
            opportunity_id, "Opportunity", "Summary", "Why now", 1, "proposed"
        )
        repository.create_opportunity(
            other_opportunity_id, "Other", "Summary", "Why now", 1, "proposed"
        )
        research_pack = repository.create_research_pack(
            "content-piece-readiness-pack", opportunity_id, 1, "Research pack"
        )
        other_research_pack = repository.create_research_pack(
            "content-piece-readiness-other-pack", other_opportunity_id, 2, "Other pack"
        )

        def assessment(assessment_id: str, pack_id: str, outcome: str):
            return repository.create_research_readiness_assessment(
                assessment_id,
                pack_id,
                outcome,
                {"summary": f"{outcome} assessment."},
                "readiness-policy-v1",
                "test",
                "persistence-test",
                "v1",
            )

        ready = assessment("content-piece-ready", research_pack.id, "Ready")
        blocked = assessment("content-piece-blocked", research_pack.id, "Blocked")
        other_ready = assessment("content-piece-other-ready", other_research_pack.id, "Ready")
        angle_fields = (
            "A readiness-authorized Angle",
            "Exact lineage is retained.",
            "Understand the provenance boundary.",
            "A focused explainer.",
            ["Ready provenance is exact."],
        )
        eligible_angle = repository.create_editorial_angle_under_research_readiness(
            "content-piece-eligible-angle",
            opportunity_id,
            research_pack.id,
            ready.id,
            *angle_fields,
        )
        legacy_angle = repository.create_editorial_angle(
            "content-piece-legacy-angle", opportunity_id, research_pack.id, *angle_fields
        )
        original_status = repository.get_opportunity(opportunity_id).status
        assessment_count = repository.connection.execute(
            "SELECT COUNT(*) FROM research_readiness_assessments"
        ).fetchone()[0]

        first = repository.create_content_piece_under_editorial_angle_readiness(
            "content-piece-ready-first",
            opportunity_id,
            eligible_angle.id,
            "video",
            "A deliberately initiated ContentPiece.",
            {"source": "v0.19-test"},
        )
        second = repository.create_content_piece_under_editorial_angle_readiness(
            "content-piece-ready-second",
            opportunity_id,
            eligible_angle.id,
            "article",
            "A second deliberately initiated ContentPiece.",
        )
        assert first.opportunity_id == opportunity_id
        assert first.editorial_angle_id == eligible_angle.id
        assert (
            repository.get_editorial_angle(
                first.editorial_angle_id
            ).research_readiness_assessment_id
            == ready.id
        )
        assert second.editorial_angle_id == eligible_angle.id
        assert len(repository.list_content_pieces_for_editorial_angle(eligible_angle.id)) == 2
        assert repository.get_opportunity(opportunity_id).status == original_status
        assert (
            repository.connection.execute(
                "SELECT COUNT(*) FROM research_readiness_assessments"
            ).fetchone()[0]
            == assessment_count
        )
        assert (
            repository.connection.execute(
                "SELECT COUNT(*) FROM scripts WHERE content_piece_id IN (?, ?)",
                (first.id, second.id),
            ).fetchone()[0]
            == 0
        )

        with pytest.raises(ValueError, match="same Opportunity"):
            repository.create_content_piece_under_editorial_angle_readiness(
                "content-piece-wrong-opportunity",
                other_opportunity_id,
                eligible_angle.id,
                "video",
                "Wrong Opportunity.",
            )
        with pytest.raises(ValueError, match="readiness provenance"):
            repository.create_content_piece_under_editorial_angle_readiness(
                "content-piece-legacy-rejected",
                opportunity_id,
                legacy_angle.id,
                "video",
                "Legacy Angle.",
            )
        legacy_piece = repository.create_content_piece(
            "content-piece-legacy-compatible",
            opportunity_id,
            legacy_angle.id,
            "video",
            "Low-level compatibility remains.",
        )
        assert legacy_piece.editorial_angle_id == legacy_angle.id

        non_ready_angle = repository.create_editorial_angle(
            "content-piece-non-ready-angle", opportunity_id, research_pack.id, *angle_fields
        )
        mismatched_angle = repository.create_editorial_angle(
            "content-piece-mismatched-angle", opportunity_id, research_pack.id, *angle_fields
        )
        corrupted_pack_angle = repository.create_editorial_angle_under_research_readiness(
            "content-piece-corrupted-pack-angle",
            opportunity_id,
            research_pack.id,
            ready.id,
            *angle_fields,
        )
        missing_assessment_angle = repository.create_editorial_angle(
            "content-piece-missing-assessment-angle",
            opportunity_id,
            research_pack.id,
            *angle_fields,
        )
        missing_pack_assessment = assessment(
            "content-piece-missing-pack-assessment", research_pack.id, "Ready"
        )
        missing_pack_angle = repository.create_editorial_angle_under_research_readiness(
            "content-piece-missing-pack-angle",
            opportunity_id,
            research_pack.id,
            missing_pack_assessment.id,
            *angle_fields,
        )
        repository.connection.execute("PRAGMA foreign_keys = OFF")
        with repository.connection:
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                (blocked.id, non_ready_angle.id),
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                (other_ready.id, mismatched_angle.id),
            )
            repository.connection.execute(
                "UPDATE research_packs SET opportunity_id = ? WHERE id = ?",
                (other_opportunity_id, research_pack.id),
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                ("missing-assessment", missing_assessment_angle.id),
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_pack_id = ? WHERE id = ?",
                ("missing-pack", missing_pack_angle.id),
            )
            repository.connection.execute(
                "UPDATE research_readiness_assessments SET research_pack_id = ? WHERE id = ?",
                ("missing-pack", missing_pack_assessment.id),
            )
        repository.connection.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(ValueError, match="Only a Ready"):
            repository.create_content_piece_under_editorial_angle_readiness(
                "content-piece-non-ready-rejected",
                opportunity_id,
                non_ready_angle.id,
                "video",
                "Non-Ready provenance.",
            )
        with pytest.raises(ValueError, match="ResearchReadinessAssessment"):
            repository.create_content_piece_under_editorial_angle_readiness(
                "content-piece-mismatched-rejected",
                opportunity_id,
                mismatched_angle.id,
                "video",
                "Mismatched provenance.",
            )
        with pytest.raises(ValueError, match="ResearchPack must belong"):
            repository.create_content_piece_under_editorial_angle_readiness(
                "content-piece-corrupted-pack-rejected",
                opportunity_id,
                corrupted_pack_angle.id,
                "video",
                "Corrupted Pack lineage.",
            )
        with pytest.raises(ValueError, match="existing ResearchReadinessAssessment"):
            repository.create_content_piece_under_editorial_angle_readiness(
                "content-piece-missing-assessment-rejected",
                opportunity_id,
                missing_assessment_angle.id,
                "video",
                "Missing assessment lineage.",
            )
        with pytest.raises(ValueError, match="existing ResearchPack"):
            repository.create_content_piece_under_editorial_angle_readiness(
                "content-piece-missing-pack-rejected",
                opportunity_id,
                missing_pack_angle.id,
                "video",
                "Missing Pack lineage.",
            )
        with pytest.raises(KeyError):
            repository.create_content_piece_under_editorial_angle_readiness(
                "content-piece-missing-opportunity",
                "missing-opportunity",
                eligible_angle.id,
                "video",
                "Missing Opportunity.",
            )
        with pytest.raises(KeyError):
            repository.create_content_piece_under_editorial_angle_readiness(
                "content-piece-missing-angle",
                opportunity_id,
                "missing-angle",
                "video",
                "Missing Angle.",
            )
    finally:
        repository.close()


def test_script_readiness_initiation_appends_immutable_versions_under_exact_lineage(
    tmp_path,
) -> None:
    """v0.20 appends Scripts only through a ContentPiece's exact Ready lineage."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        opportunity_id = "script-readiness-opportunity"
        other_opportunity_id = "script-readiness-other-opportunity"
        repository.create_opportunity(
            opportunity_id, "Opportunity", "Summary", "Why now", 1, "proposed"
        )
        repository.create_opportunity(
            other_opportunity_id, "Other", "Summary", "Why now", 1, "proposed"
        )
        research_pack = repository.create_research_pack(
            "script-readiness-pack", opportunity_id, 1, "Research pack"
        )
        other_research_pack = repository.create_research_pack(
            "script-readiness-other-pack", other_opportunity_id, 1, "Other research pack"
        )

        def assessment(assessment_id: str, pack_id: str, outcome: str):
            return repository.create_research_readiness_assessment(
                assessment_id,
                pack_id,
                outcome,
                {"summary": f"{outcome} assessment."},
                "readiness-policy-v1",
                "test",
                "persistence-test",
                "v1",
            )

        def angle(angle_id: str, pack_id: str, assessment_id: str | None = None):
            fields = (
                "A readiness-authorized Angle",
                "Exact stored provenance authorizes drafting.",
                "Understand the lineage.",
                "A focused explainer.",
                ["Provenance is exact."],
            )
            if assessment_id is None:
                return repository.create_editorial_angle(angle_id, opportunity_id, pack_id, *fields)
            return repository.create_editorial_angle_under_research_readiness(
                angle_id, opportunity_id, pack_id, assessment_id, *fields
            )

        ready = assessment("script-ready", research_pack.id, "Ready")
        blocked = assessment("script-blocked", research_pack.id, "Blocked")
        other_ready = assessment("script-other-ready", other_research_pack.id, "Ready")
        eligible_angle = angle("script-eligible-angle", research_pack.id, ready.id)
        eligible_piece = repository.create_content_piece_under_editorial_angle_readiness(
            "script-eligible-piece",
            opportunity_id,
            eligible_angle.id,
            "video",
            "An eligible ContentPiece.",
        )
        original_piece = repository.get_content_piece(eligible_piece.id)
        original_angle = repository.get_editorial_angle(eligible_angle.id)
        original_assessment = repository.get_research_readiness_assessment(ready.id)
        original_pack = repository.get_research_pack(research_pack.id)
        original_visual_plan_count = len(
            repository.list_visual_plans_for_content_piece(eligible_piece.id)
        )

        first = repository.create_script_under_content_piece_readiness(
            "script-eligible-v1",
            eligible_piece.id,
            "Original complete narration.",
            {"source": "v0.20-test"},
        )
        second = repository.create_script_under_content_piece_readiness(
            "script-eligible-v2", eligible_piece.id, "Revised complete narration."
        )
        third = repository.create_script_under_content_piece_readiness(
            "script-eligible-v3", eligible_piece.id, "A third complete narration."
        )
        assert [first.version, second.version, third.version] == [1, 2, 3]
        assert [
            script.version
            for script in repository.list_scripts_for_content_piece(eligible_piece.id)
        ] == [1, 2, 3]
        assert repository.get_script(first.id).narration_text == "Original complete narration."
        assert repository.latest_script_for_content_piece(eligible_piece.id) == third
        assert all(
            script.content_piece_id == eligible_piece.id
            for script in repository.list_scripts_for_content_piece(eligible_piece.id)
        )
        assert repository.get_content_piece(eligible_piece.id) == original_piece
        assert repository.get_editorial_angle(eligible_angle.id) == original_angle
        assert repository.get_research_readiness_assessment(ready.id) == original_assessment
        assert repository.get_research_pack(research_pack.id) == original_pack
        assert (
            len(repository.list_visual_plans_for_content_piece(eligible_piece.id))
            == original_visual_plan_count
        )

        legacy_angle = angle("script-legacy-angle", research_pack.id)
        legacy_piece = repository.create_content_piece(
            "script-legacy-piece",
            opportunity_id,
            legacy_angle.id,
            "video",
            "A legacy ContentPiece.",
        )
        low_level_script = repository.create_script(
            "script-low-level-compatible",
            legacy_piece.id,
            7,
            "Compatibility Script version.",
        )
        assert low_level_script.version == 7

        blocked_angle = angle("script-blocked-angle", research_pack.id)
        blocked_piece = repository.create_content_piece(
            "script-blocked-piece", opportunity_id, blocked_angle.id, "video", "Blocked."
        )
        mismatched_angle = angle("script-mismatched-angle", research_pack.id)
        mismatched_piece = repository.create_content_piece(
            "script-mismatched-piece", opportunity_id, mismatched_angle.id, "video", "Mismatched."
        )
        missing_assessment_angle = angle("script-missing-assessment-angle", research_pack.id)
        missing_assessment_piece = repository.create_content_piece(
            "script-missing-assessment-piece",
            opportunity_id,
            missing_assessment_angle.id,
            "video",
            "Missing assessment.",
        )
        missing_angle = angle("script-missing-angle", research_pack.id)
        missing_angle_piece = repository.create_content_piece(
            "script-missing-angle-piece",
            opportunity_id,
            missing_angle.id,
            "video",
            "Missing angle.",
        )
        missing_pack = repository.create_research_pack(
            "script-missing-pack", opportunity_id, 2, "Missing-pack research."
        )
        missing_pack_ready = assessment("script-missing-pack-ready", missing_pack.id, "Ready")
        missing_pack_angle = angle(
            "script-missing-pack-angle", missing_pack.id, missing_pack_ready.id
        )
        missing_pack_piece = repository.create_content_piece_under_editorial_angle_readiness(
            "script-missing-pack-piece",
            opportunity_id,
            missing_pack_angle.id,
            "video",
            "Missing pack.",
        )
        wrong_opportunity_pack = repository.create_research_pack(
            "script-wrong-opportunity-pack", opportunity_id, 3, "Wrong-opportunity research."
        )
        wrong_opportunity_ready = assessment(
            "script-wrong-opportunity-ready", wrong_opportunity_pack.id, "Ready"
        )
        wrong_opportunity_angle = angle(
            "script-wrong-opportunity-angle", wrong_opportunity_pack.id, wrong_opportunity_ready.id
        )
        wrong_opportunity_piece = repository.create_content_piece_under_editorial_angle_readiness(
            "script-wrong-opportunity-piece",
            opportunity_id,
            wrong_opportunity_angle.id,
            "video",
            "Wrong opportunity.",
        )
        repository.connection.execute("PRAGMA foreign_keys = OFF")
        with repository.connection:
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                (blocked.id, blocked_angle.id),
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                (other_ready.id, mismatched_angle.id),
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_readiness_assessment_id = ? WHERE id = ?",
                ("missing-assessment", missing_assessment_angle.id),
            )
            repository.connection.execute(
                "DELETE FROM editorial_angles WHERE id = ?", (missing_angle.id,)
            )
            repository.connection.execute(
                "UPDATE editorial_angles SET research_pack_id = ? WHERE id = ?",
                ("missing-pack", missing_pack_angle.id),
            )
            repository.connection.execute(
                "UPDATE research_readiness_assessments SET research_pack_id = ? WHERE id = ?",
                ("missing-pack", missing_pack_ready.id),
            )
            repository.connection.execute(
                "UPDATE research_packs SET opportunity_id = ? WHERE id = ?",
                (other_opportunity_id, wrong_opportunity_pack.id),
            )
        repository.connection.execute("PRAGMA foreign_keys = ON")

        for content_piece_id, error in (
            (legacy_piece.id, "readiness provenance"),
            (blocked_piece.id, "Only a Ready"),
            (mismatched_piece.id, "ResearchReadinessAssessment"),
            (missing_assessment_piece.id, "existing ResearchReadinessAssessment"),
            (missing_angle_piece.id, "existing EditorialAngle"),
            (missing_pack_piece.id, "existing ResearchPack"),
            (wrong_opportunity_piece.id, "ResearchPack must belong"),
        ):
            with pytest.raises(ValueError, match=error):
                repository.create_script_under_content_piece_readiness(
                    f"script-rejected-{content_piece_id}", content_piece_id, "Rejected narration."
                )
        with pytest.raises(KeyError):
            repository.create_script_under_content_piece_readiness(
                "script-missing-content-piece", "missing-content-piece", "Missing ContentPiece."
            )
        table_names = {
            row[0]
            for row in repository.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert {"titles", "hooks", "script_claims", "workflow_states"}.isdisjoint(table_names)
    finally:
        repository.close()


def test_editorial_package_records_are_append_only_and_exact_under_ready_lineage(tmp_path) -> None:
    """v0.21 freezes explicit alternatives without selection, mutation, or downstream work."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        opportunity_id = "editorial-package-opportunity"
        repository.create_opportunity(
            opportunity_id, "Opportunity", "Summary", "Why now", 1, "proposed"
        )
        pack = repository.create_research_pack(
            "editorial-package-pack", opportunity_id, 1, "Research pack"
        )
        ready = repository.create_research_readiness_assessment(
            "editorial-package-ready",
            pack.id,
            "Ready",
            {"summary": "Ready for package testing."},
            "policy-v1",
            "test",
            "persistence-test",
            "v1",
        )
        fields = (
            "Ready Angle",
            "Exact readiness lineage permits editorial drafting.",
            "Understand the boundary.",
            "A focused explainer.",
            ["Lineage is exact."],
        )
        angle = repository.create_editorial_angle_under_research_readiness(
            "editorial-package-angle", opportunity_id, pack.id, ready.id, *fields
        )
        content_piece = repository.create_content_piece_under_editorial_angle_readiness(
            "editorial-package-piece",
            opportunity_id,
            angle.id,
            "video",
            "Compatibility working title",
        )
        original_piece = repository.get_content_piece(content_piece.id)
        script_v1 = repository.create_script_under_content_piece_readiness(
            "editorial-package-script-v1", content_piece.id, "Original narration."
        )
        title_v1 = repository.create_title_option_under_content_piece_readiness(
            "editorial-package-title-v1",
            content_piece.id,
            "First exact title",
            {"author": "human"},
        )
        title_v2 = repository.create_title_option_under_content_piece_readiness(
            "editorial-package-title-v2", content_piece.id, "Revised exact title"
        )
        hook_v1 = repository.create_hook_option_under_content_piece_readiness(
            "editorial-package-hook-v1", content_piece.id, "First exact hook"
        )
        hook_v2 = repository.create_hook_option_under_content_piece_readiness(
            "editorial-package-hook-v2", content_piece.id, "Revised exact hook"
        )
        snapshot_v1 = repository.create_editorial_package_snapshot(
            "editorial-package-snapshot-v1",
            content_piece.id,
            title_v1.id,
            hook_v1.id,
            script_v1.id,
        )
        script_v2 = repository.create_script_under_content_piece_readiness(
            "editorial-package-script-v2", content_piece.id, "Revised narration."
        )
        snapshot_v2 = repository.create_editorial_package_snapshot(
            "editorial-package-snapshot-v2",
            content_piece.id,
            title_v2.id,
            hook_v2.id,
            script_v2.id,
        )

        assert [
            option.text
            for option in repository.list_title_options_for_content_piece(content_piece.id)
        ] == [
            "First exact title",
            "Revised exact title",
        ]
        assert [
            option.text
            for option in repository.list_hook_options_for_content_piece(content_piece.id)
        ] == [
            "First exact hook",
            "Revised exact hook",
        ]
        assert repository.get_title_option(title_v1.id).metadata == {"author": "human"}
        assert repository.get_content_piece(content_piece.id) == original_piece
        assert [
            (snapshot.title_option_id, snapshot.hook_option_id, snapshot.script_id)
            for snapshot in repository.list_editorial_package_snapshots_for_content_piece(
                content_piece.id
            )
        ] == [
            (title_v1.id, hook_v1.id, script_v1.id),
            (title_v2.id, hook_v2.id, script_v2.id),
        ]
        assert repository.get_editorial_package_snapshot(snapshot_v1.id) == snapshot_v1
        assert repository.get_editorial_package_snapshot(snapshot_v2.id) == snapshot_v2
        assert repository.list_visual_plans_for_content_piece(content_piece.id) == []

        other_piece = repository.create_content_piece_under_editorial_angle_readiness(
            "editorial-package-other-piece",
            opportunity_id,
            angle.id,
            "video",
            "Other compatibility title",
        )
        other_title = repository.create_title_option_under_content_piece_readiness(
            "editorial-package-other-title", other_piece.id, "Other title"
        )
        other_hook = repository.create_hook_option_under_content_piece_readiness(
            "editorial-package-other-hook", other_piece.id, "Other hook"
        )
        other_script = repository.create_script_under_content_piece_readiness(
            "editorial-package-other-script", other_piece.id, "Other narration."
        )
        for title_id, hook_id, script_id in (
            (other_title.id, hook_v1.id, script_v1.id),
            (title_v1.id, other_hook.id, script_v1.id),
            (title_v1.id, hook_v1.id, other_script.id),
        ):
            with pytest.raises(ValueError, match="same ContentPiece"):
                repository.create_editorial_package_snapshot(
                    f"editorial-package-rejected-{title_id}",
                    content_piece.id,
                    title_id,
                    hook_id,
                    script_id,
                )

        legacy_angle = repository.create_editorial_angle(
            "editorial-package-legacy-angle", opportunity_id, pack.id, *fields
        )
        legacy_piece = repository.create_content_piece(
            "editorial-package-legacy-piece",
            opportunity_id,
            legacy_angle.id,
            "video",
            "Legacy title",
        )
        with pytest.raises(ValueError, match="readiness provenance"):
            repository.create_title_option_under_content_piece_readiness(
                "editorial-package-legacy-title", legacy_piece.id, "Rejected title"
            )
        with pytest.raises(ValueError, match="readiness provenance"):
            repository.create_hook_option_under_content_piece_readiness(
                "editorial-package-legacy-hook", legacy_piece.id, "Rejected hook"
            )
        with pytest.raises(ValueError, match="readiness provenance"):
            repository.create_editorial_package_snapshot(
                "editorial-package-legacy-snapshot",
                legacy_piece.id,
                title_v1.id,
                hook_v1.id,
                script_v1.id,
            )
        with pytest.raises(ValueError, match="non-empty"):
            repository.create_title_option_under_content_piece_readiness(
                "editorial-package-empty-title", content_piece.id, ""
            )
        with pytest.raises(sqlite3.IntegrityError), repository.connection:
            repository.connection.execute("DELETE FROM title_options WHERE id = ?", (title_v1.id,))

        title_columns = {
            row[1] for row in repository.connection.execute("PRAGMA table_info(title_options)")
        }
        snapshot_columns = {
            row[1]
            for row in repository.connection.execute(
                "PRAGMA table_info(editorial_package_snapshots)"
            )
        }
        assert {"selected", "current", "latest", "approved", "score"}.isdisjoint(title_columns)
        assert {"selected", "current", "latest", "approved", "version"}.isdisjoint(snapshot_columns)
    finally:
        repository.close()


def test_migration_16_adds_editorial_package_schema_without_backfill(tmp_path) -> None:
    """Migration 16 is additive over a v0.20 database and leaves historical rows untouched."""

    database = tmp_path / "atlas-v020.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for version, statements in MIGRATIONS[:15]:
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, '2026-08-20T00:00:00+00:00')",
                (version,),
            )
        connection.execute(
            "INSERT INTO opportunities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "historical-package-opportunity",
                "Title",
                "Summary",
                "Why",
                1,
                "proposed",
                "{}",
                "now",
                "now",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    repository = AtlasRepository(database)
    try:
        assert repository.get_opportunity("historical-package-opportunity").title == "Title"
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM title_options").fetchone()[0] == 0
        )
        assert repository.connection.execute("SELECT COUNT(*) FROM hook_options").fetchone()[0] == 0
        assert (
            repository.connection.execute(
                "SELECT COUNT(*) FROM editorial_package_snapshots"
            ).fetchone()[0]
            == 0
        )
        assert repository.connection.execute(
            "SELECT version FROM schema_migrations WHERE version = 16"
        ).fetchone()
    finally:
        repository.close()


def test_migration_17_adds_closed_script_claim_provenance_without_backfill(tmp_path) -> None:
    """Migration 17 is additive over v0.21 and adds no Claim or Script copies."""

    database = tmp_path / "atlas-v021.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for version, statements in MIGRATIONS[:16]:
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, '2026-08-20T00:00:00+00:00')",
                (version,),
            )
        connection.execute(
            "INSERT INTO opportunities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "historical-script-opportunity",
                "Title",
                "Summary",
                "Why",
                1,
                "proposed",
                "{}",
                "now",
                "now",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    repository = AtlasRepository(database)
    try:
        table_names = {
            row[0]
            for row in repository.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert {"script_claim_sets", "script_claim_links"} <= table_names
        assert repository.get_opportunity("historical-script-opportunity").title == "Title"
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM script_claim_sets").fetchone()[0]
            == 0
        )
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM script_claim_links").fetchone()[0]
            == 0
        )
        assert repository.connection.execute(
            "SELECT version FROM schema_migrations WHERE version = 17"
        ).fetchone()
    finally:
        repository.close()


def test_editorial_readiness_assessments_are_append_only_and_server_derived(tmp_path) -> None:
    """v0.23 assesses only exact immutable packages and frozen Script provenance."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        opportunity_id = "editorial-readiness-opportunity"
        repository.create_opportunity(
            opportunity_id, "Opportunity", "Summary", "Why now", 1, "proposed"
        )
        pack = repository.create_research_pack(
            "editorial-readiness-pack", opportunity_id, 1, "Research pack"
        )
        claim = repository.create_claim(
            "editorial-readiness-claim",
            pack.id,
            "Frozen Claim.",
            "fact",
            "high",
            "current",
            "reviewed",
            "",
        )
        source = repository.create_source(
            "editorial-readiness-source",
            "primary",
            "Source",
            "Publisher",
            "https://example.test/editorial-readiness",
            "2026-08-20T00:00:00+00:00",
        )
        repository.link_claim_evidence(claim.id, source.id, "supports", "p. 1")
        ready = repository.create_research_readiness_assessment(
            "editorial-readiness-research-ready",
            pack.id,
            "Ready",
            {"summary": "Ready."},
            "policy-v1",
            "test",
            "persistence-test",
            "v1",
        )
        fields = ("Angle", "Thesis", "Promise", "Frame", ["Takeaway"])
        angle = repository.create_editorial_angle_under_research_readiness(
            "editorial-readiness-angle", opportunity_id, pack.id, ready.id, *fields
        )
        repository.link_claim_to_editorial_angle(angle.id, claim.id, "core")
        piece = repository.create_content_piece_under_editorial_angle_readiness(
            "editorial-readiness-piece", opportunity_id, angle.id, "video", "Working title"
        )
        original_piece = repository.get_content_piece(piece.id)

        def package(script_id: str, suffix: str):
            title = repository.create_title_option_under_content_piece_readiness(
                f"editorial-readiness-title-{suffix}", piece.id, f"Title {suffix}"
            )
            hook = repository.create_hook_option_under_content_piece_readiness(
                f"editorial-readiness-hook-{suffix}", piece.id, f"Hook {suffix}"
            )
            return repository.create_editorial_package_snapshot(
                f"editorial-readiness-package-{suffix}", piece.id, title.id, hook.id, script_id
            )

        missing_script = repository.create_script_under_content_piece_readiness(
            "editorial-readiness-missing-script", piece.id, "Missing set narration."
        )
        missing_package = package(missing_script.id, "missing")
        not_ready = repository.create_editorial_readiness_assessment(
            "editorial-readiness-not-ready", missing_package.id
        )
        assert not_ready.editorial_package_snapshot_id == missing_package.id
        assert not_ready.outcome == "NotReady"
        assert not_ready.findings == {
            "findings": [
                {
                    "code": "SCRIPT_CLAIM_SET_MISSING",
                    "severity": "error",
                    "blocking": True,
                    "message": "The package Script does not have a closed claim provenance set.",
                }
            ]
        }
        assert not_ready.schema_version == 1
        assert not_ready.evaluator_id == "deterministic-editorial-readiness"
        assert not_ready.evaluator_version == "v1"

        empty_script = repository.create_script_under_content_piece_readiness(
            "editorial-readiness-empty-script", piece.id, "Empty set narration."
        )
        empty_package = package(empty_script.id, "empty")
        repository.create_script_claim_set("editorial-readiness-empty-set", empty_script.id, [])
        ready_empty = repository.create_editorial_readiness_assessment(
            "editorial-readiness-empty-ready", empty_package.id
        )
        assert ready_empty.outcome == "Ready"
        assert ready_empty.findings == {"findings": []}

        populated_script = repository.create_script_under_content_piece_readiness(
            "editorial-readiness-populated-script", piece.id, "Populated set narration."
        )
        populated_package = package(populated_script.id, "populated")
        repository.create_script_claim_set(
            "editorial-readiness-populated-set", populated_script.id, [claim.id]
        )
        ready_populated = repository.create_editorial_readiness_assessment(
            "editorial-readiness-populated-ready", populated_package.id
        )
        prior_payload = repository.editorial_readiness_assessment_payload(ready_populated.id)
        prior_claim_set_payload = repository.script_claim_set_payload(populated_script.id)
        repository.update_claim(replace(claim, text="Changed live Claim."))
        with repository.connection:
            repository.connection.execute(
                "UPDATE sources SET title = ? WHERE id = ?", ("Changed live Source.", source.id)
            )
        assert (
            repository.editorial_readiness_assessment_payload(ready_populated.id) == prior_payload
        )
        assert repository.script_claim_set_payload(populated_script.id) == prior_claim_set_payload

        repeated = repository.create_editorial_readiness_assessment(
            "editorial-readiness-populated-rerun", populated_package.id
        )
        assert [
            assessment.id
            for assessment in repository.list_editorial_readiness_assessments(populated_package.id)
        ] == [ready_populated.id, repeated.id]
        assert repository.get_editorial_readiness_assessment(ready_populated.id) == ready_populated
        assert repository.get_content_piece(piece.id) == original_piece
        assert repository.list_visual_plans_for_content_piece(piece.id) == []

        with pytest.raises(sqlite3.IntegrityError), repository.connection:
            repository.connection.execute(
                "DELETE FROM editorial_package_snapshots WHERE id = ?", (populated_package.id,)
            )

        other_piece = repository.create_content_piece_under_editorial_angle_readiness(
            "editorial-readiness-other-piece", opportunity_id, angle.id, "video", "Other title"
        )
        other_title = repository.create_title_option_under_content_piece_readiness(
            "editorial-readiness-other-title", other_piece.id, "Other Title"
        )
        with repository.connection:
            repository.connection.execute(
                "INSERT INTO editorial_package_snapshots VALUES (?, ?, ?, ?, ?, ?)",
                (
                    "editorial-readiness-corrupt-package",
                    piece.id,
                    other_title.id,
                    repository.get_hook_option(empty_package.hook_option_id).id,
                    empty_script.id,
                    "2026-08-20T00:00:00+00:00",
                ),
            )
        before_failed_integrity = repository.connection.execute(
            "SELECT COUNT(*) FROM editorial_readiness_assessments"
        ).fetchone()[0]
        with pytest.raises(ValueError, match="TitleOption"):
            repository.create_editorial_readiness_assessment(
                "editorial-readiness-corrupt-package-assessment",
                "editorial-readiness-corrupt-package",
            )
        assert (
            repository.connection.execute(
                "SELECT COUNT(*) FROM editorial_readiness_assessments"
            ).fetchone()[0]
            == before_failed_integrity
        )

        with repository.connection:
            repository.connection.execute(
                "UPDATE research_readiness_assessments "
                "SET frozen_evidence_state_json = ? WHERE id = ?",
                ('{"claims":[],"claim_evidence":[],"sources":[]}', ready.id),
            )
        before_failed_frozen_integrity = repository.connection.execute(
            "SELECT COUNT(*) FROM editorial_readiness_assessments"
        ).fetchone()[0]
        with pytest.raises(ValueError, match="frozen evidence"):
            repository.create_editorial_readiness_assessment(
                "editorial-readiness-corrupt", populated_package.id
            )
        assert (
            repository.connection.execute(
                "SELECT COUNT(*) FROM editorial_readiness_assessments"
            ).fetchone()[0]
            == before_failed_frozen_integrity
        )

        table_names = {
            row[0]
            for row in repository.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert "editorial_readiness_assessments" in table_names
        assert {"editorial_gates", "editorial_readiness_findings", "cost_ledgers"}.isdisjoint(
            table_names
        )
        columns = {
            row[1]
            for row in repository.connection.execute(
                "PRAGMA table_info(editorial_readiness_assessments)"
            )
        }
        assert {"current", "latest", "superseded", "score", "provider", "model"}.isdisjoint(columns)
    finally:
        repository.close()


def test_migration_18_adds_editorial_readiness_assessments_without_backfill(tmp_path) -> None:
    """Migration 18 is additive over v0.22 and preserves historical packages."""

    database = tmp_path / "atlas-v022.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for version, statements in MIGRATIONS[:17]:
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, '2026-08-20T00:00:00+00:00')",
                (version,),
            )
        connection.commit()
    finally:
        connection.close()

    repository = AtlasRepository(database)
    try:
        assert (
            repository.connection.execute(
                "SELECT COUNT(*) FROM editorial_readiness_assessments"
            ).fetchone()[0]
            == 0
        )
        assert repository.connection.execute(
            "SELECT version FROM schema_migrations WHERE version = 18"
        ).fetchone()
        assert repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' "
            "AND name = 'idx_editorial_readiness_assessments_package_created'"
        ).fetchone()
    finally:
        repository.close()


def test_script_claim_sets_close_explicit_frozen_claim_provenance(tmp_path) -> None:
    """v0.22 closes explicit Script Claim identity sets against exact frozen readiness evidence."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        opportunity_id = "script-claim-opportunity"
        other_opportunity_id = "script-claim-other-opportunity"
        repository.create_opportunity(
            opportunity_id, "Opportunity", "Summary", "Why now", 1, "proposed"
        )
        repository.create_opportunity(
            other_opportunity_id, "Other", "Summary", "Why now", 1, "proposed"
        )
        pack = repository.create_research_pack("script-claim-pack", opportunity_id, 1, "Research")
        other_pack = repository.create_research_pack(
            "script-claim-other-pack", other_opportunity_id, 1, "Other research"
        )
        claim_one = repository.create_claim(
            "script-claim-one",
            pack.id,
            "Frozen Claim one.",
            "fact",
            "low",
            "current",
            "reviewed",
            "",
        )
        claim_two = repository.create_claim(
            "script-claim-two",
            pack.id,
            "Frozen Claim two.",
            "fact",
            "low",
            "current",
            "reviewed",
            "",
        )
        unlinked_claim = repository.create_claim(
            "script-claim-unlinked",
            pack.id,
            "Frozen but unlinked.",
            "fact",
            "low",
            "current",
            "reviewed",
            "",
        )
        other_claim = repository.create_claim(
            "script-claim-other",
            other_pack.id,
            "Other Claim.",
            "fact",
            "low",
            "current",
            "reviewed",
            "",
        )
        source = repository.create_source(
            "script-claim-source",
            "primary",
            "Source",
            "Publisher",
            "https://example.test/script",
            "now",
        )
        repository.link_claim_evidence(claim_one.id, source.id, "supports", "p. 1")
        ready = repository.create_research_readiness_assessment(
            "script-claim-ready",
            pack.id,
            "Ready",
            {"summary": "Ready."},
            "policy-v1",
            "test",
            "persistence-test",
            "v1",
        )
        fields = ("Angle", "Thesis", "Promise", "Frame", ["Takeaway"])
        angle = repository.create_editorial_angle_under_research_readiness(
            "script-claim-angle", opportunity_id, pack.id, ready.id, *fields
        )
        repository.link_claim_to_editorial_angle(angle.id, claim_one.id, "core")
        repository.link_claim_to_editorial_angle(angle.id, claim_two.id, "supporting")
        piece = repository.create_content_piece_under_editorial_angle_readiness(
            "script-claim-piece", opportunity_id, angle.id, "video", "Compatibility title"
        )
        script_one = repository.create_script_under_content_piece_readiness(
            "script-claim-script-one", piece.id, "Original complete narration."
        )
        assert repository.script_claim_set_payload(script_one.id) is None

        closed_set = repository.create_script_claim_set(
            "script-claim-set-one", script_one.id, [claim_two.id, claim_one.id]
        )
        assert closed_set.script_id == script_one.id
        assert [link.claim_id for link in repository.list_script_claim_links(closed_set.id)] == [
            claim_one.id,
            claim_two.id,
        ]
        frozen_payload = repository.script_claim_set_payload(script_one.id)
        assert frozen_payload is not None
        assert frozen_payload["claim_ids"] == [claim_one.id, claim_two.id]
        assert [claim["text"] for claim in frozen_payload["frozen_claims"]] == [
            "Frozen Claim one.",
            "Frozen Claim two.",
        ]
        assert frozen_payload["frozen_claim_evidence"][0]["claim_id"] == claim_one.id
        assert frozen_payload["frozen_sources"][0]["id"] == source.id
        with pytest.raises(ValueError, match="only one"):
            repository.create_script_claim_set("script-claim-set-again", script_one.id, [])
        with pytest.raises(sqlite3.IntegrityError), repository.connection:
            repository.connection.execute(
                "DELETE FROM script_claim_sets WHERE id = ?", (closed_set.id,)
            )
        with pytest.raises(sqlite3.IntegrityError), repository.connection:
            repository.connection.execute("DELETE FROM claims WHERE id = ?", (claim_one.id,))

        repository.update_claim(replace(claim_one, text="Later mutable Claim text."))
        later_source = repository.create_source(
            "script-claim-later-source",
            "primary",
            "Later",
            "Publisher",
            "https://example.test/later",
            "now",
        )
        repository.link_claim_evidence(claim_one.id, later_source.id, "context", "p. 2")
        repository.update_editorial_angle_claim_role(angle.id, claim_one.id, "supporting")
        with repository.connection:
            repository.connection.execute(
                "DELETE FROM editorial_angle_claims WHERE editorial_angle_id = ? AND claim_id = ?",
                (angle.id, claim_one.id),
            )
        assert repository.script_claim_set_payload(script_one.id) == frozen_payload

        script_two = repository.create_script_under_content_piece_readiness(
            "script-claim-script-two", piece.id, "Corrected complete narration."
        )
        repository.link_claim_to_editorial_angle(angle.id, claim_one.id, "core")
        second_set = repository.create_script_claim_set(
            "script-claim-set-two", script_two.id, [claim_one.id]
        )
        assert [link.claim_id for link in repository.list_script_claim_links(second_set.id)] == [
            claim_one.id
        ]
        script_three = repository.create_script_under_content_piece_readiness(
            "script-claim-script-three", piece.id, "Editorial-only narration."
        )
        empty_set = repository.create_script_claim_set(
            "script-claim-set-empty", script_three.id, []
        )
        assert repository.get_script_claim_set_for_script(script_three.id) == empty_set
        assert repository.list_script_claim_links(empty_set.id) == []
        assert repository.script_claim_set_payload(script_three.id)["claim_ids"] == []

        late_claim = repository.create_claim(
            "script-claim-late",
            pack.id,
            "Too late for frozen evidence.",
            "fact",
            "low",
            "current",
            "reviewed",
            "",
        )
        repository.link_claim_to_editorial_angle(angle.id, late_claim.id, "core")
        script_invalid = repository.create_script_under_content_piece_readiness(
            "script-claim-script-invalid", piece.id, "Another narration."
        )
        for claim_ids, error in (
            ([claim_one.id, claim_one.id], "duplicates"),
            ([other_claim.id], "ResearchPack"),
            ([late_claim.id], "frozen evidence"),
            ([unlinked_claim.id], "originating EditorialAngle"),
        ):
            with pytest.raises(ValueError, match=error):
                repository.create_script_claim_set(
                    f"script-claim-rejected-{len(claim_ids)}-{claim_ids[0]}",
                    script_invalid.id,
                    claim_ids,
                )
            assert repository.get_script_claim_set_for_script(script_invalid.id) is None

        table_names = {
            row[0]
            for row in repository.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert {"script_claim_sets", "script_claim_links"} <= table_names
        assert {"claim_snapshots", "script_claim_evidence", "script_segments"}.isdisjoint(
            table_names
        )
        assert "research_readiness_assessment_id" not in {
            row[1] for row in repository.connection.execute("PRAGMA table_info(script_claim_sets)")
        }
        assert repository.list_editorial_package_snapshots_for_content_piece(piece.id) == []
    finally:
        repository.close()


def test_migration_15_adds_nullable_angle_readiness_lineage_without_backfill(tmp_path) -> None:
    """Migration 15 preserves pre-v0.18 Angles while adding restrictive provenance."""

    database = tmp_path / "atlas-v017.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for version, statements in MIGRATIONS[:14]:
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, '2026-08-17T00:00:00+00:00')",
                (version,),
            )
        connection.execute(
            "INSERT INTO opportunities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "historical-angle-opportunity",
                "Title",
                "Summary",
                "Why now",
                1,
                "proposed",
                "{}",
                "now",
                "now",
            ),
        )
        connection.execute(
            "INSERT INTO research_packs "
            "(id, opportunity_id, version, summary, as_of_date, metadata_json, created_at, "
            "updated_at, idea_gate_decision_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "historical-angle-pack",
                "historical-angle-opportunity",
                1,
                "Summary",
                None,
                "{}",
                "now",
                "now",
                None,
            ),
        )
        connection.execute(
            "INSERT INTO editorial_angles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "historical-angle",
                "historical-angle-opportunity",
                "historical-angle-pack",
                "Title",
                "Thesis",
                "Promise",
                "Frame",
                '["One"]',
                "{}",
                "now",
                "now",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    repository = AtlasRepository(database)
    try:
        assert (
            repository.get_editorial_angle("historical-angle").research_readiness_assessment_id
            is None
        )
        assert repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name='idx_editorial_angles_research_readiness_assessment'"
        ).fetchone()
        assert (
            repository.connection.execute(
                "SELECT COUNT(*) FROM editorial_angles "
                "WHERE research_readiness_assessment_id IS NOT NULL"
            ).fetchone()[0]
            == 0
        )
    finally:
        repository.close()


def test_migration_11_adds_reference_lineage_without_backfilling_history(
    tmp_path,
) -> None:
    """Migration 11 preserves prior executions while adding nullable reference lineage."""

    database = tmp_path / "atlas-v010.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for version, statements in MIGRATIONS[:10]:
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, '2026-08-13T00:00:00+00:00')",
                (version,),
            )
        connection.commit()
    finally:
        connection.close()

    repository = AtlasRepository(database)
    try:
        assert [
            row["version"]
            for row in repository.connection.execute("SELECT version FROM schema_migrations")
        ] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        assert repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='character_reference_sets'"
        ).fetchone()
        assert repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='character_reference_set_members'"
        ).fetchone()
        assert (
            repository.get_asset_spec(
                "asset-spec-isa-scene-01-hamster-sorting-v1"
            ).character_profile_id
            == "character-profile-similarstoic-hamster-core-v1"
        )
        assert (
            repository.connection.execute("PRAGMA table_info(assets)").fetchall()[-1]["name"]
            == "content_digest"
        )
        assert (
            repository.connection.execute("PRAGMA table_info(generation_executions)").fetchall()[
                -1
            ]["name"]
            == "character_reference_set_id"
        )
    finally:
        repository.close()


def test_generated_assets_store_digest_of_exact_managed_bytes(tmp_path) -> None:
    """The unchanged production path records a digest beside every new generated Asset."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    try:
        result = generate_character_asset(
            repository, storage_root, "asset-spec-isa-scene-01-hamster-sorting-v1"
        )
        asset = result.asset
        assert asset.content_digest == sha256(b"deterministic png bytes").hexdigest()
        assert (
            asset.content_digest
            == sha256((storage_root / asset.storage_path).read_bytes()).hexdigest()
        )
        failed = GenerationService(
            repository,
            FakeImageGenerator(failure=GenerationFailure("Rejected", error_code="rejected")),
            LocalAssetStorage(storage_root),
        ).generate_asset_spec("asset-spec-isa-scene-03-hamster-reaction-v1")
        assert failed.asset is None
        assert len(repository.list_assets_for_asset_spec(failed.execution.asset_spec_id)) == 0
    finally:
        repository.close()


def test_character_reference_sets_are_ordered_immutable_versions(tmp_path) -> None:
    """Selection records complete ordered visual bases without a mutable current state."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    profile_id = "character-profile-similarstoic-hamster-core-v1"
    try:
        first = generate_character_asset(
            repository, storage_root, "asset-spec-isa-scene-01-hamster-sorting-v1"
        ).asset
        second = generate_character_asset(
            repository, storage_root, "asset-spec-isa-scene-03-hamster-reaction-v1"
        ).asset
        reference_set = repository.create_character_reference_set(
            "character-reference-set-test-v1", profile_id, [second.id, first.id]
        )
        assert reference_set.version == 2
        assert [
            (member.position, member.asset_id)
            for member in repository.list_character_reference_set_members(reference_set.id)
        ] == [(1, second.id), (2, first.id)]
        replacement = repository.create_character_reference_set(
            "character-reference-set-test-v2", profile_id, [first.id]
        )
        assert replacement.version == 3
        assert [
            member.asset_id
            for member in repository.list_character_reference_set_members(reference_set.id)
        ] == [second.id, first.id]
        third = generate_character_asset(
            repository, storage_root, "asset-spec-isa-scene-01-hamster-sorting-v1"
        ).asset
        try:
            with repository.connection:
                repository.connection.execute(
                    "INSERT INTO character_reference_set_members "
                    "(character_reference_set_id, asset_id, position, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (reference_set.id, third.id, 1, "2026-08-13T00:00:00+00:00"),
                )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("A CharacterReferenceSet accepted duplicate member positions.")
        assert not hasattr(repository, "update_character_reference_set")
        assert not hasattr(repository, "delete_character_reference_set")
    finally:
        repository.close()


def test_character_reference_set_rejects_invalid_or_partial_selection(tmp_path) -> None:
    """Reference selection validates all members before creating an immutable set."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    profile_id = "character-profile-similarstoic-hamster-core-v1"
    try:
        character = generate_character_asset(
            repository, storage_root, "asset-spec-isa-scene-01-hamster-sorting-v1"
        ).asset
        environment = (
            GenerationService(repository, FakeImageGenerator(), LocalAssetStorage(storage_root))
            .generate_asset_spec("asset-spec-isa-scene-01-kitchen-background-v1")
            .asset
        )
        assert environment is not None
        graphic = (
            GenerationService(repository, FakeImageGenerator(), LocalAssetStorage(storage_root))
            .generate_asset_spec("asset-spec-isa-scene-02-tax-year-calendar-v1")
            .asset
        )
        assert graphic is not None
        for asset_ids, expected in (
            ([character.id, character.id], "more than once"),
            ([environment.id], "character AssetSpecs"),
            ([graphic.id], "character AssetSpecs"),
        ):
            try:
                repository.create_character_reference_set(
                    f"character-reference-set-invalid-{len(asset_ids)}-{expected[:3]}",
                    profile_id,
                    asset_ids,
                )
            except ValueError as error:
                assert expected in str(error)
            else:
                raise AssertionError("Invalid character reference selection was accepted.")
        assert len(repository.list_character_reference_sets(profile_id)) == 1

        manual = repository.create_asset(
            "manual-character-reference-test-v1",
            repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1").id,
            2,
            "manual-character.png",
            "image/png",
            "manual",
        )
        try:
            repository.create_character_reference_set(
                "character-reference-set-manual", profile_id, [manual.id]
            )
        except ValueError as error:
            assert "generated Assets" in str(error)
        else:
            raise AssertionError("A manual Asset was accepted as a reference.")

        imported = repository.create_asset(
            "imported-character-reference-test-v1",
            repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1").id,
            3,
            "imported-character.png",
            "image/png",
            "imported",
        )
        executionless_generated = repository.create_asset(
            "executionless-generated-character-reference-test-v1",
            repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1").id,
            4,
            "generated-but-unlinked-character.png",
            "image/png",
            "generated",
            content_digest=sha256(b"unlinked bytes").hexdigest(),
        )
        for asset in (imported, executionless_generated):
            try:
                repository.create_character_reference_set(
                    f"character-reference-set-invalid-{asset.id}", profile_id, [asset.id]
                )
            except ValueError as error:
                assert "generated Assets" in str(error)
            else:
                raise AssertionError(
                    "An Asset without generated execution provenance was accepted."
                )

        alternate_profile = repository.create_character_profile(
            "character-profile-reference-test-v2",
            "reference-test-hamster",
            1,
            "Reference test hamster",
            "A distinct test character identity.",
            "Depict the distinct test character identity.",
        )
        alternate_spec = repository.create_asset_spec(
            "asset-spec-reference-test-character-v1",
            "scene-isa-deadline-video-v1-01",
            "character",
            "Test another character lineage.",
            "A different character for eligibility validation.",
            "Depict a different character.",
            character_profile_id=alternate_profile.id,
        )
        alternate_asset = generate_character_asset(
            repository, storage_root, alternate_spec.id
        ).asset
        try:
            repository.create_character_reference_set(
                "character-reference-set-other-profile", profile_id, [alternate_asset.id]
            )
        except ValueError as error:
            assert "identity lineage" in str(error)
        else:
            raise AssertionError("A different CharacterProfile Asset was accepted as a reference.")

        unavailable = generate_character_asset(
            repository, storage_root, "asset-spec-isa-scene-03-hamster-reaction-v1"
        ).asset
        (storage_root / unavailable.storage_path).unlink()
        try:
            repository.create_character_reference_set(
                "character-reference-set-missing-file", profile_id, [unavailable.id]
            )
        except ValueError as error:
            assert "does not exist" in str(error)
        else:
            raise AssertionError("An unavailable managed Asset was accepted as a reference.")

        with repository.connection:
            repository.connection.execute(
                "UPDATE assets SET content_digest = NULL WHERE id = ?", (character.id,)
            )
        try:
            repository.create_character_reference_set(
                "character-reference-set-null-digest", profile_id, [character.id]
            )
        except ValueError as error:
            assert "digest" in str(error)
        else:
            raise AssertionError("A digest-less generated Asset was accepted as a reference.")
        assert len(repository.list_character_reference_sets(profile_id)) == 1
    finally:
        repository.close()


def test_character_reference_eligibility_uses_frozen_execution_asset_spec_type(tmp_path) -> None:
    """Later AssetSpec edits cannot redefine what an Asset was generated as."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    profile_id = "character-profile-similarstoic-hamster-core-v1"
    try:
        character = generate_character_asset(
            repository, storage_root, "asset-spec-isa-scene-01-hamster-sorting-v1"
        ).asset
        execution = repository.get_generation_execution(character.generation_execution_id or "")
        assert execution.outcome == "succeeded"
        assert execution.asset_spec_snapshot["asset_type"] == "character"
        current_spec = repository.get_asset_spec(character.asset_spec_id)
        repository.update_asset_spec(
            replace(current_spec, asset_type="environment", character_profile_id=None)
        )
        assert repository.get_asset_spec(current_spec.id).asset_type == "environment"
        eligible_asset_ids = [
            asset.id for asset in repository.list_eligible_character_reference_assets(profile_id)
        ]
        assert character.id in eligible_asset_ids
        assert (
            repository.create_character_reference_set(
                "character-reference-set-snapshot-character-v1", profile_id, [character.id]
            ).version
            == 2
        )

        graphic = (
            GenerationService(repository, FakeImageGenerator(), LocalAssetStorage(storage_root))
            .generate_asset_spec("asset-spec-isa-scene-02-tax-year-calendar-v1")
            .asset
        )
        assert graphic is not None
        graphic_spec = repository.get_asset_spec(graphic.asset_spec_id)
        repository.update_asset_spec(
            replace(graphic_spec, asset_type="character", character_profile_id=profile_id)
        )
        try:
            repository.create_character_reference_set(
                "character-reference-set-snapshot-graphic-v1", profile_id, [graphic.id]
            )
        except ValueError as error:
            assert "character AssetSpecs" in str(error)
        else:
            raise AssertionError(
                "A historical graphic execution became character-reference eligible."
            )
    finally:
        repository.close()


def test_character_reference_rejects_managed_file_digest_mismatch(tmp_path) -> None:
    """Reference selection verifies stored byte identity rather than trusting file location."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    try:
        asset = generate_character_asset(
            repository, storage_root, "asset-spec-isa-scene-01-hamster-sorting-v1"
        ).asset
        (storage_root / asset.storage_path).write_bytes(b"altered managed bytes")
        try:
            repository.create_character_reference_set(
                "character-reference-set-digest-mismatch-v1",
                "character-profile-similarstoic-hamster-core-v1",
                [asset.id],
            )
        except ValueError as error:
            assert "do not match" in str(error)
        else:
            raise AssertionError("Altered managed bytes were accepted as a canonical reference.")
    finally:
        repository.close()


def test_character_reference_set_restricts_asset_and_membership_deletion(tmp_path) -> None:
    """Raw SQL cannot silently sever an immutable visual-reference selection."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    try:
        asset = generate_character_asset(
            repository, storage_root, "asset-spec-isa-scene-01-hamster-sorting-v1"
        ).asset
        reference_set = repository.create_character_reference_set(
            "character-reference-set-restrict-v1",
            "character-profile-similarstoic-hamster-core-v1",
            [asset.id],
        )
        for statement, parameter in (
            ("DELETE FROM assets WHERE id = ?", asset.id),
            ("DELETE FROM character_reference_sets WHERE id = ?", reference_set.id),
        ):
            try:
                with repository.connection:
                    repository.connection.execute(statement, (parameter,))
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError("Restrictive character-reference provenance was deleted.")
    finally:
        repository.close()


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
        ] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        assert repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='generation_executions'"
        ).fetchone()
        assert repository.get_asset("existing-manual-asset").generation_execution_id is None
        assert repository.get_asset("existing-manual-asset").content_digest is None
        assert (
            repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v1").version
            == 1
        )
        assert repository.get_asset_spec("existing-asset-spec").character_profile_id is None
    finally:
        repository.close()


def test_idea_gate_snapshots_and_decisions_preserve_additive_history(tmp_path) -> None:
    """Idea Gate freezes the displayed Opportunity and records one decision per cycle."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        opportunity = repository.get_opportunity("uk-isa-rules")
        initial_research_count = repository.connection.execute(
            "SELECT COUNT(*) FROM research_packs"
        ).fetchone()[0]

        first_snapshot = repository.create_idea_gate_review_snapshot(
            "idea-gate-review-snapshot-isa-v1", opportunity.id
        )
        assert first_snapshot.payload_schema_version == 1
        assert first_snapshot.review_payload["opportunity"]["title"] == opportunity.title
        assert first_snapshot.review_payload["subjects"] == [
            {
                "id": "subject-isa",
                "slug": "isa",
                "name": "ISA",
                "relationship_role": "primary",
            }
        ]

        rejected_snapshot = repository.create_idea_gate_review_snapshot(
            "idea-gate-review-snapshot-isa-reject", opportunity.id
        )
        assert rejected_snapshot.review_payload == first_snapshot.review_payload
        rejected_decision = repository.record_idea_gate_decision(
            "idea-gate-decision-isa-reject",
            rejected_snapshot.id,
            "Reject",
            founder_comment="The audience benefit is not strong enough yet.",
        )
        assert rejected_decision.founder_comment == "The audience benefit is not strong enough yet."

        first_decision = repository.record_idea_gate_decision(
            "idea-gate-decision-isa-v1",
            first_snapshot.id,
            "Steer",
            founder_comment="Make the opening more practical.",
            founder_direction="Focus on the deadline decision for first-time ISA savers.",
        )
        assert first_decision.outcome == "Steer"
        assert first_decision.founder_direction == (
            "Focus on the deadline decision for first-time ISA savers."
        )
        with pytest.raises(ValueError, match="only one decision"):
            repository.record_idea_gate_decision(
                "idea-gate-decision-isa-duplicate",
                first_snapshot.id,
                "Proceed",
            )
        validation_snapshot = repository.create_idea_gate_review_snapshot(
            "idea-gate-review-snapshot-isa-invalid", opportunity.id
        )
        with pytest.raises(ValueError, match="requires non-empty"):
            repository.record_idea_gate_decision(
                "idea-gate-decision-isa-invalid-steer",
                validation_snapshot.id,
                "Steer",
            )

        repository.create_subject(
            "subject-isa-deadline", "isa-deadline", "ISA deadline", "A date-sensitive ISA topic."
        )
        repository.associate_subject(opportunity.id, "subject-isa-deadline", "supporting")
        repository.update_opportunity(
            replace(
                opportunity,
                title="Updated mutable ISA opportunity",
                summary="Updated mutable summary.",
            )
        )
        assert (
            repository.get_idea_gate_review_snapshot(first_snapshot.id).review_payload[
                "opportunity"
            ]["title"]
            == opportunity.title
        )
        assert repository.get_idea_gate_review_snapshot(first_snapshot.id).review_payload[
            "subjects"
        ] == [
            {
                "id": "subject-isa",
                "slug": "isa",
                "name": "ISA",
                "relationship_role": "primary",
            }
        ]

        second_snapshot = repository.create_idea_gate_review_snapshot(
            "idea-gate-review-snapshot-isa-v2", opportunity.id
        )
        repository.record_idea_gate_decision(
            "idea-gate-decision-isa-v2", second_snapshot.id, "Proceed"
        )
        history = repository.idea_gate_history_payload(opportunity.id)
        assert {item["snapshot"]["id"] for item in history["history"]} == {
            first_snapshot.id,
            rejected_snapshot.id,
            "idea-gate-review-snapshot-isa-invalid",
            second_snapshot.id,
        }
        assert [item["snapshot"]["created_at"] for item in history["history"]] == sorted(
            item["snapshot"]["created_at"] for item in history["history"]
        )
        assert {
            item["snapshot"]["id"]: item["decision"] and item["decision"]["outcome"]
            for item in history["history"]
        } == {
            first_snapshot.id: "Steer",
            rejected_snapshot.id: "Reject",
            "idea-gate-review-snapshot-isa-invalid": None,
            second_snapshot.id: "Proceed",
        }
        assert repository.get_opportunity(opportunity.id).status == opportunity.status
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[0]
            == initial_research_count
        )
    finally:
        repository.close()


def test_migration_13_preserves_historical_research_packs_with_null_provenance(tmp_path) -> None:
    """The additive provenance migration leaves pre-v0.16 ResearchPacks untouched."""

    database = tmp_path / "atlas-v015.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for version, statements in MIGRATIONS[:12]:
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, '2026-08-17T00:00:00+00:00')",
                (version,),
            )
        connection.execute(
            "INSERT INTO opportunities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "legacy-opportunity",
                "Legacy opportunity",
                "Legacy summary",
                "Legacy why now",
                50,
                "proposed",
                "{}",
                "2026-08-17T00:00:00+00:00",
                "2026-08-17T00:00:00+00:00",
            ),
        )
        connection.execute(
            "INSERT INTO research_packs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "research-pack-legacy-v1",
                "legacy-opportunity",
                1,
                "A historical ResearchPack.",
                None,
                "{}",
                "2026-08-17T00:00:00+00:00",
                "2026-08-17T00:00:00+00:00",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    repository = AtlasRepository(database)
    try:
        legacy = repository.get_research_pack("research-pack-legacy-v1")
        assert legacy.idea_gate_decision_id is None
        assert [
            row["version"]
            for row in repository.connection.execute("SELECT version FROM schema_migrations")
        ] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        assert repository.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' "
            "AND name = 'idx_research_packs_idea_gate_decision'"
        ).fetchone()
    finally:
        repository.close()


def test_authorized_research_pack_creation_preserves_idea_gate_provenance(tmp_path) -> None:
    """Only qualifying same-Opportunity decisions deliberately create provenance-linked packs."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        opportunity = repository.get_opportunity("uk-isa-rules")
        original_status = opportunity.status
        initial_count = repository.connection.execute(
            "SELECT COUNT(*) FROM research_packs"
        ).fetchone()[0]
        assert (
            repository.get_research_pack("research-pack-isa-deadline-v1").idea_gate_decision_id
            is None
        )

        proceed_snapshot = repository.create_idea_gate_review_snapshot(
            "idea-gate-review-snapshot-authorized-proceed", opportunity.id
        )
        proceed = repository.record_idea_gate_decision(
            "idea-gate-decision-authorized-proceed", proceed_snapshot.id, "Proceed"
        )
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[0]
            == initial_count
        )
        first_pack = repository.create_research_pack_under_idea_gate_authorization(
            "research-pack-isa-authorized-v2",
            opportunity.id,
            2,
            "A deliberately initiated Proceed ResearchPack.",
            proceed.id,
            metadata={"scope": "initial"},
        )
        second_pack = repository.create_research_pack_under_idea_gate_authorization(
            "research-pack-isa-authorized-v3",
            opportunity.id,
            3,
            "A later ResearchPack under the same Proceed decision.",
            proceed.id,
        )
        assert first_pack.opportunity_id == opportunity.id
        assert first_pack.idea_gate_decision_id == proceed.id
        assert second_pack.idea_gate_decision_id == proceed.id
        assert first_pack.metadata == {"scope": "initial"}
        assert "founder_direction" not in first_pack.metadata
        provenance = repository.research_pack_payload(first_pack.id)["idea_gate_provenance"]
        assert provenance["decision"]["id"] == proceed.id
        assert provenance["decision"]["outcome"] == "Proceed"
        assert provenance["snapshot"]["id"] == proceed_snapshot.id

        steer_snapshot = repository.create_idea_gate_review_snapshot(
            "idea-gate-review-snapshot-authorized-steer", opportunity.id
        )
        steer = repository.record_idea_gate_decision(
            "idea-gate-decision-authorized-steer",
            steer_snapshot.id,
            "Steer",
            founder_direction="Prioritize the practical deadline choice.",
        )
        steer_pack = repository.create_research_pack_under_idea_gate_authorization(
            "research-pack-isa-authorized-v4",
            opportunity.id,
            4,
            "A deliberately initiated Steer ResearchPack.",
            steer.id,
        )
        steer_provenance = repository.research_pack_payload(steer_pack.id)["idea_gate_provenance"]
        assert steer_provenance["decision"]["founder_direction"] == (
            "Prioritize the practical deadline choice."
        )
        assert steer_pack.metadata == {}

        reject_snapshot = repository.create_idea_gate_review_snapshot(
            "idea-gate-review-snapshot-authorized-reject", opportunity.id
        )
        reject = repository.record_idea_gate_decision(
            "idea-gate-decision-authorized-reject", reject_snapshot.id, "Reject"
        )
        with pytest.raises(ValueError, match="Only Proceed or Steer"):
            repository.create_research_pack_under_idea_gate_authorization(
                "research-pack-isa-rejected-v5",
                opportunity.id,
                5,
                "This must not be created.",
                reject.id,
            )
        other_snapshot = repository.create_idea_gate_review_snapshot(
            "idea-gate-review-snapshot-authorized-other", "credit-utilisation"
        )
        other_decision = repository.record_idea_gate_decision(
            "idea-gate-decision-authorized-other", other_snapshot.id, "Proceed"
        )
        with pytest.raises(ValueError, match="must belong"):
            repository.create_research_pack_under_idea_gate_authorization(
                "research-pack-isa-mismatch-v5",
                opportunity.id,
                5,
                "This must not be created.",
                other_decision.id,
            )
        with pytest.raises(KeyError):
            repository.create_research_pack_under_idea_gate_authorization(
                "research-pack-isa-missing-decision-v5",
                opportunity.id,
                5,
                "This must not be created.",
                "missing-decision",
            )
        with pytest.raises(sqlite3.IntegrityError):
            repository.create_research_pack_under_idea_gate_authorization(
                "research-pack-isa-duplicate-v2",
                opportunity.id,
                2,
                "Duplicate versions remain invalid.",
                proceed.id,
            )
        with pytest.raises(sqlite3.IntegrityError), repository.connection:
            repository.connection.execute(
                "DELETE FROM idea_gate_decisions WHERE id = ?", (proceed.id,)
            )
        assert repository.get_opportunity(opportunity.id).status == original_status
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[0]
            == initial_count + 3
        )
    finally:
        repository.close()


def test_failed_migration_is_atomic_and_not_recorded(tmp_path) -> None:
    """A broken later statement rolls back the entire migration transaction."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        failing_migration = (
            (
                19,
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
                "SELECT version FROM schema_migrations WHERE version = 19"
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


def test_seeded_scene_one_environment_remains_a_background_layer(tmp_path) -> None:
    """Scene 1 keeps setting, character action, and later calendar graphic requirements separate."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        environment = repository.get_asset_spec("asset-spec-isa-scene-01-kitchen-background-v1")
        character = repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        calendar = repository.get_asset_spec("asset-spec-isa-scene-02-tax-year-calendar-v1")
        assert environment.scene_id == "scene-isa-deadline-video-v1-01"
        assert environment.asset_type == "environment"
        assert environment.generation_prompt == (
            "Simple calm young-professional kitchen-table background for a SimilarStoic "
            "ISA decision scene, with a predominantly open light canvas, minimal kitchen "
            "and table cues, and generous clear space for later foreground layers."
        )
        prompt_words = environment.generation_prompt.lower()
        assert not any(
            forbidden in prompt_words
            for forbidden in ("hamster", "person", "character", "envelope", "calendar", "signage")
        )
        assert character.scene_id == environment.scene_id
        assert character.asset_type == "character"
        assert "sorting four labelled envelopes" in character.generation_prompt
        assert calendar.scene_id == "scene-isa-deadline-video-v1-02"
        assert calendar.asset_type == "graphic"

        profile = repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v1")
        generation_input = PromptComposer().compose(environment, profile).payload()
        environment_rules = generation_input["style"]["rules"]["asset_type_rules"]
        assert generation_input["schema_version"] == 3
        assert "character" not in generation_input
        assert environment.generation_prompt in generation_input["prompt"]
        assert environment_rules["role"] == "background setting layer only"
        assert "sibling AssetSpec requirements" in environment_rules["layer_discipline"]
        assert (
            "foreground characters unless they are part of the environment itself"
            in environment_rules["avoid"]
        )
        assert character.generation_prompt not in generation_input["prompt"]
        assert calendar.generation_prompt not in generation_input["prompt"]
    finally:
        repository.close()


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
                        None,
                        None,
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
        assert asset_spec.generation_prompt in persisted.generation_input["prompt"]
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

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    try:
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        ensure_character_reference_set(repository, storage_root)
        assert asset_spec.asset_type == "character"
        result = GenerationService(
            repository, FakeImageGenerator(), LocalAssetStorage(storage_root)
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
    except MissingProviderConfiguration as error:
        assert "OPENAI_API_KEY" in str(error)
    else:
        raise AssertionError("OpenAI image generation ran without a configured API key.")


def test_visual_style_profile_is_seeded_immutable_and_validated(tmp_path) -> None:
    """Profiles are versioned immutable configuration, not editable workflow state."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        v1 = repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v1")
        v2 = repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v2")
        v3 = repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v3")
        assert (v1.style_key, v1.version, v1.name) == (
            "similarstoic-core",
            1,
            "SimilarStoic Core",
        )
        assert (v2.style_key, v2.version, v2.name) == (
            "similarstoic-core",
            2,
            "SimilarStoic Core",
        )
        assert (v3.style_key, v3.version, v3.name) == (
            "similarstoic-core",
            3,
            "SimilarStoic Core",
        )
        assert (
            set(v1.rules["asset_types"])
            == set(v2.rules["asset_types"])
            == {
                "environment",
                "character",
                "graphic",
                "prop",
            }
        )
        assert "rendering_language" not in v1.rules["global"]
        assert (
            "hand-drawn black or dark line illustration" in v2.rules["global"]["rendering_language"]
        )
        assert v2.rules["global"]["background"] == "predominantly white or very light background"
        assert "no colour unless helpful" in v2.rules["global"]["colour"]
        assert v2.rules["global"]["shading"] == "no soft or tonal shading"
        assert "warm tan/orange" in v3.rules["global"]["colour"]
        assert "flat green, blue, orange, yellow, red and black" in v3.rules["global"]["colour"]
        assert "large distinctive hamster-like ears" in v3.rules["global"]["shapes"]
        assert "long whiskers" in v3.rules["global"]["shapes"]
        assert {
            "soft shaded colour",
            "subtle colour variation",
            "gradient shading",
            "textured colouring or fills",
        } <= set(v2.rules["global"]["avoid"])
        assert v2.rules["asset_types"]["environment"]["role"] == "background setting layer only"
        assert not hasattr(repository, "update_visual_style_profile")
        assert not hasattr(repository, "delete_visual_style_profile")
        for invalid_version in (0, -1, True, "1"):
            try:
                repository.create_visual_style_profile(
                    f"invalid-version-{invalid_version}",
                    "test-style",
                    invalid_version,
                    "Test",
                    "Test description.",
                    "Test guidance.",
                    {},
                )
            except ValueError:
                pass
            else:
                raise AssertionError("A non-positive/exact-integer profile version was accepted.")
        for field_name in ("style_key", "name", "description", "generation_guidance"):
            values = {
                "style_key": "test-style",
                "version": 1,
                "name": "Test",
                "description": "Test description.",
                "generation_guidance": "Test guidance.",
                "rules": {},
            }
            values[field_name] = "   "
            try:
                repository.create_visual_style_profile(
                    f"invalid-{field_name}",
                    **values,
                )
            except ValueError:
                pass
            else:
                raise AssertionError("An empty VisualStyleProfile text field was accepted.")
        for invalid_rules, invalid_metadata in (([], {}), ({}, [])):
            try:
                repository.create_visual_style_profile(
                    "invalid-profile-json",
                    "test-style",
                    1,
                    "Test",
                    "Test description.",
                    "Test guidance.",
                    invalid_rules,  # type: ignore[arg-type]
                    invalid_metadata,  # type: ignore[arg-type]
                )
            except ValueError:
                pass
            else:
                raise AssertionError("A non-object profile JSON field was accepted.")
        with repository.connection:
            repository.connection.execute(
                "UPDATE visual_style_profiles SET name = ? WHERE id = ?",
                ("Founder-preserved v1 profile", v1.id),
            )
            repository.connection.execute(
                "UPDATE visual_style_profiles SET name = ? WHERE id = ?",
                ("Founder-preserved v2 profile", v2.id),
            )
            repository.connection.execute(
                "UPDATE visual_style_profiles SET name = ? WHERE id = ?",
                ("Founder-preserved v3 profile", v3.id),
            )
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert reopened.get_visual_style_profile(v1.id).name == "Founder-preserved v1 profile"
        assert reopened.get_visual_style_profile(v2.id).name == "Founder-preserved v2 profile"
        assert reopened.get_visual_style_profile(v3.id).name == "Founder-preserved v3 profile"
        assert len(reopened.list_visual_style_profiles()) == 3
    finally:
        reopened.close()

    restored = AtlasRepository(database)
    try:
        with restored.connection:
            restored.connection.execute("DELETE FROM visual_style_profiles WHERE id = ?", (v2.id,))
    finally:
        restored.close()

    restored = AtlasRepository(database)
    try:
        assert restored.get_visual_style_profile(v1.id).name == "Founder-preserved v1 profile"
        assert restored.get_visual_style_profile(v2.id).version == 2
        assert restored.get_visual_style_profile(v3.id).name == "Founder-preserved v3 profile"
        assert len(restored.list_visual_style_profiles()) == 3
    finally:
        restored.close()


def test_prompt_composer_resolves_only_relevant_deterministic_style_rules(tmp_path) -> None:
    """The Atlas composer is deterministic and never leaks other type rules into v3 input."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        profile = repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v2")
        prop = repository.create_asset_spec(
            "asset-spec-isa-style-prop-v1",
            "scene-isa-deadline-video-v1-01",
            "prop",
            "Clarify the decision.",
            "One envelope.",
            "Illustrate one practical envelope.",
        )
        composer = PromptComposer()
        for asset_spec in (
            repository.get_asset_spec("asset-spec-isa-scene-01-kitchen-background-v1"),
            repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1"),
            repository.get_asset_spec("asset-spec-isa-scene-02-tax-year-calendar-v1"),
            prop,
        ):
            first = composer.compose(asset_spec, profile).payload()
            second = composer.compose(asset_spec, profile).payload()
            assert first == second
            assert first["schema_version"] == 3
            assert first["style"]["version"] == 2
            assert first["style"]["rules"]["asset_type"] == asset_spec.asset_type
            assert (
                first["style"]["rules"]["asset_type_rules"]
                == profile.rules["asset_types"][asset_spec.asset_type]
            )
            assert "character" not in first["style"]["rules"]
            assert asset_spec.generation_prompt in first["prompt"]
            assert "rendering language:" in first["prompt"]
            assert "no colour unless helpful" in first["prompt"]
            assert "soft shaded colour" in first["prompt"]
            assert "gradient shading" in first["prompt"]
            assert first["prompt"].index("visual ideas:") < first["prompt"].index(
                "rendering language:"
            )
            assert first["prompt"].index("rendering language:") < first["prompt"].index("shapes:")
    finally:
        repository.close()


def test_generation_service_uses_profile_provenance_and_missing_profile_stops_early(
    tmp_path, monkeypatch
) -> None:
    """Styled runs freeze exact profile lineage; an unavailable profile never invokes a provider."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-01-kitchen-background-v1")
        blocked_generator = FakeImageGenerator()
        blocked = GenerationService(
            repository,
            blocked_generator,
            LocalAssetStorage(tmp_path / "blocked-assets"),
            "missing-visual-style-profile",
        )
        try:
            blocked.generate_asset_spec(asset_spec.id)
        except MissingVisualStyleProfile as error:
            assert "does not exist" in str(error)
        else:
            raise AssertionError("A missing VisualStyleProfile crossed the generator boundary.")
        assert blocked_generator.inputs == []
        assert repository.list_generation_executions_for_asset_spec(asset_spec.id) == []
        assert repository.connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 0

        generator = FakeImageGenerator()
        service = GenerationService(repository, generator, LocalAssetStorage(tmp_path / "assets"))
        assert (
            service.visual_style_summary()["profile_id"]
            == "visual-style-profile-similarstoic-core-v3"
        )
        result = service.generate_asset_spec(asset_spec.id)
        profile = repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v3")
        assert result.execution.visual_style_profile_id == profile.id
        assert result.execution.generation_input["schema_version"] == 3
        assert result.execution.generation_input["style"]["profile_id"] == profile.id
        assert result.execution.generation_input["style"]["style_key"] == profile.style_key
        assert result.execution.generation_input["style"]["version"] == profile.version
        assert generator.inputs[0].prompt == result.execution.generation_input["prompt"]
        assert isinstance(generator.inputs[0], GenerationInput)

        v1_id = "visual-style-profile-similarstoic-core-v1"
        monkeypatch.setenv("ATLAS_VISUAL_STYLE_PROFILE_ID", v1_id)
        configured_generator = FakeImageGenerator()
        configured = GenerationService(
            repository, configured_generator, LocalAssetStorage(tmp_path / "configured-assets")
        )
        assert configured.visual_style_summary()["profile_id"] == v1_id
        v1_result = configured.generate_asset_spec(asset_spec.id)
        assert v1_result.execution.visual_style_profile_id == v1_id
        assert v1_result.execution.generation_input["style"]["version"] == 1

        assert len(repository.list_generation_executions_for_asset_spec(asset_spec.id)) == 2
        assert repository.connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 2
    finally:
        repository.close()


def test_existing_v1_generation_execution_remains_readable_after_style_migration(tmp_path) -> None:
    """v0.8 input and historical SimilarStoic Core v1 lineage remain readable."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-01-kitchen-background-v1")
        v1_input = {"schema_version": 1, "asset_type": "environment", "prompt": "Historical"}
        execution = repository.create_failed_generation_execution(
            "generation-execution-v1-history",
            asset_spec.id,
            {"schema_version": 1, "asset_spec_id": asset_spec.id},
            v1_input,
            "historical-generator",
        )
        assert execution.visual_style_profile_id is None
        assert execution.generation_input == v1_input
        styled = GenerationService(
            repository,
            FakeImageGenerator(),
            LocalAssetStorage(tmp_path / "v1-assets"),
            "visual-style-profile-similarstoic-core-v1",
        ).generate_asset_spec(asset_spec.id)
        assert (
            styled.execution.visual_style_profile_id == "visual-style-profile-similarstoic-core-v1"
        )
        assert styled.execution.generation_input["style"]["version"] == 1
    finally:
        repository.close()


def test_character_profile_seed_is_immutable_and_attached_only_to_hamster_specs(tmp_path) -> None:
    """The canonical hamster identity is durable, versioned, and not general style state."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        profile = repository.get_character_profile("character-profile-similarstoic-hamster-core-v1")
        assert (profile.character_key, profile.version, profile.name) == (
            "similarstoic-hamster-core",
            1,
            "SimilarStoic Hamster Core",
        )
        identity_text = f"{profile.identity_description} {profile.generation_guidance}".lower()
        assert all(
            required in identity_text
            for required in (
                "recognisable classic hamster",
                "sling/crossbody bag",
                "hamster-native behaviour",
                "money, work, behaviour and life-strategy concepts",
            )
        )
        assert not any(
            forbidden in identity_text
            for forbidden in ("cheeky", "relaxed", "finance guru", "corporate mascot", "squishy")
        )
        assert not hasattr(repository, "update_character_profile")
        assert not hasattr(repository, "delete_character_profile")

        hamster_specs = (
            repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1"),
            repository.get_asset_spec("asset-spec-isa-scene-03-hamster-reaction-v1"),
        )
        assert all(spec.character_profile_id == profile.id for spec in hamster_specs)
        assert (
            repository.get_asset_spec(
                "asset-spec-isa-scene-01-kitchen-background-v1"
            ).character_profile_id
            is None
        )
        assert (
            repository.get_asset_spec(
                "asset-spec-isa-scene-02-tax-year-calendar-v1"
            ).character_profile_id
            is None
        )
        try:
            repository.create_asset_spec(
                "asset-spec-invalid-character-profile-v1",
                "scene-isa-deadline-video-v1-01",
                "graphic",
                "Test invalid identity ownership.",
                "A graphic that must not own a character identity.",
                "Illustrate a graphic without a character.",
                character_profile_id=profile.id,
            )
        except ValueError as error:
            assert "Only character AssetSpecs" in str(error)
        else:
            raise AssertionError("A non-character AssetSpec accepted a CharacterProfile.")
    finally:
        repository.close()


def test_character_generation_freezes_v4_identity_and_reference_provenance(tmp_path) -> None:
    """Character generation freezes identity and selected reference evidence before the adapter."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    try:
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        style_profile = repository.get_visual_style_profile(
            "visual-style-profile-similarstoic-core-v2"
        )
        character_profile = repository.get_character_profile(asset_spec.character_profile_id)
        reference_set_id = ensure_character_reference_set(repository, storage_root)
        generation_input = (
            PromptComposer().compose(asset_spec, style_profile, character_profile).payload()
        )
        assert generation_input["schema_version"] == 3
        assert generation_input["character"] == {
            "profile_id": character_profile.id,
            "character_key": character_profile.character_key,
            "version": character_profile.version,
            "name": character_profile.name,
            "identity_description": character_profile.identity_description,
            "generation_guidance": character_profile.generation_guidance,
        }
        assert generation_input["prompt"].index("Visual style guidance:") < generation_input[
            "prompt"
        ].index("Global visual rules:")
        assert generation_input["prompt"].index("Global visual rules:") < generation_input[
            "prompt"
        ].index("character visual rules:")
        assert generation_input["prompt"].index("character visual rules:") < generation_input[
            "prompt"
        ].index("Character identity guidance:")
        assert generation_input["prompt"].index("Character identity guidance:") < generation_input[
            "prompt"
        ].index("AssetSpec requirement:")

        generator = FakeImageGenerator()
        result = GenerationService(
            repository, generator, LocalAssetStorage(storage_root)
        ).generate_asset_spec(asset_spec.id)
        assert result.execution.character_profile_id == character_profile.id
        assert result.execution.character_reference_set_id == reference_set_id
        assert result.execution.generation_input["schema_version"] == 4
        assert result.execution.generation_input["character"] == generation_input["character"]
        assert (
            result.execution.generation_input["character_references"]["reference_set_id"]
            == reference_set_id
        )
        assert result.asset is not None
        assert isinstance(generator.inputs[0], GenerationInput)
        assert not isinstance(generator.inputs[0], CharacterProfile)
        assert generator.inputs[0].character == generation_input["character"]
        payload = repository.generation_execution_payload(result.execution.id)
        assert payload["character_profile"] == {
            "id": character_profile.id,
            "name": character_profile.name,
            "version": character_profile.version,
            "identity_description": character_profile.identity_description,
        }
    finally:
        repository.close()


def test_failed_character_generation_retains_reference_lineage_without_an_asset(tmp_path) -> None:
    """A failed attempt preserves v4 character/reference provenance without an Asset."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    try:
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-03-hamster-reaction-v1")
        reference_set_id = ensure_character_reference_set(repository, storage_root)
        result = GenerationService(
            repository,
            FakeImageGenerator(
                failure=GenerationFailure("Rejected character request.", error_code="rejected")
            ),
            LocalAssetStorage(storage_root),
        ).generate_asset_spec(asset_spec.id)
        assert result.asset is None
        assert result.execution.outcome == "failed"
        assert result.execution.character_profile_id == asset_spec.character_profile_id
        assert result.execution.character_reference_set_id == reference_set_id
        assert result.execution.generation_input["schema_version"] == 4
        assert (
            result.execution.generation_input["character"]["profile_id"]
            == asset_spec.character_profile_id
        )
        assert repository.get_asset_for_generation_execution(result.execution.id) is None
    finally:
        repository.close()


def test_existing_v2_generation_input_remains_readable_without_character_lineage(tmp_path) -> None:
    """Historical styled v2 executions remain valid after v3 character provenance is introduced."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-01-kitchen-background-v1")
        profile = repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v1")
        v2_input = PromptComposer().compose(asset_spec, profile).payload()
        v2_input["schema_version"] = 2
        execution = repository.create_failed_generation_execution(
            "generation-execution-v2-history",
            asset_spec.id,
            {"schema_version": 1, "asset_spec_id": asset_spec.id},
            v2_input,
            "historical-generator",
            visual_style_profile_id=profile.id,
        )
        assert execution.generation_input == v2_input
        assert execution.character_profile_id is None
        assert execution.character_reference_set_id is None
        assert repository.generation_execution_payload(execution.id)["character_profile"] is None
    finally:
        repository.close()


def test_existing_v08_database_upgrades_character_seed_without_legacy_prompt_drift(
    tmp_path,
) -> None:
    """Migration 9 normalizes only the two canonical hamster requirements from v0.10."""

    database = tmp_path / "atlas-v08.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for version, statements in MIGRATIONS[:8]:
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, '2026-08-12T00:00:00+00:00')",
                (version,),
            )
        old_specs = (
            (
                "asset-spec-isa-scene-01-hamster-sorting-v1",
                "scene-isa-deadline-video-v1-01",
                "character",
                "Illustrate the viewer sorting practical ISA options.",
                "The sling-bag hamster sorts four labelled envelopes at the kitchen table.",
                (
                    "Illustrated SimilarStoic hamster with its small everyday sling bag, calmly "
                    "sorting four labelled envelopes at a kitchen table; retain the canonical "
                    "relaxed, curious young-adult character identity."
                ),
                "similarstoic-hamster-core",
                "{}",
                "2026-08-12T00:00:00+00:00",
                "2026-08-12T00:00:00+00:00",
            ),
            (
                "asset-spec-isa-scene-03-hamster-reaction-v1",
                "scene-isa-deadline-video-v1-03",
                "character",
                "Add a relatable reaction to the completed decision-tree branches.",
                "The sling-bag hamster reacts to the completed decision-tree branches.",
                (
                    "Illustrated SimilarStoic hamster with its small everyday sling bag reacting "
                    "to a completed decision tree; retain the canonical relaxed, curious "
                    "young-adult character identity with a lightly cheeky expression."
                ),
                "similarstoic-hamster-core",
                "{}",
                "2026-08-12T00:00:00+00:00",
                "2026-08-12T00:00:00+00:00",
            ),
        )
        for asset_spec in old_specs:
            connection.execute(
                "INSERT INTO asset_specs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", asset_spec
            )
        connection.commit()
    finally:
        connection.close()

    repository = AtlasRepository(database)
    try:
        assert [
            row["version"]
            for row in repository.connection.execute("SELECT version FROM schema_migrations")
        ] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        profile = repository.get_character_profile("character-profile-similarstoic-hamster-core-v1")
        sorting = repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        reaction = repository.get_asset_spec("asset-spec-isa-scene-03-hamster-reaction-v1")
        assert sorting.character_profile_id == reaction.character_profile_id == profile.id
        assert sorting.generation_prompt == (
            "Illustrated hamster calmly sorting four labelled envelopes at a kitchen table."
        )
        assert (
            reaction.generation_prompt
            == "Illustrated hamster reacting to a completed decision tree."
        )
        assert not {"relaxed", "curious", "cheeky"} & set(
            f"{sorting.generation_prompt} {reaction.generation_prompt}".lower().split()
        )
        assert (
            repository.get_asset_spec(
                "asset-spec-isa-scene-01-kitchen-background-v1"
            ).character_profile_id
            is None
        )
        assert (
            repository.get_asset_spec(
                "asset-spec-isa-scene-02-tax-year-calendar-v1"
            ).character_profile_id
            is None
        )
    finally:
        repository.close()


def test_character_profile_seed_preserves_an_existing_accepted_version(tmp_path) -> None:
    """Idempotent bootstrap must not rewrite an existing immutable profile version."""

    database = tmp_path / "atlas.db"
    repository = AtlasRepository(database)
    try:
        profile_id = "character-profile-similarstoic-hamster-core-v1"
        with repository.connection:
            repository.connection.execute(
                "UPDATE character_profiles SET name = ? WHERE id = ?",
                ("Founder-preserved Hamster Core", profile_id),
            )
    finally:
        repository.close()

    reopened = AtlasRepository(database)
    try:
        assert reopened.get_character_profile(profile_id).name == "Founder-preserved Hamster Core"
        assert len(reopened.list_character_profiles()) == 1
    finally:
        reopened.close()


def test_referenced_character_profile_uses_restrictive_deletion(tmp_path) -> None:
    """Character identity provenance cannot be deleted while requirements reference it."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        profile_id = "character-profile-similarstoic-hamster-core-v1"
        try:
            with repository.connection:
                repository.connection.execute(
                    "DELETE FROM character_profiles WHERE id = ?", (profile_id,)
                )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("A referenced CharacterProfile was deleted.")
    finally:
        repository.close()


def test_character_execution_remains_historical_after_asset_spec_identity_changes(tmp_path) -> None:
    """Execution lineage remains stable when a mutable AssetSpec relationship changes."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    try:
        original_profile = repository.get_character_profile(
            "character-profile-similarstoic-hamster-core-v1"
        )
        alternate_profile = repository.create_character_profile(
            "character-profile-similarstoic-hamster-core-v2",
            "similarstoic-hamster-core",
            2,
            "SimilarStoic Hamster Core",
            "A second immutable test version of the canonical SimilarStoic hamster identity.",
            "Depict the second immutable test version of the canonical SimilarStoic hamster.",
        )
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        ensure_character_reference_set(repository, storage_root)
        result = GenerationService(
            repository, FakeImageGenerator(), LocalAssetStorage(storage_root)
        ).generate_asset_spec(asset_spec.id)
        repository.update_asset_spec(replace(asset_spec, character_profile_id=alternate_profile.id))
        execution = repository.get_generation_execution(result.execution.id)
        assert execution.character_profile_id == original_profile.id
        assert execution.asset_spec_snapshot["character_profile_id"] == original_profile.id
        assert execution.generation_input["character"]["profile_id"] == original_profile.id
        assert repository.get_asset_spec(asset_spec.id).character_profile_id == alternate_profile.id
        assert repository.generation_execution_payload(execution.id)["character_profile"]["id"] == (
            original_profile.id
        )
    finally:
        repository.close()


def test_v3_character_provenance_requires_complete_frozen_guidance(tmp_path) -> None:
    """Validation rejects incomplete character lineage while allowing v3 non-characters."""

    repository = AtlasRepository(tmp_path / "atlas.db")
    try:
        character_spec = repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        profile = repository.get_character_profile(character_spec.character_profile_id)
        style = repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v2")
        valid_input = PromptComposer().compose(character_spec, style, profile).payload()
        for field_name in ("identity_description", "generation_guidance"):
            for case in ("missing", "altered"):
                malformed = {**valid_input, "character": {**valid_input["character"]}}
                if case == "missing":
                    malformed["character"].pop(field_name)
                else:
                    malformed["character"][field_name] = "Not the frozen canonical guidance."
                try:
                    repository.create_failed_generation_execution(
                        f"generation-execution-v3-{case}-{field_name}",
                        character_spec.id,
                        {"schema_version": 1, "asset_spec_id": character_spec.id},
                        malformed,
                        "test-generator",
                        visual_style_profile_id=style.id,
                        character_profile_id=profile.id,
                    )
                except ValueError as error:
                    assert "CharacterProfile" in str(error)
                else:
                    raise AssertionError(f"A v3 character input accepted {case} {field_name}.")

        environment_spec = repository.get_asset_spec(
            "asset-spec-isa-scene-01-kitchen-background-v1"
        )
        non_character_input = PromptComposer().compose(environment_spec, style).payload()
        valid = repository.create_failed_generation_execution(
            "generation-execution-v3-environment",
            environment_spec.id,
            {"schema_version": 1, "asset_spec_id": environment_spec.id},
            non_character_input,
            "test-generator",
            visual_style_profile_id=style.id,
        )
        assert valid.character_profile_id is None
        assert "character" not in valid.generation_input
    finally:
        repository.close()


def test_reference_grounded_generation_requires_exact_reference_set_before_attempt(
    tmp_path,
) -> None:
    """A character request cannot silently fall back to prompt-only generation."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    generator = FakeImageGenerator()
    asset_spec_id = "asset-spec-isa-scene-01-hamster-sorting-v1"
    try:
        try:
            GenerationService(
                repository, generator, LocalAssetStorage(storage_root)
            ).generate_asset_spec(asset_spec_id)
        except MissingCharacterReferenceSet:
            pass
        else:
            raise AssertionError("Character generation fell back without a CharacterReferenceSet.")
        assert repository.list_generation_executions_for_asset_spec(asset_spec_id) == []
        assert repository.list_assets_for_asset_spec(asset_spec_id) == []
        assert generator.inputs == []
    finally:
        repository.close()


def test_character_reference_bootstrap_generates_v3_candidate_without_a_reference_set(
    tmp_path,
) -> None:
    """An explicit bootstrap creates eligible pre-reference character evidence only."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    try:
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        normal_generator = FakeImageGenerator()
        normal_service = GenerationService(
            repository, normal_generator, LocalAssetStorage(storage_root)
        )
        try:
            normal_service.generate_asset_spec(asset_spec.id)
        except MissingCharacterReferenceSet:
            pass
        else:
            raise AssertionError("Ordinary character generation silently used bootstrap behavior.")
        assert normal_generator.inputs == []

        generator = FakeImageGenerator()
        result = GenerationService(
            repository, generator, LocalAssetStorage(storage_root)
        ).bootstrap_character_reference_asset(asset_spec.id)

        assert result.asset is not None
        assert len(generator.inputs) == 1
        assert result.execution.outcome == "succeeded"
        assert result.execution.character_profile_id == asset_spec.character_profile_id
        assert result.execution.character_reference_set_id is None
        assert result.execution.generation_input["schema_version"] == 3
        assert "character_references" not in result.execution.generation_input
        assert generator.inputs[0].reference_images == ()
        assert (
            repository.get_latest_character_reference_set(asset_spec.character_profile_id) is None
        )
        assert result.asset.id in {
            asset.id
            for asset in repository.list_eligible_character_reference_assets(
                asset_spec.character_profile_id
            )
        }
    finally:
        repository.close()


def test_character_reference_bootstrap_records_provider_failure_without_an_asset(tmp_path) -> None:
    """A failed bootstrap remains one v3 terminal execution without an Asset."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    try:
        asset_spec = repository.get_asset_spec("asset-spec-isa-scene-03-hamster-reaction-v1")
        generator = FakeImageGenerator(
            failure=GenerationFailure("Bootstrap rejected.", error_code="rejected")
        )
        result = GenerationService(
            repository, generator, LocalAssetStorage(storage_root)
        ).bootstrap_character_reference_asset(asset_spec.id)

        assert len(generator.inputs) == 1
        assert result.asset is None
        assert result.execution.outcome == "failed"
        assert result.execution.character_profile_id == asset_spec.character_profile_id
        assert result.execution.character_reference_set_id is None
        assert result.execution.generation_input["schema_version"] == 3
        assert "character_references" not in result.execution.generation_input
    finally:
        repository.close()


def test_character_reference_bootstrap_uses_the_non_reference_openai_request(tmp_path) -> None:
    """Bootstrap uses the ordinary image-generation transport with a truthful v3 input."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    captured = {}

    class Response:
        headers = {"x-request-id": "bootstrap-openai-request"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        @staticmethod
        def read() -> bytes:
            return b'{"created": 1, "data": [{"b64_json": "b3V0cHV0"}]}'

    def opener(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    try:
        result = GenerationService(
            repository,
            OpenAIImageGenerator(api_key="test-key", opener=opener),
            LocalAssetStorage(storage_root),
        ).bootstrap_character_reference_asset("asset-spec-isa-scene-01-hamster-sorting-v1")

        request = captured["request"]
        assert request.full_url == "https://api.openai.com/v1/images/generations"
        assert request.headers["Content-type"] == "application/json"
        assert json.loads(request.data) == {
            "model": "gpt-image-2",
            "prompt": result.execution.generation_input["prompt"],
            "n": 1,
            "output_format": "png",
        }
        assert result.execution.generation_input["schema_version"] == 3
        assert "character_references" not in result.execution.generation_input
        assert result.execution.character_reference_set_id is None
    finally:
        repository.close()


def test_character_reference_bootstrap_rejects_ineligible_specs_and_existing_sets(tmp_path) -> None:
    """Bootstrap is pre-provider-only for an unreferenced Scene-owned character AssetSpec."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    try:
        generator = FakeImageGenerator()
        service = GenerationService(repository, generator, LocalAssetStorage(storage_root))
        executions_before = repository.connection.execute(
            "SELECT COUNT(*) FROM generation_executions"
        ).fetchone()[0]
        for asset_spec_id in (
            "asset-spec-isa-scene-01-kitchen-background-v1",
            "asset-spec-isa-scene-02-tax-year-calendar-v1",
        ):
            try:
                service.bootstrap_character_reference_asset(asset_spec_id)
            except InvalidCharacterReferenceBootstrap:
                pass
            else:
                raise AssertionError("Bootstrap accepted a non-character AssetSpec.")

        character_spec = repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        repository.update_asset_spec(replace(character_spec, character_profile_id=None))
        try:
            service.bootstrap_character_reference_asset(character_spec.id)
        except InvalidCharacterReferenceBootstrap:
            pass
        else:
            raise AssertionError(
                "Bootstrap accepted a character AssetSpec without identity lineage."
            )
        repository.update_asset_spec(character_spec)

        ensure_character_reference_set(
            repository, storage_root, character_spec.character_profile_id
        )
        try:
            service.bootstrap_character_reference_asset(character_spec.id)
        except InvalidCharacterReferenceBootstrap:
            pass
        else:
            raise AssertionError("Bootstrap continued after a CharacterReferenceSet existed.")
        assert generator.inputs == []
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM generation_executions").fetchone()[
                0
            ]
            == executions_before + 1
        )
    finally:
        repository.close()


def test_character_reference_bootstrap_isolated_to_the_exact_character_profile(tmp_path) -> None:
    """A reference set for profile A cannot block explicit bootstrap for profile B."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    try:
        first_profile_id = "character-profile-similarstoic-hamster-core-v1"
        ensure_character_reference_set(repository, storage_root, first_profile_id)
        second_profile = repository.create_character_profile(
            "character-profile-bootstrap-isolation-v1",
            "bootstrap-isolation",
            1,
            "Bootstrap isolation hamster",
            "A distinct test CharacterProfile for bootstrap isolation.",
            "Depict the distinct test hamster consistently.",
        )
        asset_spec = repository.create_asset_spec(
            "asset-spec-bootstrap-isolation-v1",
            "scene-isa-deadline-video-v1-01",
            "character",
            "Bootstrap a distinct profile's first legitimate reference candidate.",
            "A distinct hamster performs a meaningful Scene-owned action.",
            "Illustrate the distinct test hamster carrying out the Scene action.",
            character_profile_id=second_profile.id,
        )
        generator = FakeImageGenerator()
        result = GenerationService(
            repository, generator, LocalAssetStorage(storage_root)
        ).bootstrap_character_reference_asset(asset_spec.id)

        assert result.asset is not None
        assert len(generator.inputs) == 1
        assert result.execution.character_profile_id == second_profile.id
        assert result.execution.character_reference_set_id is None
        assert result.execution.generation_input["schema_version"] == 3
        assert repository.get_latest_character_reference_set(second_profile.id) is None
    finally:
        repository.close()


def test_v4_freezes_highest_ordered_reference_set_and_execution_lineage(tmp_path) -> None:
    """Later reference selections cannot rewrite a historical grounded request."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    profile_id = "character-profile-similarstoic-hamster-core-v1"
    try:
        first_set_id = ensure_character_reference_set(repository, storage_root, profile_id)
        first = GenerationService(
            repository, FakeImageGenerator(), LocalAssetStorage(storage_root)
        ).generate_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        assert first.asset is not None
        frozen = first.execution.generation_input["character_references"]
        assert first.execution.character_reference_set_id == first_set_id
        assert frozen["intent"] == "character_identity_grounding"
        assert frozen["reference_set_id"] == first_set_id
        assert frozen["reference_set_version"] == 1
        assert [member["position"] for member in frozen["members"]] == [1]
        assert frozen["members"][0]["asset_id"] == "asset-test-reference-basis-" + profile_id
        assert (
            frozen["members"][0]["content_digest"]
            == sha256(b"historical reference png bytes").hexdigest()
        )
        assert frozen["members"][0]["media_type"] == "image/png"
        assert "reference_images" not in first.execution.generation_input

        later_set = repository.create_character_reference_set(
            "character-reference-set-later-v2",
            profile_id,
            [first.asset.id, frozen["members"][0]["asset_id"]],
        )
        assert later_set.version == 2
        second_generator = FakeImageGenerator()
        second = GenerationService(
            repository, second_generator, LocalAssetStorage(storage_root)
        ).generate_asset_spec("asset-spec-isa-scene-03-hamster-reaction-v1")
        assert second.execution.character_reference_set_id == later_set.id
        second_references = second.execution.generation_input["character_references"]
        assert second_references["reference_set_id"] == later_set.id
        assert [member["position"] for member in second_references["members"]] == [1, 2]
        runtime_references = second_generator.inputs[0].reference_images
        assert [image.asset_id for image in runtime_references] == [
            member["asset_id"] for member in second_references["members"]
        ]
        assert [image.position for image in runtime_references] == [1, 2]
        assert [sha256(image.content).hexdigest() for image in runtime_references] == [
            member["content_digest"] for member in second_references["members"]
        ]
        assert repository.get_generation_execution(first.execution.id).generation_input == (
            first.execution.generation_input
        )
        assert (
            repository.generation_execution_payload(first.execution.id)[
                "character_reference_set_id"
            ]
            == first_set_id
        )
    finally:
        repository.close()


def test_reference_byte_failures_stop_before_provider_attempt(tmp_path) -> None:
    """Reference file availability, path safety, and byte identity are pre-provider checks."""

    for mutation in ("missing", "unsafe", "digest_mismatch", "unsupported_media"):
        storage_root = tmp_path / mutation
        repository = AtlasRepository(tmp_path / f"{mutation}.db", asset_storage_root=storage_root)
        asset_spec_id = "asset-spec-isa-scene-01-hamster-sorting-v1"
        try:
            reference_set_id = ensure_character_reference_set(repository, storage_root)
            member = repository.list_character_reference_set_members(reference_set_id)[0]
            asset = repository.get_asset(member.asset_id)
            path = storage_root / asset.storage_path
            if mutation == "missing":
                path.unlink()
            elif mutation == "unsafe":
                with repository.connection:
                    repository.connection.execute(
                        "UPDATE assets SET storage_path = ? WHERE id = ?",
                        ("../outside.png", asset.id),
                    )
            elif mutation == "digest_mismatch":
                path.write_bytes(b"altered reference bytes")
            else:
                with repository.connection:
                    repository.connection.execute(
                        "UPDATE assets SET media_type = ? WHERE id = ?", ("text/plain", asset.id)
                    )
            generator = FakeImageGenerator()
            try:
                GenerationService(
                    repository, generator, LocalAssetStorage(storage_root)
                ).generate_asset_spec(asset_spec_id)
            except ValueError:
                pass
            else:
                raise AssertionError(f"{mutation} reference bytes reached the provider.")
            assert repository.list_generation_executions_for_asset_spec(asset_spec_id) == []
            assert generator.inputs == []
        finally:
            repository.close()


def test_openai_reference_request_preserves_order_and_keeps_bytes_runtime_only() -> None:
    """OpenAI receives ordered multipart image references without persistence leakage."""

    captured = {}

    class Response:
        headers = {"x-request-id": "request-openai-test"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        @staticmethod
        def read() -> bytes:
            return b'{"created": 1, "data": [{"b64_json": "b3V0cHV0"}]}'

    def opener(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    references = (
        ReferenceImage("asset-reference-first", "image/png", b"first-reference", 1),
        ReferenceImage("asset-reference-second", "image/jpeg", b"second-reference", 2),
    )
    generation_input = GenerationInput(
        "character",
        "Generate the canonical hamster.",
        None,
        {},
        style={"profile_id": "style"},
        character={"profile_id": "character"},
        character_references={
            "intent": "character_identity_grounding",
            "reference_set_id": "reference-set",
            "reference_set_version": 1,
            "character_profile": {
                "profile_id": "character",
                "character_key": "hamster",
                "version": 1,
            },
            "members": [],
        },
        reference_images=references,
    )
    artifact = OpenAIImageGenerator(api_key="test-key", opener=opener).generate(generation_input)
    request = captured["request"]
    body = request.data
    assert request.full_url == "https://api.openai.com/v1/images/edits"
    assert request.headers["Content-type"].startswith("multipart/form-data; boundary=")
    assert body.count(b'name="image[]"') == 2
    assert body.index(b"first-reference") < body.index(b"second-reference")
    assert body.index(b"reference-1.png") < body.index(b"reference-2.jpg")
    assert generation_input.payload()["schema_version"] == 4
    assert b"first-reference" not in json.dumps(generation_input.payload()).encode()
    assert artifact.content == b"output"


def test_provider_attempt_boundaries_preserve_reference_lineage(tmp_path) -> None:
    """Configuration failure has no execution; network failure retains frozen reference lineage."""

    storage_root = tmp_path / "assets"
    repository = AtlasRepository(tmp_path / "atlas.db", asset_storage_root=storage_root)
    asset_spec_id = "asset-spec-isa-scene-01-hamster-sorting-v1"
    try:
        reference_set_id = ensure_character_reference_set(repository, storage_root)
        no_key = GenerationService(
            repository, OpenAIImageGenerator(api_key=""), LocalAssetStorage(storage_root)
        )
        try:
            no_key.generate_asset_spec(asset_spec_id)
        except MissingProviderConfiguration:
            pass
        else:
            raise AssertionError(
                "Missing OpenAI configuration reached the provider-attempt history."
            )
        assert repository.list_generation_executions_for_asset_spec(asset_spec_id) == []

        def failing_opener(_request, timeout):
            raise URLError("offline")

        failed = GenerationService(
            repository,
            OpenAIImageGenerator(api_key="test-key", opener=failing_opener),
            LocalAssetStorage(storage_root),
        ).generate_asset_spec(asset_spec_id)
        assert failed.asset is None
        assert failed.execution.outcome == "failed"
        assert failed.execution.error_code == "network_error"
        assert failed.execution.character_reference_set_id == reference_set_id
        assert failed.execution.generation_input["character_references"]["reference_set_id"] == (
            reference_set_id
        )

        def failing_http_opener(request, timeout):
            raise HTTPError(
                request.full_url,
                400,
                "Bad Request",
                {"x-request-id": "request-http-failure"},
                BytesIO(b'{"error": {"message": "Rejected", "code": "rejected"}}'),
            )

        http_failed = GenerationService(
            repository,
            OpenAIImageGenerator(api_key="test-key", opener=failing_http_opener),
            LocalAssetStorage(storage_root),
        ).generate_asset_spec(asset_spec_id)
        assert http_failed.asset is None
        assert http_failed.execution.outcome == "failed"
        assert http_failed.execution.error_code == "rejected"
        assert http_failed.execution.character_reference_set_id == reference_set_id
        try:
            with repository.connection:
                repository.connection.execute(
                    "DELETE FROM character_reference_sets WHERE id = ?", (reference_set_id,)
                )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("Consumed CharacterReferenceSet provenance was deleted.")
    finally:
        repository.close()
