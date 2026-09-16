"""Network-free tests for the manual-route YouTube observation adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from project_atlas.publishing_state import TARGET_CHANNEL, PublishingPackage
from project_atlas.youtube_adapter import (
    UnsupportedYouTubeMutation,
    YouTubeObservationBlocked,
    YouTubeReadOnlyObservationAdapter,
)
from project_atlas.youtube_preflight import YOUTUBE_READONLY_SCOPE


@dataclass
class Credentials:
    valid: bool = True
    expired: bool = False
    scopes: tuple[str, ...] = (YOUTUBE_READONLY_SCOPE,)
    granted_scopes: tuple[str, ...] = (YOUTUBE_READONLY_SCOPE,)
    refresh_token: str | None = None


class Provider:
    def __init__(self, credentials: Credentials | None = None) -> None:
        self.credentials = credentials or Credentials()

    def acquire(self):
        return self.credentials


class Client:
    def __init__(self) -> None:
        self.channels = [TARGET_CHANNEL]
        self.resource = {
            "id": "remote-1",
            "snippet": {
                "channelId": TARGET_CHANNEL,
                "title": "AI's Hidden Bottleneck Is the Power Grid",
                "description": "Exact description",
                "tags": ["AI infrastructure", "data centres", "power grid"],
                "categoryId": "27",
                "defaultLanguage": "en-GB",
            },
            "status": {
                "privacyStatus": "private",
                "uploadStatus": "processed",
                "selfDeclaredMadeForKids": False,
                "containsSyntheticMedia": False,
            },
            "processingDetails": {"processingStatus": "succeeded"},
            "contentDetails": {"caption": "true", "hasCustomThumbnail": True},
            "authorization": "must-not-survive",
        }

    def authenticated_channel_ids(self, credentials):
        return self.channels

    def video_resource(self, credentials, remote_id):
        return self.resource


def package() -> PublishingPackage:
    manifest = {
        "title": "AI's Hidden Bottleneck Is the Power Grid",
        "description": "Exact description",
        "tags": ["AI infrastructure", "data centres", "power grid"],
        "language": "en-GB",
        "category": {"id": "27", "name": "Education"},
        "audience": {"made_for_kids": False},
        "compliance": {
            "altered_or_synthetic_media": {"declare_to_youtube": False},
        },
    }
    return PublishingPackage(
        "package-1",
        "pilot",
        1,
        1,
        None,
        "artifact-1",
        "a" * 64,
        "youtube",
        TARGET_CHANNEL,
        "2026-W39",
        manifest,
        "b" * 64,
        "2026-09-16T00:00:00+00:00",
    )


def test_exact_channel_and_private_observation_are_sanitized():
    client = Client()
    adapter = YouTubeReadOnlyObservationAdapter(
        Provider(), client, lambda: datetime(2026, 9, 16, tzinfo=UTC)
    )
    assert adapter.authenticated_channel() == TARGET_CHANNEL
    observed = adapter.observe_remote("remote-1", package())
    assert observed.privacy == "private"
    assert observed.processing == "succeeded"
    assert observed.metadata_matches is True
    evidence = repr(observed.provider_payload)
    assert "must-not-survive" not in evidence
    assert "authorization" not in evidence.lower()


@pytest.mark.parametrize(
    ("channels", "resource", "category"),
    [
        (["wrong-channel"], None, "authenticated_channel_mismatch"),
        ([TARGET_CHANNEL], None, "remote_video_inaccessible"),
    ],
)
def test_wrong_channel_and_inaccessible_video_fail_closed(channels, resource, category):
    client = Client()
    client.channels = channels
    client.resource = resource
    adapter = YouTubeReadOnlyObservationAdapter(Provider(), client)
    with pytest.raises(YouTubeObservationBlocked, match=category):
        adapter.observe_remote("remote-1", package())


def test_remote_wrong_channel_and_metadata_mismatch_fail_closed():
    client = Client()
    client.resource["snippet"]["channelId"] = "wrong-channel"
    adapter = YouTubeReadOnlyObservationAdapter(Provider(), client)
    with pytest.raises(YouTubeObservationBlocked, match="remote_video_channel_mismatch"):
        adapter.observe_remote("remote-1", package())

    client = Client()
    client.resource["snippet"]["title"] = "Wrong title"
    observed = YouTubeReadOnlyObservationAdapter(Provider(), client).observe_remote(
        "remote-1", package()
    )
    assert observed.metadata_matches is False
    assert observed.provider_payload["metadata_checks"]["title"] is False


def test_scope_is_exact_and_mutations_are_unavailable():
    credentials = Credentials(
        scopes=(YOUTUBE_READONLY_SCOPE, "https://www.googleapis.com/auth/youtube.upload"),
        granted_scopes=(YOUTUBE_READONLY_SCOPE, "https://www.googleapis.com/auth/youtube.upload"),
    )
    adapter = YouTubeReadOnlyObservationAdapter(Provider(credentials), Client())
    with pytest.raises(YouTubeObservationBlocked, match="unexpected_scope_granted"):
        adapter.authenticated_channel()

    adapter = YouTubeReadOnlyObservationAdapter(Provider(), Client())
    for call in (
        lambda: adapter.begin_private_transfer(package(), SimpleNamespace()),
        lambda: adapter.inspect_or_resume_transfer(SimpleNamespace()),
        lambda: adapter.request_public_transition(SimpleNamespace(), SimpleNamespace()),
        lambda: adapter.aggregate_performance(SimpleNamespace(), "24h"),
    ):
        with pytest.raises(UnsupportedYouTubeMutation):
            call()
