"""Network-free proofs of the founder-confirmed YouTube upload path (videos.insert only)."""

from __future__ import annotations

import html
import json
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from project_atlas.media import LocalMediaStorage
from project_atlas.persistence import AtlasRepository
from project_atlas.publishing import PublishingService
from project_atlas.publishing_state import TARGET_CHANNEL
from project_atlas.web import create_server
from project_atlas.youtube_adapter import (
    UnsupportedYouTubeMutation,
    YouTubeObservationBlocked,
    YouTubeReadOnlyObservationAdapter,
)
from project_atlas.youtube_preflight import (
    KEYRING_ACCOUNT,
    YOUTUBE_READONLY_SCOPE,
    GoogleInstalledCredentialProvider,
    PreflightBlocked,
)
from project_atlas.youtube_upload import (
    REQUIRED_UPLOAD_NOTICE,
    UPLOAD_KEYRING_ACCOUNT,
    UPLOAD_SCOPES,
    YOUTUBE_UPLOAD_SCOPE,
    GoogleYouTubeUploadClient,
    YouTubeUploadAdapter,
    YouTubeUploadController,
    validate_upload_values,
)
from tests.test_publishing import _artifact, _manifest
from tests.test_youtube_adapter import Credentials, Provider
from tests.test_youtube_preflight import FakeRefreshTokenStore, _write_client_config

CLOCK = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
SECRETS = ("synthetic-refresh-token", "synthetic-access-token", "SECRET-SESSION-ID")


def upload_credentials(scopes=UPLOAD_SCOPES) -> Credentials:
    credentials = Credentials(scopes=tuple(scopes), granted_scopes=tuple(scopes))
    credentials.refresh_token = "synthetic-refresh-token"
    credentials.token = "synthetic-access-token"
    return credentials


class FakeUploadClient:
    """Records exactly what would be sent; no network."""

    def __init__(self) -> None:
        self.channels = [TARGET_CHANNEL]
        self.inserts: list[dict] = []
        self.resource: dict | None = None

    def authenticated_channel_ids(self, credentials):
        return self.channels

    def channel_title(self, credentials):
        return "SimilarStoic"

    def insert_video(self, credentials, media_path: Path, body: dict) -> dict:
        self.inserts.append({"path": media_path, "body": body})
        self.resource = {
            "id": "remote-upload-1",
            "snippet": {
                "channelId": TARGET_CHANNEL,
                "title": body["snippet"]["title"],
                "description": body["snippet"]["description"],
                "tags": body["snippet"]["tags"],
                "categoryId": body["snippet"].get("categoryId"),
                "defaultAudioLanguage": body["snippet"]["defaultAudioLanguage"],
            },
            "status": {
                "privacyStatus": body["status"]["privacyStatus"],
                "uploadStatus": "uploaded",
                "selfDeclaredMadeForKids": body["status"]["selfDeclaredMadeForKids"],
                "containsSyntheticMedia": body["status"]["containsSyntheticMedia"],
            },
            "processingDetails": {"processingStatus": "succeeded"},
            "contentDetails": {"caption": "true", "hasCustomThumbnail": True},
        }
        return self.resource

    def video_resource(self, credentials, remote_id):
        return self.resource


def manifest() -> dict:
    return {
        **_manifest(),
        "language": "en-GB",
        "category": {"id": "27", "name": "Education"},
        "compliance": {"altered_or_synthetic_media": {"declare_to_youtube": True}},
    }


@pytest.fixture
def env(tmp_path):
    repo = AtlasRepository(tmp_path / "offline-upload.sqlite")
    storage = LocalMediaStorage(tmp_path / "media")
    _artifact(repo, storage)
    client = FakeUploadClient()

    def media_for(package):
        artifact = repo.get_final_media_artifact(package.final_media_artifact_id)
        storage.read_verified(artifact.storage_path, package.artifact_digest)
        return storage.path(artifact.storage_path)

    provider = Provider(upload_credentials())
    adapter = YouTubeUploadAdapter(provider, media_for, client, lambda: CLOCK)
    service = PublishingService(repo, storage, adapter, lambda: CLOCK)
    package = service.prepare_package(
        "package-1", "synthetic-pilot", 1, 1, "fake-artifact", manifest()
    )
    service.approve_package("founder-approval-1", package.id, "synthetic-founder")
    controller = YouTubeUploadController(service, adapter, monotonic=lambda: 0.0)
    yield repo, storage, client, provider, adapter, service, package, controller
    repo.close()


