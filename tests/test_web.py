"""Tests for the local MVP UI shell."""

import json
import os
import threading
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from project_atlas.demo_data import chat_reply, content_payload, opportunity_payload
from project_atlas.generation import (
    GeneratedArtifact,
    GenerationFailure,
    LocalAssetStorage,
    PromptComposer,
    asset_spec_snapshot,
)
from project_atlas.web import create_server


class FakeImageGenerator:
    """Deterministic generator for HTTP tests; it never uses the network."""

    generator_key = "fake-http-image"

    def __init__(self, failure: GenerationFailure | None = None) -> None:
        self.failure = failure
        self.inputs: list[object] = []

    def supports(self, asset_type: str) -> bool:
        return asset_type in {"environment", "character", "graphic", "prop"}

    def generate(self, generation_input: object) -> GeneratedArtifact:
        self.inputs.append(generation_input)
        if self.failure:
            raise self.failure
        return GeneratedArtifact(
            b"http fake image",
            "image/png",
            provider_key="fake-http-provider",
            model_key="fake-http-model",
            provider_request_id="fake-http-request",
        )


def ensure_character_reference_set(server, storage_root: Path) -> str:
    """Seed historical v0.12 character evidence before exercising v0.13 HTTP generation."""

    repository = server.repository
    profile_id = "character-profile-similarstoic-hamster-core-v1"
    existing = repository.get_latest_character_reference_set(profile_id)
    if existing is not None:
        return existing.id
    profile = repository.get_character_profile(profile_id)
    asset_spec = repository.create_asset_spec(
        "asset-spec-http-reference-basis-v1",
        "scene-isa-deadline-video-v1-01",
        "character",
        "Historical HTTP character-reference basis.",
        "A historical character reference for HTTP tests.",
        "Illustrate the canonical hamster reference basis.",
        character_profile_id=profile.id,
    )
    storage = LocalAssetStorage(storage_root)
    content = b"http historical reference png bytes"
    stored = storage.write(asset_spec.id, "asset-http-reference-basis-v1", content, "image/png")
    style = repository.get_visual_style_profile("visual-style-profile-similarstoic-core-v2")
    repository.record_successful_generation(
        "generation-execution-http-reference-basis-v1",
        "asset-http-reference-basis-v1",
        asset_spec.id,
        asset_spec_snapshot(asset_spec),
        PromptComposer().compose(asset_spec, style, profile).payload(),
        "historical-http-generator",
        storage.relative_path(stored),
        "image/png",
        visual_style_profile_id=style.id,
        character_profile_id=profile.id,
        content_digest=sha256(content).hexdigest(),
    )
    return repository.create_character_reference_set(
        "character-reference-set-http-basis-v1", profile.id, ["asset-http-reference-basis-v1"]
    ).id


def test_demo_data_represents_future_content_concepts() -> None:
    """Demo data keeps opportunities and content-package concepts separate."""

    assert 5 <= len(opportunity_payload()) <= 10
    assert {"claim_count", "source_count", "lifecycle"} <= content_payload().keys()


def test_demo_chat_is_local_and_deterministic() -> None:
    """The local chat is useful without a model integration."""

    assert "ISA" in chat_reply("What should we make tomorrow?")


