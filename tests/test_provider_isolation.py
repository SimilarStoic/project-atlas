"""Every test runs without provider keys and cannot reach a provider over the network."""

from __future__ import annotations

import os
import socket
import urllib.request

import pytest

from project_atlas.generation import GenerationFailure, GenerationInput, OpenAIImageGenerator
from tests.conftest import PROVIDER_KEY_VARIABLES, ProviderIsolationError


def test_provider_keys_are_absent_in_every_test() -> None:
    assert not [name for name in PROVIDER_KEY_VARIABLES if name in os.environ]
    assert not [name for name in os.environ if name.endswith("_API_KEY")]


def test_a_provider_host_cannot_be_reached() -> None:
    with pytest.raises(ProviderIsolationError):
        socket.getaddrinfo("api.openai.com", 443)
    with pytest.raises(ProviderIsolationError):
        socket.create_connection(("93.184.216.34", 443), timeout=1)
    with pytest.raises(OSError):
        urllib.request.urlopen("https://api.inworld.ai/", timeout=1)


def test_an_unmocked_image_call_fails_without_spending() -> None:
    # Even with a key supplied in code, the request cannot leave the machine; the adapter
    # records it as a network failure.
    generator = OpenAIImageGenerator(api_key="not-a-real-key")
    with pytest.raises(GenerationFailure) as failure:
        generator.generate(GenerationInput("environment", "x", None, {}))
    assert failure.value.error_code == "network_error"


def test_loopback_stays_available() -> None:
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    client = socket.create_connection(server.getsockname(), timeout=1)
    client.close()
    server.close()
