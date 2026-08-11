"""Tests for the local MVP UI shell."""

from project_atlas.demo_data import chat_reply, content_payload, opportunity_payload
from project_atlas.web import create_server


def test_demo_data_represents_future_content_concepts() -> None:
    """Demo data keeps opportunities and content-package concepts separate."""

    assert 5 <= len(opportunity_payload()) <= 10
    assert {"claim_count", "source_count", "lifecycle"} <= content_payload().keys()


def test_demo_chat_is_local_and_deterministic() -> None:
    """The local chat is useful without a model integration."""

    assert "ISA" in chat_reply("What should we make tomorrow?")


def test_server_can_be_created_for_local_use() -> None:
    """The server binds an ephemeral local port for testability."""

    server = create_server(port=0)
    try:
        assert server.server_address[1] > 0
    finally:
        server.server_close()
