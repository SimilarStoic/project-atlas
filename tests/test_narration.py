"""Offline Daniel configuration and additive migration proof; no live provider access."""

import base64
import dataclasses
import io
import json
import sqlite3
import wave
from hashlib import sha256
from types import SimpleNamespace

import pytest

from project_atlas import persistence
from project_atlas.media import (
    LocalMediaStorage,
    MediaService,
    NarrationSynthesis,
    NarrationSynthesisError,
)
from project_atlas.narration import (
    CURRENT_NARRATOR_PROFILE_ID,
    LEGACY_NARRATOR_PROFILE_ID,
    NARRATOR_PROFILES,
    SIMILARSTOIC_INSTRUCTION,
    SIMILARSTOIC_INSTRUCTION_SHA256,
    SIMILARSTOIC_INSTRUCTION_V2,
    SIMILARSTOIC_PRONUNCIATION_ALIASES,
    apply_pronunciation_aliases,
    narrator_profile,
    resolve_narrator,
    settings_sha256,
)
from project_atlas.persistence import MIGRATIONS, AtlasRepository


def record(repo, identity, provider):
    return repo.record_failed_narration_generation(
        identity,
        "script-isa-deadline-video-v1",
        provider,
        "fixture",
        "fixture",
        "en-US",
        {},
        "Fixture",
        "offline fixture",
        "2026-09-22T00:00:00Z",
        "2026-09-22T00:00:01Z",
    )


def test_migration_26_upgrade_preserves_history_and_constraints(tmp_path, monkeypatch):
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS[:25])
    repo = AtlasRepository(tmp_path / "upgrade.db")
    for provider in ("local_system_speech", "openai_tts"):
        record(repo, provider, provider)
    repo.record_successful_generated_narration(
        "historical-success",
        "historical-audio",
        "script-isa-deadline-video-v1",
        "fixture.wav",
        "audio/wav",
        "a" * 64,
        1000,
        "openai_tts",
        "fixture",
        "marin",
        "en-GB",
        {},
        "2026-09-22T00:00:00Z",
        "2026-09-22T00:00:01Z",
    )
    before = repo.connection.execute("SELECT * FROM narration_generation_executions").fetchall()
    before = [tuple(row) for row in before]
    monkeypatch.setattr(persistence, "MIGRATIONS", MIGRATIONS)
    with pytest.raises(sqlite3.DatabaseError):
        repo.apply_migrations(((26, MIGRATIONS[25][1] + ("INVALID SQL",)),))
    assert repo.connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert repo.connection.execute("SELECT max(version) FROM schema_migrations").fetchone()[0] == 25
    assert [
        tuple(r) for r in repo.connection.execute("SELECT * FROM narration_generation_executions")
    ] == before
    repo.apply_migrations()
    assert [
        tuple(r) for r in repo.connection.execute("SELECT * FROM narration_generation_executions")
    ] == before
    for provider in persistence.NARRATION_GENERATION_ENGINE_KINDS:
        assert record(repo, "new-" + provider, provider).engine_kind == provider
    with pytest.raises(ValueError):
        record(repo, "invalid", "bogus")
    with pytest.raises(sqlite3.IntegrityError):
        repo.connection.execute("UPDATE narration_generation_executions SET engine_kind = 'bogus'")
    repo.connection.rollback()
    repo.apply_migrations()
    assert repo.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert repo.connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert repo.get_narration_asset("historical-audio").content_digest == "a" * 64
    assert repo.connection.execute("SELECT max(version) FROM schema_migrations").fetchone()[0] == 29
    repo.close()


def test_fresh_schema_and_execution_guard(tmp_path):
    repo = AtlasRepository(tmp_path / "fresh.db")
    assert record(repo, "inworld", "inworld_tts").engine_kind == "inworld_tts"
    service = MediaService.__new__(MediaService)
    service.repository = repo
    with pytest.raises(NarrationSynthesisError, match="authorization"):
        service.generate_brand_narration("x", "y", "z", brand_key="similarstoic")
    repo.connection.execute("DELETE FROM schema_migrations WHERE version = 26")
    with pytest.raises(NarrationSynthesisError, match="Migration 26"):
        service.generate_brand_narration(
            "x", "y", "z", brand_key="similarstoic", execution_authorized=True
        )
    repo.close()


