"""Pre-synthesis Script preflight evidence for the deterministic editorial readiness evaluator.

Every finding is advisory evidence for the human Editorial Gate: it never blocks readiness,
never rewrites the Script and never replaces editorial judgement. The Script and its frozen
ScriptClaimSet stay the only authorities; figures are recognised only through the existing
``narration_verification`` normalization, never a second number parser.
"""

from __future__ import annotations

import re
from typing import Any

from project_atlas.narration_verification import FIGURE_WORDS, normalize_tokens, spoken_figures

PREFLIGHT_VERSION = "script-preflight-v1"
# Content words within this many canonical tokens of a figure are its stated qualifier.
SCRIPT_QUALIFIER_WINDOW = 3
SOURCE_QUALIFIER_WINDOW = 8
REPETITION_MIN_WORDS = 3
# A repeated run is "nearby" within the same sentence or the next one.
REPETITION_SENTENCE_SPAN = 2
# Function words and comparatives (more/less) never state a figure's category.
STOPWORDS = frozenset(
    {
        "a",
        "about",
        "almost",
        "an",
        "and",
        "approximately",
        "are",
        "around",
        "as",
        "at",
        "be",
        "but",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "had",
        "has",
        "have",
        "he",
        "her",
        "his",
        "if",
        "in",
        "including",
        "is",
        "it",
        "its",
        "just",
        "less",
        "nearly",
        "more",
        "not",
        "of",
        "on",
        "only",
        "or",
        "our",
        "roughly",
        "she",
        "so",
        "some",
        "than",
        "that",
        "the",
        "their",
        "there",
        "these",
        "they",
        "this",
        "those",
        "to",
        "was",
        "we",
        "were",
        "which",
        "will",
        "with",
        "would",
        "you",
        "your",
    }
)
_SENTENCE_BREAK = re.compile(r"(?<=[.?!])\s+")


def sentences(text: str) -> list[str]:
    """Split Script text at sentence-final punctuation followed by whitespace."""

    return [part.strip() for part in _SENTENCE_BREAK.split(text.strip()) if part.strip()]


def finding(code: str, message: str, evidence: dict[str, Any], rule_version: str) -> dict:
    """One advisory finding: evidence for the Editorial Gate, never a readiness block."""

    return {
        "code": code,
        "severity": "warning",
        "blocking": False,
        "requires_editorial_judgement": True,
        "rule_version": rule_version,
        "message": message,
        "evidence": evidence,
    }


def _occurrences(tokens: list[str], run: list[str]) -> list[int]:
    width = len(run)
    return [
        index for index in range(len(tokens) - width + 1) if tokens[index : index + width] == run
    ]


def _qualifiers(tokens: list[str], start: int, end: int, window: int) -> set[str]:
    nearby = tokens[max(0, start - window) : start] + tokens[end : end + window]
    return {token for token in nearby if token not in STOPWORDS and token not in FIGURE_WORDS}


def _context(tokens: list[str], start: int, end: int, window: int) -> str:
    return " ".join(tokens[max(0, start - window) : end + window])


