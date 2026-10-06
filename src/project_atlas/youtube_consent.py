"""Conveyor-side YouTube consent governance (YouTube API Services Developer Policies).

* Versioned privacy-policy acceptance before any authorization or YouTube API use.
* Independent 30-day reconfirmation of the read-only and upload authorizations, performed
  automatically before API use; definitive revocation deletes the credential and purges
  YouTube API data, while a transient failure fails closed and purges nothing.
* Conveyor-side revocation (Google revoke endpoint + local credential deletion + purge) and a
  user deletion request, both usable without acceptance or a working authorization.
* Stored YouTube API payloads older than 30 days that were not refreshed are deleted.

Operational consent state (accepted policy version, last reconfirmation per authorization)
holds no secrets and lives in a small JSON file outside the repository. Losing it is safe: the
policy must be accepted again and every authorization becomes due for reconfirmation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from project_atlas.youtube_preflight import (
    EXPECTED_CHANNEL_ID,
    KEYRING_ACCOUNT,
    YOUTUBE_READONLY_SCOPE,
    GoogleInstalledCredentialProvider,
    GoogleReadOnlyChannelClient,
    PreflightBlocked,
    WindowsCredentialRefreshTokenStore,
    _outside_repository,
    _write_sanitized_json,
    verify_exact_channel,
)

# The version declared on the published policy page ("Policy version: 2026-10-06").
POLICY_VERSION = "2026-10-06"
PRIVACY_POLICY_URL = "https://conveyoros.co.uk/privacy/"
YOUTUBE_TERMS_URL = "https://www.youtube.com/t/terms"
GOOGLE_PRIVACY_URL = "https://www.google.com/policies/privacy"
GOOGLE_SECURITY_SETTINGS_URL = "https://security.google.com/settings/security/permissions"
GOOGLE_REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
RECONFIRM_AFTER = timedelta(days=30)
STATE_SCHEMA = "youtube-consent-state-v1"

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
UPLOAD_SCOPES = (YOUTUBE_READONLY_SCOPE, YOUTUBE_UPLOAD_SCOPE)
# A distinct credential-store entry: the read-only token can never satisfy an upload.
UPLOAD_KEYRING_ACCOUNT = f"{EXPECTED_CHANNEL_ID}:upload-v1"
AUTHORIZATIONS: dict[str, tuple[str, tuple[str, ...]]] = {
    "readonly": (KEYRING_ACCOUNT, (YOUTUBE_READONLY_SCOPE,)),
    "upload": (UPLOAD_KEYRING_ACCOUNT, UPLOAD_SCOPES),
}
# Failures that prove the stored authorization is revoked or no longer the approved grant.
DEFINITIVE_FAILURES = frozenset(
    {
        "authorization_revoked",
        "required_scope_missing",
        "unexpected_scope_granted",
        "authenticated_channel_mismatch",
        "authenticated_channel_missing",
        "authenticated_channel_ambiguous",
    }
)
DELETION_NOTICE = (
    "This deletes the YouTube API data stored by Conveyor. It does not delete anything stored "
    "on YouTube; to delete videos or other data on YouTube, use YouTube Studio or another "
    "authorized YouTube application."
)


class PolicyAcceptanceRequired(PreflightBlocked):
    """The current Conveyor Privacy Policy version has not been accepted."""

    def __init__(self) -> None:
        super().__init__("privacy_policy_acceptance_required")


def _now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _parse(value: Any) -> datetime | None:
    try:
        moment = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return moment if moment.tzinfo else None


class ConsentRegistry:
    """Accepted policy version and per-authorization reconfirmation times; no secrets."""

    def __init__(self, path: Path, repository_root: Path | None = None) -> None:
        if repository_root is not None:
            _outside_repository(path, repository_root)
        self.path = Path(path)

    def _load(self) -> dict[str, Any]:
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            state = None
        if not isinstance(state, dict) or state.get("schema") != STATE_SCHEMA:
            state = {"schema": STATE_SCHEMA, "policy_acceptance": None, "authorizations": {}}
        if not isinstance(state.get("authorizations"), dict):
            state["authorizations"] = {}
        return state

    def _save(self, state: dict[str, Any]) -> None:
        _write_sanitized_json(self.path, state)

    def accepted_version(self) -> str | None:
        acceptance = self._load().get("policy_acceptance")
        return acceptance.get("version") if isinstance(acceptance, dict) else None

    def is_current(self) -> bool:
        return self.accepted_version() == POLICY_VERSION

    def accept(self, actor: str, now: datetime) -> dict[str, Any]:
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError("Policy acceptance requires the accepting person.")
        state = self._load()
        state["policy_acceptance"] = {
            "version": POLICY_VERSION,
            "policy_url": PRIVACY_POLICY_URL,
            "actor": actor.strip(),
            "accepted_at": now.replace(microsecond=0).isoformat(),
        }
        self._save(state)
        return state["policy_acceptance"]

    def last_reconfirmed(self, kind: str) -> datetime | None:
        record = self._load()["authorizations"].get(kind)
        return _parse(record.get("last_reconfirmed_at")) if isinstance(record, dict) else None

    def due(self, kind: str, now: datetime) -> bool:
        last = self.last_reconfirmed(kind)
        return last is None or now - last >= RECONFIRM_AFTER

    def mark_reconfirmed(self, kind: str, now: datetime) -> None:
        state = self._load()
        state["authorizations"][kind] = {
            "last_reconfirmed_at": now.replace(microsecond=0).isoformat()
        }
        self._save(state)

    def clear(self, kind: str) -> None:
        state = self._load()
        if state["authorizations"].pop(kind, None) is not None:
            self._save(state)

    def status(self, now: datetime) -> dict[str, Any]:
        return {
            "policy_version_required": POLICY_VERSION,
            "policy_version_accepted": self.accepted_version(),
            "policy_acceptance_current": self.is_current(),
            "authorizations": {
                kind: {
                    "last_reconfirmed_at": (
                        self.last_reconfirmed(kind).isoformat()
                        if self.last_reconfirmed(kind)
                        else None
                    ),
                    "reconfirmation_due": self.due(kind, now),
                }
                for kind in AUTHORIZATIONS
            },
        }


def post_token_revocation(refresh_token: str) -> str:
    """Ask Google to revoke one token; returns 'confirmed' or 'unconfirmed', never the token."""

    request = urllib.request.Request(
        GOOGLE_REVOKE_ENDPOINT,
        data=urllib.parse.urlencode({"token": refresh_token}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return "confirmed" if response.status == 200 else "unconfirmed"
    except Exception:
        # Any HTTP error (including 400) or network failure leaves revocation unconfirmed.
        return "unconfirmed"


class YouTubeGovernance:
    """Acceptance gate, reconfirmation, revocation and deletion over existing purge machinery."""

    def __init__(
        self,
        registry: ConsentRegistry,
        repository: Any,
        *,
        store_for: Callable[[str], Any] | None = None,
        revoke_token: Callable[[str], str] = post_token_revocation,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self.registry = registry
        self.repository = repository
        self.store_for = store_for or (
            lambda account: WindowsCredentialRefreshTokenStore(account=account)
        )
        self.revoke_token = revoke_token
        self.clock = clock

    def require_acceptance(self) -> None:
        if not self.registry.is_current():
            raise PolicyAcceptanceRequired()

    def purge_api_data(self) -> dict[str, int]:
        return self.repository.purge_all_youtube_api_data()

    def enforce_stale_data(self) -> dict[str, int]:
        return self.repository.purge_stale_youtube_api_data(self.clock() - RECONFIRM_AFTER)

    def _delete_credential(self, kind: str) -> dict[str, Any]:
        """Delete one local credential; a store failure is recorded, never raised."""

        account, _scopes = AUTHORIZATIONS[kind]
        self.registry.clear(kind)
        try:
            return {"local_credential_deleted": self.store_for(account).delete(), "error": None}
        except Exception:
            return {"local_credential_deleted": False, "error": "credential_delete_failed"}

    def handle_definitive(self, kind: str) -> dict[str, Any]:
        """Revoked or invalid authorization: delete it and the YouTube API data it covered."""

        try:
            return {"credential": self._delete_credential(kind)}
        finally:
            self.purge_api_data()

    def provider(
        self, kind: str, inner: Any, channel_client: Any | None = None
    ) -> GovernedCredentialProvider:
        return GovernedCredentialProvider(self, kind, inner, channel_client)

    def reconfirm(self, kind: str, inner: Any, channel_client: Any | None = None) -> Any:
        """Refresh + exact scope/channel verification; record success, act on the outcome."""

        _account, scopes = AUTHORIZATIONS[kind]
        now = self.clock()
        try:
            credentials = inner.acquire()
            result = verify_exact_channel(
                credentials,
                channel_client or GoogleReadOnlyChannelClient(),
                required_scopes=frozenset(scopes),
                now=now,
            )
            category = None if result.status == "PASS" else result.error_category
        except PreflightBlocked as exc:
            category = exc.category
        if category is None:
            self.registry.mark_reconfirmed(kind, now)
            return credentials
        if category in DEFINITIVE_FAILURES:
            self.handle_definitive(kind)
        # Transient failures fail closed without deleting anything.
        raise PreflightBlocked(category)

    def _revoke_one(self, kind: str) -> dict[str, Any]:
        """Revoke and delete one authorization; every failure is recorded, none raised."""

        account, _scopes = AUTHORIZATIONS[kind]
        errors: list[str] = []
        try:
            token = self.store_for(account).get()
            readable = True
        except Exception:
            token, readable = None, False
            errors.append("credential_read_failed")
        if not readable:
            remote = "unconfirmed"
        elif token is None:
            remote = "no_stored_authorization"
        else:
            try:
                remote = self.revoke_token(token)
            except Exception:
                remote = "unconfirmed"
        deletion = self._delete_credential(kind)
        if deletion["error"]:
            errors.append(deletion["error"])
        return {
            "remote_revocation": remote,
            "local_credential_deleted": deletion["local_credential_deleted"],
            "errors": errors,
        }

    def revoke(self) -> dict[str, Any]:
        """Revoke every stored YouTube authorization independently, then always purge data."""

        results: dict[str, Any] = {}
        try:
            for kind in AUTHORIZATIONS:
                results[kind] = self._revoke_one(kind)
        finally:
            purged = self.purge_api_data()
        unconfirmed = any(
            item["remote_revocation"] == "unconfirmed" or item["errors"]
            for item in results.values()
        )
        return {
            "authorizations": results,
            "purged": purged,
            "remote_revocation_unconfirmed": unconfirmed,
            "google_security_settings": GOOGLE_SECURITY_SETTINGS_URL if unconfirmed else None,
        }

    def delete_data(self) -> dict[str, Any]:
        return {"purged": self.purge_api_data(), "notice": DELETION_NOTICE}

    def maintain(self, inner_for: Callable[[str], Any]) -> dict[str, Any]:
        """Daily unattended maintenance.

        Always deletes stale stored YouTube API data locally. Only with current policy acceptance
        does it reconfirm the authorizations that are due, each independently; transient
        failures fail closed and keep credentials and data.
        """

        report: dict[str, Any] = {"stale_purged": self.enforce_stale_data()}
        if not self.registry.is_current():
            report["policy_acceptance"] = "missing_or_stale"
            report["reconfirmation"] = "skipped_without_current_acceptance"
            return report
        report["policy_acceptance"] = "current"
        results: dict[str, str] = {}
        for kind, (account, _scopes) in AUTHORIZATIONS.items():
            try:
                stored = self.store_for(account).get() is not None
            except Exception:
                results[kind] = "credential_store_unavailable"
                continue
            if not stored:
                results[kind] = "no_stored_authorization"
            elif not self.registry.due(kind, self.clock()):
                results[kind] = "not_due"
            else:
                try:
                    self.reconfirm(kind, inner_for(kind))
                    results[kind] = "reconfirmed"
                except PreflightBlocked as exc:
                    results[kind] = exc.category
        report["reconfirmation"] = results
        return report

    def startup(self) -> dict[str, Any]:
        """Local-only inspection: due state and stale-data deletion; no YouTube API call."""

        return {
            "status": self.registry.status(self.clock()),
            "stale_purged": self.enforce_stale_data(),
        }


class GovernedCredentialProvider:
    """Every YouTube API use passes acceptance, stale-data and 30-day reconfirmation gates."""

    def __init__(
        self, governance: YouTubeGovernance, kind: str, inner: Any, channel_client: Any | None
    ) -> None:
        self.governance = governance
        self.kind = kind
        self.inner = inner
        self.channel_client = channel_client

    def acquire(self) -> Any:
        self.governance.require_acceptance()
        self.governance.enforce_stale_data()
        if self.governance.registry.due(self.kind, self.governance.clock()):
            return self.governance.reconfirm(self.kind, self.inner, self.channel_client)
        try:
            return self.inner.acquire()
        except PreflightBlocked as exc:
            if exc.category in DEFINITIVE_FAILURES:
                self.governance.handle_definitive(self.kind)
            raise


def governed_provider(
    kind: str,
    client_config: Path,
    repository_root: Path,
    governance: YouTubeGovernance,
) -> GovernedCredentialProvider:
    """Non-interactive governed credentials for API use (never opens a consent window)."""

    account, scopes = AUTHORIZATIONS[kind]
    inner = GoogleInstalledCredentialProvider(
        client_config,
        governance.store_for(account),
        repository_root,
        scopes=scopes,
        interactive=False,
    )
    return governance.provider(kind, inner)


def _repository(db_path: str | None) -> Any:
    from project_atlas.persistence import AtlasRepository

    path = db_path or os.environ.get("ATLAS_DB_PATH", "").strip()
    if not path:
        raise SystemExit("--db or ATLAS_DB_PATH is required.")
    return AtlasRepository(Path(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--consent-state", type=Path, required=True)
    parser.add_argument("--db")
    sub = parser.add_subparsers(dest="command", required=True)
    accept = sub.add_parser("accept", help="Accept the current Conveyor Privacy Policy version.")
    accept.add_argument("--actor", required=True)
    accept.add_argument("--accept-version", required=True)
    sub.add_parser("status", help="Local acceptance and reconfirmation state (no API call).")
    reconfirm = sub.add_parser("reconfirm", help="Reconfirm stored authorizations now.")
    reconfirm.add_argument("--client-config", type=Path, required=True)
    maintain = sub.add_parser(
        "maintain", help="Daily unattended maintenance (stale-data purge + due reconfirmation)."
    )
    maintain.add_argument("--client-config", type=Path, required=True)
    sub.add_parser("revoke", help="Revoke and delete every stored YouTube authorization.")
    sub.add_parser("delete-data", help="Delete the YouTube API data stored by Conveyor.")
    args = parser.parse_args(argv)
    repository_root = Path(__file__).resolve().parents[2]
    registry = ConsentRegistry(args.consent_state, repository_root)
    if args.command == "accept":
        if args.accept_version != POLICY_VERSION:
            print(f"The current Conveyor Privacy Policy version is {POLICY_VERSION}.")
            return 2
        print(json.dumps(registry.accept(args.actor, _now()), sort_keys=True))
        return 0
    if args.command == "status":
        print(json.dumps(registry.status(_now()), sort_keys=True))
        return 0
    repository = _repository(args.db)
    try:
        governance = YouTubeGovernance(registry, repository)
        if args.command == "maintain":

            def inner_for(kind: str) -> Any:
                account, scopes = AUTHORIZATIONS[kind]
                return GoogleInstalledCredentialProvider(
                    args.client_config,
                    governance.store_for(account),
                    repository_root,
                    scopes=scopes,
                    interactive=False,
                )

            result: dict[str, Any] = governance.maintain(inner_for)
            print(json.dumps(result, sort_keys=True))
            failures = set((result.get("reconfirmation") or {}).values()) - {
                "reconfirmed",
                "not_due",
                "no_stored_authorization",
            }
            return 1 if isinstance(result.get("reconfirmation"), dict) and failures else 0
        if args.command == "revoke":
            result = governance.revoke()
        elif args.command == "delete-data":
            result = governance.delete_data()
        else:
            governance.require_acceptance()
            result = {}
            for kind, (account, _scopes) in AUTHORIZATIONS.items():
                if governance.store_for(account).get() is None:
                    result[kind] = "no_stored_authorization"
                    continue
                provider = governed_provider(kind, args.client_config, repository_root, governance)
                try:
                    governance.reconfirm(kind, provider.inner)
                    result[kind] = "reconfirmed"
                except PreflightBlocked as exc:
                    result[kind] = exc.category
        print(json.dumps(result, sort_keys=True))
    except PreflightBlocked as exc:
        print(json.dumps({"status": "BLOCKER", "error_category": exc.category}))
        return 2
    finally:
        repository.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
