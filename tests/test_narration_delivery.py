"""Provisional sentence-delivery scoring; pure, offline and provider-free."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from project_atlas import narration_delivery
from project_atlas.narration_delivery import (
    CLASSIFIER_VERSION,
    PROVISIONAL_TARGET_MS,
    assess_delivery,
    score_boundaries,
)

SCRIPT = "One two. Three four. Five six. Seven eight, nine ten. Eleven twelve."


def _words(script: str, gaps_ms: dict[int, int]) -> tuple[list[dict], list[tuple[float, float]]]:
    """Recognizer words 300 ms apart; a silence of gaps_ms[i] ms follows word i."""

    words, silences, clock = [], [], 0.0
    for index, word in enumerate(script.split()):
        words.append({"word": word.strip(".,"), "start": clock / 1000, "end": (clock + 300) / 1000})
        clock += 300
        if index in gaps_ms:
            silences.append((clock, clock + gaps_ms[index]))
            clock += gaps_ms[index]
    return words, silences


def test_sentence_and_internal_pauses_are_classified_against_script_punctuation() -> None:
    # Words 1, 3, 5 and 9 end sentences; word 7 ends a comma phrase.
    words, silences = _words(SCRIPT, {1: 500, 3: 400, 5: 450, 7: 200, 9: 600})
    report = assess_delivery(SCRIPT, words, silences)
    assert report["classifier_version"] == CLASSIFIER_VERSION
    assert report["alignment_reliable"] and report["aligned_token_fraction"] == 1.0
    assert [(b["boundary"], b["pause_ms"]) for b in report["sentence_boundaries"]] == [
        ("two. | Three", 500.0),
        ("four. | Five", 400.0),
        ("six. | Seven", 450.0),
        ("ten. | Eleven", 600.0),
    ]
    assert report["internal_pauses"] == [
        {"start_ms": 3750, "duration_ms": 200.0, "at": "eight, | nine", "kind": "phrase"}
    ]
    # Lowest max(3, ceil(4/4)) = 3 boundaries: (400 + 450 + 500) / 3.
    assert report["score_ms"] == 450.0 and report["outcome"] == "passed"


def test_a_missing_sentence_pause_scores_zero_and_falls_below_target() -> None:
    words, silences = _words(SCRIPT, {1: 500, 5: 300, 9: 600})
    report = assess_delivery(SCRIPT, words, silences)
    # "four. | Five" is timestamped on both sides but silent: a genuine 0 ms boundary.
    assert report["unresolved_sentence_boundaries"] == []
    assert [b["pause_ms"] for b in report["sentence_boundaries"]] == [500.0, 0.0, 300.0, 600.0]
    assert report["score_ms"] == round((0 + 300 + 500) / 3, 1)
    assert report["outcome"] == "below_target" and report["score_ms"] < PROVISIONAL_TARGET_MS


def test_unreliable_alignment_fails_closed_instead_of_guessing() -> None:
    _words_, silences = _words(SCRIPT, {1: 500, 3: 400, 5: 450, 9: 600})
    garbled = [{"word": "zzz", "start": i * 0.3, "end": i * 0.3 + 0.3} for i in range(12)]
    for words in ([], garbled):
        report = assess_delivery(SCRIPT, words, silences)
        assert report["outcome"] == "unreliable" and report["score_ms"] is None
        assert report["sentence_boundaries"] is None and report["internal_pauses"] is None
    # Silences far from any timestamped junction are reported, not assigned.
    words, _ = _words(SCRIPT, {1: 500, 3: 400, 5: 450, 9: 600})
    far = silences + [(90_000, 90_400), (95_000, 95_400)]
    report = assess_delivery(SCRIPT, words, far)
    assert report["outcome"] == "unreliable" and len(report["unclassified_silences"]) == 2


def test_scripts_with_too_few_sentences_are_not_applicable() -> None:
    words, silences = _words("One two. Three four. Five.", {1: 500, 3: 500})
    report = assess_delivery("One two. Three four. Five.", words, silences)
    assert report["outcome"] == "not_applicable" and report["score_ms"] is None


@pytest.mark.parametrize(
    ("pauses", "expected"),
    [
        ([500, 400, 300], 400.0),
        ([900, 100, 200, 300, 800], 200.0),
        ([float(v) for v in range(100, 1300, 100)], 200.0),
        ([float(v) for v in range(100, 1400, 100)], 250.0),
    ],
)
def test_score_is_the_mean_of_the_lowest_quarter_with_at_least_three(pauses, expected) -> None:
    assert score_boundaries(pauses) == expected


def test_policy_is_versioned_provisional_and_cites_its_calibration() -> None:
    assert narration_delivery.POLICY_ID == "similarstoic-sentence-delivery-v1"
    assert narration_delivery.POLICY_VERSION == 1
    assert PROVISIONAL_TARGET_MS == 358
    assert "fb4137108b09bba7c31bc0d9851c8e3ffb55408ae0f0d3f40b3215effd6d2478" in (
        narration_delivery.TARGET_EVIDENCE
    )
    assert narration_delivery.MODES == ("record_only", "prefer", "enforce")
    assert narration_delivery.IMPLEMENTED_MODES == ("record_only", "prefer")


LONG_SCRIPT = (
    "Alpha beta gamma delta epsilon. Zeta eta theta iota kappa. Lambda mu nu xi omicron. "
    "Pi rho sigma tau upsilon. Phi chi psi omega final."
)


def test_an_untimed_word_at_a_sentence_boundary_is_unreliable_not_a_zero_pause() -> None:
    gaps = {4: 450, 9: 450, 14: 450, 19: 450}
    words, silences = _words(LONG_SCRIPT, gaps)
    assert assess_delivery(LONG_SCRIPT, words, silences)["outcome"] == "passed"
    # The recognizer drops "Lambda", the word opening sentence three: 24 of 25 tokens align.
    missing = [item for item in words if item["word"] != "Lambda"]
    report = assess_delivery(LONG_SCRIPT, missing, silences)
    assert report["aligned_token_fraction"] == 0.96 >= narration_delivery.MIN_ALIGNED_FRACTION
    assert report["unresolved_sentence_boundaries"] == ["kappa. | Lambda"]
    assert report["outcome"] == "unreliable" and report["score_ms"] is None
    assert report["alignment_reliable"] is False and report["sentence_boundaries"] is None


def test_the_recorded_calibration_takes_reproduce_their_scores() -> None:
    fixture = json.loads(
        (Path(__file__).parent / "fixtures" / "sentence_delivery_calibration.json").read_text(
            encoding="utf-8"
        )
    )
    scores = {}
    for case in fixture["cases"]:
        report = assess_delivery(
            fixture["script"],
            case["words"],
            [tuple(item) for item in case["internal_silences_ms"]],
        )
        assert report["unresolved_sentence_boundaries"] == [], case["take"]
        assert [b["pause_ms"] for b in report["sentence_boundaries"]] == (
            case["expected_sentence_boundary_pauses_ms"]
        ), case["take"]
        scores[case["take"]] = (report["score_ms"], report["outcome"])
    assert scores == {
        "B1": (401.9, "passed"),
        "S1": (439.2, "passed"),
        "I2": (415.4, "passed"),
        "I3": (313.4, "below_target"),
        "I1": (310.1, "below_target"),
        "P10-R2 narration-1": (300.5, "below_target"),
        "S3": (218.0, "below_target"),
    }
