"""Founder-operated, read-only YouTube OAuth exact-channel preflight."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
EXPECTED_CHANNEL_ID = "UC1cX-OTF9-LZeNo5TaFgrgQ"
CHANNELS_ENDPOINT = "https://www.googleapis.com/youtube/v3/channels"
PREFLIGHT_VERSION = "youtube-channel-preflight-v1"
KEYRING_SERVICE = "project-atlas-youtube-oauth"
KEYRING_ACCOUNT = EXPECTED_CHANNEL_ID


class CredentialView(Protocol):
    valid: bool
    expired: bool
    scopes: list[str] | tuple[str, ...] | None
    granted_scopes: list[str] | tuple[str, ...] | None
    refresh_token: str | None


class ReadOnlyChannelClient(Protocol):
    def authenticated_channel_ids(self, credentials: CredentialView) -> list[str]: ...


class RefreshTokenStore(Protocol):
    def get(self) -> str | None: ...

    def set(self, refresh_token: str) -> None: ...


@dataclass(frozen=True)
class ChannelPreflightResult:
    schema: str
    status: str
    error_category: str | None
    expected_channel_id: str
    observed_channel_id: str | None
    exact_match: bool
    granted_scopes: tuple[str, ...]
    verified_at: str
    oauth_client_type: str
    api_call: str
    refresh_capable: bool

    def evidence(self) -> dict[str, Any]:
        return asdict(self)


class PreflightBlocked(RuntimeError):
    """Sanitized, credential-free preflight failure."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


def _scope_set(credentials: CredentialView) -> set[str]:
    return set(credentials.granted_scopes or credentials.scopes or ())


def verify_exact_channel(
    credentials: CredentialView,
    client: ReadOnlyChannelClient,
    *,
    expected_channel_id: str = EXPECTED_CHANNEL_ID,
    now: datetime | None = None,
) -> ChannelPreflightResult:
    """Return only normalized evidence; no Google object crosses this boundary."""

    verified_at = (now or datetime.now(UTC)).replace(microsecond=0).isoformat()
    scopes = _scope_set(credentials)
    common = {
        "schema": PREFLIGHT_VERSION,
        "expected_channel_id": expected_channel_id,
        "granted_scopes": tuple(sorted(scopes)),
        "verified_at": verified_at,
        "oauth_client_type": "desktop",
        "api_call": "channels.list(part=id,mine=true)",
        "refresh_capable": bool(credentials.refresh_token),
    }

    def blocked(category: str, observed: str | None = None) -> ChannelPreflightResult:
        return ChannelPreflightResult(
            status="BLOCKER",
            error_category=category,
            observed_channel_id=observed,
            exact_match=False,
            **common,
        )

    if not credentials.valid or credentials.expired:
        return blocked("authorization_unusable")
    if YOUTUBE_READONLY_SCOPE not in scopes:
        return blocked("required_scope_missing")
    if scopes != {YOUTUBE_READONLY_SCOPE}:
        return blocked("unexpected_scope_granted")
    try:
        channel_ids = client.authenticated_channel_ids(credentials)
    except PreflightBlocked as exc:
        return blocked(exc.category)
    if not channel_ids:
        return blocked("authenticated_channel_missing")
    if len(channel_ids) != 1:
        return blocked("authenticated_channel_ambiguous")
    observed = channel_ids[0]
    if observed != expected_channel_id:
        return blocked("authenticated_channel_mismatch", observed)
    return ChannelPreflightResult(
        status="PASS",
        error_category=None,
        observed_channel_id=observed,
        exact_match=True,
        **common,
    )


def _read_json(path: Path, category: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreflightBlocked(category) from exc
    if not isinstance(value, dict):
        raise PreflightBlocked(category)
    return value


def _client_config(path: Path) -> dict[str, Any]:
    value = _read_json(path, "client_configuration_invalid")
    installed = value.get("installed")
    required = {"client_id", "client_secret", "auth_uri", "token_uri"}
    if not isinstance(installed, dict) or not required <= installed.keys():
        raise PreflightBlocked("client_configuration_invalid")
    return value


def _outside_repository(path: Path, repository_root: Path) -> None:
    try:
        path.resolve().relative_to(repository_root.resolve())
    except ValueError:
        return
    raise PreflightBlocked("credential_path_inside_repository")


def _write_sanitized_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"))
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    os.replace(temporary, path)
    os.chmod(path, 0o600)


class WindowsCredentialRefreshTokenStore:
    """Store one refresh token in the native Windows Credential Locker."""

    def __init__(self, keyring_module: Any | None = None) -> None:
        self._keyring_module = keyring_module

    def _native_keyring(self) -> Any:
        try:
            if self._keyring_module is None:
                import keyring

                module = keyring
            else:
                module = self._keyring_module
            backend = module.get_keyring()
        except Exception as exc:
            raise PreflightBlocked("credential_store_unavailable") from exc
        backend_type = type(backend)
        if (
            backend_type.__module__ != "keyring.backends.Windows"
            or backend_type.__name__ != "WinVaultKeyring"
        ):
            raise PreflightBlocked("credential_store_unavailable")
        return module

    def get(self) -> str | None:
        module = self._native_keyring()
        try:
            refresh_token = module.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
        except Exception as exc:
            raise PreflightBlocked("credential_store_unavailable") from exc
        if refresh_token is None:
            return None
        if not isinstance(refresh_token, str) or not refresh_token.strip():
            raise PreflightBlocked("credential_store_invalid")
        return refresh_token

    def set(self, refresh_token: str) -> None:
        if not isinstance(refresh_token, str) or not refresh_token.strip():
            raise PreflightBlocked("credential_store_invalid")
        module = self._native_keyring()
        try:
            module.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, refresh_token)
        except Exception as exc:
            raise PreflightBlocked("credential_store_unavailable") from exc


