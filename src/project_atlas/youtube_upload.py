"""Founder-confirmed YouTube upload (videos.insert) of one approved Conveyor PublishingPackage.

The only YouTube mutation is one ``videos.insert`` for the exact artifact bound to an approved
package, with the title, description and privacy the founder confirmed on the local upload
screen. There is no videos.update, privacy transition, delete or resumable-session persistence.
Authorization uses a separate, freshly consented token for exactly ``youtube.readonly`` +
``youtube.upload``; the read-only observation token is never treated as upload-capable.
"""

from __future__ import annotations

import argparse
import html
import json
import secrets
import sys
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from project_atlas.media import LocalMediaStorage, MediaRuntimeError
from project_atlas.publishing import PublishingService, TransferResult
from project_atlas.publishing_state import PublicationOperation, PublishingPackage
from project_atlas.youtube_adapter import (
    CredentialProvider,
    GoogleReadOnlyYouTubeClient,
    YouTubeObservationBlocked,
    YouTubeReadOnlyObservationAdapter,
)
from project_atlas.youtube_preflight import (
    CHANNELS_ENDPOINT,
    EXPECTED_CHANNEL_ID,
    YOUTUBE_READONLY_SCOPE,
    GoogleInstalledCredentialProvider,
    GoogleReadOnlyChannelClient,
    PreflightBlocked,
    WindowsCredentialRefreshTokenStore,
    _outside_repository,
    _write_sanitized_json,
    verify_exact_channel,
)

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
UPLOAD_SCOPES = (YOUTUBE_READONLY_SCOPE, YOUTUBE_UPLOAD_SCOPE)
# A distinct credential-store entry: the read-only token can never satisfy an upload.
UPLOAD_KEYRING_ACCOUNT = f"{EXPECTED_CHANNEL_ID}:upload-v1"
UPLOAD_ENDPOINT = "https://www.googleapis.com/upload/youtube/v3/videos"
UPLOAD_ADAPTER_VERSION = "youtube-founder-confirmed-upload-v1"
YOUTUBE_TERMS_URL = "https://www.youtube.com/t/terms"
# YouTube API Services Terms of Service, section 9.1 (Required Notice), verbatim, with the
# non-mobile URL that section prescribes for uploads from a personal computer.
REQUIRED_UPLOAD_NOTICE = (
    "By clicking 'upload,' you certify that the content you are uploading complies with the "
    "YouTube Terms of Service (including the YouTube Community Guidelines) at "
    f"{YOUTUBE_TERMS_URL}. Please be sure not to violate others' copyright or privacy rights."
)
PRIVACY_CHOICES = ("public", "private", "unlisted")
MAX_TITLE_CHARACTERS = 100
MAX_DESCRIPTION_BYTES = 5000
NONCE_SECONDS = 15 * 60


class YouTubeUploadBlocked(RuntimeError):
    """Definitive, credential-free failure before any upload bytes were accepted."""


class YouTubeUploadUncertain(RuntimeError):
    """The request may have reached YouTube; the outcome must be reconciled, not repeated."""


def validate_upload_values(title: Any, description: Any, privacy: Any) -> list[str]:
    """Check YouTube's own upload constraints without imposing narrower ones."""

    errors = []
    if not isinstance(title, str) or not title.strip():
        errors.append("A title is required.")
    elif len(title) > MAX_TITLE_CHARACTERS:
        errors.append("YouTube titles are limited to 100 characters.")
    if not isinstance(description, str):
        errors.append("A description is required.")
    elif len(description.encode("utf-8")) > MAX_DESCRIPTION_BYTES:
        errors.append("YouTube descriptions are limited to 5000 bytes.")
    for name, value in (("title", title), ("description", description)):
        if isinstance(value, str) and ("<" in value or ">" in value):
            errors.append(f"YouTube does not accept < or > in the {name}.")
    if privacy not in PRIVACY_CHOICES:
        errors.append("Choose public, private or unlisted.")
    return errors


