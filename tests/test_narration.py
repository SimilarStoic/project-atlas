"""Offline Daniel configuration and additive migration proof; no live provider access."""

import base64
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
    SIMILARSTOIC_INSTRUCTION_SHA256,
    resolve_narrator,
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
        repo.apply_migrations(((26, MIGRATIONS[-1][1] + ("INVALID SQL",)),))
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
    assert repo.connection.execute("SELECT max(version) FROM schema_migrations").fetchone()[0] == 27
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
    text = "Exact approved text.\nDon't paraphrase."
    monkeypatch.setenv("INWORLD_API_KEY", "fixture-secret")

    def respond(request, **kwargs):
        calls.append(request)
        assert request.full_url == "https://api.inworld.ai/tts/v1/voice"
        assert request.get_header("Authorization") == "Basic fixture-secret"
        assert json.loads(request.data) == {"text": text, **engine.settings}
        return io.BytesIO(
            json.dumps({"audioContent": base64.b64encode(audio.getvalue()).decode()}).encode()
        )

    monkeypatch.setattr("urllib.request.urlopen", respond)
    result = engine.synthesize(text)
    assert result.engine_kind == "inworld_tts"
    assert result.content == audio.getvalue()
    assert "fixture-secret" not in repr(result)
    assert len(calls) == 1


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
