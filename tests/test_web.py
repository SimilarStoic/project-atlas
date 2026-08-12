"""Tests for the local MVP UI shell."""

import json
import threading
from dataclasses import replace
from pathlib import Path
from urllib.request import Request, urlopen

from project_atlas.demo_data import chat_reply, content_payload, opportunity_payload
from project_atlas.generation import GeneratedArtifact, GenerationFailure
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
        assert payload["asset"]["generation_execution_id"] == payload["execution"]["id"]
        assert generator.inputs[0].prompt == asset_spec.generation_prompt
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
