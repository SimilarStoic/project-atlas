"""Approved brand narration configuration and isolated Inworld one-take adapter.

Resolution is offline. Execution requires separate founder spend authorization;
the explicit execution flag is a caller assertion, not a grant of authority.
"""

from __future__ import annotations

import base64
import io
import json
import os
import urllib.request
import wave
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


class InworldNarrationSynthesizer:
    """Exact approved Daniel configuration; no fallback, retry or hidden processing."""

    engine_kind = "inworld_tts"
    engine_identity = "Inworld:inworld-tts-2"
    voice_identity = "Daniel"
    locale = "en-US"

    def __init__(self, *, execution_authorized: bool = False) -> None:
        self.execution_authorized = execution_authorized

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
            "instruction": SIMILARSTOIC_INSTRUCTION,
            "timestampType": "WORD",
            "applyTextNormalization": "ON",
            "enhanceGeneration": False,
        }

    def synthesize(self, text: str) -> NarrationSynthesis:
        if not self.execution_authorized:
            raise NarrationSynthesisError("Separate narration spend authorization is required.")
        if not text.strip():
            raise NarrationSynthesisError("Narration text must not be empty.")
        if sha256(SIMILARSTOIC_INSTRUCTION.encode()).hexdigest() != SIMILARSTOIC_INSTRUCTION_SHA256:
            raise NarrationSynthesisError("Approved instruction hash mismatch.")
        credential = os.environ.get("INWORLD_API_KEY", "")
        if not credential:
            raise NarrationSynthesisError("INWORLD_API_KEY is required; no provider fallback.")
        request = urllib.request.Request(
            "https://api.inworld.ai/tts/v1/voice",
            json.dumps({"text": text, **self.settings}, ensure_ascii=False).encode("utf-8"),
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


def resolve_narrator(brand_key: str, *, execution_authorized: bool = False):
    """Resolve only an explicit approved brand; unknown brands cannot silently inherit it."""
    if brand_key != "similarstoic":
        raise ValueError("No approved narrator configured for this brand.")
    return InworldNarrationSynthesizer(execution_authorized=execution_authorized)
