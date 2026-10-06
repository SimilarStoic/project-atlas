"""Network-free proofs of YouTube Developer Policies governance and release governance."""

from __future__ import annotations

import ast
import re
import threading
from datetime import timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from project_atlas import youtube_consent
from project_atlas.web import YOUTUBE_MUTATION_ROUTES, AtlasRequestHandler, create_server
from project_atlas.youtube_consent import (
    DELETION_NOTICE,
    GOOGLE_PRIVACY_URL,
    GOOGLE_SECURITY_SETTINGS_URL,
    POLICY_VERSION,
    PRIVACY_POLICY_URL,
    ConsentRegistry,
    PolicyAcceptanceRequired,
)
from project_atlas.youtube_preflight import (
    KEYRING_ACCOUNT,
    GoogleInstalledCredentialProvider,
    PreflightBlocked,
)
from project_atlas.youtube_upload import (
    UPLOAD_KEYRING_ACCOUNT,
    UPLOAD_SCOPES,
    YOUTUBE_TERMS_URL,
    YouTubeUploadController,
)
from tests.test_publishing import _private
from tests.test_youtube_preflight import _write_client_config
from tests.test_youtube_upload import (
    CLOCK,
    ChannelClient,
    ConsentFlow,
    FakeStore,
    _authorize,
    _consent,
    form_for,
    governance_for,
    manifest,
    upload_credentials,
)

EXPECTED_MUTATION_ROUTES = {
    ("POST", "/youtube/upload"),
    ("POST", "/youtube/privacy/accept"),
    ("POST", "/youtube/revoke"),
    ("POST", "/youtube/delete-data"),
}


def _api_data(repo) -> dict:
    connection = repo.connection
    return {
        "remote_ids": [
            row[0]
            for row in connection.execute(
                "SELECT remote_id FROM platform_publications WHERE identity_source = 'api'"
            )
        ],
        "status_payloads": connection.execute(
            "SELECT COUNT(*) FROM publication_status_snapshots WHERE provider_purged_at IS NULL"
        ).fetchone()[0],
        "operation_evidence": connection.execute(
            "SELECT COUNT(*) FROM publication_operation_events WHERE provider_evidence_json "
            "IS NOT NULL"
        ).fetchone()[0],
    }


def _authored(repo) -> tuple:
    connection = repo.connection
    return tuple(
        connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in (
            "publishing_packages",
            "publication_gate_decisions",
            "publication_operations",
            "publication_operation_events",
            "platform_publications",
        )
    )


def _stores():
    return {KEYRING_ACCOUNT: FakeStore("ro-token"), UPLOAD_KEYRING_ACCOUNT: FakeStore("up-token")}


# --- 1. Revocation -------------------------------------------------------------------------


def test_revoke_calls_google_deletes_credentials_purges_and_repeats_safely(setup, tmp_path):
    repo, _storage, _fake, service = setup
    _private(service)
    before = _api_data(repo)
    assert before["remote_ids"] == ["fake-video-1"] and before["status_payloads"] == 1
    authored = _authored(repo)
    stores, revoked = _stores(), []
    governance = governance_for(
        repo,
        tmp_path,
        stores=stores,
        revoke_token=lambda token: revoked.append(token) or "confirmed",
    )
    for kind in ("readonly", "upload"):
        governance.registry.mark_reconfirmed(kind, CLOCK)
    result = governance.revoke()
    assert sorted(revoked) == ["ro-token", "up-token"]
    assert all(item["local_credential_deleted"] for item in result["authorizations"].values())
    assert all(store.token is None for store in stores.values())
    assert governance.registry.last_reconfirmed("readonly") is None
    assert _api_data(repo) == {"remote_ids": [None], "status_payloads": 0, "operation_evidence": 0}
    assert _authored(repo) == authored  # Conveyor-authored records remain.
    assert result["google_security_settings"] is None
    again = governance.revoke()
    assert revoked == sorted(revoked) and len(revoked) == 2
    assert {item["remote_revocation"] for item in again["authorizations"].values()} == {
        "no_stored_authorization"
    }


