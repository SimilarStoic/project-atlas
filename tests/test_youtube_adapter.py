"""Network-free tests for the manual-route YouTube observation adapter."""

from __future__ import annotations

from dataclasses import dataclass, replace
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
                "defaultAudioLanguage": "en-GB",
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
    assert "defaultLanguage" not in client.resource["snippet"]
    assert observed.provider_payload["metadata_checks"]["language"] is True
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


def test_wrong_or_missing_default_audio_language_does_not_fall_back():
    client = Client()
    client.resource["snippet"]["defaultLanguage"] = "en-GB"
    client.resource["snippet"]["defaultAudioLanguage"] = "fr-FR"
    adapter = YouTubeReadOnlyObservationAdapter(Provider(), client)
    observed = adapter.observe_remote("remote-1", package())
    assert observed.provider_payload["metadata_checks"]["language"] is False
    assert observed.metadata_matches is False

    del client.resource["snippet"]["defaultAudioLanguage"]
    observed = adapter.observe_remote("remote-1", package())
    assert observed.provider_payload["metadata_checks"]["language"] is False
    assert observed.metadata_matches is False


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


# --- Caption / cover declarations ------------------------------------------------------------


def _declared(caption=None, cover=None) -> PublishingPackage:
    base = package()
    manifest = dict(base.manifest)
    if caption is not None:
        manifest["caption_artifact"] = caption
    if cover is not None:
        manifest["cover_choice"] = cover
    return replace(base, manifest=manifest)


def _observe(target, **content):
    client = Client()
    client.resource["contentDetails"] = {"caption": "true", "hasCustomThumbnail": True, **content}
    return YouTubeReadOnlyObservationAdapter(Provider(), client).observe_remote("remote-1", target)


def test_burned_in_captions_skip_only_the_caption_track_check():
    target = _declared(caption={"kind": "burned_in"})
    observed = _observe(target, caption="false")
    checks = observed.provider_payload["metadata_checks"]
    assert "captions_present" not in checks and checks["custom_cover_present"] is True
    assert observed.metadata_matches is True
    # The custom-cover requirement is unchanged for this package.
    assert _observe(target, caption="false", hasCustomThumbnail=False).metadata_matches is False


def test_platform_default_cover_skips_only_the_custom_thumbnail_check():
    target = _declared(cover={"kind": "platform_default"})
    observed = _observe(target, hasCustomThumbnail=False)
    checks = observed.provider_payload["metadata_checks"]
    assert "custom_cover_present" not in checks and checks["captions_present"] is True
    assert observed.metadata_matches is True
    assert _observe(target, caption="false", hasCustomThumbnail=False).metadata_matches is False


def test_declarations_leave_every_other_verification_active():
    target = _declared(caption={"kind": "burned_in"}, cover={"kind": "platform_default"})
    clean = _observe(target, caption="false", hasCustomThumbnail=False)
    assert clean.metadata_matches is True
    assert set(clean.provider_payload["metadata_checks"]) == {
        "title",
        "description",
        "tags",
        "category",
        "language",
        "audience",
        "altered_or_synthetic_media",
    }
    for field, value in (("title", "Other"), ("description", "Other"), ("tags", ["x"])):
        client = Client()
        client.resource["snippet"][field] = value
        observed = YouTubeReadOnlyObservationAdapter(Provider(), client).observe_remote(
            "remote-1", target
        )
        assert observed.metadata_matches is False
    wrong_channel = Client()
    wrong_channel.resource["snippet"]["channelId"] = "UC-other"
    with pytest.raises(YouTubeObservationBlocked, match="remote_video_channel_mismatch"):
        YouTubeReadOnlyObservationAdapter(Provider(), wrong_channel).observe_remote(
            "remote-1", target
        )


def test_tags_match_regardless_of_youtube_order_but_stay_exact():
    target = _declared(caption={"kind": "burned_in"}, cover={"kind": "platform_default"})
    expected = target.manifest["tags"]
    for tags, matches in (
        (sorted(expected, reverse=True), True),
        (list(reversed(expected)), True),
        ([tag.upper() for tag in expected], False),
        ([f" {expected[0]}", *expected[1:]], False),
        (expected[:-1], False),
        ([*expected, expected[0]], False),
        ([], False),
    ):
        client = Client()
        client.resource["snippet"]["tags"] = tags
        observed = YouTubeReadOnlyObservationAdapter(Provider(), client).observe_remote(
            "remote-1", target
        )
        assert observed.provider_payload["metadata_checks"]["tags"] is matches, tags
        assert observed.metadata_matches is matches, tags


def test_asset_backed_caption_and_cover_packages_keep_both_checks():
    asset_backed = _declared(
        caption={"format": "srt", "path": "captions.srt", "sha256": "c" * 64},
        cover={"kind": "fallback_frame", "path": "cover.png", "sha256": "d" * 64},
    )
    for content, expected in (
        ({}, True),
        ({"caption": "false"}, False),
        ({"hasCustomThumbnail": False}, False),
    ):
        observed = _observe(asset_backed, **content)
        assert {"captions_present", "custom_cover_present"} <= set(
            observed.provider_payload["metadata_checks"]
        )
        assert observed.metadata_matches is expected