def form_for(controller, package, **overrides) -> dict:
    status, page = controller.page(package.id)
    assert status == 200
    nonce = re.search(r"name='nonce' value='([^']+)'", page).group(1)
    values = {
        "nonce": nonce,
        "package_id": package.id,
        "package_digest": package.package_digest,
        "title": package.manifest["title"],
        "description": package.manifest["description"],
        "privacy": "private",
        "founder_confirmation": "confirmed",
    }
    values.update(overrides)
    return {key: value for key, value in values.items() if value is not None}


def test_exact_two_scope_authorization_is_accepted(env):
    *_, adapter, _service, _package, _controller = env
    assert set(UPLOAD_SCOPES) == {YOUTUBE_READONLY_SCOPE, YOUTUBE_UPLOAD_SCOPE}
    assert adapter.authenticated_channel() == TARGET_CHANNEL


@pytest.mark.parametrize(
    ("scopes", "category"),
    [
        ((YOUTUBE_READONLY_SCOPE,), "required_scope_missing"),
        (
            (*UPLOAD_SCOPES, "https://www.googleapis.com/auth/youtube"),
            "unexpected_scope_granted",
        ),
    ],
)
def test_read_only_or_broader_token_is_rejected_for_upload(env, scopes, category):
    _repo, _storage, client, provider, adapter, _service, package, controller = env
    provider.credentials = upload_credentials(scopes)
    with pytest.raises(YouTubeObservationBlocked, match=category):
        adapter.authenticated_channel()
    status, page = controller.page(package.id)
    assert status == 409 and "authorization is not usable" in page
    assert client.inserts == []


def test_upload_authorization_is_separate_and_never_opens_consent_from_a_request(tmp_path):
    assert UPLOAD_KEYRING_ACCOUNT != KEYRING_ACCOUNT
    repository = tmp_path / "repository"
    repository.mkdir()
    client_config = tmp_path / "client.json"
    _write_client_config(client_config)
    provider = GoogleInstalledCredentialProvider(
        client_config,
        FakeRefreshTokenStore(None),
        repository,
        scopes=UPLOAD_SCOPES,
        interactive=False,
    )
    with pytest.raises(PreflightBlocked) as error:
        provider.acquire()
    assert error.value.category == "authorization_missing"


def test_wrong_channel_is_rejected_before_any_upload(env):
    _repo, _storage, client, _provider, adapter, _service, package, controller = env
    client.channels = ["UC-some-other-channel"]
    with pytest.raises(YouTubeObservationBlocked, match="authenticated_channel_mismatch"):
        adapter.authenticated_channel()
    status, _page = controller.page(package.id)
    assert status == 409
    assert client.inserts == []


def test_no_upload_without_explicit_founder_confirmation(env):
    repo, _storage, client, _provider, adapter, service, package, controller = env
    status, page = controller.submit(form_for(controller, package, founder_confirmation=None))
    assert status == 400 and "Founder confirmation is required" in page
    assert client.inserts == []
    # Even a reserved operation without confirmed values never reaches videos.insert.
    operation = service.reserve_upload(package.id)
    assert adapter.begin_private_transfer(package, operation).reason == (
        "founder_confirmation_missing"
    )
    assert client.inserts == []
    # A screen nonce is single-use and bound to the package.
    form = form_for(controller, package)
    assert controller.submit({**form, "package_digest": "0" * 64})[0] == 409
    assert controller.submit(form)[0] == 409
    assert client.inserts == []
    assert repo.connection.execute("SELECT COUNT(*) FROM publication_operations").fetchone()[0] == 1


def test_package_or_artifact_mismatch_is_rejected(env):
    repo, storage, client, _provider, _adapter, service, package, controller = env
    # An unapproved package (no API-route approval) offers no upload form at all.
    other = service.prepare_package(
        "package-2", "synthetic-pilot", 2, 1, "fake-artifact", {**manifest(), "pilot_slot": 2}
    )
    status, page = controller.page(other.id)
    assert status == 409 and "<form" not in page
    # Artifact bytes that no longer match the approved package digest are never uploaded.
    form = form_for(controller, package)
    artifact = repo.get_final_media_artifact(package.final_media_artifact_id)
    storage.path(artifact.storage_path).write_bytes(b"tampered")
    status, page = controller.submit(form)
    assert status == 409 and "refused" in page
    assert client.inserts == []


