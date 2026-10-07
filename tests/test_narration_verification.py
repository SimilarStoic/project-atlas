"""Narration completeness verification: normalization, strict reconciliation, transcriber."""

from __future__ import annotations

import io
import json
from hashlib import sha256

import pytest

from project_atlas import narration_verification as nv
from project_atlas.narration import SIMILARSTOIC_PRONUNCIATION_ALIASES
from project_atlas.narration_verification import (
    NORMALIZATION_VERSION,
    NarrationVerificationError,
    Transcription,
    WhisperTranscriber,
    normalize_tokens,
    number_words,
    verify_narration_audio,
    verify_transcript,
)

P10_SCRIPT = (
    "The energy price cap went up 4% on the first of October. But it isn't a cap on your bill. "
    "It limits the price of each unit of energy, and the standing charge. So the more you use, "
    "the more you pay. Ofgem puts a typical Direct Debit household at £1,723 a year — £60 more. "
    "It only covers default tariffs: around 20 million households, including prepayment. "
    "On a fixed deal? This price-cap change doesn't affect you. Ofgem says some fixed deals are "
    "£100 or more below the cap. And if you're struggling, talk to your supplier about an "
    "affordable payment plan."
)


def _kinds(report: dict) -> list[tuple[str, list[str], list[str]]]:
    return [(d["kind"], d["expected"], d["observed"]) for d in report["differences"]]


def test_exact_script_passes_with_full_recovery() -> None:
    report = verify_transcript(P10_SCRIPT, P10_SCRIPT)
    assert report["outcome"] == "passed"
    assert report["normalization_version"] == NORMALIZATION_VERSION
    assert report["recovered_token_count"] == report["expected_token_count"] > 100
    assert report["differences"] == []


@pytest.mark.parametrize(
    "script, heard",
    [
        ("went up 4% on", "went up four percent on"),
        ("went up 4% on", "went up 4 percent on"),
        ("went up 4% on", "went up 4 per cent on"),
        ("went up 4% on", "went up four per cent on"),
        ("at £1,723 a year", "at one thousand seven hundred and twenty-three pounds a year"),
        ("at £1,723 a year", "at 1,723 pounds a year"),
        ("at £1,723 a year", "at £1723 a year"),
        ("— £60 more.", ", 60 pounds more."),
        ("— £60 more.", "sixty pounds more"),
        ("are £100 or more", "are a hundred pounds or more"),
        ("are £100 or more", "are one hundred pounds or more"),
        ("are £100 or more", "are 100 pounds or more"),
        ("around 20 million households", "around twenty million households"),
        ("around 20 million households", "around 20,000,000 households"),
        ("by Direct Debit now", "by direct debit now"),
        ("by Direct Debit now", "by direct-debit now"),
        ("Ofgem says", "OFGEM says"),
        ("Ofgem says", "Of gem says"),
        ("the first of October", "the 1st of October"),
        ("it isn't a cap", "it is not a cap"),
        ("doesn't affect you", "does not affect you"),
        ("if you're struggling", "if you are struggling"),
        ("This price-cap change", "This price cap change"),
        ("including prepayment.", "including pre-payment."),
    ],
)
def test_equivalent_spoken_forms_pass(script: str, heard: str) -> None:
    report = verify_transcript(script, heard)
    assert report["outcome"] == "passed", _kinds(report)


@pytest.mark.parametrize(
    "script, heard, kind",
    [
        ("went up 4% on", "went up 14 percent on", "substitution"),
        ("at £1,723 a year", "at £1,732 a year", "substitution"),
        ("— £60 more.", "£16 more.", "substitution"),
        ("are £100 or more", "are £1,000 or more", "substitution"),
        ("around 20 million households", "around 20 households", "omission"),
        ("Ofgem says", "Ofjem says", "substitution"),
        ("by Direct Debit now", "by credit now", "substitution"),
    ],
)
def test_material_number_and_name_changes_fail(script: str, heard: str, kind: str) -> None:
    report = verify_transcript(script, heard)
    assert report["outcome"] == "failed"
    assert kind in {d["kind"] for d in report["differences"]}, _kinds(report)


def test_the_p10_duplicated_phrase_fails_as_a_repetition() -> None:
    heard = P10_SCRIPT.replace(
        "including prepayment.", "including prepayment, including prepayment."
    )
    report = verify_transcript(P10_SCRIPT, heard)
    assert report["outcome"] == "failed"
    assert _kinds(report) == [("repetition", [], ["including", "prepayment"])]