def build_insert_body(package: PublishingPackage, intent: dict[str, Any]) -> dict[str, Any]:
    """videos.insert resource: confirmed title/description/privacy, package-approved rest."""

    manifest = package.manifest
    snippet: dict[str, Any] = {
        "title": intent["title"],
        "description": intent["description"],
        "tags": list(manifest.get("tags", [])),
        "defaultAudioLanguage": manifest.get("language"),
    }
    category = manifest.get("category") or {}
    if category.get("id") is not None:
        snippet["categoryId"] = str(category["id"])
    synthetic = (manifest.get("compliance") or {}).get("altered_or_synthetic_media") or {}
    return {
        "snippet": snippet,
        "status": {
            "privacyStatus": intent["privacy"],
            "selfDeclaredMadeForKids": bool((manifest.get("audience") or {}).get("made_for_kids")),
            "containsSyntheticMedia": bool(synthetic.get("declare_to_youtube")),
        },
    }


class GoogleYouTubeUploadClient(GoogleReadOnlyYouTubeClient):
    """Read methods plus exactly one mutation: videos.insert (single resumable session)."""

    def channel_title(self, credentials: Any) -> str | None:
        payload = self._get(
            credentials, CHANNELS_ENDPOINT, {"part": "snippet", "mine": "true", "maxResults": 1}
        )
        items = payload.get("items") or []
        if len(items) != 1 or not isinstance(items[0], dict):
            return None
        title = (items[0].get("snippet") or {}).get("title")
        return title if isinstance(title, str) else None

    def insert_video(
        self, credentials: Any, media_path: Path, body: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            from google.auth.transport.requests import AuthorizedSession

            session = AuthorizedSession(credentials)
            size = media_path.stat().st_size
            start = session.post(
                UPLOAD_ENDPOINT,
                params={"uploadType": "resumable", "part": "snippet,status"},
                json=body,
                headers={
                    "X-Upload-Content-Type": "video/mp4",
                    "X-Upload-Content-Length": str(size),
                },
                timeout=60,
            )
        except Exception as exc:
            # No session was established, so no video can exist.
            raise YouTubeUploadBlocked("youtube_request_failed") from exc
        if start.status_code in {401, 403}:
            raise YouTubeUploadBlocked("authorization_unusable")
        location = start.headers.get("Location") if start.status_code == 200 else None
        if not location:
            raise YouTubeUploadBlocked("youtube_upload_rejected")
        # The session URL is protected material: it is used here once and never stored/logged.
        try:
            with media_path.open("rb") as handle:
                response = session.put(
                    location,
                    data=handle,
                    headers={"Content-Type": "video/mp4", "Content-Length": str(size)},
                    timeout=3600,
                )
        except Exception as exc:
            raise YouTubeUploadUncertain("upload_response_lost") from exc
        if response.status_code not in {200, 201}:
            raise YouTubeUploadUncertain("upload_response_not_success")
        try:
            resource = response.json()
        except ValueError as exc:
            raise YouTubeUploadUncertain("upload_response_invalid") from exc
        if not isinstance(resource, dict):
            raise YouTubeUploadUncertain("upload_response_invalid")
        return resource


class YouTubeUploadAdapter(YouTubeReadOnlyObservationAdapter):
    """Observation plus one founder-confirmed videos.insert; no other mutation."""

    REQUIRED_SCOPES = UPLOAD_SCOPES

    def __init__(
        self,
        credential_provider: CredentialProvider,
        media_resolver: Callable[[PublishingPackage], Path],
        client: GoogleYouTubeUploadClient | Any | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__(credential_provider, client or GoogleYouTubeUploadClient(), clock)
        self.media_resolver = media_resolver

    @classmethod
    def from_upload_config(
        cls,
        client_config: Path,
        repository_root: Path,
        media_resolver: Callable[[PublishingPackage], Path],
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> YouTubeUploadAdapter:
        """Non-interactive: a missing upload authorization fails closed, never opens consent."""

        provider = GoogleInstalledCredentialProvider(
            client_config,
            WindowsCredentialRefreshTokenStore(account=UPLOAD_KEYRING_ACCOUNT),
            repository_root,
            scopes=UPLOAD_SCOPES,
            interactive=False,
        )
        return cls(provider, media_resolver, clock=clock)

    def authenticated_channel_title(self) -> str | None:
        credentials = self._authorized()
        return self.client.channel_title(credentials)

    def _now(self) -> str:
        return self.clock().replace(microsecond=0).isoformat()

    def begin_private_transfer(
        self, package: PublishingPackage, operation: PublicationOperation
    ) -> TransferResult:
        intent = operation.intent
        confirmation = intent.get("founder_confirmation") or {}
        if (
            intent.get("schema") != "confirmed-upload-v1"
            or not confirmation.get("actor")
            or validate_upload_values(
                intent.get("title"), intent.get("description"), intent.get("privacy")
            )
        ):
            return TransferResult(
                "failed", package.channel_id, reason="founder_confirmation_missing"
            )
        try:
            credentials = self._authorized()
            media_path = self.media_resolver(package)
        except (YouTubeObservationBlocked, MediaRuntimeError, ValueError) as exc:
            return TransferResult("failed", package.channel_id, reason=str(exc))
        requested_at = self._now()
        try:
            resource = self.client.insert_video(
                credentials, media_path, build_insert_body(package, intent)
            )
        except YouTubeUploadBlocked as exc:
            return TransferResult("failed", package.channel_id, reason=str(exc))
        except YouTubeUploadUncertain as exc:
            return TransferResult("unknown", package.channel_id, reason=str(exc))
        try:
            remote_id = resource["id"]
            channel_id = resource["snippet"]["channelId"]
            status = resource.get("status") or {}
        except (KeyError, TypeError):
            return TransferResult("unknown", package.channel_id, reason="upload_response_invalid")
        if not isinstance(remote_id, str) or not remote_id:
            return TransferResult("unknown", package.channel_id, reason="upload_response_invalid")
        return TransferResult(
            "succeeded",
            channel_id,
            remote_id,
            evidence={
                "schema": UPLOAD_ADAPTER_VERSION,
                "api_call": "videos.insert(part=snippet,status)",
                "requested_privacy": intent["privacy"],
                "returned_privacy": status.get("privacyStatus"),
                "upload_status": status.get("uploadStatus"),
                "requested_at": requested_at,
                "completed_at": self._now(),
            },
        )


def _page(title: str, body: str) -> str:
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title><style>"
        "body{font:16px/1.5 system-ui,sans-serif;max-width:760px;margin:24px auto;padding:0 16px;"
        "color:#1d1e1f;background:#fffdf8}h1{font-size:24px}dl{display:grid;"
        "grid-template-columns:max-content 1fr;gap:4px 16px}dt{font-weight:600}dd{margin:0;"
        "overflow-wrap:anywhere}label{display:block;font-weight:600;margin-top:16px}"
        "input[type=text],textarea{width:100%;box-sizing:border-box;font:inherit;padding:8px}"
        "textarea{min-height:180px}.notice{border:2px solid #c00;padding:12px;margin:20px 0}"
        "button{font:inherit;font-weight:700;padding:10px 28px;background:#c00;color:#fff;"
        "border:0;border-radius:4px}.blocked{border:2px solid #555;padding:12px}"
        "fieldset{border:1px solid #999;margin-top:16px}"
        "</style></head><body>"
        f"{body}</body></html>"
    )


def _rows(values: list[tuple[str, Any]]) -> str:
    return (
        "<dl>"
        + "".join(
            f"<dt>{html.escape(name)}</dt><dd>{html.escape(str(value))}</dd>"
            for name, value in values
        )
        + "</dl>"
    )


class YouTubeUploadController:
    """Local founder upload screen: one approved package, one confirmed videos.insert."""

    def __init__(
        self,
        service: PublishingService,
        adapter: YouTubeUploadAdapter,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.service = service
        self.repository = service.repository
        self.adapter = adapter
        self.monotonic = monotonic
        self._nonces: dict[str, tuple[str, str, float]] = {}

    @classmethod
    def from_client_config(
        cls,
        repository: Any,
        media_storage_root: Path | None,
        client_config: Path,
        repository_root: Path,
    ) -> YouTubeUploadController:
        storage = LocalMediaStorage(media_storage_root)

        def media_for(package: PublishingPackage) -> Path:
            artifact = repository.get_final_media_artifact(package.final_media_artifact_id)
            storage.read_verified(artifact.storage_path, package.artifact_digest)
            return storage.path(artifact.storage_path)

        adapter = YouTubeUploadAdapter.from_upload_config(client_config, repository_root, media_for)
        return cls(PublishingService(repository, storage, adapter), adapter)

    @staticmethod
    def allowed_request(host: str | None, origin: str | None, port: int) -> bool:
        """Refuse requests not addressed to this loopback server (DNS rebinding/cross-site)."""

        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if host not in hosts:
            return False
        return origin is None or origin in {f"http://{value}" for value in hosts}

    def _approval(self, package: PublishingPackage):
        approval = self.repository.effective_publication_approval(package.id)
        if (
            approval is None
            or approval.package_digest != package.package_digest
            or approval.transfer_route != "api"
        ):
            return None
        return approval

    def page(self, package_id: str) -> tuple[int, str]:
        try:
            package = self.repository.get_publishing_package(package_id)
        except KeyError:
            return 404, _page("YouTube upload", "<h1>YouTube upload</h1><p>Package not found.</p>")
        approval = self._approval(package)
        artifact = self.repository.get_final_media_artifact(package.final_media_artifact_id)
        package_rows = _rows(
            [
                ("Conveyor package", f"{package.id} (version {package.version})"),
                ("Package digest", package.package_digest),
                ("Artifact", package.final_media_artifact_id),
                ("Artifact SHA-256", package.artifact_digest),
                ("Duration", f"{artifact.duration_ms / 1000:.3f} s"),
                ("Founder approval", approval.id if approval else "none for API upload"),
            ]
        )
        header = (
            "<h1>YouTube upload</h1><p>This screen uploads one video to YouTube using the "
            "YouTube Data API (videos.insert). Nothing is sent until you press "
            "<b>Upload</b>.</p>"
        )
        if approval is None:
            return 409, _page(
                "YouTube upload",
                header + package_rows + "<p class='blocked'>This package has no effective "
                "founder approval for an API upload, so it cannot be uploaded here.</p>",
            )
        try:
            channel_id = self.adapter.authenticated_channel()
            channel_title = self.adapter.authenticated_channel_title()
        except YouTubeObservationBlocked as exc:
            return 409, _page(
                "YouTube upload",
                header + package_rows + "<p class='blocked'>YouTube upload authorization is "
                f"not usable ({html.escape(str(exc))}). Authorize the exact SimilarStoic channel "
                "for youtube.readonly + youtube.upload with "
                "<code>python -m project_atlas.youtube_upload authorize</code>, then reload.</p>",
            )
        nonce = secrets.token_urlsafe(32)
        self._nonces[nonce] = (package.id, package.package_digest, self.monotonic())
        manifest = package.manifest
        private_first = manifest.get("private_first") is True
        choices = "".join(
            f"<label><input type='radio' name='privacy' value='{value}' required> "
            f"{value.capitalize()}</label>"
            for value in PRIVACY_CHOICES
        )
        body = (
            header
            + "<h2>YouTube channel</h2>"
            + _rows(
                [
                    ("Authenticated channel", f"{channel_title or '(title unavailable)'}"),
                    ("Authenticated channel ID", channel_id),
                    ("Target channel ID", package.channel_id),
                ]
            )
            + "<h2>Conveyor package</h2>"
            + package_rows
            + "<form method='post' action='/youtube/upload'>"
            + f"<input type='hidden' name='package_id' value='{html.escape(package.id)}'>"
            + f"<input type='hidden' name='package_digest' value='{package.package_digest}'>"
            + f"<input type='hidden' name='nonce' value='{nonce}'>"
            + "<label for='title'>Title</label>"
            + f"<input type='text' id='title' name='title' maxlength='{MAX_TITLE_CHARACTERS}' "
            + f"value='{html.escape(str(manifest.get('title', '')), quote=True)}' required>"
            + "<label for='description'>Description</label>"
            + "<textarea id='description' name='description'>"
            + html.escape(str(manifest.get("description", "")))
            + "</textarea>"
            + "<fieldset><legend><b>Privacy</b> (choose one)</legend>"
            + choices
            + (
                "<p>This package was approved private-first. Unverified API projects can "
                "only upload private videos.</p>"
                if private_first
                else ""
            )
            + "</fieldset>"
            + _rows(
                [
                    ("Tags", ", ".join(manifest.get("tags", []))),
                    ("Audio language", manifest.get("language")),
                    (
                        "Made for kids",
                        bool((manifest.get("audience") or {}).get("made_for_kids")),
                    ),
                ]
            )
            + "<label><input type='checkbox' name='founder_confirmation' value='confirmed' "
            + "required> I confirm this YouTube upload of "
            + f"{html.escape(package.final_media_artifact_id)} "
            + f"to channel {html.escape(channel_title or channel_id)} ({html.escape(channel_id)}) "
            + "with the title, description and privacy shown above.</label>"
            + f"<p class='notice' id='youtube-upload-notice'>{html.escape(REQUIRED_UPLOAD_NOTICE)}"
            + f" <a href='{YOUTUBE_TERMS_URL}' target='_blank' rel='noopener'>"
            + "YouTube Terms of Service</a></p>"
            + "<button type='submit'>Upload</button></form>"
        )
        return 200, _page("YouTube upload", body)

    def submit(self, form: dict[str, str]) -> tuple[int, str]:
        nonce = form.get("nonce", "")
        binding = self._nonces.pop(nonce, None)
        if binding is None or self.monotonic() - binding[2] > NONCE_SECONDS:
            return 409, _page(
                "YouTube upload",
                "<h1>YouTube upload</h1><p class='blocked'>This upload screen has expired or was "
                "already used. Reload the upload screen; nothing was sent to YouTube.</p>",
            )
        package_id, package_digest, _issued = binding
        try:
            package = self.repository.get_publishing_package(package_id)
        except KeyError:
            return 404, _page("YouTube upload", "<p>Package not found.</p>")
        approval = self._approval(package)
        if (
            form.get("package_id") != package_id
            or form.get("package_digest") != package_digest
            or package.package_digest != package_digest
            or approval is None
        ):
            return 409, _page(
                "YouTube upload",
                "<h1>YouTube upload</h1><p class='blocked'>The package or its approval changed. "
                "Nothing was sent to YouTube.</p>",
            )
        if form.get("founder_confirmation") != "confirmed":
            return 400, _page(
                "YouTube upload",
                "<h1>YouTube upload</h1><p class='blocked'>Founder confirmation is required. "
                "Nothing was sent to YouTube.</p>",
            )
        title, description, privacy = (
            form.get("title"),
            form.get("description"),
            form.get("privacy"),
        )
        errors = validate_upload_values(title, description, privacy)
        if errors:
            return 400, _page(
                "YouTube upload",
                "<h1>YouTube upload</h1><p class='blocked'>"
                + " ".join(html.escape(error) for error in errors)
                + " Nothing was sent to YouTube.</p>",
            )
        operation = None
        try:
            operation = self.service.reserve_upload(
                package.id,
                upload={
                    "title": title,
                    "description": description,
                    "privacy": privacy,
                    "founder_actor": approval.founder_actor,
                    "founder_confirmed": True,
                },
            )
            self.service.begin_api_upload(operation.id)
        except Exception as exc:
            if operation is not None and self._dispatched(operation.id):
                # Past dispatch, an exception never means nothing reached YouTube.
                return 200, self.result_page(operation.id)
            if isinstance(exc, (ValueError, MediaRuntimeError, YouTubeObservationBlocked)):
                return 409, _page(
                    "YouTube upload",
                    "<h1>YouTube upload</h1><p class='blocked'>The upload was refused before "
                    f"anything was sent to YouTube: {html.escape(str(exc))}</p>",
                )
            raise
        return 200, self.result_page(operation.id)

    def _dispatched(self, operation_id: str) -> bool:
        return any(
            event.kind == "dispatch_started"
            for event in self.repository.get_publication_operation_events(operation_id)
        )

    def result_page(self, operation_id: str) -> str:
        operation = self.repository.get_publication_operation(operation_id)
        events = self.repository.get_publication_operation_events(operation_id)
        provider = (
            next(
                (
                    event.provider_evidence
                    for event in events
                    if event.kind == "remote_identity_observed"
                ),
                None,
            )
            or {}
        )
        last = events[-1]
        reason = (last.provider_evidence or {}).get("reason") or last.evidence.get("reason")
        rows = [
            ("Operation", operation.id),
            ("Outcome", operation.outcome),
            ("Requested privacy", operation.intent.get("privacy")),
        ]
        if provider:
            rows += [
                ("YouTube video ID", provider.get("remote_id")),
                ("YouTube channel ID", provider.get("channel_id")),
                ("Returned privacy", provider.get("returned_privacy")),
                ("Upload status", provider.get("upload_status")),
                ("Requested at", provider.get("requested_at")),
                ("Completed at", provider.get("completed_at")),
            ]
        elif reason:
            rows.append(("Reason", reason))
        if operation.outcome == "succeeded":
            summary = "<p>YouTube accepted the upload.</p>"
        elif operation.outcome == "failed":
            # Definitive: YouTube did not create a video (no upload session was accepted).
            summary = "<p class='blocked'>YouTube did not accept this upload.</p>"
        else:
            summary = (
                "<p class='blocked' id='upload-outcome-unknown'>The outcome of this upload is "
                "unknown. The video may have reached YouTube. Do not upload it again: check the "
                "channel in YouTube Studio and reconcile this operation first.</p>"
            )
        return _page(
            "YouTube upload result",
            "<h1>YouTube upload result</h1>" + summary + _rows(rows),
        )


def authorize(
    client_config: Path,
    result_file: Path,
    *,
    store: Any | None = None,
    channel_client: Any | None = None,
) -> int:
    """Always-fresh consent for exactly youtube.readonly + youtube.upload.

    The new refresh token is stored only after the exact scope set and the exact SimilarStoic
    channel both verify; any failure leaves the previously stored upload token unchanged.
    """

    repository_root = Path(__file__).resolve().parents[2]
    _outside_repository(result_file, repository_root)
    store = store or WindowsCredentialRefreshTokenStore(account=UPLOAD_KEYRING_ACCOUNT)
    provider = GoogleInstalledCredentialProvider(
        client_config,
        store,
        repository_root,
        scopes=UPLOAD_SCOPES,
        interactive=True,
        success_message="Conveyor YouTube upload authorization completed. You may close this tab.",
    )
    try:
        credentials = provider.fresh_consent()
        result = verify_exact_channel(
            credentials,
            channel_client or GoogleReadOnlyChannelClient(),
            required_scopes=frozenset(UPLOAD_SCOPES),
        )
        evidence = {**result.evidence(), "stored": False}
        if result.status == "PASS":
            store.set(credentials.refresh_token)
            evidence["stored"] = True
    except PreflightBlocked as exc:
        evidence = {"status": "BLOCKER", "error_category": exc.category, "stored": False}
    _write_sanitized_json(result_file, evidence)
    print(json.dumps(evidence, sort_keys=True))
    return 0 if evidence.get("status") == "PASS" else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    consent = sub.add_parser("authorize", help="Fresh consent for youtube.readonly + upload.")
    consent.add_argument("--client-config", type=Path, required=True)
    consent.add_argument("--result-file", type=Path, required=True)
    args = parser.parse_args(argv)
    return authorize(args.client_config, args.result_file)


def upload_screen_path(package_id: str) -> str:
    return f"/youtube/upload?package={quote(package_id)}"


if __name__ == "__main__":
    sys.exit(main())