def test_server_can_be_created_for_local_use(tmp_path: Path) -> None:
    """The server binds an ephemeral local port for testability."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    try:
        assert server.server_address[1] > 0
    finally:
        server.server_close()


def test_content_endpoint_adapts_persisted_research_angle_piece_script_and_scenes(
    tmp_path: Path,
) -> None:
    """The Content Workspace receives persistence through v0.6 while QA remains demo-backed."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    try:
        angle = server.repository.get_editorial_angle("editorial-angle-isa-decision-tree-v1")
        server.repository.update_editorial_angle(
            replace(angle, thesis="A persisted thesis exposed through the Content Workspace.")
        )
        content_piece = server.repository.get_content_piece("content-piece-isa-deadline-video-v1")
        server.repository.update_content_piece(
            replace(content_piece, working_title="A persisted ContentPiece title.")
        )
        server.repository.create_script(
            "script-isa-deadline-video-v2",
            content_piece.id,
            2,
            "A persisted latest narration version exposed through the Content Workspace.",
        )
        visual_plan = server.repository.get_visual_plan("visual-plan-isa-deadline-video-v1")
        server.repository.update_visual_plan(
            replace(
                visual_plan,
                visual_direction=(
                    "A persisted visual direction exposed through the Content Workspace."
                ),
            )
        )
        scene = server.repository.get_scene("scene-isa-deadline-video-v1-01")
        server.repository.update_scene(
            replace(scene, visual_intent="A persisted first ordered Scene intent.")
        )
        asset_spec = server.repository.get_asset_spec(
            "asset-spec-isa-scene-01-kitchen-background-v1"
        )
        server.repository.update_asset_spec(
            replace(asset_spec, description="A persisted AssetSpec description.")
        )
        server.repository.create_asset(
            "asset-isa-kitchen-background-v1",
            asset_spec.id,
            1,
            "assets/isa-kitchen-background-v1.png",
            "image/png",
            "manual",
        )
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content") as response:
            payload = json.load(response)
        thread.join(timeout=2)
        content = payload["content"]
        assert content["visual_style"] == {
            "profile_id": "visual-style-profile-similarstoic-core-v3",
            "style_key": "similarstoic-core",
            "version": 3,
            "name": "SimilarStoic Core",
        }
        assert content["selected_angle"] == "The 15-minute ISA decision tree before the deadline."
        assert content["research"]["opportunity_id"] == "uk-isa-rules"
        assert content["research"]["version"] == 1
        assert len(content["research"]["claims"]) == 3
        assert content["research"]["claims"][0]["evidence"]
        assert content["editorial_angle"]["thesis"] == (
            "A persisted thesis exposed through the Content Workspace."
        )
        assert len(content["editorial_angles"]) == 2
        assert {claim["role"] for claim in content["editorial_angle"]["claims"]} == {
            "core",
            "supporting",
        }
        assert content["content_piece"]["working_title"] == "A persisted ContentPiece title."
        assert content["content_piece"]["latest_script"]["version"] == 2
        assert content["title"] == "A persisted ContentPiece title."
        assert content["script"] == (
            "A persisted latest narration version exposed through the Content Workspace."
        )
        assert content["visual_plan"]["visual_direction"] == (
            "A persisted visual direction exposed through the Content Workspace."
        )
        assert [scene["sequence"] for scene in content["visual_plan"]["scenes"]] == [1, 2, 3]
        assert content["visual_plan"]["scenes"][0]["visual_intent"] == (
            "A persisted first ordered Scene intent."
        )
        asset_specs = content["visual_plan"]["scenes"][0]["asset_specs"]
        assert len(asset_specs) == 2
        persisted_asset_spec = next(
            asset_spec
            for asset_spec in asset_specs
            if asset_spec["id"] == "asset-spec-isa-scene-01-kitchen-background-v1"
        )
        assert persisted_asset_spec["description"] == "A persisted AssetSpec description."
        assert persisted_asset_spec["generation_prompt"]
        persisted_asset_specs = [
            candidate
            for scene in content["visual_plan"]["scenes"]
            for candidate in scene["asset_specs"]
        ]
        assert {candidate["asset_type"] for candidate in persisted_asset_specs} == {
            "environment",
            "character",
            "graphic",
        }
        hamster_asset_spec = next(
            candidate
            for candidate in persisted_asset_specs
            if candidate["id"] == "asset-spec-isa-scene-01-hamster-sorting-v1"
        )
        assert hamster_asset_spec["character_profile"] == {
            "id": "character-profile-similarstoic-hamster-core-v1",
            "name": "SimilarStoic Hamster Core",
            "version": 1,
            "identity_description": (
                "A recognisable classic hamster with a recurring consistent identity, "
                "young-professional relatability and a small everyday sling/crossbody bag. "
                "The hamster uses hamster-native behaviour to embody SimilarStoic money, "
                "work, behaviour and life-strategy concepts, and is intended to remain "
                "recognisably the same individual across character assets."
            ),
        }
        assert persisted_asset_spec["character_profile"] is None
        assert all(
            candidate["generation_supported"]
            for candidate in persisted_asset_specs
            if candidate["asset_type"] == "character"
        )
        assert persisted_asset_spec["assets"] == [
            {
                "id": "asset-isa-kitchen-background-v1",
                "version": 1,
                "storage_path": "assets/isa-kitchen-background-v1.png",
                "media_type": "image/png",
                "source_kind": "manual",
            }
        ]
        assert all(
            not asset_spec["assets"]
            for scene in content["visual_plan"]["scenes"]
            for asset_spec in scene["asset_specs"]
            if asset_spec["id"] != "asset-spec-isa-scene-01-kitchen-background-v1"
        )
        assert content["scene_plan"] == " ".join(
            scene["visual_intent"] for scene in content["visual_plan"]["scenes"]
        )
        assert content["scene_plan"] != content_payload()["scene_plan"]
        assert content["qa"] == content_payload()["qa"]
    finally:
        server.server_close()


