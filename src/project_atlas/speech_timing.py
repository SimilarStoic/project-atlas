"""Pure narration timing: script phrases, word-timing evidence and caption cue grouping.

Timing evidence acquisition is kept separate from cue grouping. ``estimate_word_timings``
turns detected narration pauses into per-word timings; a future provider word-timestamp
source must produce the same ``WordTiming`` list and feed the same ``build_caption_cues``
and ``recommend_scene_durations`` builders rather than a second caption path.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

CAPTION_POLICY = "pause-aligned-phrase-captions-v1"
# Cue display: tail after the last spoken word (Production 4), a readable minimum display that
# may extend into following silence, and the gap kept before the next cue.
CUE_TAIL_MS = 160
CUE_MIN_MS = 800
CUE_GAP_MS = 30
# A silence touching the start or end of the audio is leading/trailing, not a phrase pause.
EDGE_TOLERANCE_MS = 50
# Pause alignment: bounded look-back keeps the dynamic program small for long scripts.
MAX_BOUNDARY_SKIP = 4
MAX_SILENCE_SKIP = 6
UNMATCHED_SENTENCE_COST = 0.8
UNMATCHED_CLAUSE_COST = 0.3
EXTRA_SILENCE_COST = 0.25
EXTRA_SILENCE_COST_PER_SECOND = 1.0

_CLAUSE_END = re.compile(r"[,;:—][\"'’”)\]]*$")
_SENTENCE_END = re.compile(r"[.?!][\"'’”)\]]*$")
_VOWEL_GROUPS = re.compile(r"[aeiouy]+")


@dataclass(frozen=True)
class Silence:
    start_ms: float
    end_ms: float

    @property
    def duration_ms(self) -> float:
        return self.end_ms - self.start_ms

    @property
    def midpoint_ms(self) -> float:
        return (self.start_ms + self.end_ms) / 2


@dataclass(frozen=True)
class Phrase:
    first_word: int
    last_word: int
    text: str
    sentence_end: bool


@dataclass(frozen=True)
class WordTiming:
    word: str
    start_ms: float
    end_ms: float


@dataclass(frozen=True)
class SpeechTiming:
    """Per-word timings plus the evidence that produced them."""

    words: tuple[WordTiming, ...]
    duration_ms: int
    source: str
    # Phrase boundary (index of the phrase's last word) -> matched pause, if any.
    boundary_pauses: dict[int, Silence]
    pauses: tuple[Silence, ...]


def script_words(text: str) -> list[str]:
    words = text.split()
    if not words:
        raise ValueError("Script narration must contain words.")
    return words


def phrases(text: str) -> list[Phrase]:
    """Split the approved script at punctuation into natural spoken phrases."""

    words = script_words(text)
    result, first = [], 0
    for index, word in enumerate(words):
        sentence_end = bool(_SENTENCE_END.search(word))
        if sentence_end or _CLAUSE_END.search(word) or index == len(words) - 1:
            result.append(Phrase(first, index, " ".join(words[first : index + 1]), sentence_end))
            first = index + 1
    return result


def syllable_weight(word: str) -> int:
    acronym = re.match(r"^\W*([A-Z]{2,})(?![a-z])", word)
    if acronym:
        return len(acronym.group(1))
    letters = re.sub(r"[^a-z0-9]", "", word.lower())
    digits = sum(character.isdigit() for character in letters)
    groups = len(_VOWEL_GROUPS.findall(re.sub(r"[0-9]", "", letters)))
    if letters.endswith("e") and groups > 1 and not letters.endswith(("le", "ee")):
        groups -= 1
    return max(1, groups + 2 * digits)


def _speech_bounds(pauses: list[Silence], duration_ms: int) -> tuple[float, float, list[Silence]]:
    onset, end, internal = 0.0, float(duration_ms), []
    for pause in pauses:
        if pause.start_ms <= EDGE_TOLERANCE_MS:
            onset = max(onset, pause.end_ms)
        elif pause.end_ms >= duration_ms - EDGE_TOLERANCE_MS:
            end = min(end, pause.start_ms)
        else:
            internal.append(pause)
    if end <= onset:
        return 0.0, float(duration_ms), []
    return onset, end, [pause for pause in internal if onset < pause.start_ms < end]


def _align(
    phrase_list: list[Phrase],
    weights: list[int],
    onset: float,
    end: float,
    pauses: list[Silence],
) -> dict[int, int]:
    """Monotonically match phrase boundaries to pauses (or neither) at the most even speech rate."""

    boundaries = phrase_list[:-1]
    cumulative = [0]
    for weight in weights:
        cumulative.append(cumulative[-1] + weight)
    boundary_weight = [cumulative[phrase.last_word + 1] for phrase in boundaries]
    total_weight = cumulative[-1]
    pause_total = sum(pause.duration_ms for pause in pauses)
    global_rate = max(1.0, end - onset - pause_total) / total_weight
    prefix = [0.0]
    for pause in pauses:
        prefix.append(prefix[-1] + pause.duration_ms)
    skip_cost = [0.0]
    for pause in pauses:
        skip_cost.append(
            skip_cost[-1]
            + EXTRA_SILENCE_COST
            + EXTRA_SILENCE_COST_PER_SECOND * pause.duration_ms / 1000
        )
    unmatched = [
        UNMATCHED_SENTENCE_COST if phrase.sentence_end else UNMATCHED_CLAUSE_COST
        for phrase in boundaries
    ]
    unmatched_prefix = [0.0]
    for cost in unmatched:
        unmatched_prefix.append(unmatched_prefix[-1] + cost)

    # Anchor nodes: 0 = speech onset, 1..m = boundaries, m+1 = speech end.
    # Pause nodes: -1 = onset/end anchor, 0..n-1 = pause index.
    def time_after(pause: int) -> float:
        return onset if pause == -1 else pauses[pause].end_ms

    def segment_cost(b_from: int, p_from: int, b_to: int, p_to: int) -> float:
        weight_from = 0 if b_from == 0 else boundary_weight[b_from - 1]
        weight_to = total_weight if b_to == len(boundaries) + 1 else boundary_weight[b_to - 1]
        start = time_after(p_from)
        stop = end if p_to == len(pauses) else pauses[p_to].start_ms
        skipped_first, skipped_last = p_from + 1, p_to
        skipped_ms = prefix[skipped_last] - prefix[skipped_first]
        voiced = stop - start - skipped_ms
        weight = weight_to - weight_from
        if voiced <= 0 or weight <= 0:
            return math.inf
        rate = voiced / weight
        return (
            math.log(rate / global_rate) ** 2
            + (skip_cost[skipped_last] - skip_cost[skipped_first])
            + (unmatched_prefix[b_to - 1] - unmatched_prefix[b_from])
        )

    best: dict[tuple[int, int], tuple[float, tuple[int, int] | None]] = {(0, -1): (0.0, None)}
    for b_to in range(1, len(boundaries) + 2):
        targets = [len(pauses)] if b_to == len(boundaries) + 1 else range(len(pauses))
        for p_to in targets:
            candidates = []
            for b_from in range(max(0, b_to - MAX_BOUNDARY_SKIP - 1), b_to):
                low = -1 if b_from == 0 else max(0, p_to - MAX_SILENCE_SKIP - 1)
                for p_from in range(low, p_to):
                    if (b_from, p_from) not in best:
                        continue
                    if b_from == 0 and p_from != -1:
                        continue
                    cost = segment_cost(b_from, p_from, b_to, p_to)
                    if math.isfinite(cost):
                        candidates.append((best[(b_from, p_from)][0] + cost, (b_from, p_from)))
            if candidates:
                best[(b_to, p_to)] = min(candidates)
    final = (len(boundaries) + 1, len(pauses))
    if final not in best:
        return {}
    matched: dict[int, int] = {}
    node = best[final][1]
    while node is not None and node[0] != 0:
        matched[node[0] - 1] = node[1]
        node = best[node][1]
    return matched


def estimate_word_timings(text: str, duration_ms: int, pauses: list[Silence]) -> SpeechTiming:
    """Estimate per-word timings anchored on detected narration pauses.

    Matched pauses fix phrase boundaries exactly; words between anchors are spread by syllable
    weight over voiced time only, so unmatched (extra) pauses are never covered by a word.
    """

    if not isinstance(duration_ms, int) or duration_ms <= 0:
        raise ValueError("Narration duration must be positive milliseconds.")
    words = script_words(text)
    phrase_list = phrases(text)
    weights = [syllable_weight(word) for word in words]
    ordered = sorted(
        (pause for pause in pauses if pause.end_ms > pause.start_ms), key=lambda p: p.start_ms
    )
    onset, end, internal = _speech_bounds(ordered, duration_ms)
    matched = _align(phrase_list, weights, onset, end, internal) if internal else {}
    boundary_pauses = {
        phrase_list[index].last_word: internal[pause] for index, pause in matched.items()
    }
    anchors = [(-1, onset)]
    for word_index in sorted(boundary_pauses):
        anchors.append((word_index, boundary_pauses[word_index].start_ms))
        anchors.append((word_index, boundary_pauses[word_index].end_ms))
    anchors.append((len(words) - 1, end))

    timings: list[WordTiming] = []
    matched_pauses = set(boundary_pauses.values())
    for (last_before, start), (last_word, stop) in zip(anchors[0::2], anchors[1::2], strict=True):
        extra = sorted(
            (p for p in internal if start < p.start_ms < stop and p not in matched_pauses),
            key=lambda p: p.start_ms,
        )
        for first, last, sub_start, sub_stop in _snap_extra_pauses(
            weights, last_before + 1, last_word, start, stop, extra
        ):
            sub_weight = sum(weights[first : last + 1])
            cursor = sub_start
            for index in range(first, last + 1):
                share = (sub_stop - sub_start) * weights[index] / sub_weight
                word_end = sub_stop if index == last else cursor + share
                timings.append(WordTiming(words[index], cursor, word_end))
                cursor = word_end
    return SpeechTiming(
        tuple(timings),
        duration_ms,
        "pause_anchored_estimate",
        boundary_pauses,
        tuple(ordered),
    )


def _snap_extra_pauses(
    weights: list[int], first: int, last: int, start: float, stop: float, extra: list[Silence]
) -> list[tuple[int, int, float, float]]:
    """Place unmatched pauses at the nearest word boundary of a span (people pause between words).

    Returns sub-spans (first word, last word, start, stop) separated by those pauses.
    """

    voiced_total = stop - start - sum(pause.duration_ms for pause in extra)
    span_weight = sum(weights[first : last + 1])
    positions, running = {}, 0
    for index in range(first, last):
        running += weights[index]
        positions[index] = voiced_total * running / span_weight
    cuts: list[tuple[int, Silence]] = []
    before = 0.0
    for pause in extra:
        voiced_at = pause.start_ms - start - before
        before += pause.duration_ms
        available = [k for k in positions if not cuts or k > cuts[-1][0]]
        if available:
            cuts.append((min(available, key=lambda k: abs(positions[k] - voiced_at)), pause))
    spans, span_first, span_start = [], first, start
    for word, pause in cuts:
        spans.append((span_first, word, span_start, pause.start_ms))
        span_first, span_start = word + 1, pause.end_ms
    spans.append((span_first, last, span_start, stop))
    return spans


_FUNCTION_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "of",
        "in",
        "on",
        "at",
        "by",
        "for",
        "with",
        "from",
        "and",
        "or",
        "but",
        "if",
        "that",
        "where",
        "which",
        "who",
        "is",
        "are",
        "was",
        "were",
        "has",
        "have",
        "had",
        "can",
        "will",
        "would",
        "you",
        "your",
        "it",
        "its",
        "they",
        "their",
        "we",
        "as",
        "so",
        "not",
        "do",
        "does",
        "than",
        "then",
    }
)
# A word gap at least this long is a real spoken pause: a permitted cue split.
SPLIT_PAUSE_MS = 120
# A scene change within about one frame of a word gap belongs to that gap.
SCENE_BOUNDARY_TOLERANCE_MS = 40
# Words a length-forced split may come before (a natural start for the next cue).
_BREAK_BEFORE_WORDS = frozenset(
    {
        *[
            "and",
            "or",
            "but",
            "so",
            "if",
            "that",
            "where",
            "which",
            "who",
            "when",
            "to",
            "of",
            "in",
            "on",
            "at",
            "by",
            "for",
            "with",
            "from",
        ],
        *[
            "is",
            "are",
            "was",
            "were",
            "has",
            "have",
            "had",
            "can",
            "will",
            "would",
            "than",
            "then",
            "as",
        ],
        *["isn't", "aren't", "wasn't", "weren't", "don't", "doesn't", "can't", "won't"],
    }
)
# Cue grouping costs: fewest length-forced splits, placed well, then fewest cues, then balance.
_LENGTH_SPLIT_COST = 1000.0
_POOR_BREAK_COST = 300.0
_GOOD_BREAK_CREDIT = 50.0
_CUE_COST = 100.0


def _plain(word: str) -> str:
    return re.sub(r"[^a-z']", "", word.lower())


def group_cues(
    timing: SpeechTiming,
    text: str,
    scene_boundaries_ms: list[int],
    fits: Callable[[str], bool],
) -> list[tuple[int, int, str]]:
    """Return (first word, last word, split reason) cues, as few and steady as possible.

    A cue always ends at a sentence end or a scene change in a word gap. Elsewhere it may end
    only at a real spoken pause, unless the renderer's two-line layout (``fits``) forces a
    length split; a comma without a pause is never a split point by itself.
    """

    words = [item.word for item in timing.words]
    sentence_end = {phrase.last_word for phrase in phrases(text) if phrase.sentence_end}

    def gap(last: int) -> float:
        return timing.words[last + 1].start_ms - timing.words[last].end_ms

    def scene_change(last: int) -> bool:
        start, stop = timing.words[last].end_ms, timing.words[last + 1].start_ms
        return any(
            start - SCENE_BOUNDARY_TOLERANCE_MS <= boundary <= stop + SCENE_BOUNDARY_TOLERANCE_MS
            for boundary in scene_boundaries_ms
        )

    def split_cost(last: int) -> float:
        if gap(last) >= SPLIT_PAUSE_MS:
            return 0.0
        # Length split, following subtitle line-break practice: break before a conjunction,
        # preposition, relative or auxiliary; never end on a function word; never cut a run of
        # words that belong together (a comma without a spoken pause gives no licence).
        cost = _LENGTH_SPLIT_COST
        if _plain(words[last]) in _FUNCTION_WORDS:
            cost += _POOR_BREAK_COST
        if _plain(words[last + 1]) in _BREAK_BEFORE_WORDS:
            cost -= _GOOD_BREAK_CREDIT
        else:
            cost += _POOR_BREAK_COST
        return cost

    def text_of(first: int, last: int) -> str:
        return " ".join(words[first : last + 1])

    forced = [
        index for index in range(len(words) - 1) if index in sentence_end or scene_change(index)
    ]
    cues: list[tuple[int, int, str]] = []
    segment_first = 0
    for segment_last in [*forced, len(words) - 1]:
        first = segment_first
        # best[j]: (cost, cue start) covering words first..j-1 with a split before word j.
        best: dict[int, tuple[float, int]] = {first: (0.0, -1)}
        for stop in range(first + 1, segment_last + 2):
            options = []
            for begin in range(first, stop):
                if begin not in best:
                    continue
                candidate = text_of(begin, stop - 1)
                if not fits(candidate) and stop - 1 > begin:
                    continue
                cost = best[begin][0] + _CUE_COST + len(candidate) ** 2 / 1000
                if begin > first:
                    cost += split_cost(begin - 1)
                options.append((cost, begin))
            if options:
                best[stop] = min(options)
        bounds, stop = [], segment_last + 1
        while stop > first:
            begin = best[stop][1]
            bounds.append((begin, stop - 1))
            stop = begin
        for begin, last in reversed(bounds):
            if last == len(words) - 1:
                reason = "end"
            elif last in sentence_end:
                reason = "sentence end"
            elif scene_change(last):
                reason = "scene change"
            elif gap(last) >= SPLIT_PAUSE_MS:
                reason = "pause"
            else:
                reason = "length"
            cues.append((begin, last, reason))
        segment_first = segment_last + 1
    return cues


def build_caption_cues(
    timing: SpeechTiming,
    text: str,
    scene_boundaries_ms: list[int],
    fits: Callable[[str], bool],
) -> list[dict[str, Any]]:
    """Build cues that start at spoken onset and stay readable without overlapping speech."""

    if [item.word for item in timing.words] != script_words(text):
        raise ValueError("Word timings must cover exactly the approved script words.")
    units = group_cues(timing, text, scene_boundaries_ms, fits)
    starts = [math.ceil(timing.words[first].start_ms) for first, _last, _reason in units]
    cues = []
    for index, (first, last, _reason) in enumerate(units):
        start = starts[index]
        spoken_end = timing.words[last].end_ms
        # A cue may linger into following silence, never into the next spoken cue or scene.
        limit = starts[index + 1] - CUE_GAP_MS if index + 1 < len(units) else timing.duration_ms
        for boundary in scene_boundaries_ms:
            if spoken_end <= boundary < limit:
                limit = boundary
        end = min(limit, max(spoken_end + CUE_TAIL_MS, start + CUE_MIN_MS))
        end = max(end, min(limit, math.ceil(spoken_end)))
        cues.append(
            {
                "text": " ".join(item.word for item in timing.words[first : last + 1]),
                "start_ms": start,
                "end_ms": max(start + 1, int(round(end))),
            }
        )
    return cues


def recommend_scene_durations(timing: SpeechTiming, scene_excerpts: list[str]) -> dict[str, Any]:
    """Recommend scene durations whose boundaries sit at the pause ending each scene's excerpt."""

    words = [item.word for item in timing.words]
    excerpt_words = [script_words(excerpt) for excerpt in scene_excerpts]
    if [word for group in excerpt_words for word in group] != words:
        raise ValueError("Scene narration excerpts must concatenate exactly to the script.")
    boundaries, evidence, last = [], [], -1
    for group in excerpt_words[:-1]:
        last += len(group)
        pause = timing.boundary_pauses.get(last)
        if pause is not None:
            boundary, source = round(pause.midpoint_ms), "matched_pause_midpoint"
        else:
            boundary = round((timing.words[last].end_ms + timing.words[last + 1].start_ms) / 2)
            source = "estimated_word_gap"
        boundaries.append(boundary)
        evidence.append(
            {
                "after_word_index": last,
                "after_text": " ".join(words[max(0, last - 3) : last + 1]),
                "boundary_ms": boundary,
                "source": source,
                "pause": (
                    {"start_ms": round(pause.start_ms), "end_ms": round(pause.end_ms)}
                    if pause
                    else None
                ),
            }
        )
    edges = [0, *boundaries, timing.duration_ms]
    durations = [right - left for left, right in zip(edges, edges[1:], strict=False)]
    if any(duration <= 0 for duration in durations):
        raise ValueError("Recommended scene durations must be positive.")
    return {"durations_ms": durations, "boundaries": evidence}


def timing_evidence(timing: SpeechTiming) -> dict[str, Any]:
    """Compact, frozen description of the timing evidence used."""

    return {
        "source": timing.source,
        "pause_count": len(timing.pauses),
        "matched_phrase_boundaries": len(timing.boundary_pauses),
        "phrase_boundaries": len(phrases(" ".join(item.word for item in timing.words))) - 1,
    }