def test_unconfirmed_remote_revocation_still_removes_local_access_and_data(setup, tmp_path):
    repo, _storage, _fake, service = setup
    _private(service)
    stores = _stores()
    governance = governance_for(
        repo, tmp_path, stores=stores, revoke_token=lambda token: "unconfirmed"
    )
    result = governance.revoke()
    assert result["remote_revocation_unconfirmed"] is True
    assert result["google_security_settings"] == GOOGLE_SECURITY_SETTINGS_URL
    assert all(store.token is None for store in stores.values())
    assert _api_data(repo)["status_payloads"] == 0


# --- 2. User deletion request --------------------------------------------------------------


def test_deletion_request_purges_api_data_and_says_youtube_is_unaffected(setup, tmp_path):
    repo, _storage, _fake, service = setup
    _private(service)
    stores = _stores()
    result = governance_for(repo, tmp_path, stores=stores).delete_data()
    assert _api_data(repo) == {"remote_ids": [None], "status_payloads": 0, "operation_evidence": 0}
    assert "does not delete anything stored on YouTube" in result["notice"]
    assert result["notice"] == DELETION_NOTICE
    assert stores[KEYRING_ACCOUNT].token == "ro-token"  # Deleting data does not revoke access.


def _nonce(page: str, action: str) -> str:
    form = page[page.index(f"action='{action}'") :]
    return re.search(r"name='nonce' value='([^']+)'", form).group(1)


def test_revoke_and_delete_controls_work_without_acceptance_or_usable_authorization(env, tmp_path):
    repo, _storage, client, _provider, adapter, service, _package, _controller = env

    class UnusableStore(FakeStore):
        def get(self):
            raise PreflightBlocked("credential_store_unavailable")

    stores = {KEYRING_ACCOUNT: UnusableStore("ro"), UPLOAD_KEYRING_ACCOUNT: FakeStore("up")}
    governance = governance_for(repo, tmp_path / "unaccepted", accepted=False, stores=stores)
    controller = YouTubeUploadController(service, adapter, governance, monotonic=lambda: 0.0)
    status, page = controller.privacy_page()
    assert status == 200
    for link in (PRIVACY_POLICY_URL, YOUTUBE_TERMS_URL, GOOGLE_PRIVACY_URL):
        assert link in page
    assert GOOGLE_SECURITY_SETTINGS_URL in page and f"version {POLICY_VERSION}" in page
    # A revoke nonce cannot be spent on another control.
    assert controller.delete_data({"nonce": _nonce(page, "/youtube/revoke")})[0] == 409
    status, page = controller.privacy_page()
    status, revoked = controller.revoke({"nonce": _nonce(page, "/youtube/revoke")})
    assert status == 200 and "YouTube access revoked" in revoked
    assert stores[UPLOAD_KEYRING_ACCOUNT].token is None and stores[KEYRING_ACCOUNT].token is None
    status, page = controller.privacy_page()
    status, deleted = controller.delete_data({"nonce": _nonce(page, "/youtube/delete-data")})
    assert status == 200 and "does not delete anything stored on YouTube" in deleted
    assert client.inserts == []


# --- 3. Automatic 30-day enforcement -------------------------------------------------------


def test_each_authorization_has_independent_reconfirmation_state(tmp_path):
    registry = ConsentRegistry(tmp_path / "state.json")
    registry.mark_reconfirmed("readonly", CLOCK)
    registry.mark_reconfirmed("upload", CLOCK + timedelta(days=20))
    later = CLOCK + timedelta(days=31)
    assert registry.due("readonly", later) and not registry.due("upload", later)
    registry.clear("upload")
    assert registry.due("upload", later) and registry.last_reconfirmed("readonly") == CLOCK


