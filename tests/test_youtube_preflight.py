"""Network-free proofs for the narrow YouTube OAuth identity boundary."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from project_atlas.youtube_preflight import (
    EXPECTED_CHANNEL_ID,
    KEYRING_ACCOUNT,
    KEYRING_SERVICE,
    YOUTUBE_READONLY_SCOPE,
    GoogleInstalledCredentialProvider,
    GoogleReadOnlyChannelClient,
    PreflightBlocked,
    WindowsCredentialRefreshTokenStore,
    verify_exact_channel,
)

NOW = datetime(2026, 9, 16, 9, 0, tzinfo=UTC)


@dataclass
class FakeCredentials:
    valid: bool = True
    expired: bool = False
    scopes: tuple[str, ...] = (YOUTUBE_READONLY_SCOPE,)
    granted_scopes: tuple[str, ...] | None = None
    refresh_token: str | None = "synthetic-refresh-capability"


class FakeReadOnlyClient:
    def __init__(self, channel_ids: list[str] | None = None, error: str | None = None) -> None:
        self.channel_ids = channel_ids if channel_ids is not None else [EXPECTED_CHANNEL_ID]
        self.error = error
        self.calls = 0

    def authenticated_channel_ids(self, credentials) -> list[str]:
        self.calls += 1
        if self.error:
            raise PreflightBlocked(self.error)
        return self.channel_ids


def test_exact_authenticated_channel_passes_with_only_readonly_scope():
    client = FakeReadOnlyClient()
    result = verify_exact_channel(FakeCredentials(), client, now=NOW)
    assert result.status == "PASS"
    assert result.observed_channel_id == EXPECTED_CHANNEL_ID
    assert result.exact_match is True
    assert result.granted_scopes == (YOUTUBE_READONLY_SCOPE,)
    assert result.api_call == "channels.list(part=id,mine=true)"
    assert client.calls == 1


@pytest.mark.parametrize(
    ("channels", "category"),
    [
        ([], "authenticated_channel_missing"),
        (["wrong-channel"], "authenticated_channel_mismatch"),
        ([EXPECTED_CHANNEL_ID, "other-channel"], "authenticated_channel_ambiguous"),
    ],
)
def test_channel_identity_failures_are_closed(channels, category):
    result = verify_exact_channel(FakeCredentials(), FakeReadOnlyClient(channels), now=NOW)
    assert result.status == "BLOCKER"
    assert result.error_category == category
    assert result.exact_match is False


def test_missing_or_broader_scope_fails_before_api_call():
    client = FakeReadOnlyClient()
    missing = verify_exact_channel(FakeCredentials(scopes=()), client, now=NOW)
    broader = verify_exact_channel(
        FakeCredentials(scopes=(YOUTUBE_READONLY_SCOPE, "synthetic-mutation-scope")),
        client,
        now=NOW,
    )
    assert missing.error_category == "required_scope_missing"
    assert broader.error_category == "unexpected_scope_granted"
    assert client.calls == 0


@pytest.mark.parametrize(
    "credentials",
    [FakeCredentials(valid=False), FakeCredentials(expired=True)],
)
def test_expired_or_unusable_authorization_fails_before_api(credentials):
    client = FakeReadOnlyClient()
    result = verify_exact_channel(credentials, client, now=NOW)
    assert result.error_category == "authorization_unusable"
    assert client.calls == 0


def test_sanitized_provider_error_never_includes_credential_material(caplog):
    secret = "synthetic-token-that-must-not-appear"
    credentials = FakeCredentials(refresh_token=secret)
    result = verify_exact_channel(
        credentials, FakeReadOnlyClient(error="authorization_unusable"), now=NOW
    )
    serialized = json.dumps(result.evidence(), sort_keys=True)
    assert secret not in serialized
    assert secret not in caplog.text
    assert "refresh_token" not in serialized
    assert result.error_category == "authorization_unusable"


def _write_client_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "installed": {
                    "client_id": "synthetic-client",
                    "client_secret": "synthetic-secret",
                    "auth_uri": "https://accounts.invalid/auth",
                    "token_uri": "https://accounts.invalid/token",
                }
            }
        ),
        encoding="utf-8",
    )


class FakeRefreshTokenStore:
    def __init__(self, refresh_token: str | None = None, error: str | None = None) -> None:
        self.refresh_token = refresh_token
        self.error = error
        self.saved: list[str] = []

    def get(self) -> str | None:
        if self.error:
            raise PreflightBlocked(self.error)
        return self.refresh_token

    def set(self, refresh_token: str) -> None:
        if self.error:
            raise PreflightBlocked(self.error)
        self.saved.append(refresh_token)


def _native_backend():
    backend_type = type("WinVaultKeyring", (), {})
    backend_type.__module__ = "keyring.backends.Windows"
    return backend_type()


class FakeKeyringModule:
    def __init__(self, stored: str | None = None, unavailable: bool = False) -> None:
        self.stored = stored
        self.unavailable = unavailable
        self.saved: list[tuple[str, str, str]] = []

    def get_keyring(self):
        if self.unavailable:
            raise RuntimeError("synthetic unavailable backend")
        return _native_backend()

    def get_password(self, service: str, account: str) -> str | None:
        return self.stored

    def set_password(self, service: str, account: str, password: str) -> None:
        self.saved.append((service, account, password))


def test_refresh_token_is_sent_only_to_native_secure_store(tmp_path):
    secret = "synthetic-refresh-token"
    keyring_module = FakeKeyringModule()
    store = WindowsCredentialRefreshTokenStore(keyring_module)
    store.set(secret)
    assert keyring_module.saved == [(KEYRING_SERVICE, KEYRING_ACCOUNT, secret)]
    assert list(tmp_path.iterdir()) == []


def test_stored_token_reconstructs_and_refreshes_google_credentials(tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    repository.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    client_config = external / "client.json"
    _write_client_config(client_config)
    refresh_store = FakeRefreshTokenStore("stored-refresh-token")
    from google.oauth2.credentials import Credentials

    def refresh_without_network(self, request):
        self.token = "memory-only-access-token"

    monkeypatch.setattr(Credentials, "refresh", refresh_without_network)
    provider = GoogleInstalledCredentialProvider(client_config, refresh_store, repository)
    credentials = provider.acquire()
    assert credentials.refresh_token == "stored-refresh-token"
    assert credentials.token == "memory-only-access-token"
    assert refresh_store.saved == []


def test_interactive_refresh_token_is_persisted_only_through_store(tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    repository.mkdir()
    client_config = tmp_path / "client.json"
    _write_client_config(client_config)
    refresh_store = FakeRefreshTokenStore()
    credentials = FakeCredentials(refresh_token="new-refresh-token")
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = SimpleNamespace(run_local_server=lambda **kwargs: credentials)
    monkeypatch.setattr(
        InstalledAppFlow,
        "from_client_config",
        classmethod(lambda cls, config, scopes, **kwargs: flow),
    )
    provider = GoogleInstalledCredentialProvider(client_config, refresh_store, repository)
    assert provider.acquire() is credentials
    assert refresh_store.saved == ["new-refresh-token"]
    assert not any(path.name == "refresh.json" for path in tmp_path.rglob("*"))


@pytest.mark.parametrize(
    ("module", "expected"),
    [
        (FakeKeyringModule(stored=None), None),
        (FakeKeyringModule(stored=""), "credential_store_invalid"),
        (FakeKeyringModule(unavailable=True), "credential_store_unavailable"),
    ],
)
def test_secure_store_missing_corrupt_or_unavailable_fails_safely(module, expected):
    store = WindowsCredentialRefreshTokenStore(module)
    if expected is None:
        assert store.get() is None
        return
    with pytest.raises(PreflightBlocked) as error:
        store.get()
    assert error.value.category == expected


def test_malformed_client_configuration_fails_safely(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    client_config = tmp_path / "broken.json"
    client_config.write_text("{}", encoding="utf-8")
    provider = GoogleInstalledCredentialProvider(client_config, FakeRefreshTokenStore(), repository)
    with pytest.raises(PreflightBlocked) as error:
        provider.acquire()
    assert error.value.category == "client_configuration_invalid"


def test_credential_paths_inside_repository_are_rejected(tmp_path):
    repository = tmp_path / "repository"
    repository.mkdir()
    with pytest.raises(PreflightBlocked) as error:
        GoogleInstalledCredentialProvider(
            repository / "client.json", FakeRefreshTokenStore(), repository
        )
    assert error.value.category == "credential_path_inside_repository"


def test_preflight_exposes_no_mutation_surface_or_persistence_dependency():
    client = GoogleReadOnlyChannelClient()
    assert set(vars(type(client))) >= {"authenticated_channel_ids"}
    assert not any(
        hasattr(client, name)
        for name in ("insert", "update", "delete", "upload", "publish", "post")
    )
    source = (
        Path(__file__).resolve().parents[1] / "src" / "project_atlas" / "youtube_preflight.py"
    ).read_text(encoding="utf-8")
    assert "videos.insert" not in source
    assert "youtube.upload" not in source
    assert "project_atlas.persistence" not in source
    assert "AtlasRepository" not in source
    assert "refresh.json" not in source
    assert "--credential-store" not in source