def test_founder_visible_values_are_exactly_what_videos_insert_receives(env):
    repo, _storage, client, _provider, _adapter, _service, package, controller = env
    title = "  Founder edited title with “quotes” & ünïcode  "
    description = "Line one\nLine two  \n"
    status, _page = controller.submit(
        form_for(controller, package, title=title, description=description, privacy="unlisted")
    )
    assert status == 200
    [sent] = client.inserts
    assert sent["body"]["snippet"]["title"] == title
    assert sent["body"]["snippet"]["description"] == description
    assert sent["body"]["status"]["privacyStatus"] == "unlisted"
    assert sent["body"]["snippet"]["tags"] == package.manifest["tags"]
    assert sent["body"]["status"]["containsSyntheticMedia"] is True
    artifact = repo.get_final_media_artifact(package.final_media_artifact_id)
    assert sent["path"].name == Path(artifact.storage_path).name
    operation_id = repo.connection.execute("SELECT id FROM publication_operations").fetchone()[0]
    intent = repo.get_publication_operation(operation_id).intent
    assert (intent["title"], intent["description"], intent["privacy"]) == (
        title,
        description,
        "unlisted",
    )
    assert intent["founder_confirmation"]["actor"] == "synthetic-founder"


def test_private_insert_returns_sanitized_evidence_and_binds_the_publication(env):
    repo, _storage, client, _provider, _adapter, service, package, controller = env
    status, page = controller.submit(form_for(controller, package))
    assert status == 200
    operation_id = repo.connection.execute("SELECT id FROM publication_operations").fetchone()[0]
    operation = repo.get_publication_operation(operation_id)
    assert operation.outcome == "succeeded"
    observed = next(
        event
        for event in repo.get_publication_operation_events(operation_id)
        if event.kind == "remote_identity_observed"
    )
    assert observed.provider_evidence == {
        "schema": "youtube-founder-confirmed-upload-v1",
        "api_call": "videos.insert(part=snippet,status)",
        "requested_privacy": "private",
        "returned_privacy": "private",
        "upload_status": "uploaded",
        "requested_at": CLOCK.isoformat(),
        "completed_at": CLOCK.isoformat(),
        "remote_id": "remote-upload-1",
        "channel_id": TARGET_CHANNEL,
    }
    for text in ("remote-upload-1", TARGET_CHANNEL, "Returned privacy"):
        assert text in page
    publication_id = repo.connection.execute("SELECT id FROM platform_publications").fetchone()[0]
    # The existing read-only observation path verifies against the confirmed values.
    snapshot = service.observe_status("status-1", publication_id)
    assert (snapshot.privacy, snapshot.verification) == ("private", "passed")
    # Re-submitting the same confirmed values re-shows that operation; no second insert.
    status, again = controller.submit(form_for(controller, package))
    assert status == 200 and "YouTube accepted the upload" in again and len(client.inserts) == 1
    # Different values for the same pilot slot are refused before anything is sent.
    status, page = controller.submit(form_for(controller, package, title="Another title"))
    assert status == 409 and "refused before anything was sent" in page
    assert len(client.inserts) == 1


def test_read_only_observation_adapter_is_unchanged():
    adapter = YouTubeReadOnlyObservationAdapter(Provider(Credentials()), FakeUploadClient())
    assert adapter.authenticated_channel() == TARGET_CHANNEL
    upload_token = YouTubeReadOnlyObservationAdapter(
        Provider(upload_credentials()), FakeUploadClient()
    )
    with pytest.raises(YouTubeObservationBlocked, match="unexpected_scope_granted"):
        upload_token.authenticated_channel()


def test_upload_adapter_has_no_update_or_public_transition():
    adapter = YouTubeUploadAdapter(Provider(upload_credentials()), lambda package: None)
    with pytest.raises(UnsupportedYouTubeMutation):
        adapter.request_public_transition(None, None)
    source = (
        Path(__file__).resolve().parents[1] / "src" / "project_atlas" / "youtube_upload.py"
    ).read_text(encoding="utf-8")
    assert "videos.update" not in source.replace("no videos.update", "")
    assert ".patch(" not in source and ".delete(" not in source