class Inner:
    def __init__(self, error=None) -> None:
        self.error, self.calls = error, 0

    def acquire(self):
        self.calls += 1
        if self.error:
            raise PreflightBlocked(self.error)
        return upload_credentials()


class CountingChannels(ChannelClient):
    def __init__(self, channels, error=None) -> None:
        super().__init__(channels)
        self.calls, self.error = 0, error

    def authenticated_channel_ids(self, credentials):
        self.calls += 1
        if self.error:
            raise PreflightBlocked(self.error)
        return self.channels


def test_due_reconfirmation_runs_automatically_before_api_use_only_after_acceptance(tmp_path):
    from project_atlas.publishing_state import TARGET_CHANNEL

    unaccepted = governance_for(None, tmp_path / "a", accepted=False)
    inner, channels = Inner(), CountingChannels([TARGET_CHANNEL])
    with pytest.raises(PolicyAcceptanceRequired):
        unaccepted.provider("upload", inner, channels).acquire()
    assert inner.calls == 0 and channels.calls == 0

    class NoData:
        def purge_stale_youtube_api_data(self, cutoff):
            return {}

    governance = governance_for(NoData(), tmp_path / "b")
    provider = governance.provider("upload", inner, channels)
    provider.acquire()  # Never reconfirmed: due, so it is verified before use.
    assert channels.calls == 1 and governance.registry.last_reconfirmed("upload") == CLOCK
    provider.acquire()  # Fresh: no extra verification call.
    assert channels.calls == 1 and inner.calls == 2
    governance.clock = lambda: CLOCK + timedelta(days=30)
    provider.acquire()  # Due again at 30 days.
    assert channels.calls == 2


@pytest.mark.parametrize(
    ("inner_error", "channel_error", "definitive"),
    [
        ("authorization_revoked", None, True),
        (None, "authenticated_channel_mismatch", True),
        ("authorization_check_transient", None, False),
        (None, "youtube_request_failed", False),
    ],
)
def test_definitive_revocation_purges_but_transient_failure_keeps_everything(
    setup, tmp_path, inner_error, channel_error, definitive
):
    from project_atlas.publishing_state import TARGET_CHANNEL

    repo, _storage, _fake, service = setup
    _private(service)
    stores = _stores()
    governance = governance_for(repo, tmp_path, stores=stores)
    governance.clock = lambda: _now_for(repo)
    channels = CountingChannels(
        ["UC-other"] if channel_error == "authenticated_channel_mismatch" else [TARGET_CHANNEL],
        None if channel_error == "authenticated_channel_mismatch" else channel_error,
    )
    with pytest.raises(PreflightBlocked):
        governance.provider("upload", Inner(inner_error), channels).acquire()
    if definitive:
        assert stores[UPLOAD_KEYRING_ACCOUNT].token is None
        assert _api_data(repo)["status_payloads"] == 0
    else:
        assert stores[UPLOAD_KEYRING_ACCOUNT].token == "up-token"
        assert _api_data(repo)["status_payloads"] == 1
    assert stores[KEYRING_ACCOUNT].token == "ro-token"  # The other authorization is untouched.


def _now_for(repo):
    from datetime import datetime

    observed = repo.connection.execute(
        "SELECT observed_at FROM publication_status_snapshots"
    ).fetchone()[0]
    return datetime.fromisoformat(observed)


def test_refresh_failures_are_classified_definitive_only_for_invalid_grant(tmp_path, monkeypatch):
    from google.auth.exceptions import RefreshError, TransportError
    from google.oauth2.credentials import Credentials

    repository = tmp_path / "repository"
    repository.mkdir()
    client_config = tmp_path / "client.json"
    _write_client_config(client_config)
    for error, category in (
        (
            RefreshError("invalid_grant: Token has been expired or revoked."),
            "authorization_revoked",
        ),
        (RefreshError("server_error: try again"), "authorization_check_transient"),
        (TransportError("connection reset"), "authorization_check_transient"),
    ):

        def refresh(self, request, error=error):
            raise error

        monkeypatch.setattr(Credentials, "refresh", refresh)
        provider = GoogleInstalledCredentialProvider(
            client_config, FakeStore("stored"), repository, scopes=UPLOAD_SCOPES, interactive=False
        )
        with pytest.raises(PreflightBlocked) as blocked:
            provider.acquire()
        assert blocked.value.category == category