class GoogleInstalledCredentialProvider:
    """Google-specific credential handling; tokens never enter domain provenance."""

    def __init__(
        self,
        client_config: Path,
        refresh_store: RefreshTokenStore,
        repository_root: Path,
    ) -> None:
        _outside_repository(client_config, repository_root)
        self.client_config = client_config
        self.refresh_store = refresh_store

    def acquire(self) -> CredentialView:
        config = _client_config(self.client_config)
        installed = config["installed"]
        try:
            from google.auth.exceptions import RefreshError
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            raise PreflightBlocked("oauth_dependency_unavailable") from exc

        credentials: Any
        refresh_token = self.refresh_store.get()
        if refresh_token is not None:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri=installed["token_uri"],
                client_id=installed["client_id"],
                client_secret=installed["client_secret"],
                scopes=[YOUTUBE_READONLY_SCOPE],
            )
            try:
                credentials.refresh(Request())
            except RefreshError as exc:
                raise PreflightBlocked("authorization_unusable") from exc
        else:
            try:
                flow = InstalledAppFlow.from_client_config(
                    config,
                    scopes=[YOUTUBE_READONLY_SCOPE],
                    autogenerate_code_verifier=True,
                )
                credentials = flow.run_local_server(
                    host="127.0.0.1",
                    port=0,
                    open_browser=True,
                    authorization_prompt_message="",
                    success_message=(
                        "Conveyor read-only channel authorization completed. "
                        "You may close this tab."
                    ),
                    access_type="offline",
                    prompt="consent",
                    include_granted_scopes="false",
                )
            except Exception as exc:
                raise PreflightBlocked("interactive_authorization_failed") from exc
            if not credentials.refresh_token:
                raise PreflightBlocked("refresh_token_missing")
            self.refresh_store.set(credentials.refresh_token)
        return credentials


class GoogleReadOnlyChannelClient:
    """One read-only endpoint only; intentionally exposes no mutation method."""

    def authenticated_channel_ids(self, credentials: CredentialView) -> list[str]:
        try:
            from google.auth.transport.requests import AuthorizedSession

            response = AuthorizedSession(credentials).get(
                CHANNELS_ENDPOINT,
                params={"part": "id", "mine": "true", "maxResults": 50},
                timeout=30,
            )
        except Exception as exc:
            raise PreflightBlocked("youtube_request_failed") from exc
        if response.status_code in {401, 403}:
            raise PreflightBlocked("authorization_unusable")
        if response.status_code != 200:
            raise PreflightBlocked("youtube_request_failed")
        try:
            payload = response.json()
            items = payload["items"]
            ids = [item["id"] for item in items]
        except (KeyError, TypeError, ValueError) as exc:
            raise PreflightBlocked("youtube_response_invalid") from exc
        if any(not isinstance(item, str) or not item for item in ids):
            raise PreflightBlocked("youtube_response_invalid")
        return ids


def execute_live_preflight(
    client_config: Path,
    repository_root: Path,
    credential_store: RefreshTokenStore | None = None,
) -> ChannelPreflightResult:
    provider = GoogleInstalledCredentialProvider(
        client_config,
        credential_store or WindowsCredentialRefreshTokenStore(),
        repository_root,
    )
    try:
        credentials = provider.acquire()
    except PreflightBlocked as exc:
        return ChannelPreflightResult(
            schema=PREFLIGHT_VERSION,
            status="BLOCKER",
            error_category=exc.category,
            expected_channel_id=EXPECTED_CHANNEL_ID,
            observed_channel_id=None,
            exact_match=False,
            granted_scopes=(),
            verified_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
            oauth_client_type="desktop",
            api_call="channels.list(part=id,mine=true)",
            refresh_capable=False,
        )
    return verify_exact_channel(credentials, GoogleReadOnlyChannelClient())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-config", type=Path, required=True)
    parser.add_argument("--result-file", type=Path, required=True)
    args = parser.parse_args(argv)
    repository_root = Path(__file__).resolve().parents[2]
    _outside_repository(args.result_file, repository_root)
    result = execute_live_preflight(args.client_config, repository_root)
    _write_sanitized_json(args.result_file, result.evidence())
    print(json.dumps(result.evidence(), sort_keys=True))
    return 0 if result.status == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