def test_content_endpoint_can_expose_explicitly_configured_v1_style(
    tmp_path: Path, monkeypatch
) -> None:
    """Profile selection remains configuration-only while v3 is the default."""

    monkeypatch.setenv("ATLAS_VISUAL_STYLE_PROFILE_ID", "visual-style-profile-similarstoic-core-v1")
    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    try:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content") as response:
            content = json.load(response)["content"]
        thread.join(timeout=2)
        assert content["visual_style"] == {
            "profile_id": "visual-style-profile-similarstoic-core-v1",
            "style_key": "similarstoic-core",
            "version": 1,
            "name": "SimilarStoic Core",
        }
        assert not {"selected", "current", "best", "approved"} & content["visual_style"].keys()
    finally:
        server.server_close()


def test_content_endpoint_has_no_demo_scene_plan_fallback_without_visual_plan(
    tmp_path: Path,
) -> None:
    """QA remains demo-backed when a temporary setup has no persisted VisualPlan."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    try:
        with server.repository.connection:
            server.repository.connection.execute("DELETE FROM assets")
            server.repository.connection.execute("DELETE FROM asset_specs")
            server.repository.connection.execute("DELETE FROM scenes")
            server.repository.connection.execute("DELETE FROM visual_plans")
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content") as response:
            payload = json.load(response)
        thread.join(timeout=2)
        content = payload["content"]
        assert "visual_plan" not in content
        assert "scene_plan" not in content
        assert content["qa"] == content_payload()["qa"]
    finally:
        server.server_close()


def test_demo_endpoints_keep_discover_and_chat_compatible(tmp_path: Path) -> None:
    """Persistent angle work leaves Discover, Command Centre assets, and chat deterministic."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    try:
        for path in ("/", "/api/demo/opportunities", "/api/demo/chat?message=tomorrow"):
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            with urlopen(f"http://127.0.0.1:{server.server_address[1]}{path}") as response:
                body = response.read()
            thread.join(timeout=2)
            if path == "/":
                assert b"Command Centre" in body
            elif "opportunities" in path:
                assert len(json.loads(body)["opportunities"]) == 6
            else:
                assert "ISA" in json.loads(body)["reply"]
    finally:
        server.server_close()


def test_discover_ui_exposes_minimal_persistent_idea_gate_controls() -> None:
    """Discover offers only snapshot review and immutable founder outcomes."""

    static_root = Path(__file__).parents[1] / "src/project_atlas/static"
    index = (static_root / "index.html").read_text(encoding="utf-8")
    script = (static_root / "app.js").read_text(encoding="utf-8")
    assert "idea-gate-review" in index
    assert "idea-gate-history" in index
    assert "open-idea-gate" in script
    assert 'data-outcome="Proceed"' in script
    assert 'data-outcome="Reject"' in script
    assert 'data-outcome="Steer"' in script
    assert "Steer requires founder direction." in script
    assert "/idea-gate-review-snapshots" in script
    assert "/idea-gate-history" in script
    assert "initiate-research" in script
    assert "data-decision-id" in script
    assert '"/research-packs"' in script
    assert "ResearchPack initiated with Idea Gate provenance." in script