def test_omission_insertion_and_substitution_each_fail() -> None:
    omitted = verify_transcript(P10_SCRIPT, P10_SCRIPT.replace("the standing charge", "the charge"))
    assert _kinds(omitted) == [("omission", ["standing"], [])]
    inserted = verify_transcript(P10_SCRIPT, P10_SCRIPT.replace("a typical", "a very typical"))
    assert _kinds(inserted) == [("insertion", [], ["very"])]
    substituted = verify_transcript(P10_SCRIPT, P10_SCRIPT.replace("default", "standard"))
    assert _kinds(substituted) == [("substitution", ["default"], ["standard"])]
    for report in (omitted, inserted, substituted):
        assert report["outcome"] == "failed"
        assert report["differences"][0]["context"]


def test_approved_pronunciation_alias_accepts_written_or_spoken_form() -> None:
    script = "Open an ISA before April."
    aliases = SIMILARSTOIC_PRONUNCIATION_ALIASES
    for heard in (
        "Open an ISA before April.",
        "Open an eye-suh before April.",
        "open an eye suh before april",
    ):
        report = verify_transcript(script, heard, aliases)
        assert report["outcome"] == "passed", (heard, _kinds(report))
    spoken = verify_transcript(script, "Open an eye-suh before April.", aliases)
    assert spoken["alias_applications"] == [{"written": "ISA", "spoken": "eye-suh", "position": 2}]
    without_alias = verify_transcript(script, "Open an eye-suh before April.")
    assert without_alias["outcome"] == "failed"


def test_number_words_are_canonical() -> None:
    assert number_words(1723) == ["one", "thousand", "seven", "hundred", "twenty", "three"]
    assert number_words(20_000_000) == ["twenty", "million"]
    assert number_words(100) == ["one", "hundred"]
    assert normalize_tokens("£1 and £2.50") == [
        "one",
        "pound",
        "and",
        "two",
        "point",
        "five",
        "zero",
        "pounds",
    ]


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_whisper_transcriber_is_prompt_free_and_never_retries(monkeypatch, tmp_path) -> None:
    wav = tmp_path / "take.wav"
    wav.write_bytes(b"RIFF-test")
    seen = []

    def urlopen(request, timeout):
        seen.append(request)
        payload = {"text": "Hello there.", "words": [{"word": "Hello", "start": 0, "end": 0.4}]}
        return _FakeResponse(json.dumps(payload).encode())

    monkeypatch.setattr(nv.urllib.request, "urlopen", urlopen)
    result = WhisperTranscriber(api_key="test-key").transcribe(wav)
    assert result.text == "Hello there." and result.model == "whisper-1"
    body = seen[0].data
    assert b'name="model"\r\n\r\nwhisper-1' in body and b"prompt" not in body
    assert seen[0].full_url == nv.TRANSCRIPTION_ENDPOINT

    def failing(request, timeout):
        seen.append(request)
        raise OSError("network down: secret-ish detail")

    monkeypatch.setattr(nv.urllib.request, "urlopen", failing)
    with pytest.raises(NarrationVerificationError) as error:
        WhisperTranscriber(api_key="test-key").transcribe(wav)
    assert "no automatic retry" in str(error.value) and "secret" not in str(error.value)
    assert len(seen) == 2  # exactly one attempt per transcribe call

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(NarrationVerificationError, match="OPENAI_API_KEY"):
        WhisperTranscriber().transcribe(wav)
    assert len(seen) == 2


def test_audio_must_match_its_persisted_digest_before_transcription(tmp_path) -> None:
    wav = tmp_path / "take.wav"
    wav.write_bytes(b"audio")
    calls = []

    class Recorder:
        def transcribe(self, path):
            calls.append(path)
            return Transcription("Narration.", "OpenAI", "whisper-1")

    with pytest.raises(NarrationVerificationError, match="digest"):
        verify_narration_audio(wav, "0" * 64, "Narration.", Recorder())
    assert calls == []
    report = verify_narration_audio(wav, sha256(b"audio").hexdigest(), "Narration.", Recorder())
    assert report["outcome"] == "passed" and report["wav_sha256"] == sha256(b"audio").hexdigest()
    assert report["transcript"] == "Narration." and len(calls) == 1
