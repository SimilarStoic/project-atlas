"""Read-only YouTube observation for founder-operated manual transfers."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from project_atlas.publishing import RemoteObservation
from project_atlas.publishing_state import (
    PlatformPublication,
    PublicationOperation,
    PublicationReceipt,
    PublishingPackage,
)
from project_atlas.youtube_preflight import (
    EXPECTED_CHANNEL_ID,
    YOUTUBE_READONLY_SCOPE,
    CredentialView,
    GoogleInstalledCredentialProvider,
    PreflightBlocked,
    WindowsCredentialRefreshTokenStore,
    verify_exact_channel,
)

VIDEOS_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
ADAPTER_VERSION = "youtube-readonly-observation-v1"


class CredentialProvider(Protocol):
    def acquire(self) -> CredentialView: ...


class ReadOnlyYouTubeClient(Protocol):
    def authenticated_channel_ids(self, credentials: CredentialView) -> list[str]: ...

    def video_resource(
        self, credentials: CredentialView, remote_id: str
    ) -> dict[str, Any] | None: ...


class YouTubeObservationBlocked(RuntimeError):
    """Credential-free, provider-response-free failure safe for ordinary logs."""


class UnsupportedYouTubeMutation(RuntimeError):
    """The adapter intentionally has no YouTube mutation capability."""


class GoogleReadOnlyYouTubeClient:
    """Two YouTube Data API read methods and no mutation surface."""

    def _get(self, credentials: CredentialView, endpoint: str, params: dict[str, Any]) -> Any:
        try:
            from google.auth.transport.requests import AuthorizedSession

            response = AuthorizedSession(credentials).get(endpoint, params=params, timeout=30)
        except Exception as exc:
            raise YouTubeObservationBlocked("youtube_request_failed") from exc
        if response.status_code in {401, 403}:
            raise YouTubeObservationBlocked("authorization_unusable")
        if response.status_code != 200:
            raise YouTubeObservationBlocked("youtube_request_failed")
        try:
            payload = response.json()
        except ValueError as exc:
            raise YouTubeObservationBlocked("youtube_response_invalid") from exc
        if not isinstance(payload, dict):
            raise YouTubeObservationBlocked("youtube_response_invalid")
        return payload

    def authenticated_channel_ids(self, credentials: CredentialView) -> list[str]:
        from project_atlas.youtube_preflight import CHANNELS_ENDPOINT

        payload = self._get(
            credentials,
            CHANNELS_ENDPOINT,
            {"part": "id", "mine": "true", "maxResults": 50},
        )
        try:
            ids = [item["id"] for item in payload["items"]]
        except (KeyError, TypeError) as exc:
            raise YouTubeObservationBlocked("youtube_response_invalid") from exc
        if any(not isinstance(item, str) or not item for item in ids):
            raise YouTubeObservationBlocked("youtube_response_invalid")
        return ids

    def video_resource(self, credentials: CredentialView, remote_id: str) -> dict[str, Any] | None:
        payload = self._get(
            credentials,
            VIDEOS_ENDPOINT,
            {
                "part": "id,snippet,status,processingDetails,contentDetails",
                "id": remote_id,
                "maxResults": 1,
            },
        )
        items = payload.get("items")
        if not isinstance(items, list):
            raise YouTubeObservationBlocked("youtube_response_invalid")
        if not items:
            return None
        if len(items) != 1 or not isinstance(items[0], dict):
            raise YouTubeObservationBlocked("youtube_response_invalid")
        return items[0]


class YouTubeReadOnlyObservationAdapter:
    """Observe one exact private/manual-route object; all mutations fail closed."""

    def __init__(
        self,
        credential_provider: CredentialProvider,
        client: ReadOnlyYouTubeClient | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.credential_provider = credential_provider
        self.client = client or GoogleReadOnlyYouTubeClient()
        self.clock = clock or (lambda: datetime.now(UTC))

    @classmethod
    def from_client_config(
        cls,
        client_config: Path,
        repository_root: Path,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> YouTubeReadOnlyObservationAdapter:
        """Use the already-established native Windows refresh-token store."""

        provider = GoogleInstalledCredentialProvider(
            client_config,
            WindowsCredentialRefreshTokenStore(),
            repository_root,
        )
        return cls(provider, clock=clock)

    def _authorized(self) -> CredentialView:
        try:
            credentials = self.credential_provider.acquire()
            result = verify_exact_channel(credentials, self.client)
        except (PreflightBlocked, YouTubeObservationBlocked) as exc:
            category = getattr(exc, "category", str(exc))
            raise YouTubeObservationBlocked(category) from exc
        if result.status != "PASS":
            raise YouTubeObservationBlocked(result.error_category or "channel_verification_failed")
        if tuple(result.granted_scopes) != (YOUTUBE_READONLY_SCOPE,):
            raise YouTubeObservationBlocked("unexpected_scope_granted")
        return credentials

    def authenticated_channel(self) -> str:
        self._authorized()
        return EXPECTED_CHANNEL_ID

    @staticmethod
    def _processing(status: dict[str, Any], details: dict[str, Any]) -> str | None:
        processing = details.get("processingStatus")
        upload = status.get("uploadStatus")
        if processing == "succeeded" or upload == "processed":
            return "succeeded"
        if processing in {"failed", "terminated"} or upload in {"failed", "rejected", "deleted"}:
            return "failed"
        if processing in {"processing", "terminating"} or upload in {"uploaded", "processing"}:
            return "pending"
        return None

    @staticmethod
    def _metadata_checks(
        package: PublishingPackage,
        snippet: dict[str, Any],
        status: dict[str, Any],
        content: dict[str, Any],
    ) -> dict[str, bool]:
        manifest = package.manifest
        category = manifest.get("category") or {}
        audience = manifest.get("audience") or {}
        compliance = manifest.get("compliance") or {}
        synthetic = compliance.get("altered_or_synthetic_media") or {}
        declared_synthetic = bool(synthetic.get("declare_to_youtube"))
        made_for_kids = status.get("selfDeclaredMadeForKids", status.get("madeForKids", False))
        return {
            "title": snippet.get("title") == manifest.get("title"),
            "description": snippet.get("description") == manifest.get("description"),
            "tags": snippet.get("tags", []) == manifest.get("tags", []),
            "category": snippet.get("categoryId") == str(category.get("id")),
            "language": snippet.get("defaultLanguage") == manifest.get("language"),
            "audience": bool(made_for_kids) is bool(audience.get("made_for_kids")),
            "altered_or_synthetic_media": bool(status.get("containsSyntheticMedia", False))
            is declared_synthetic,
            "captions_present": content.get("caption") == "true",
            "custom_cover_present": content.get("hasCustomThumbnail") is True,
        }

    def observe_remote(
        self, remote_id: str, package: PublishingPackage | None = None
    ) -> RemoteObservation:
        if not isinstance(remote_id, str) or not remote_id.strip():
            raise YouTubeObservationBlocked("remote_video_id_invalid")
        credentials = self._authorized()
        item = self.client.video_resource(credentials, remote_id)
        if item is None:
            raise YouTubeObservationBlocked("remote_video_inaccessible")
        try:
            observed_id = item["id"]
            snippet = item["snippet"]
            status = item["status"]
            details = item.get("processingDetails", {})
            content = item.get("contentDetails", {})
            channel_id = snippet["channelId"]
            privacy = status["privacyStatus"]
        except (KeyError, TypeError) as exc:
            raise YouTubeObservationBlocked("youtube_response_invalid") from exc
        if observed_id != remote_id:
            raise YouTubeObservationBlocked("remote_video_identity_mismatch")
        if channel_id != EXPECTED_CHANNEL_ID:
            raise YouTubeObservationBlocked("remote_video_channel_mismatch")
        checks = self._metadata_checks(package, snippet, status, content) if package else None
        metadata_matches = all(checks.values()) if checks is not None else None
        upload_status = status.get("uploadStatus")
        processing_status = details.get("processingStatus")
        processing = self._processing(status, details)
        public_at = snippet.get("publishedAt") if privacy == "public" else None
        provider_payload = {
            "schema": ADAPTER_VERSION,
            "remote_id_matches": True,
            "channel_id_matches": True,
            "privacy": privacy,
            "upload_status": upload_status,
            "processing_status": processing_status,
            "metadata_checks": checks,
        }
        return RemoteObservation(
            remote_id,
            channel_id,
            privacy,
            processing,
            metadata_matches,
            upload_status in {"failed", "rejected", "deleted"},
            self.clock().replace(microsecond=0).isoformat(),
            public_at,
            provider_payload,
        )

    def begin_private_transfer(self, package: PublishingPackage, operation: PublicationOperation):
        raise UnsupportedYouTubeMutation("YouTube upload is unavailable in the read-only adapter.")

    def inspect_or_resume_transfer(self, operation: PublicationOperation):
        raise UnsupportedYouTubeMutation("YouTube upload is unavailable in the read-only adapter.")

    def request_public_transition(
        self, publication: PlatformPublication, operation: PublicationOperation
    ):
        raise UnsupportedYouTubeMutation(
            "YouTube public transition is unavailable in the read-only adapter."
        )

    def aggregate_performance(self, receipt: PublicationReceipt, checkpoint: str):
        raise UnsupportedYouTubeMutation(
            "YouTube analytics are unavailable in the read-only adapter."
        )