def test_stale_api_payloads_are_deleted_fresh_ones_kept(setup, tmp_path):
    repo, _storage, _fake, service = setup
    _private(service)
    now = _now_for(repo)
    assert repo.purge_stale_youtube_api_data(now - timedelta(days=30)) == {
        "status_snapshots": 0,
        "performance_snapshots": 0,
        "operations": 0,
        "publications": 0,
    }
    assert _api_data(repo)["status_payloads"] == 1
    governance = governance_for(repo, tmp_path)
    governance.clock = lambda: now + timedelta(days=31)
    startup = governance.startup()  # Local only: no store or API access.
    assert startup["stale_purged"]["status_snapshots"] == 1
    assert startup["stale_purged"]["publications"] == 1
    assert _api_data(repo) == {"remote_ids": [None], "status_payloads": 0, "operation_evidence": 0}
    assert startup["status"]["authorizations"]["upload"]["reconfirmation_due"] is True


# --- 4. Versioned privacy-policy acceptance ------------------------------------------------


def test_no_authorization_or_api_call_without_current_acceptance(env, tmp_path, monkeypatch):
    repo, _storage, client, _provider, adapter, service, package, _controller = env
    flow = ConsentFlow(upload_credentials())
    _consent(monkeypatch, flow, [])
    store = FakeStore("prior")
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    code, evidence = _authorize(fresh, store, ["unused"], accepted=False)
    assert code == 2 and evidence["error_category"] == "privacy_policy_acceptance_required"
    assert flow.calls == 0 and store.saved == []

    from project_atlas import youtube_preflight

    monkeypatch.setattr(
        youtube_preflight,
        "execute_live_preflight",
        lambda *args, **kwargs: pytest.fail("No YouTube API call before acceptance."),
    )
    result_file = tmp_path / "evidence" / "preflight.json"
    assert (
        youtube_preflight.main(
            [
                "--client-config",
                str(tmp_path / "client.json"),
                "--result-file",
                str(result_file),
                "--consent-state",
                str(tmp_path / "never-accepted.json"),
            ]
        )
        == 2
    )

    calls = []
    client.authenticated_channel_ids = lambda credentials: calls.append(1) or []
    governance = governance_for(repo, tmp_path / "unaccepted", accepted=False)
    controller = YouTubeUploadController(service, adapter, governance, monotonic=lambda: 0.0)
    status, page = controller.page(package.id)
    assert status == 409 and "/youtube/privacy" in page and calls == []


def test_policy_version_change_requires_reacceptance(tmp_path, monkeypatch):
    registry = ConsentRegistry(tmp_path / "state.json")
    assert POLICY_VERSION == "2026-10-05"
    registry.accept("founder", CLOCK)
    assert registry.is_current()
    monkeypatch.setattr(youtube_consent, "POLICY_VERSION", "2027-01-01")
    assert not registry.is_current()
    assert registry.accepted_version() == "2026-10-05"
    registry.accept("founder", CLOCK)
    assert registry.is_current() and registry.accepted_version() == "2027-01-01"


def test_acceptance_records_the_exact_version_from_the_screen(env, tmp_path):
    repo, _storage, _client, _provider, adapter, service, _package, _controller = env
    governance = governance_for(repo, tmp_path / "accept", accepted=False)
    controller = YouTubeUploadController(service, adapter, governance, monotonic=lambda: 0.0)
    status, page = controller.privacy_page()
    nonce = _nonce(page, "/youtube/privacy/accept")
    bad = {"nonce": nonce, "accepted": "accepted", "accept_version": "2020-01-01"}
    assert controller.accept_policy(bad)[0] == 400 and not governance.registry.is_current()
    status, page = controller.privacy_page()
    nonce = _nonce(page, "/youtube/privacy/accept")
    good = {"nonce": nonce, "accepted": "accepted", "accept_version": POLICY_VERSION}
    assert controller.accept_policy(good)[0] == 200
    assert governance.registry.accepted_version() == POLICY_VERSION


