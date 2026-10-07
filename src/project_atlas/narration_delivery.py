"""Provisional SimilarStoic sentence-delivery scoring of one completeness-verified narration take.

The score reuses evidence the completeness gate already holds: the same ``whisper-1`` word
timestamps, the local FFmpeg silence detector and the canonical Script punctuation. It makes
no provider call. Each internal silence is assigned to the nearest timestamped Script word
junction and classified as a sentence-boundary or an internal (phrase / mid-phrase) pause.
Alignment that cannot support that classification is reported as unreliable, never guessed.

The rule and its target are provisional calibration, not a settled quality law: they were
fitted on seven takes of one Script (narration-tests/2026-10-07-sentence-delivery,
manifest SHA-256 fb4137108b09bba7c31bc0d9851c8e3ffb55408ae0f0d3f40b3215effd6d2478).
"""

from __future__ import annotations

import math
import statistics
from difflib import SequenceMatcher
from typing import Any

from project_atlas.narration_verification import normalize_tokens

CLASSIFIER_VERSION = "sentence-pause-classifier-v1"
POLICY_ID = "similarstoic-sentence-delivery-v1"
POLICY_VERSION = 1
SCORE_RULE = "mean of the lowest max(3, ceil(n/4)) sentence-boundary pauses"
# Midpoint between the founder-preferred calibration takes (>= 402 ms) and the others (<= 313 ms).
PROVISIONAL_TARGET_MS = 358
TARGET_EVIDENCE = (
    "narration-tests/2026-10-07-sentence-delivery/manifest.json "
    "(sha256 fb4137108b09bba7c31bc0d9851c8e3ffb55408ae0f0d3f40b3215effd6d2478)"
)
MODES = ("record_only", "prefer", "enforce")
# "enforce" is defined for a later policy decision but is not yet accepted by requests.
IMPLEMENTED_MODES = ("record_only", "prefer")
MAX_JUNCTION_DISTANCE_MS = 500
MIN_ALIGNED_FRACTION = 0.95
MAX_UNCLASSIFIED_SILENCES = 1
MIN_SENTENCE_BOUNDARIES = 3
_SENTENCE_END = (".", "?", "!")
_PHRASE_END = (",", ":", ";")


