"""Approved brand narration configuration and isolated Inworld one-take adapter.

Resolution is offline. Execution requires separate founder spend authorization;
the explicit execution flag is a caller assertion, not a grant of authority.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import urllib.request
import wave
from dataclasses import dataclass
from hashlib import sha256

from project_atlas.media import NarrationSynthesis, NarrationSynthesisError

SIMILARSTOIC_INSTRUCTION = (
    "Speak like a relaxed, intelligent young adult explaining something useful to a friend. "
    "Conversational, grounded and lightly amused. Confident without selling. Let humour land "
    "through understatement, not performance. Use natural clause-level pauses and relaxed "
    "sentence endings. Never sound like an announcer, corporate presenter, finance guru, "
    "advertisement, podcast intro, or hyperactive social-media creator. "
    "Do not add, omit or paraphrase words."
)
SIMILARSTOIC_INSTRUCTION_SHA256 = "4334ac0e0cb2e5c0870a8ef7f0b1d5f40bf0afc8381b108d7916e7d1e6f3b5cb"
# The exact instruction of founder-preferred calibration take I2 (narration-tests/
# 2026-10-07-sentence-delivery): the v1 instruction plus one appended sentence-delivery brief.
SIMILARSTOIC_INSTRUCTION_V2 = (
    SIMILARSTOIC_INSTRUCTION
    + " Keep the delivery natural and conversational. Give each complete sentence a clear "
    "ending and a brief natural beat before beginning the next sentence. Do not rush sentence "
    "openings. Keep declarative sentence endings settled rather than using exaggerated rising "
    "or falling intonation."
)
SIMILARSTOIC_INSTRUCTION_V2_SHA256 = (
    "abd56573e2c068f147b84403c3322f42b16733a7e9d2a5f97643298256bff4cb"
)
SIMILARSTOIC_PRONUNCIATION_ALIASES = (("ISA", "eye-suh"),)


@dataclass(frozen=True)
class NarratorProfile:
    """One immutable, named narrator configuration a production request can freeze."""

    profile_id: str
    brand_key: str
    instruction: str
    instruction_sha256: str
    settings_sha256: str


# The single narrator authority. Profiles are append-only: a frozen request names one by
# id and settings digest, so changing a later profile never alters an earlier request.
NARRATOR_PROFILES = {
    profile.profile_id: profile
    for profile in (
        NarratorProfile(
            "similarstoic-daniel-v1",
            "similarstoic",
            SIMILARSTOIC_INSTRUCTION,
            SIMILARSTOIC_INSTRUCTION_SHA256,
            "9c8e560b2a761df11b107db96ce92b989137cb6b55117f7465dcbe4361750f2e",
        ),
        NarratorProfile(
            "similarstoic-daniel-v2",
            "similarstoic",
            SIMILARSTOIC_INSTRUCTION_V2,
            SIMILARSTOIC_INSTRUCTION_V2_SHA256,
            "8e06b555cc23e8b653dae76cf95b04f74e43e0ac2282f7be900775f286d27c24",
        ),
    )
}
# Requests that freeze no narrator keep the historical behaviour they were frozen under.
LEGACY_NARRATOR_PROFILE_ID = "similarstoic-daniel-v1"
CURRENT_NARRATOR_PROFILE_ID = "similarstoic-daniel-v2"


def settings_sha256(settings: dict) -> str:
    """Digest of one narrator's canonical settings JSON."""

    return sha256(
        json.dumps(settings, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def narrator_profile(profile_id: str) -> NarratorProfile:
    """Resolve one registered profile whose instruction and settings still match their pins."""

    profile = NARRATOR_PROFILES.get(profile_id)
    if profile is None:
        raise ValueError(f"Unknown narrator profile {profile_id!r}.")
    if sha256(profile.instruction.encode()).hexdigest() != profile.instruction_sha256:
        raise ValueError(f"Narrator profile {profile_id!r} instruction hash mismatch.")
    if settings_sha256(InworldNarrationSynthesizer(profile=profile).settings) != (
        profile.settings_sha256
    ):
        raise ValueError(f"Narrator profile {profile_id!r} settings hash mismatch.")
    return profile


def apply_pronunciation_aliases(
    text: str,
    aliases: tuple[tuple[str, str], ...] = SIMILARSTOIC_PRONUNCIATION_ALIASES,
) -> str:
    """Return provider-facing speech text without changing the editorial Script."""

    spoken = text
    for written, pronunciation in sorted(aliases, key=lambda item: len(item[0]), reverse=True):
        if not written or not pronunciation or any(character.isspace() for character in written):
            raise ValueError("Pronunciation aliases require one written token and spoken text.")
        spoken = re.sub(
            rf"(?<![\w]){re.escape(written)}(?![\w])",
            lambda _match, replacement=pronunciation: replacement,
            spoken,
        )
    return spoken


class InworldNarrationSynthesizer:
    """Exact approved Daniel configuration; no fallback, retry or hidden processing."""

    engine_kind = "inworld_tts"
    engine_identity = "Inworld:inworld-tts-2"
    voice_identity = "Daniel"
    locale = "en-US"

    def __init__(
        self, *, execution_authorized: bool = False, profile: NarratorProfile | None = None
    ) -> None:
        self.execution_authorized = execution_authorized
        self.profile = profile or NARRATOR_PROFILES[LEGACY_NARRATOR_PROFILE_ID]

    @property
    def settings(self) -> dict:
        return {
            "voiceId": self.voice_identity,
            "modelId": "inworld-tts-2",
            "audioConfig": {
                "audioEncoding": "WAV",
                "sampleRateHertz": 48000,
                "speakingRate": 1.0,
            },
            "language": self.locale,
            "deliveryMode": "BALANCED",
            "instruction": self.profile.instruction,
            "timestampType": "WORD",
            "applyTextNormalization": "ON",
            "enhanceGeneration": False,
            "pronunciationAliases": [
                {"written": written, "spoken": spoken}
                for written, spoken in SIMILARSTOIC_PRONUNCIATION_ALIASES
            ],
        }

    @property
    def provider_settings(self) -> dict:
        """Return only fields accepted by Inworld; aliases are applied to ``text``."""

        settings = self.settings
        settings.pop("pronunciationAliases")
        return settings

    def synthesize(self, text: str) -> NarrationSynthesis:
        if not self.execution_authorized:
            raise NarrationSynthesisError("Separate narration spend authorization is required.")
        if not text.strip():
            raise NarrationSynthesisError("Narration text must not be empty.")
        if sha256(self.profile.instruction.encode()).hexdigest() != (
            self.profile.instruction_sha256
        ):
            raise NarrationSynthesisError("Approved instruction hash mismatch.")
        credential = os.environ.get("INWORLD_API_KEY", "")
        if not credential:
            raise NarrationSynthesisError("INWORLD_API_KEY is required; no provider fallback.")
        spoken_text = apply_pronunciation_aliases(text)
        request = urllib.request.Request(
            "https://api.inworld.ai/tts/v1/voice",
            json.dumps({"text": spoken_text, **self.provider_settings}, ensure_ascii=False).encode(
                "utf-8"
            ),
            {"Authorization": f"Basic {credential}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read())
            content = base64.b64decode(result["audioContent"], validate=True)
            with wave.open(io.BytesIO(content)) as audio:
                if audio.getframerate() != 48000 or audio.getnchannels() != 1:
                    raise ValueError("Unexpected audio format")
                if audio.getnframes() <= 0:
                    raise ValueError("Empty audio")
        except Exception:
            # Never persist provider bodies, authorization headers or transport exceptions.
            raise NarrationSynthesisError("Inworld synthesis failed; no automatic retry.") from None
        return NarrationSynthesis(
            content,
            "audio/wav",
            self.engine_kind,
            self.engine_identity,
            self.voice_identity,
            self.locale,
            self.settings,
        )


def resolve_narrator(
    brand_key: str, *, execution_authorized: bool = False, profile_id: str | None = None
):
    """Resolve only an explicit approved brand; unknown brands cannot silently inherit it.

    Without a frozen profile the brand resolves to its historical (v1) narrator.
    """
    if brand_key != "similarstoic":
        raise ValueError("No approved narrator configured for this brand.")
    profile = narrator_profile(profile_id or LEGACY_NARRATOR_PROFILE_ID)
    if profile.brand_key != brand_key:
        raise ValueError("The narrator profile belongs to a different brand.")
    return InworldNarrationSynthesizer(execution_authorized=execution_authorized, profile=profile)