def test_google_client_streams_once_and_never_persists_session_or_tokens(
    env, monkeypatch, tmp_path
):
    repo, _storage, _client, _provider, _adapter, _service, _package, _controller = env
    calls = []

    class Response:
        def __init__(self, status_code, headers=None, payload=None):
            self.status_code, self.headers, self._payload = status_code, headers or {}, payload

        def json(self):
            return self._payload

    class FakeSession:
        def __init__(self, credentials):
            pass

        def post(self, url, **kwargs):
            calls.append(("post", url, kwargs["params"], kwargs["json"]))
            return Response(
                200,
                {
                    "Location": "https://www.googleapis.com/upload/youtube/v3/videos?upload_id=SECRET-SESSION-ID"
                },
            )

        def put(self, url, data=None, **kwargs):
            calls.append(("put", url, data.read()))
            return Response(
                200, payload={"id": "remote-2", "snippet": {"channelId": TARGET_CHANNEL}}
            )

    import google.auth.transport.requests as requests_module

    monkeypatch.setattr(requests_module, "AuthorizedSession", FakeSession)
    media = tmp_path / "video.mp4"
    media.write_bytes(b"synthetic-video")
    body = {"snippet": {"title": "t"}, "status": {"privacyStatus": "private"}}
    resource = GoogleYouTubeUploadClient().insert_video(upload_credentials(), media, body)
    assert resource["id"] == "remote-2"
    assert calls[0][2] == {"uploadType": "resumable", "part": "snippet,status"}
    assert calls[0][3] == body and calls[1][2] == b"synthetic-video"
    assert len(calls) == 2


def test_no_secret_or_session_material_in_persisted_or_rendered_evidence(env, capsys):
    repo, _storage, _client, _provider, _adapter, _service, package, controller = env
    status, page = controller.submit(form_for(controller, package))
    assert status == 200
    dump = "\n".join(repo.connection.iterdump())
    output = capsys.readouterr()
    for secret in SECRETS:
        assert secret not in dump and secret not in page
        assert secret not in output.out and secret not in output.err


def test_final_upload_screen_shows_required_notice_channel_and_choices(env):
    *_, package, controller = env
    status, page = controller.page(package.id)
    assert status == 200
    assert html.escape(REQUIRED_UPLOAD_NOTICE) in page
    assert "https://www.youtube.com/t/terms" in page
    assert "<button type='submit'>Upload</button>" in page
    assert page.index("youtube-upload-notice") < page.index("<button type='submit'>Upload")
    for value in ("public", "private", "unlisted"):
        assert f"name='privacy' value='{value}' required>" in page
    assert "checked" not in page
    assert "SimilarStoic" in page and TARGET_CHANNEL in page
    assert package.final_media_artifact_id in page and package.artifact_digest in page
    assert "maxlength='100'" in page


def test_upload_value_validation_follows_youtube_limits_only():
    assert validate_upload_values("x" * 100, "d" * 5000, "public") == []
    assert validate_upload_values("x" * 101, "d", "private")
    assert validate_upload_values("ok", "é" * 2501, "private")
    assert validate_upload_values("a <b>", "d", "private")
    assert validate_upload_values("ok", "d", "draft")


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