def _script_tokens(script: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Canonical tokens tagged with their Script word and the punctuation ending that word."""

    words = script.split()
    tokens = []
    for index, word in enumerate(words):
        parts = normalize_tokens(word)
        for position, token in enumerate(parts):
            mark = None
            if position == len(parts) - 1 and index < len(words) - 1:
                if word.endswith(_SENTENCE_END):
                    mark = "sentence"
                elif word.endswith(_PHRASE_END):
                    mark = "phrase"
                else:
                    mark = "word"
            tokens.append({"token": token, "word_index": index, "boundary_after": mark})
    if [item["token"] for item in tokens] != normalize_tokens(script):
        raise ValueError("Script word-level tokenization diverges from the canonical tokens.")
    return tokens, words


def _token_times(expected: list[dict[str, Any]], words: list[dict[str, Any]]) -> list[Any]:
    """Attach recognizer times to Script tokens through equal and pure re-tokenized blocks."""

    observed = [
        {"token": token, "start_ms": item["start"] * 1000, "end_ms": item["end"] * 1000}
        for item in words
        for token in normalize_tokens(item["word"])
    ]
    matcher = SequenceMatcher(
        None,
        [item["token"] for item in expected],
        [item["token"] for item in observed],
        autojunk=False,
    )
    times: list[Any] = [None] * len(expected)
    for tag, e1, e2, o1, o2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(e2 - e1):
                item = observed[o1 + offset]
                times[e1 + offset] = (item["start_ms"], item["end_ms"])
        elif tag == "replace" and "".join(i["token"] for i in expected[e1:e2]) == "".join(
            i["token"] for i in observed[o1:o2]
        ):
            span = (observed[o1]["start_ms"], observed[o2 - 1]["end_ms"])
            for index in range(e1, e2):
                times[index] = span
    return times


def score_boundaries(pauses_ms: list[float]) -> float:
    """Mean of the lowest max(3, ceil(n/4)) sentence-boundary pauses."""

    count = max(MIN_SENTENCE_BOUNDARIES, math.ceil(len(pauses_ms) / 4))
    return round(statistics.mean(sorted(pauses_ms)[:count]), 1)


def assess_delivery(
    script: str,
    words: list[dict[str, Any]],
    internal_silences: list[tuple[float, float]],
    target_ms: float = PROVISIONAL_TARGET_MS,
) -> dict[str, Any]:
    """Classify internal silences against Script punctuation and score sentence boundaries.

    Outcomes: ``passed`` (score at or above target), ``below_target``, ``unreliable``
    (alignment cannot support classification, including any sentence boundary whose
    neighbouring words lack timestamps) or ``not_applicable`` (too few sentences).
    """

    expected, script_words = _script_tokens(script)
    sentence_ends = [
        index for index, word in enumerate(script_words[:-1]) if word.endswith(_SENTENCE_END)
    ]
    times = _token_times(expected, list(words)) if words else [None] * len(expected)
    aligned = sum(item is not None for item in times) / len(times)
    junctions = []
    for index in range(len(expected) - 1):
        mark = expected[index]["boundary_after"]
        if mark is None or times[index] is None or times[index + 1] is None:
            continue
        word_index = expected[index]["word_index"]
        junctions.append(
            {
                "after_word_index": word_index,
                "kind": mark,
                "label": f"{script_words[word_index]} | {script_words[word_index + 1]}",
                "at_ms": (times[index][1] + times[index + 1][0]) / 2,
            }
        )
    # A sentence boundary is scored only when the words on both sides carry timestamps; an
    # unresolved boundary is never treated as a 0 ms pause.
    resolved = {j["after_word_index"] for j in junctions if j["kind"] == "sentence"}
    unresolved = [
        f"{script_words[index]} | {script_words[index + 1]}"
        for index in sentence_ends
        if index not in resolved
    ]
    boundary_ms = {index: 0.0 for index in sentence_ends}
    internal, unclassified = [], []
    for start, end in internal_silences:
        middle, duration = (start + end) / 2, round(end - start, 1)
        nearest = min(junctions, key=lambda j: abs(j["at_ms"] - middle)) if junctions else None
        if nearest is None or abs(nearest["at_ms"] - middle) > MAX_JUNCTION_DISTANCE_MS:
            unclassified.append({"start_ms": round(start), "duration_ms": duration})
        elif nearest["kind"] == "sentence":
            boundary_ms[nearest["after_word_index"]] += duration
        else:
            internal.append(
                {
                    "start_ms": round(start),
                    "duration_ms": duration,
                    "at": nearest["label"],
                    "kind": nearest["kind"],
                }
            )
    boundaries = [
        {
            "boundary": f"{script_words[index]} | {script_words[index + 1]}",
            "pause_ms": round(boundary_ms[index], 1),
        }
        for index in sentence_ends
    ]
    reliable = (
        bool(words)
        and aligned >= MIN_ALIGNED_FRACTION
        and len(unclassified) <= MAX_UNCLASSIFIED_SILENCES
        and not unresolved
    )
    if len(sentence_ends) < MIN_SENTENCE_BOUNDARIES:
        outcome, score = "not_applicable", None
    elif not reliable:
        outcome, score = "unreliable", None
    else:
        score = score_boundaries([item["pause_ms"] for item in boundaries])
        outcome = "passed" if score >= target_ms else "below_target"
    return {
        "classifier_version": CLASSIFIER_VERSION,
        "score_rule": SCORE_RULE,
        "target_ms": target_ms,
        "aligned_token_fraction": round(aligned, 3),
        "alignment_reliable": reliable,
        "unclassified_silences": unclassified,
        "unresolved_sentence_boundaries": unresolved,
        "sentence_boundaries": boundaries if reliable else None,
        "internal_pauses": internal if reliable else None,
        "score_ms": score,
        "outcome": outcome,
    }