def test_daniel_offline_configuration_and_no_fallback(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Resolution or unauthorized execution must not call providers")

    monkeypatch.setattr("urllib.request.urlopen", forbidden)
    engine = resolve_narrator("similarstoic")
    assert (engine.engine_kind, engine.voice_identity, engine.locale) == (
        "inworld_tts",
        "Daniel",
        "en-US",
    )
    settings = engine.settings
    assert settings["modelId"] == "inworld-tts-2"
    assert settings["deliveryMode"] == "BALANCED"
    assert settings["audioConfig"] == {
        "audioEncoding": "WAV",
        "sampleRateHertz": 48000,
        "speakingRate": 1.0,
    }
    assert settings["timestampType"] == "WORD"
    assert settings["applyTextNormalization"] == "ON"
    assert settings["enhanceGeneration"] is False
    assert settings["pronunciationAliases"] == [{"written": "ISA", "spoken": "eye-suh"}]
    assert sha256(settings["instruction"].encode()).hexdigest() == SIMILARSTOIC_INSTRUCTION_SHA256
    settings["audioConfig"]["speakingRate"] = 2
    assert engine.settings["audioConfig"]["speakingRate"] == 1.0
    with pytest.raises(NarrationSynthesisError, match="authorization"):
        engine.synthesize("Text")
    monkeypatch.delenv("INWORLD_API_KEY", raising=False)
    with pytest.raises(NarrationSynthesisError, match="no provider fallback"):
        resolve_narrator("similarstoic", execution_authorized=True).synthesize("Text")
    with pytest.raises(ValueError):
        resolve_narrator("another-brand")


def test_exact_request_and_truthful_output(monkeypatch):
    audio = io.BytesIO()
    with wave.open(audio, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(48000)
        wav.writeframes(b"\0\0" * 100)
    engine = resolve_narrator("similarstoic", execution_authorized=True)
    calls = []
    text = "An ISA keeps the exact approved text.\nDon't paraphrase."
    monkeypatch.setenv("INWORLD_API_KEY", "fixture-secret")

    def respond(request, **kwargs):
        calls.append(request)
        assert request.full_url == "https://api.inworld.ai/tts/v1/voice"
        assert request.get_header("Authorization") == "Basic fixture-secret"
        assert json.loads(request.data) == {
            "text": "An eye-suh keeps the exact approved text.\nDon't paraphrase.",
            **engine.provider_settings,
        }
        return io.BytesIO(
            json.dumps({"audioContent": base64.b64encode(audio.getvalue()).decode()}).encode()
        )

    monkeypatch.setattr("urllib.request.urlopen", respond)
    result = engine.synthesize(text)
    assert result.engine_kind == "inworld_tts"
    assert result.content == audio.getvalue()
    assert result.settings["pronunciationAliases"] == [{"written": "ISA", "spoken": "eye-suh"}]
    assert text == "An ISA keeps the exact approved text.\nDon't paraphrase."
    assert "fixture-secret" not in repr(result)
    assert len(calls) == 1


def test_pronunciation_alias_is_token_bound_and_does_not_rewrite_editorial_text() -> None:
    editorial = "ISA guidance differs from ISAs and MISALIGNED labels."

    spoken = apply_pronunciation_aliases(editorial)

    assert SIMILARSTOIC_PRONUNCIATION_ALIASES == (("ISA", "eye-suh"),)
    assert spoken == "eye-suh guidance differs from ISAs and MISALIGNED labels."
    assert editorial == "ISA guidance differs from ISAs and MISALIGNED labels."


def test_multiple_pronunciation_aliases_use_their_own_replacements() -> None:
    spoken = apply_pronunciation_aliases(
        "ISA meets APR.",
        (("ISA", "eye-suh"), ("APR", "A-P-R")),
    )

    assert spoken == "eye-suh meets A-P-R."


def test_failure_is_sanitized_and_not_retried(monkeypatch):
    monkeypatch.setenv("INWORLD_API_KEY", "fixture-secret")
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise OSError("fixture-secret provider body")

    monkeypatch.setattr("urllib.request.urlopen", fail)
    with pytest.raises(NarrationSynthesisError) as error:
        resolve_narrator("similarstoic", execution_authorized=True).synthesize("Text")
    assert "fixture-secret" not in str(error.value)
    assert calls == [1]


def test_brand_service_persists_inworld_without_changing_script(tmp_path, monkeypatch):
    repo = AtlasRepository(tmp_path / "service.db")
    script = repo.get_script("script-isa-deadline-video-v1")
    calls = []

    def synthesize(engine, text):
        assert engine.execution_authorized
        assert text == script.narration_text
        calls.append(text)
        return NarrationSynthesis(
            b"offline fixture",
            "audio/wav",
            engine.engine_kind,
            engine.engine_identity,
            engine.voice_identity,
            engine.locale,
            engine.settings,
        )

    monkeypatch.setattr(
        "project_atlas.narration.InworldNarrationSynthesizer.synthesize", synthesize
    )
    runtime = SimpleNamespace(
        probe=lambda path: SimpleNamespace(media_type="audio", duration_ms=1000),
        assert_audible=lambda path: None,
    )
    service = MediaService(repo, runtime, LocalMediaStorage(tmp_path / "media"))
    result = service.generate_brand_narration(
        "daniel-execution",
        "daniel-asset",
        script.id,
        brand_key="similarstoic",
        execution_authorized=True,
    )
    assert result.narration_asset is not None
    assert result.execution.engine_kind == "inworld_tts"
    assert result.execution.voice_identity == "Daniel"
    assert result.execution.settings == resolve_narrator("similarstoic").settings
    assert repo.get_script(script.id) == script
    assert calls == [script.narration_text]
    assert repo.connection.execute("PRAGMA foreign_key_check").fetchall() == []
    repo.close()


# --- Versioned narrator profiles ---------------------------------------------------------------

V2_ADDITION = (
    "Keep the delivery natural and conversational. Give each complete sentence a clear ending "
    "and a brief natural beat before beginning the next sentence. Do not rush sentence openings. "
    "Keep declarative sentence endings settled rather than using exaggerated rising or falling "
    "intonation."
)


def test_profiles_pin_the_historical_and_the_calibrated_daniel_exactly():
    v1, v2 = narrator_profile("similarstoic-daniel-v1"), narrator_profile("similarstoic-daniel-v2")
    assert v1.profile_id == LEGACY_NARRATOR_PROFILE_ID
    assert v2.profile_id == CURRENT_NARRATOR_PROFILE_ID
    assert v1.instruction == SIMILARSTOIC_INSTRUCTION
    assert sha256(v1.instruction.encode()).hexdigest() == (
        "4334ac0e0cb2e5c0870a8ef7f0b1d5f40bf0afc8381b108d7916e7d1e6f3b5cb"
    )
    # The exact instruction of founder-preferred calibration take I2, never reworded.
    assert v2.instruction == SIMILARSTOIC_INSTRUCTION + " " + V2_ADDITION
    assert sha256(v2.instruction.encode()).hexdigest() == (
        "abd56573e2c068f147b84403c3322f42b16733a7e9d2a5f97643298256bff4cb"
    )
    assert (v1.settings_sha256, v2.settings_sha256) == (
        "9c8e560b2a761df11b107db96ce92b989137cb6b55117f7465dcbe4361750f2e",
        "8e06b555cc23e8b653dae76cf95b04f74e43e0ac2282f7be900775f286d27c24",
    )
    s1 = resolve_narrator("similarstoic").settings
    s2 = resolve_narrator("similarstoic", profile_id="similarstoic-daniel-v2").settings
    assert settings_sha256(s1) == v1.settings_sha256 and settings_sha256(s2) == v2.settings_sha256
    # Only the instruction differs: model, voice, BALANCED, rate 1.0, audio and aliases are kept.
    assert {key for key in s1 if s1[key] != s2[key]} == {"instruction"} and set(s1) == set(s2)
    assert s2["deliveryMode"] == "BALANCED" and s2["audioConfig"]["speakingRate"] == 1.0


def test_unknown_or_tampered_profiles_never_resolve(monkeypatch):
    with pytest.raises(ValueError, match="Unknown narrator profile"):
        resolve_narrator("similarstoic", profile_id="similarstoic-daniel-v9")
    tampered = dataclasses.replace(
        NARRATOR_PROFILES["similarstoic-daniel-v2"], instruction="Read it like an announcer."
    )
    monkeypatch.setitem(NARRATOR_PROFILES, "similarstoic-daniel-v2", tampered)
    with pytest.raises(ValueError, match="instruction hash mismatch"):
        narrator_profile("similarstoic-daniel-v2")


def test_brand_service_synthesizes_with_the_frozen_profile(tmp_path, monkeypatch):
    repo = AtlasRepository(tmp_path / "profile.db")
    script = repo.get_script("script-isa-deadline-video-v1")
    used = []

    def synthesize(engine, text):
        used.append(engine.settings["instruction"])
        return NarrationSynthesis(
            b"offline fixture",
            "audio/wav",
            engine.engine_kind,
            engine.engine_identity,
            engine.voice_identity,
            engine.locale,
            engine.settings,
        )

    monkeypatch.setattr(
        "project_atlas.narration.InworldNarrationSynthesizer.synthesize", synthesize
    )
    runtime = SimpleNamespace(
        probe=lambda path: SimpleNamespace(media_type="audio", duration_ms=1000),
        assert_audible=lambda path: None,
    )
    service = MediaService(repo, runtime, LocalMediaStorage(tmp_path / "media"))
    result = service.generate_brand_narration(
        "daniel-v2-execution",
        "daniel-v2-asset",
        script.id,
        brand_key="similarstoic",
        execution_authorized=True,
        narrator_profile_id="similarstoic-daniel-v2",
    )
    assert used == [SIMILARSTOIC_INSTRUCTION_V2]
    assert settings_sha256(result.execution.settings) == (
        NARRATOR_PROFILES["similarstoic-daniel-v2"].settings_sha256
    )
    repo.close()
