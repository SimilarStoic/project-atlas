"""Tests for the local MVP UI shell."""

import json
import threading
from dataclasses import replace
from pathlib import Path
from urllib.request import urlopen

from project_atlas.demo_data import chat_reply, content_payload, opportunity_payload
from project_atlas.web import create_server


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


def test_content_endpoint_adapts_persisted_research_and_angle_without_changing_demo_package(
    tmp_path: Path,
) -> None:
    """The Content Workspace receives v0.4 data plus its remaining demo content fields."""

    server = create_server(port=0, database_path=tmp_path / "atlas.db")
    try:
        angle = server.repository.get_editorial_angle("editorial-angle-isa-decision-tree-v1")
        server.repository.update_editorial_angle(
            replace(angle, thesis="A persisted thesis exposed through the Content Workspace.")
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
        assert content["script"] == content_payload()["script"]
        assert content["scene_plan"] == content_payload()["scene_plan"]
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