def _source_figures(claim_evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every figure occurrence in a verbatim frozen quote, with its qualifier window."""

    located = []
    for item in claim_evidence:
        reference = item.get("reference")
        if not isinstance(reference, str) or not reference.strip():
            continue
        tokens = normalize_tokens(reference)
        for figure in {tuple(value) for value in spoken_figures(reference)}:
            for start in _occurrences(tokens, list(figure)):
                end = start + len(figure)
                located.append(
                    {
                        "figure": figure,
                        "claim_id": item.get("claim_id"),
                        "source_id": item.get("source_id"),
                        "qualifiers": _qualifiers(tokens, start, end, SOURCE_QUALIFIER_WINDOW),
                        "context": _context(tokens, start, end, SOURCE_QUALIFIER_WINDOW),
                    }
                )
    return located


def number_findings(script_text: str, claim_set: dict[str, Any] | None) -> list[dict]:
    """Compare each Script figure's stated qualifier with the frozen verbatim source quotes.

    A mismatch is reported when a qualifier word stated beside the Script figure appears in
    the sources only beside a different figure (a crossed category), or when the Script and
    source qualifiers share no word at all. Whether it is a real error is editorial judgement.
    """

    claim_set = claim_set or {}
    claim_evidence = [
        item for item in claim_set.get("frozen_claim_evidence", []) if isinstance(item, dict)
    ]
    sourced_texts = [
        normalize_tokens(text)
        for text in [claim.get("text") for claim in claim_set.get("frozen_claims", [])]
        + [item.get("notes") for item in claim_evidence]
        if isinstance(text, str) and text.strip()
    ]
    source_figures = _source_figures(claim_evidence)
    findings, seen = [], set()
    for index, sentence in enumerate(sentences(script_text)):
        tokens = normalize_tokens(sentence)
        for figure in spoken_figures(sentence):
            key = (index, tuple(figure))
            if key in seen:
                continue
            seen.add(key)
            for start in _occurrences(tokens, figure):
                stated = _qualifiers(tokens, start, start + len(figure), SCRIPT_QUALIFIER_WINDOW)
                same = [item for item in source_figures if item["figure"] == tuple(figure)]
                base = {
                    "sentence_index": index,
                    "sentence": sentence,
                    "figure": " ".join(figure),
                    "script_qualifiers": sorted(stated),
                }
                if not same:
                    if any(_occurrences(text, figure) for text in sourced_texts):
                        findings.append(
                            finding(
                                "SOURCED_NUMBER_WITHOUT_QUOTE",
                                "A Script figure appears in the frozen Claims but in no verbatim "
                                "source quote, so its stated qualifier cannot be checked.",
                                base,
                                PREFLIGHT_VERSION,
                            )
                        )
                    else:
                        findings.append(
                            finding(
                                "SCRIPT_NUMBER_NOT_IN_FROZEN_EVIDENCE",
                                "A Script figure does not appear in the Script's frozen claim "
                                "evidence.",
                                base,
                                PREFLIGHT_VERSION,
                            )
                        )
                    continue
                source_words = set().union(*(item["qualifiers"] for item in same))
                missing = stated - source_words
                crossed = [
                    {
                        "qualifier": word,
                        "source_figure": " ".join(item["figure"]),
                        "claim_id": item["claim_id"],
                        "source_id": item["source_id"],
                        "source_context": item["context"],
                    }
                    for word in sorted(missing)
                    for item in source_figures
                    if item["figure"] != tuple(figure) and word in item["qualifiers"]
                ]
                if crossed or (stated and not stated & source_words):
                    findings.append(
                        finding(
                            "SCRIPT_NUMBER_QUALIFIER_MISMATCH",
                            "The qualifier stated beside a Script figure does not match the "
                            "frozen source quote for that figure.",
                            base
                            | {
                                "qualifiers_not_beside_figure_in_sources": sorted(missing),
                                "source_contexts": [
                                    {
                                        "claim_id": item["claim_id"],
                                        "source_id": item["source_id"],
                                        "context": item["context"],
                                    }
                                    for item in same
                                ],
                                "crossed_pairings": crossed,
                            },
                            PREFLIGHT_VERSION,
                        )
                    )
                break
    return findings


def repetition_findings(script_text: str) -> list[dict]:
    """Report each canonical run of three or more words repeated in nearby sentences."""

    parts = sentences(script_text)
    tokenized = [normalize_tokens(sentence) for sentence in parts]
    findings, reported = [], set()
    for first, tokens in enumerate(tokenized):
        for second in range(first, min(first + REPETITION_SENTENCE_SPAN, len(tokenized))):
            other = tokenized[second]
            index = 0
            while index <= len(tokens) - REPETITION_MIN_WORDS:
                width = 0
                for length in range(REPETITION_MIN_WORDS, len(tokens) - index + 1):
                    run = tokens[index : index + length]
                    starts = _occurrences(other, run)
                    if second == first:
                        starts = [start for start in starts if start >= index + length]
                    if not starts:
                        break
                    width = length
                run = tokens[index : index + width] if width else []
                if run and any(token not in STOPWORDS for token in run):
                    phrase = " ".join(run)
                    if phrase not in reported and not any(phrase in item for item in reported):
                        reported.add(phrase)
                        findings.append(
                            finding(
                                "SCRIPT_PHRASE_REPETITION",
                                "A phrase of three or more words repeats in nearby sentences.",
                                {
                                    "phrase": phrase,
                                    "sentence_indices": sorted({first, second}),
                                    "sentences": [parts[first]]
                                    + ([parts[second]] if second != first else []),
                                },
                                PREFLIGHT_VERSION,
                            )
                        )
                    index += width
                else:
                    index += 1
    return findings