def test_web_route_is_loopback_same_origin_and_absent_unless_configured(env, tmp_path):
    repo, storage, _client, _provider, adapter, service, package, _controller = env
    plain = create_server(port=0, database_path=tmp_path / "plain.db")
    try:
        base = f"http://127.0.0.1:{plain.server_address[1]}"
        status, _body, _headers = _serve(plain, f"{base}/youtube/upload?package={package.id}")
        assert status == 503
    finally:
        plain.server_close()

    configured = create_server(
        port=0,
        database_path=tmp_path / "configured.db",
        youtube_upload=lambda _repository: YouTubeUploadController(service, adapter),
    )
    try:
        port = configured.server_address[1]
        base = f"http://127.0.0.1:{port}"
        status, body, headers = _serve(configured, f"{base}/youtube/upload?package={package.id}")
        assert status == 200 and "youtube-upload-notice" in body
        assert headers["X-Frame-Options"] == "DENY"
        assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
        cross_site = Request(
            f"{base}/youtube/upload",
            data=urlencode({"founder_confirmation": "confirmed"}).encode(),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://attacker.invalid",
            },
            method="POST",
        )
        assert _serve(configured, cross_site)[0] == 403
        rebinding = Request(f"{base}/youtube/upload?package={package.id}")
        rebinding.add_header("Host", f"attacker.invalid:{port}")
        assert _serve(configured, rebinding)[0] == 403
        forged = Request(
            f"{base}/youtube/upload",
            data=urlencode(
                {"package_id": package.id, "founder_confirmation": "confirmed", "nonce": "guess"}
            ).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        assert _serve(configured, forged)[0] == 409
    finally:
        configured.server_close()


# --- Review fixes: loopback surface, fresh verified consent, post-dispatch uncertainty -------


def test_loopback_detection_accepts_only_literal_loopback_addresses():
    from project_atlas.web import is_loopback

    for value in ("127.0.0.1", "127.5.5.5", "::1", "::ffff:127.0.0.1"):
        assert is_loopback(value)
    for value in ("0.0.0.0", "192.168.1.5", "203.0.113.9", "localhost", "", "::"):
        assert not is_loopback(value)


def test_upload_server_refuses_a_non_loopback_bind(env, tmp_path):
    *_, adapter, service, _package, _controller = env
    with pytest.raises(ValueError, match="loopback"):
        create_server(
            host="0.0.0.0",
            port=0,
            database_path=tmp_path / "exposed.db",
            youtube_upload=lambda _repository: YouTubeUploadController(service, adapter),
        )


def test_non_loopback_peer_is_refused_even_with_forged_localhost_host(env, tmp_path, monkeypatch):
    *_, adapter, service, package, _controller = env
    from project_atlas.web import AtlasRequestHandler

    server = create_server(
        port=0,
        database_path=tmp_path / "peer.db",
        youtube_upload=lambda _repository: YouTubeUploadController(service, adapter),
    )
    original_setup = AtlasRequestHandler.setup

    def remote_peer(handler):
        original_setup(handler)
        handler.client_address = ("203.0.113.9", 40000)

    monkeypatch.setattr(AtlasRequestHandler, "setup", remote_peer)
    try:
        port = server.server_address[1]
        request = Request(f"http://127.0.0.1:{port}/youtube/upload?package={package.id}")
        request.add_header("Host", f"127.0.0.1:{port}")
        status, body, _headers = _serve(server, request)
        assert status == 403 and "youtube-upload-notice" not in body
        forged_post = Request(
            f"http://127.0.0.1:{port}/youtube/upload",
            data=urlencode({"founder_confirmation": "confirmed"}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        forged_post.add_header("Host", f"localhost:{port}")
        assert _serve(server, forged_post)[0] == 403
    finally:
        server.server_close()


class ConsentFlow:
    def __init__(self, credentials=None, error=None) -> None:
        self.credentials, self.error, self.calls = credentials, error, 0

    def run_local_server(self, **kwargs):
        self.calls += 1
        assert kwargs["prompt"] == "consent" and kwargs["include_granted_scopes"] == "false"
        if self.error:
            raise self.error
        return self.credentials


class ChannelClient:
    def __init__(self, channels) -> None:
        self.channels = channels

    def authenticated_channel_ids(self, credentials):
        return self.channels


def _consent(monkeypatch, flow, requested):
    from google_auth_oauthlib.flow import InstalledAppFlow

    def from_client_config(cls, config, scopes, **kwargs):
        requested.append(tuple(scopes))
        return flow

    monkeypatch.setattr(InstalledAppFlow, "from_client_config", classmethod(from_client_config))


def _fresh(scopes=UPLOAD_SCOPES, token="new-upload-token") -> Credentials:
    credentials = Credentials(scopes=tuple(scopes), granted_scopes=tuple(scopes))
    credentials.refresh_token = token
    return credentials


def _authorize(tmp_path, store, channels):
    from project_atlas.youtube_upload import authorize

    client_config = tmp_path / "client.json"
    _write_client_config(client_config)
    result = tmp_path / "evidence" / "authorize.json"
    code = authorize(client_config, result, store=store, channel_client=ChannelClient(channels))
    return code, json.loads(result.read_text(encoding="utf-8"))


def test_authorize_is_always_fresh_and_stores_only_after_exact_verification(tmp_path, monkeypatch):
    store = FakeRefreshTokenStore("prior-upload-token")
    requested: list[tuple] = []
    flow = ConsentFlow(_fresh())
    _consent(monkeypatch, flow, requested)
    # Wrong channel: consent ran, nothing replaced the prior authorization.
    code, evidence = _authorize(tmp_path, store, ["UC-some-other-channel"])
    assert code == 2 and evidence["status"] == "BLOCKER" and evidence["stored"] is False
    assert evidence["error_category"] == "authenticated_channel_mismatch"
    assert store.saved == [] and store.refresh_token == "prior-upload-token"
    # A later run consents again (the stored token is never reused) and stores on PASS.
    code, evidence = _authorize(tmp_path, store, [TARGET_CHANNEL])
    assert code == 0 and evidence["status"] == "PASS" and evidence["stored"] is True
    assert store.saved == ["new-upload-token"]
    assert flow.calls == 2 and requested == [UPLOAD_SCOPES, UPLOAD_SCOPES]
    assert "new-upload-token" not in json.dumps(evidence)


@pytest.mark.parametrize(
    ("flow", "category"),
    [
        (ConsentFlow(_fresh(scopes=(YOUTUBE_READONLY_SCOPE,))), "required_scope_missing"),
        (
            ConsentFlow(_fresh(scopes=(*UPLOAD_SCOPES, "https://www.googleapis.com/auth/youtube"))),
            "unexpected_scope_granted",
        ),
        (ConsentFlow(error=RuntimeError("consent closed")), "interactive_authorization_failed"),
        (ConsentFlow(_fresh(token=None)), "refresh_token_missing"),
    ],
)
def test_failed_or_wrong_scope_consent_never_poisons_the_stored_upload_token(
    tmp_path, monkeypatch, flow, category
):
    store = FakeRefreshTokenStore("prior-upload-token")
    _consent(monkeypatch, flow, [])
    code, evidence = _authorize(tmp_path, store, [TARGET_CHANNEL])
    assert code == 2 and evidence["error_category"] == category and evidence["stored"] is False
    assert store.saved == [] and store.refresh_token == "prior-upload-token"


def test_read_only_preflight_consent_behaviour_is_unchanged(tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    repository.mkdir()
    client_config = tmp_path / "client.json"
    _write_client_config(client_config)
    requested: list[tuple] = []
    flow = ConsentFlow(_fresh(scopes=(YOUTUBE_READONLY_SCOPE,), token="ro"))
    _consent(monkeypatch, flow, requested)
    store = FakeRefreshTokenStore()
    GoogleInstalledCredentialProvider(client_config, store, repository).acquire()
    assert requested == [(YOUTUBE_READONLY_SCOPE,)] and store.saved == ["ro"]


def test_post_dispatch_uncertainty_is_never_reported_as_nothing_sent(env):
    from project_atlas.youtube_upload import YouTubeUploadUncertain

    repo, _storage, client, _provider, _adapter, _service, package, controller = env

    def lost_response(credentials, media_path, body):
        client.inserts.append({"path": media_path, "body": body})
        raise YouTubeUploadUncertain("upload_response_lost")

    client.insert_video = lost_response
    status, page = controller.submit(form_for(controller, package))
    assert status == 200
    assert "upload-outcome-unknown" in page and "Do not upload it again" in page
    assert "nothing was sent" not in page.lower()
    operation_id = repo.connection.execute("SELECT id FROM publication_operations").fetchone()[0]
    assert repo.get_publication_operation(operation_id).outcome == "unknown"
    # Re-submitting shows the same unresolved operation, never a second insert.
    status, again = controller.submit(form_for(controller, package))
    assert status == 200 and "upload-outcome-unknown" in again and len(client.inserts) == 1
    status, page = controller.submit(form_for(controller, package, title="Another title"))
    assert status == 409 and len(client.inserts) == 1


def test_an_exception_after_dispatch_shows_unknown_not_refused(env):
    repo, _storage, client, _provider, _adapter, _service, package, controller = env
    original = client.insert_video

    def wrong_channel(credentials, media_path, body):
        resource = original(credentials, media_path, body)
        resource["snippet"]["channelId"] = "UC-some-other-channel"
        return resource

    client.insert_video = wrong_channel
    status, page = controller.submit(form_for(controller, package))
    assert status == 200 and "upload-outcome-unknown" in page
    assert "refused before anything was sent" not in page
    operation_id = repo.connection.execute("SELECT id FROM publication_operations").fetchone()[0]
    assert repo.get_publication_operation(operation_id).outcome == "unknown"


def test_pre_dispatch_refusal_may_say_nothing_was_sent(env):
    repo, storage, client, _provider, _adapter, _service, package, controller = env
    form = form_for(controller, package)
    artifact = repo.get_final_media_artifact(package.final_media_artifact_id)
    storage.path(artifact.storage_path).write_bytes(b"tampered")
    status, page = controller.submit(form)
    assert status == 409 and "refused before anything was sent to YouTube" in page
    assert client.inserts == []
