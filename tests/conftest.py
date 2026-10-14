"""Shared fixtures: provider isolation for every test, plus the YouTube consent fixtures."""

from __future__ import annotations

import ipaddress
import os
import socket

import pytest

from tests.test_publishing import setup  # noqa: F401
from tests.test_youtube_upload import env  # noqa: F401

# Every provider credential the application reads. Tests never see a real key.
PROVIDER_KEY_VARIABLES = ("OPENAI_API_KEY", "INWORLD_API_KEY", "LEONARDO_API_KEY")
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0", ""}


class ProviderIsolationError(ConnectionRefusedError):
    """A test tried to reach a non-loopback network address."""


def _is_loopback(host: object) -> bool:
    if host is None:
        return True
    text = host.decode() if isinstance(host, bytes) else str(host)
    if text.lower() in _LOCAL_HOSTS:
        return True
    try:
        return ipaddress.ip_address(text.split("%", 1)[0]).is_loopback
    except ValueError:
        return False


@pytest.fixture(autouse=True)
def provider_isolation(monkeypatch):
    """No test may hold a provider key or open a connection beyond this machine.

    Provider keys are removed from the environment and name resolution or connection to any
    non-loopback address raises, so an unmocked provider call fails loudly instead of spending.
    """

    for name in PROVIDER_KEY_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    for name in list(os.environ):
        if name.endswith("_API_KEY"):
            monkeypatch.delenv(name, raising=False)
    real_getaddrinfo = socket.getaddrinfo
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex

    def guarded_getaddrinfo(host, *args, **kwargs):
        if not _is_loopback(host):
            raise ProviderIsolationError(f"Tests may not resolve non-local host {host!r}.")
        return real_getaddrinfo(host, *args, **kwargs)

    def _check(address):
        host = address[0] if isinstance(address, tuple) else None
        if isinstance(address, tuple) and not _is_loopback(host):
            raise ProviderIsolationError(f"Tests may not connect to {address!r}.")

    def guarded_connect(self, address):
        _check(address)
        return real_connect(self, address)

    def guarded_connect_ex(self, address):
        _check(address)
        return real_connect_ex(self, address)

    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