# --- 5. Exact mutation-route allowlist -----------------------------------------------------


def test_exact_publishing_and_youtube_mutation_route_allowlist():
    assert set(YOUTUBE_MUTATION_ROUTES) == EXPECTED_MUTATION_ROUTES
    source = (Path(__file__).resolve().parents[1] / "src" / "project_atlas" / "web.py").read_text(
        encoding="utf-8"
    )
    literals = {
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    youtube_paths = {value for value in literals if value.startswith("/youtube")}
    assert youtube_paths == {
        "/youtube/upload",
        "/youtube/privacy",
        "/youtube/privacy/accept",
        "/youtube/revoke",
        "/youtube/delete-data",
        "/youtube/",
    }
    assert not any("/publish" in value or "publishing" in value for value in literals)
    handlers = {name for name in vars(AtlasRequestHandler) if name.startswith("do_")}
    assert handlers == {"do_GET", "do_POST", "do_PUT"}
    assert "publishing_packages" not in source and "PublicationOperation" not in source


def _serve(server, request):
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    try:
        with urlopen(request) as response:
            return response.status, response.read().decode(), dict(response.headers)
    except HTTPError as error:
        return error.code, error.read().decode(), dict(error.headers)
    finally:
        thread.join(timeout=5)


def test_every_allowlisted_mutation_route_is_protected(env, tmp_path, monkeypatch):
    _repo, _storage, _client, _provider, adapter, service, _package, controller = env
    server = create_server(
        port=0,
        database_path=tmp_path / "routes.db",
        youtube_upload=lambda _repository: controller,
    )
    try:
        port = server.server_address[1]
        base = f"http://127.0.0.1:{port}"

        def post(path, origin=None, host=None):
            request = Request(
                f"{base}{path}",
                data=urlencode({"nonce": "forged", "accepted": "accepted"}).encode(),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            if origin:
                request.add_header("Origin", origin)
            if host:
                request.add_header("Host", host)
            return _serve(server, request)

        for _method, path in sorted(EXPECTED_MUTATION_ROUTES):
            status, _body, headers = post(path)
            assert status in {400, 409}, path  # Reached only with a valid single-use nonce.
            assert headers["X-Frame-Options"] == "DENY"
            assert post(path, origin="https://attacker.invalid")[0] == 403
            assert post(path, host=f"attacker.invalid:{port}")[0] == 403
        assert post("/youtube/anything-else")[0] == 404
        assert _serve(server, Request(f"{base}/youtube/revoke", method="DELETE"))[0] == 501
        original_setup = AtlasRequestHandler.setup

        def remote_peer(handler):
            original_setup(handler)
            handler.client_address = ("203.0.113.9", 40000)

        monkeypatch.setattr(AtlasRequestHandler, "setup", remote_peer)
        for _method, path in sorted(EXPECTED_MUTATION_ROUTES):
            assert post(path)[0] == 403, path
    finally:
        server.server_close()


# --- 6. Public / unlisted governance ------------------------------------------------------


def test_public_or_unlisted_upload_requires_open_approved_api_release_time(env):
    _repo, _storage, client, _provider, _adapter, service, package, controller = env
    service.clock = lambda: CLOCK + timedelta(hours=1)
    for privacy in ("unlisted", "public"):
        status, page = controller.submit(form_for(controller, package, privacy=privacy))
        assert status == 409 and "refused before anything was sent" in page
        assert "approved publication time" in page
    assert client.inserts == []
    # Private uploads are unaffected by the public window.
    status, page = controller.submit(form_for(controller, package, privacy="private"))
    assert status == 200 and len(client.inserts) == 1


def test_public_upload_requires_api_release_route_and_a_clear_pilot_week(env):
    repo, _storage, client, _provider, _adapter, service, package, controller = env
    status, _page = controller.submit(form_for(controller, package, privacy="public"))
    assert status == 200 and len(client.inserts) == 1
    second = service.prepare_package(
        "package-2", "synthetic-pilot", 2, 1, "fake-artifact", {**manifest(), "pilot_slot": 2}
    )
    service.approve_package("founder-approval-2", second.id, "synthetic-founder")
    status, page = controller.submit(form_for(controller, second, privacy="unlisted"))
    assert status == 409 and "pilot week" in page and len(client.inserts) == 1
    manual_window = {
        "timezone": "Europe/London",
        "mode": "window",
        "start": "2026-10-05T12:30:00+01:00",
        "end": "2026-10-05T13:30:00+01:00",
    }
    manual = service.prepare_package(
        "package-3",
        "synthetic-pilot",
        3,
        1,
        "fake-artifact",
        {
            **manifest(),
            "pilot_slot": 3,
            "release_route": "manual",
            "publication_timing": manual_window,
        },
    )
    service.approve_package("founder-approval-3", manual.id, "synthetic-founder")
    status, page = controller.submit(form_for(controller, manual, privacy="public"))
    assert status == 409 and "API public release" in page and len(client.inserts) == 1
    status, _page = controller.submit(form_for(controller, manual, privacy="private"))
    assert status == 200 and len(client.inserts) == 2
    assert repo is not None


# --- Final fixes: robust revocation, strict revoke response, daily maintenance --------------


class DeleteFails(FakeStore):
    def delete(self) -> bool:
        raise PreflightBlocked("credential_store_unavailable")


class ReadFails(FakeStore):
    def get(self):
        raise PreflightBlocked("credential_store_unavailable")


@pytest.mark.parametrize("broken", [DeleteFails, ReadFails])
def test_revoke_processes_each_authorization_independently_and_always_purges(
    setup, tmp_path, broken
):
    repo, _storage, _fake, service = setup
    _private(service)
    stores = {KEYRING_ACCOUNT: broken("ro-token"), UPLOAD_KEYRING_ACCOUNT: FakeStore("up-token")}
    revoked = []
    governance = governance_for(
        repo,
        tmp_path,
        stores=stores,
        revoke_token=lambda token: revoked.append(token) or "confirmed",
    )
    governance.registry.mark_reconfirmed("readonly", CLOCK)
    result = governance.revoke()
    upload = result["authorizations"]["upload"]
    assert "up-token" in revoked and upload["local_credential_deleted"] is True
    assert stores[UPLOAD_KEYRING_ACCOUNT].token is None
    readonly = result["authorizations"]["readonly"]
    assert readonly["errors"] and readonly["local_credential_deleted"] is (broken is ReadFails)
    assert governance.registry.last_reconfirmed("readonly") is None
    assert _api_data(repo) == {"remote_ids": [None], "status_payloads": 0, "operation_evidence": 0}
    assert result["google_security_settings"] == GOOGLE_SECURITY_SETTINGS_URL


def test_google_revocation_http_400_is_unconfirmed_and_surfaces_security_settings(
    setup, tmp_path, monkeypatch
):
    import io
    import urllib.request
    from urllib.error import HTTPError as UrlHTTPError

    from project_atlas.youtube_consent import post_token_revocation

    def bad_request(request, timeout=None):
        raise UrlHTTPError(request.full_url, 400, "Bad Request", {}, io.BytesIO(b"{}"))

    monkeypatch.setattr(urllib.request, "urlopen", bad_request)
    assert post_token_revocation("synthetic-token") == "unconfirmed"
    repo, _storage, _fake, service = setup
    _private(service)
    stores = _stores()
    governance = governance_for(repo, tmp_path, stores=stores, revoke_token=post_token_revocation)
    result = governance.revoke()
    assert {item["remote_revocation"] for item in result["authorizations"].values()} == {
        "unconfirmed"
    }
    assert result["google_security_settings"] == GOOGLE_SECURITY_SETTINGS_URL
    assert all(store.token is None for store in stores.values())
    assert _api_data(repo)["status_payloads"] == 0


def _stale_setup(setup, tmp_path, accepted=True, stores=None):
    repo, _storage, _fake, service = setup
    _private(service)
    governance = governance_for(repo, tmp_path, accepted=accepted, stores=stores or _stores())
    observed = _now_for(repo)
    governance.clock = lambda: observed + timedelta(days=31)
    return repo, governance, observed


def test_maintenance_purges_stale_data_but_makes_no_api_call_without_acceptance(setup, tmp_path):
    repo, governance, _observed = _stale_setup(setup, tmp_path, accepted=False)
    report = governance.maintain(lambda kind: pytest.fail("No API use before acceptance."))
    assert report["policy_acceptance"] == "missing_or_stale"
    assert report["stale_purged"]["status_snapshots"] == 1
    assert _api_data(repo)["status_payloads"] == 0


def test_maintenance_reconfirms_only_due_authorizations_independently(setup, tmp_path):
    from project_atlas.publishing_state import TARGET_CHANNEL

    stores = {KEYRING_ACCOUNT: ReadFails("ro"), UPLOAD_KEYRING_ACCOUNT: FakeStore("up")}
    repo, governance, _observed = _stale_setup(setup, tmp_path, stores=stores)
    used = []

    def inner_for(kind):
        used.append(kind)
        return Inner()

    original = governance.reconfirm
    governance.reconfirm = lambda kind, inner: original(
        kind, inner, CountingChannels([TARGET_CHANNEL])
    )
    report = governance.maintain(inner_for)
    assert report["reconfirmation"] == {
        "readonly": "credential_store_unavailable",
        "upload": "reconfirmed",
    }
    assert used == ["upload"]
    report = governance.maintain(inner_for)  # Upload is now fresh: not due, no API use.
    assert report["reconfirmation"]["upload"] == "not_due" and used == ["upload"]


@pytest.mark.parametrize(
    ("error", "deleted"),
    [("authorization_check_transient", False), ("authorization_revoked", True)],
)
def test_maintenance_transient_failure_keeps_credentials_definitive_deletes(
    setup, tmp_path, error, deleted
):
    stores = _stores()
    repo, governance, observed = _stale_setup(setup, tmp_path, stores=stores)
    governance.clock = lambda: observed  # Data fresh; only reconfirmation is due.
    report = governance.maintain(lambda kind: Inner(error))
    assert report["reconfirmation"] == {"readonly": error, "upload": error}
    assert all((store.token is None) is deleted for store in stores.values())
    assert (_api_data(repo)["status_payloads"] == 0) is deleted


def test_never_release_package_screen_allows_private_and_refuses_public(env):
    _repo, _storage, client, _provider, _adapter, service, _package, controller = env
    evidence = service.prepare_package(
        "evidence-screen",
        "synthetic-evidence",
        1,
        1,
        "fake-artifact",
        {
            **manifest(),
            "release_policy": "never_release",
            "release_route": "manual",
            "publication_timing": {"mode": "never_release"},
            "private_first": True,
        },
    )
    service.approve_package("evidence-screen-approval", evidence.id, "synthetic-founder")
    status, page = controller.page(evidence.id)
    assert status == 200 and "never-release package" in page
    for privacy in ("public", "unlisted"):
        status, page = controller.submit(form_for(controller, evidence, privacy=privacy))
        assert status == 409 and "refused before anything was sent" in page
        assert "never-release" in page
    assert client.inserts == []
    status, _page = controller.submit(form_for(controller, evidence, privacy="private"))
    assert status == 200 and len(client.inserts) == 1
    assert client.inserts[0]["body"]["status"]["privacyStatus"] == "private"