def test_idea_gate_endpoints_freeze_reviews_and_persist_one_decision(tmp_path: Path) -> None:
    """The narrow Idea Gate API stores additive snapshots without downstream effects."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request | str) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    try:
        opportunity_id = "uk-isa-rules"
        original = server.repository.get_opportunity(opportunity_id)
        research_count = server.repository.connection.execute(
            "SELECT COUNT(*) FROM research_packs"
        ).fetchone()[0]
        snapshot_response, status = request_json(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/idea-gate-review-snapshots",
                method="POST",
            )
        )
        assert status == 201
        snapshot = snapshot_response["snapshot"]
        assert snapshot_response["kind"] == "idea_gate_review_snapshot"
        assert snapshot["payload_schema_version"] == 1
        assert snapshot["review_payload"]["opportunity"]["title"] == original.title
        assert snapshot["review_payload"]["subjects"][0]["id"] == "subject-isa"

        fetched, status = request_json(
            f"{base_url}/api/idea-gate-review-snapshots/{snapshot['id']}"
        )
        assert status == 200
        assert fetched["snapshot"] == snapshot

        thread = threading.Thread(target=server.handle_request)
        thread.start()
        invalid_steer = Request(
            f"{base_url}/api/idea-gate-review-snapshots/{snapshot['id']}/decisions",
            data=json.dumps({"outcome": "Steer", "founder_direction": "   "}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(invalid_steer)
        except HTTPError as error:
            assert error.code == 400
            assert "requires non-empty" in error.read().decode()
        else:
            raise AssertionError("Idea Gate accepted an empty Steer direction.")
        thread.join(timeout=2)

        decision_response, status = request_json(
            Request(
                f"{base_url}/api/idea-gate-review-snapshots/{snapshot['id']}/decisions",
                data=json.dumps(
                    {
                        "outcome": "Steer",
                        "founder_direction": "Lead with the practical deadline choice.",
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        assert decision_response["decision"]["outcome"] == "Steer"
        assert decision_response["decision"]["founder_direction"] == (
            "Lead with the practical deadline choice."
        )

        server.repository.update_opportunity(
            replace(original, title="A later mutable Opportunity presentation")
        )
        history, status = request_json(
            f"{base_url}/api/opportunities/{opportunity_id}/idea-gate-history"
        )
        assert status == 200
        assert history["history"][0]["snapshot"]["review_payload"]["opportunity"]["title"] == (
            original.title
        )
        assert history["history"][0]["decision"]["id"] == decision_response["decision"]["id"]
        assert server.repository.get_opportunity(opportunity_id).status == original.status
        assert (
            server.repository.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[
                0
            ]
            == research_count
        )

        thread = threading.Thread(target=server.handle_request)
        thread.start()
        duplicate = Request(
            f"{base_url}/api/idea-gate-review-snapshots/{snapshot['id']}/decisions",
            data=json.dumps({"outcome": "Proceed"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(duplicate)
        except HTTPError as error:
            assert error.code == 400
            assert "only one decision" in error.read().decode()
        else:
            raise AssertionError("Idea Gate accepted a second decision for one snapshot.")
        thread.join(timeout=2)
    finally:
        server.server_close()


def test_research_pack_initiation_endpoint_preserves_idea_gate_provenance(tmp_path: Path) -> None:
    """The narrow API deliberately creates only qualifying provenance-linked ResearchPacks."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    def request_error(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            urlopen(request)
        except HTTPError as error:
            payload = json.loads(error.read())
            status = error.code
        else:
            raise AssertionError("The invalid research-initiation request unexpectedly succeeded.")
        thread.join(timeout=2)
        return payload, status

    def initiate(opportunity_id: str, payload: dict) -> tuple[dict, int]:
        return request_json(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )

    try:
        repository = server.repository
        opportunity_id = "uk-isa-rules"
        original_status = repository.get_opportunity(opportunity_id).status
        initial_count = repository.connection.execute(
            "SELECT COUNT(*) FROM research_packs"
        ).fetchone()[0]

        proceed_snapshot = repository.create_idea_gate_review_snapshot(
            "http-initiation-proceed-snapshot", opportunity_id
        )
        proceed = repository.record_idea_gate_decision(
            "http-initiation-proceed-decision", proceed_snapshot.id, "Proceed"
        )
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[0]
            == initial_count
        )
        created, status = initiate(
            opportunity_id,
            {
                "id": "research-pack-http-proceed-v2",
                "version": 2,
                "summary": "A deliberately initiated Proceed ResearchPack.",
                "idea_gate_decision_id": proceed.id,
            },
        )
        assert status == 201
        assert created["kind"] == "research_pack"
        research_pack = created["research_pack"]
        assert research_pack["id"] == "research-pack-http-proceed-v2"
        assert research_pack["opportunity_id"] == opportunity_id
        assert research_pack["idea_gate_decision_id"] == proceed.id
        assert research_pack["idea_gate_provenance"]["decision"]["outcome"] == "Proceed"
        assert research_pack["idea_gate_provenance"]["snapshot"]["id"] == proceed_snapshot.id

        steer_snapshot = repository.create_idea_gate_review_snapshot(
            "http-initiation-steer-snapshot", opportunity_id
        )
        steer = repository.record_idea_gate_decision(
            "http-initiation-steer-decision",
            steer_snapshot.id,
            "Steer",
            founder_direction="Lead with the practical deadline choice.",
        )
        created, status = initiate(
            opportunity_id,
            {
                "id": "research-pack-http-steer-v3",
                "version": 3,
                "summary": "A deliberately initiated Steer ResearchPack.",
                "idea_gate_decision_id": steer.id,
                "metadata": {"review": "manual"},
            },
        )
        assert status == 201
        assert (
            created["research_pack"]["idea_gate_provenance"]["decision"]["founder_direction"]
            == "Lead with the practical deadline choice."
        )
        assert repository.get_research_pack("research-pack-http-steer-v3").metadata == {
            "review": "manual"
        }

        reject_snapshot = repository.create_idea_gate_review_snapshot(
            "http-initiation-reject-snapshot", opportunity_id
        )
        reject = repository.record_idea_gate_decision(
            "http-initiation-reject-decision", reject_snapshot.id, "Reject"
        )
        payload, status = request_error(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=json.dumps(
                    {
                        "id": "research-pack-http-reject-v4",
                        "version": 4,
                        "summary": "This must not be created.",
                        "idea_gate_decision_id": reject.id,
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "Proceed or Steer" in payload["error"]

        payload, status = request_error(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=json.dumps(
                    {
                        "id": "research-pack-http-missing-v4",
                        "version": 4,
                        "summary": "This must not be created.",
                        "idea_gate_decision_id": "missing-decision",
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 404
        assert "not found" in payload["error"]

        other_snapshot = repository.create_idea_gate_review_snapshot(
            "http-initiation-other-snapshot", "credit-utilisation"
        )
        other_decision = repository.record_idea_gate_decision(
            "http-initiation-other-decision", other_snapshot.id, "Proceed"
        )
        payload, status = request_error(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=json.dumps(
                    {
                        "id": "research-pack-http-mismatch-v4",
                        "version": 4,
                        "summary": "This must not be created.",
                        "idea_gate_decision_id": other_decision.id,
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "must belong" in payload["error"]

        payload, status = request_error(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=json.dumps(
                    {
                        "id": "research-pack-http-duplicate-v2",
                        "version": 2,
                        "summary": "Duplicate version.",
                        "idea_gate_decision_id": proceed.id,
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "UNIQUE constraint failed" in payload["error"]

        payload, status = request_error(
            Request(
                f"{base_url}/api/opportunities/{opportunity_id}/research-packs",
                data=b"[]",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "must be an object" in payload["error"]
        assert repository.get_opportunity(opportunity_id).status == original_status
        assert (
            repository.connection.execute("SELECT COUNT(*) FROM research_packs").fetchone()[0]
            == initial_count + 2
        )
    finally:
        server.server_close()


def test_generation_endpoint_uses_persisted_prompt_and_exposes_execution(tmp_path: Path) -> None:
    """POST generation ignores caller prompt text and returns durable provenance."""

    generator = FakeImageGenerator()
    server = create_server(
        port=0,
        database_path=tmp_path / "atlas.db",
        generator=generator,
        asset_storage_root=tmp_path / "assets",
    )
    try:
        asset_spec = server.repository.get_asset_spec(
            "asset-spec-isa-scene-01-kitchen-background-v1"
        )
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        request = Request(
            f"http://127.0.0.1:{server.server_address[1]}/api/asset-specs/{asset_spec.id}/generate",
            data=b'{"prompt":"caller supplied replacement"}',
            method="POST",
        )
        with urlopen(request) as response:
            payload = json.load(response)
        thread.join(timeout=2)
        assert payload["execution"]["outcome"] == "succeeded"
        assert (
            payload["execution"]["visual_style_profile_id"]
            == "visual-style-profile-similarstoic-core-v3"
        )
        assert payload["asset"]["generation_execution_id"] == payload["execution"]["id"]
        assert asset_spec.generation_prompt in generator.inputs[0].prompt
        assert generator.inputs[0].style["style_key"] == "similarstoic-core"
        assert (
            tmp_path / "assets" / server.repository.get_asset(payload["asset"]["id"]).storage_path
        ).exists()

        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content") as response:
            content = json.load(response)["content"]
        thread.join(timeout=2)
        persisted_spec = next(
            candidate
            for scene in content["visual_plan"]["scenes"]
            for candidate in scene["asset_specs"]
            if candidate["id"] == asset_spec.id
        )
        assert persisted_spec["generation_executions"][-1]["outcome"] == "succeeded"
        assert persisted_spec["assets"][-1]["generation_execution_id"] == payload["execution"]["id"]
        assert persisted_spec["generation_supported"] is True
    finally:
        server.server_close()


def test_generation_endpoint_represents_provider_failure_without_asset(tmp_path: Path) -> None:
    """A provider failure is visible to the Workspace but does not register an Asset."""

    server = create_server(
        port=0,
        database_path=tmp_path / "atlas.db",
        generator=FakeImageGenerator(
            GenerationFailure("Fake provider rejected generation.", error_code="rejected")
        ),
        asset_storage_root=tmp_path / "assets",
    )
    try:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        request = Request(
            "http://127.0.0.1:"
            f"{server.server_address[1]}/api/asset-specs/"
            "asset-spec-isa-scene-01-kitchen-background-v1/generate",
            method="POST",
        )
        with urlopen(request) as response:
            payload = json.load(response)
        thread.join(timeout=2)
        assert payload["execution"]["outcome"] == "failed"
        assert payload["execution"]["error_code"] == "rejected"
        assert payload["asset"] is None
        assert (
            server.repository.connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0] == 0
        )
    finally:
        server.server_close()


def test_bootstrap_reference_endpoint_is_explicit_and_stops_after_first_set(tmp_path: Path) -> None:
    """The local UI API exposes first-reference generation without changing normal generation."""

    storage_root = tmp_path / "assets"
    generator = FakeImageGenerator()
    server = create_server(
        port=0,
        database_path=tmp_path / "atlas.db",
        generator=generator,
        asset_storage_root=storage_root,
    )
    try:
        asset_spec_id = "asset-spec-isa-scene-01-hamster-sorting-v1"

        def request_json(request: Request | str) -> tuple[dict, int]:
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            with urlopen(request) as response:
                payload = json.load(response)
                status = response.status
            thread.join(timeout=2)
            return payload, status

        content, _ = request_json(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content")
        character_spec = next(
            candidate
            for scene in content["content"]["visual_plan"]["scenes"]
            for candidate in scene["asset_specs"]
            if candidate["id"] == asset_spec_id
        )
        assert character_spec["bootstrap_reference_generation_available"] is True

        bootstrapped, status = request_json(
            Request(
                "http://127.0.0.1:"
                f"{server.server_address[1]}/api/asset-specs/{asset_spec_id}/"
                "bootstrap-character-reference",
                method="POST",
            )
        )
        assert status == 200
        assert bootstrapped["kind"] == "character_reference_bootstrap"
        assert bootstrapped["execution"]["character_reference_set_id"] is None
        assert bootstrapped["asset"] is not None
        assert len(generator.inputs) == 1
        assert generator.inputs[0].payload()["schema_version"] == 3

        profile_id = "character-profile-similarstoic-hamster-core-v1"
        reference_set, status = request_json(
            Request(
                "http://127.0.0.1:"
                f"{server.server_address[1]}/api/character-profiles/{profile_id}/reference-sets",
                data=json.dumps({"asset_ids": [bootstrapped["asset"]["id"]]}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        assert reference_set["reference_set"]["version"] == 1

        thread = threading.Thread(target=server.handle_request)
        thread.start()
        blocked_request = Request(
            "http://127.0.0.1:"
            f"{server.server_address[1]}/api/asset-specs/{asset_spec_id}/"
            "bootstrap-character-reference",
            method="POST",
        )
        try:
            urlopen(blocked_request)
        except HTTPError as error:
            assert error.code == 400
            assert "unavailable after a CharacterReferenceSet exists" in error.read().decode()
        else:
            raise AssertionError("Bootstrap API accepted a profile with a reference set.")
        thread.join(timeout=2)
        assert len(generator.inputs) == 1

        refreshed, _ = request_json(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content")
        refreshed_spec = next(
            candidate
            for scene in refreshed["content"]["visual_plan"]["scenes"]
            for candidate in scene["asset_specs"]
            if candidate["id"] == asset_spec_id
        )
        assert refreshed_spec["bootstrap_reference_generation_available"] is False
    finally:
        server.server_close()


def test_reference_review_serves_eligible_hamster_and_creates_ordered_set(tmp_path: Path) -> None:
    """The local UI API exposes only eligible generated hamster evidence for selection."""

    storage_root = tmp_path / "assets"
    server = create_server(
        port=0,
        database_path=tmp_path / "atlas.db",
        generator=FakeImageGenerator(),
        asset_storage_root=storage_root,
    )
    profile_id = "character-profile-similarstoic-hamster-core-v1"
    ensure_character_reference_set(server, storage_root)

    def request_json(request: Request | str) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    try:
        first, _ = request_json(
            Request(
                "http://127.0.0.1:"
                f"{server.server_address[1]}/api/asset-specs/"
                "asset-spec-isa-scene-01-hamster-sorting-v1/generate",
                method="POST",
            )
        )
        second, _ = request_json(
            Request(
                "http://127.0.0.1:"
                f"{server.server_address[1]}/api/asset-specs/"
                "asset-spec-isa-scene-03-hamster-reaction-v1/generate",
                method="POST",
            )
        )
        first_asset_id = first["asset"]["id"]
        second_asset_id = second["asset"]["id"]

        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(
            f"http://127.0.0.1:{server.server_address[1]}/api/assets/{first_asset_id}/content"
        ) as response:
            assert response.headers["Content-Type"] == "image/png"
            assert response.read() == b"http fake image"
        thread.join(timeout=2)

        content, _ = request_json(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content")
        review = content["content"]["character_reference_review"]
        assert review["character_profile"]["id"] == profile_id
        assert {first_asset_id, second_asset_id} <= {
            candidate["id"] for candidate in review["eligible_assets"]
        }
        assert review["eligible_assets"][0]["content_digest"]
        assert (
            review["eligible_assets"][0]["generation_execution"]["character_profile"]["id"]
            == profile_id
        )

        created, status = request_json(
            Request(
                "http://127.0.0.1:"
                f"{server.server_address[1]}/api/character-profiles/{profile_id}/reference-sets",
                data=json.dumps({"asset_ids": [second_asset_id, first_asset_id]}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        assert created["reference_set"]["version"] == 2
        assert [member["asset"]["id"] for member in created["reference_set"]["members"]] == [
            second_asset_id,
            first_asset_id,
        ]

        content, _ = request_json(f"http://127.0.0.1:{server.server_address[1]}/api/demo/content")
        retained = content["content"]["character_reference_review"]["reference_sets"]
        assert retained[-1]["members"][0]["asset"]["content_digest"]
        assert (
            "At character-generation time, Atlas resolves the highest version"
            in (Path(__file__).parents[1] / "src/project_atlas/static/app.js").read_text()
        )
        script = (Path(__file__).parents[1] / "src/project_atlas/static/app.js").read_text()
        assert "referenceSelection.push(assetId)" in script
        assert "asset_ids: referenceSelection" in script
    finally:
        server.server_close()


def test_asset_content_endpoint_rejects_unknown_missing_and_unsafe_files(tmp_path: Path) -> None:
    """Asset content is resolved by Atlas ID and never by an arbitrary filesystem path."""

    storage_root = tmp_path / "assets"
    server = create_server(
        port=0,
        database_path=tmp_path / "atlas.db",
        generator=FakeImageGenerator(),
        asset_storage_root=storage_root,
    )
    try:
        asset_spec = server.repository.get_asset_spec("asset-spec-isa-scene-01-hamster-sorting-v1")
        ensure_character_reference_set(server, storage_root)
        missing = server.generation_service.generate_asset_spec(asset_spec.id).asset
        assert missing is not None
        (storage_root / missing.storage_path).unlink()
        unsafe = server.repository.create_asset(
            "asset-unsafe-generated-path-v1",
            asset_spec.id,
            2,
            "../outside.png",
            "image/png",
            "generated",
        )
        absolute = server.repository.create_asset(
            "asset-absolute-generated-path-v1",
            asset_spec.id,
            3,
            str((tmp_path / "outside.png").resolve()),
            "image/png",
            "generated",
        )
        unsupported_media = server.repository.create_asset(
            "asset-unsupported-media-v1",
            asset_spec.id,
            4,
            "unsupported.txt",
            "text/plain",
            "generated",
        )
        rejected_asset_ids = [
            "missing-asset",
            missing.id,
            unsafe.id,
            absolute.id,
            unsupported_media.id,
        ]
        if os.name == "nt":
            backslash_escape = server.repository.create_asset(
                "asset-backslash-generated-path-v1",
                asset_spec.id,
                5,
                r"..\outside.png",
                "image/png",
                "generated",
            )
            rejected_asset_ids.append(backslash_escape.id)
        for asset_id in rejected_asset_ids:
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            try:
                urlopen(
                    f"http://127.0.0.1:{server.server_address[1]}/api/assets/{asset_id}/content"
                )
            except HTTPError as error:
                assert error.code == 404
            else:
                raise AssertionError("Unsafe or unknown Asset content was served.")
            thread.join(timeout=2)
    finally:
        server.server_close()


def test_research_readiness_assessment_api_is_server_frozen_and_history_only(
    tmp_path: Path,
) -> None:
    """The v0.17 API persists additive assessment history without a UI or evaluator."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    base_url = f"http://127.0.0.1:{server.server_address[1]}"

    def request_json(request: Request | str) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        with urlopen(request) as response:
            payload = json.load(response)
            status = response.status
        thread.join(timeout=2)
        return payload, status

    def request_error(request: Request) -> tuple[dict, int]:
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            urlopen(request)
        except HTTPError as error:
            payload = json.loads(error.read())
            status = error.code
        else:
            raise AssertionError("The invalid readiness request unexpectedly succeeded.")
        thread.join(timeout=2)
        return payload, status

    try:
        pack_id = "research-pack-isa-deadline-v1"
        history, status = request_json(
            f"{base_url}/api/research-packs/{pack_id}/readiness-assessments"
        )
        assert status == 200
        assert history["kind"] == "research_readiness_assessment_history"
        assert history["assessments"] == []

        endpoint = f"{base_url}/api/research-packs/{pack_id}/readiness-assessments"
        base_payload = {
            "id": "http-readiness-assessment-a",
            "outcome": "Ready",
            "findings": {"summary": "The stored evidence is ready for this test."},
            "policy_version": "readiness-policy-v1",
            "producer_kind": "test",
            "producer_identifier": "http-test",
            "producer_implementation_version": "v1",
        }
        created, status = request_json(
            Request(
                endpoint,
                data=json.dumps(base_payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        assessment = created["assessment"]
        assert assessment["outcome"] == "Ready"
        assert assessment["frozen_evidence_state"]["research_pack"]["id"] == pack_id
        assert assessment["frozen_evidence_state"]["schema_version"] == 1

        fetched, status = request_json(
            f"{base_url}/api/research-readiness-assessments/{assessment['id']}"
        )
        assert status == 200
        assert fetched["assessment"] == assessment

        second_payload = base_payload | {
            "id": "http-readiness-assessment-b",
            "outcome": "Blocked",
            "findings": {"summary": "The required source is unavailable."},
        }
        created_second, status = request_json(
            Request(
                endpoint,
                data=json.dumps(second_payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 201
        history, status = request_json(endpoint)
        assert status == 200
        assert [item["id"] for item in history["assessments"]] == [
            assessment["id"],
            created_second["assessment"]["id"],
        ]

        invalid, status = request_error(
            Request(
                endpoint,
                data=json.dumps(base_payload | {"id": "http-invalid", "outcome": "ready"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "outcome" in invalid["error"]
        for key in (
            "findings",
            "policy_version",
            "producer_kind",
            "producer_identifier",
            "producer_implementation_version",
        ):
            incomplete, status = request_error(
                Request(
                    endpoint,
                    data=json.dumps(
                        {
                            item_key: value
                            for item_key, value in (base_payload | {"id": f"http-{key}"}).items()
                            if item_key != key
                        }
                    ).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
            )
            assert status == 400
            assert incomplete["error"]
        duplicate, status = request_error(
            Request(
                endpoint,
                data=json.dumps(base_payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "already exists" in duplicate["error"]
        rejected_snapshot, status = request_error(
            Request(
                endpoint,
                data=json.dumps(
                    base_payload | {"id": "http-snapshot", "frozen_evidence_state": {}}
                ).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 400
        assert "built by the server" in rejected_snapshot["error"]
        missing, status = request_error(
            Request(
                f"{base_url}/api/research-packs/missing/readiness-assessments",
                data=json.dumps(base_payload | {"id": "http-missing"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        )
        assert status == 404
        assert "ResearchPack" in missing["error"]
        missing_get, status = request_error(
            Request(
                f"{base_url}/api/research-readiness-assessments/missing",
                method="GET",
            )
        )
        assert status == 404
        assert "not found" in missing_get["error"]
    finally:
        server.server_close()
