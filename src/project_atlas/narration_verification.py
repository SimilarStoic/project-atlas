"""Independent narration completeness verification against the approved canonical Script.

The persisted narration WAV is transcribed by an independent speech recognizer (OpenAI
``whisper-1``, the method used for Productions 1-4) and strictly reconciled with the Script.
Both sides are normalized by one deterministic, versioned procedure that only removes
differences which do not change the spoken words: case, punctuation, ordinary contractions,
tokenization splits, approved pronunciation aliases, and numbers, currency and percentages.
Any remaining insertion, omission, repetition or substitution fails closed. The Script stays
the only editorial authority; nothing here is a second spoken script.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import Path
from typing import Any

NORMALIZATION_VERSION = "narration-completeness-v1"
VERIFICATION_METHOD = "independent-transcription-strict-reconciliation-v1"
TRANSCRIPTION_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"


class NarrationVerificationError(RuntimeError):
    """Transcription could not be obtained; nothing was reconciled and nothing is admitted."""


@dataclass(frozen=True)
class Transcription:
    text: str
    provider: str
    model: str
    words: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    request_parameters: dict[str, Any] = field(default_factory=dict)


class WhisperTranscriber:
    """One prompt-free ``whisper-1`` transcription of exact audio; no retry, no fallback."""

    provider = "OpenAI"
    model = "whisper-1"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    @property
    def request_parameters(self) -> dict[str, Any]:
        # No prompt: a prompt containing the Script would bias recognition toward it.
        return {
            "model": self.model,
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
            "language": "en",
            "temperature": "0",
        }

    def transcribe(self, path: Path) -> Transcription:
        credential = self._api_key or os.environ.get("OPENAI_API_KEY", "")
        if not credential:
            raise NarrationVerificationError("OPENAI_API_KEY is required for transcription.")
        boundary = f"conveyor-{uuid.uuid4().hex}"
        body = bytearray()
        for name, value in self.request_parameters.items():
            body += (
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode()
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="{path.name}"\r\nContent-Type: audio/wav\r\n\r\n'
        ).encode()
        body += path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
        request = urllib.request.Request(
            TRANSCRIPTION_ENDPOINT,
            bytes(body),
            {
                "Authorization": f"Bearer {credential}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.loads(response.read())
            text = result["text"]
            if not isinstance(text, str):
                raise ValueError("Transcription text is missing.")
            words = tuple(
                {"word": item["word"], "start": item["start"], "end": item["end"]}
                for item in result.get("words") or []
            )
        except Exception:
            # Never persist provider bodies, headers or transport exceptions.
            raise NarrationVerificationError(
                "Narration transcription failed; no automatic retry."
            ) from None
        return Transcription(text, self.provider, self.model, words, self.request_parameters)


# --- Deterministic normalization ------------------------------------------------------------

_ONES = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]
_TENS = ["_", "_", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_SCALES = ((10**9, "billion"), (10**6, "million"), (10**3, "thousand"))
_ORDINAL_WORDS = {
    "one": "first",
    "two": "second",
    "three": "third",
    "five": "fifth",
    "eight": "eighth",
    "nine": "ninth",
    "twelve": "twelfth",
}
_NUMBER_WORDS = set(_ONES) | set(_TENS[2:]) | {"hundred", "thousand", "million", "billion"}
_CURRENCIES = {"£": ("pound", "pounds"), "$": ("dollar", "dollars"), "€": ("euro", "euros")}
_SCALE_SUFFIX = {"thousand", "million", "billion"}
_CONTRACTIONS = {
    "can't": "can not",
    "cannot": "can not",
    "won't": "will not",
    "shan't": "shall not",
    "i'm": "i am",
    "let's": "let us",
}
_IS_CONTRACTION_BASES = {"it", "that", "there", "what", "here", "he", "she", "who", "where"}
_AMOUNT = re.compile(
    r"(?P<currency>[£$€])?\s?(?P<number>\d{1,3}(?:,\d{3})+|\d+)(?:\.(?P<decimal>\d+))?"
    r"(?:\s?(?P<scale>thousand|million|billion)\b)?"
    r"(?:\s?(?P<percent>%|per\s?cent\b|percent\b))?"
    r"(?P<ordinal>st|nd|rd|th)?\b"
)


def number_words(value: int) -> list[str]:
    """Spell a non-negative integer in one canonical form, without 'and'."""

    if value < 0:
        raise ValueError("Only non-negative numbers are spelled.")
    if value < 20:
        return [_ONES[value]]
    if value < 100:
        tens, ones = divmod(value, 10)
        return [_TENS[tens]] + ([_ONES[ones]] if ones else [])
    if value < 1000:
        hundreds, rest = divmod(value, 100)
        return [_ONES[hundreds], "hundred"] + (number_words(rest) if rest else [])
    for scale, name in _SCALES:
        if value >= scale:
            high, rest = divmod(value, scale)
            return number_words(high) + [name] + (number_words(rest) if rest else [])
    raise AssertionError("unreachable")


def _ordinal(words: list[str]) -> list[str]:
    last = words[-1]
    if last in _ORDINAL_WORDS:
        return words[:-1] + [_ORDINAL_WORDS[last]]
    if last.endswith("y"):
        return words[:-1] + [last[:-1] + "ieth"]
    return words[:-1] + [last + "th"]


def _spell_amount(match: re.Match[str]) -> str:
    number = int(match.group("number").replace(",", ""))
    words = number_words(number)
    if match.group("decimal"):
        words += ["point"] + [_ONES[int(digit)] for digit in match.group("decimal")]
    if match.group("ordinal"):
        words = _ordinal(words)
    if match.group("scale"):
        words.append(match.group("scale"))
    currency = match.group("currency")
    if currency:
        singular, plural = _CURRENCIES[currency]
        unit = (
            singular
            if number == 1 and not match.group("decimal") and not match.group("scale")
            else plural
        )
        words.append(unit)
    if match.group("percent"):
        words.append("percent")
    return " " + " ".join(words) + " "


def _expand_contraction(token: str) -> list[str]:
    if token in _CONTRACTIONS:
        return _CONTRACTIONS[token].split()
    if token.endswith("n't"):
        return [token[:-3], "not"]
    for suffix, word in (("'re", "are"), ("'ve", "have"), ("'ll", "will")):
        if token.endswith(suffix) and len(token) > len(suffix):
            return [token[: -len(suffix)], word]
    if token.endswith("'s") and token[:-2] in _IS_CONTRACTION_BASES:
        return [token[:-2], "is"]
    return [token]


def normalize_tokens(text: str) -> list[str]:
    """Return canonical spoken tokens for one text under ``NORMALIZATION_VERSION``."""

    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("‘", "'").lower()
    text = re.sub(r"\bper\s+cent\b", "percent", text)
    text = _AMOUNT.sub(_spell_amount, text)
    text = text.replace("%", " percent ")
    # Hyphens and dashes separate tokens; any split/joined spelling is reconciled later.
    text = re.sub(r"[-‐‑‒–—―]", " ", text)
    text = re.sub(r"[^\w'£$€ ]+", " ", text)
    tokens: list[str] = []
    for raw in text.split():
        token = raw.strip("'")
        if token:
            tokens.extend(_expand_contraction(token))
    canonical: list[str] = []
    for index, token in enumerate(tokens):
        previous = canonical[-1] if canonical else None
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        # "seven hundred and twenty" -> "seven hundred twenty": 'and' joining number words.
        if token == "and" and previous in _NUMBER_WORDS and following in _NUMBER_WORDS:
            continue
        # "a hundred" / "a million" -> "one hundred" / "one million".
        if (
            token == "a"
            and following in {"hundred", "thousand", "million", "billion"}
            and previous not in _NUMBER_WORDS
        ):
            canonical.append("one")
            continue
        canonical.append(token)
    return canonical


# Canonical tokens that only spell a figure (numbers, units of amount), never a qualifier.
FIGURE_WORDS = frozenset(
    _NUMBER_WORDS
    | {"point", "percent"}
    | {unit for pair in _CURRENCIES.values() for unit in pair}
    | {_ordinal([word])[0] for word in _ONES[1:] + _TENS[2:]}
)


def spoken_figures(text: str) -> list[list[str]]:
    """Canonical spoken tokens of each figure written with digits in ``text``, in order.

    Uses exactly the ``NORMALIZATION_VERSION`` amount grammar; figures written in words are
    not detected as figures.
    """

    prepared = unicodedata.normalize("NFKC", text).replace("’", "'").replace("‘", "'").lower()
    prepared = re.sub(r"\bper\s+cent\b", "percent", prepared)
    figures = []
    for match in _AMOUNT.finditer(prepared):
        end = match.end()
        # normalize_tokens spells a "%" left outside the amount match as "percent" afterwards.
        if prepared[end : end + 1] == "%":
            end += 1
        tokens = normalize_tokens(prepared[match.start() : end])
        if tokens:
            figures.append(tokens)
    return figures


def _apply_aliases(tokens: list[str], aliases: tuple[tuple[str, str], ...]) -> tuple[list, list]:
    """Map an approved spoken alias form back to its written Script token."""

    applied = []
    for written, spoken in aliases:
        written_tokens = normalize_tokens(written)
        spoken_tokens = normalize_tokens(spoken)
        if not spoken_tokens or spoken_tokens == written_tokens:
            continue
        index = 0
        while index <= len(tokens) - len(spoken_tokens):
            if tokens[index : index + len(spoken_tokens)] == spoken_tokens:
                tokens = tokens[:index] + written_tokens + tokens[index + len(spoken_tokens) :]
                applied.append({"written": written, "spoken": spoken, "position": index})
                index += len(written_tokens)
            else:
                index += 1
    return tokens, applied


# --- Strict reconciliation ------------------------------------------------------------------


def _context(tokens: list[str], start: int, end: int) -> str:
    return " ".join(tokens[max(0, start - 3) : start]) + " [...] " + " ".join(tokens[end : end + 3])


def reconcile(expected: list[str], observed: list[str]) -> dict[str, Any]:
    """Sequence-align canonical tokens; every unexplained difference is reported."""

    matcher = SequenceMatcher(None, expected, observed, autojunk=False)
    differences, equivalences, recovered = [], [], 0
    for tag, e1, e2, o1, o2 in matcher.get_opcodes():
        expected_block, observed_block = expected[e1:e2], observed[o1:o2]
        if tag == "equal":
            recovered += e2 - e1
            continue
        if expected_block and observed_block and "".join(expected_block) == "".join(observed_block):
            # Only the token boundaries differ (e.g. "price cap" / "pricecap", "of gem").
            recovered += e2 - e1
            equivalences.append({"expected": expected_block, "observed": observed_block})
            continue
        if tag == "insert":
            size = len(observed_block)
            repeated = observed[o1 - size : o1] == observed_block or (
                observed[o2 : o2 + size] == observed_block
            )
            kind = "repetition" if repeated else "insertion"
        elif tag == "delete":
            kind = "omission"
        else:
            kind = "substitution"
        differences.append(
            {
                "kind": kind,
                "expected": expected_block,
                "observed": observed_block,
                "expected_index": e1,
                "observed_index": o1,
                "context": _context(expected, e1, e2),
            }
        )
    return {
        "differences": differences,
        "tokenization_equivalences": equivalences,
        "expected_token_count": len(expected),
        "observed_token_count": len(observed),
        "recovered_token_count": recovered,
    }


def verify_transcript(
    script_text: str, transcript: str, aliases: tuple[tuple[str, str], ...] = ()
) -> dict[str, Any]:
    """Strictly reconcile one transcript with the canonical Script (no provider call)."""

    expected = normalize_tokens(script_text)
    observed, alias_applications = _apply_aliases(normalize_tokens(transcript), aliases)
    report = reconcile(expected, observed)
    passed = not report["differences"] and report["recovered_token_count"] == len(expected)
    return {
        "outcome": "passed" if passed else "failed",
        "normalization_version": NORMALIZATION_VERSION,
        "alias_applications": alias_applications,
        **report,
    }


def verify_narration_audio(
    audio_path: Path,
    expected_sha256: str,
    script_text: str,
    transcriber: Any,
    aliases: tuple[tuple[str, str], ...] = (),
) -> dict[str, Any]:
    """Transcribe the exact persisted WAV once and reconcile it against the Script."""

    content = audio_path.read_bytes()
    actual = sha256(content).hexdigest()
    if actual != expected_sha256:
        raise NarrationVerificationError("Narration bytes differ from the persisted digest.")
    transcription = transcriber.transcribe(audio_path)
    return {
        "method": VERIFICATION_METHOD,
        "provider": transcription.provider,
        "model": transcription.model,
        "request_parameters": dict(transcription.request_parameters),
        "wav_sha256": actual,
        "transcript": transcription.text,
        "transcript_words": list(transcription.words),
        **verify_transcript(script_text, transcription.text, aliases),
    }
