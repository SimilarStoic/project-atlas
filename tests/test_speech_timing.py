"""Pause-aligned phrase captions and narration-based retime recommendation."""

from __future__ import annotations

import pytest

from project_atlas import speech_timing as st
from project_atlas.media import MediaService
from project_atlas.speech_timing import Silence

# Production 9 Attempt 2 narration evidence (Inworld Daniel, 34.380 s), recorded with the
# canonical silencedetect settings; used as a realistic, provider-free fixture.
P9_SCRIPT = (
    "Buy now, pay later just got grown-up rules. Since the fifteenth of July, twenty "
    "twenty-six, many buy now, pay later deals are regulated by the FCA. Before lending, the "
    "provider has to check you can afford it. You get clear details up front: when payments are "
    "due, and what happens if you miss one. If you're struggling, they have to help. And if "
    "something goes wrong, you can complain to the Financial Ombudsman. But deals from before "
    "that date aren't covered, and neither are ones where the shop itself lends to you. So "
    "check the date, and check the lender on the FCA's Firm Checker."
)
P9_BEATS = [
    "Buy now, pay later just got grown-up rules.",
    "Since the fifteenth of July, twenty twenty-six, many buy now, pay later deals are "
    "regulated by the FCA.",
    "Before lending, the provider has to check you can afford it.",
    "You get clear details up front: when payments are due, and what happens if you miss one.",
    "If you're struggling, they have to help.",
    "And if something goes wrong, you can complain to the Financial Ombudsman.",
    "But deals from before that date aren't covered, and neither are ones where the shop itself "
    "lends to you.",
    "So check the date, and check the lender on the FCA's Firm Checker.",
]
P9_PAUSES = [
    Silence(start, end)
    for start, end in (
        (543.687, 806.354),
        (1333.417, 1677.188),
        (2805.583, 3430.292),
        (4732.792, 4923.958),
        (5954.708, 6352.979),
        (9711.396, 10154.917),
        (10849.604, 11262.146),
        (13276.396, 13622.937),
        (15175.25, 15587.875),
        (16588.333, 16946.625),
        (18308.021, 18817.333),
        (19617.979, 19877.167),
        (20608.708, 21008.542),
        (22235.833, 22466.583),
        (24529.146, 25034.896),
        (27116.375, 27360.396),
        (29829.292, 30280.562),
        (31227.208, 31537.292),
        (33881.271, 34380.0),
    )
]
P9_DURATION = 34380
# Founder-approved Production 9 render v2 durations, computed by hand from the same pauses.
P9_V2_DURATIONS = [3118, 6815, 3517, 5113, 2246, 3973, 5273, 4325]


def _p9_timing() -> st.SpeechTiming:
    return st.estimate_word_timings(P9_SCRIPT, P9_DURATION, P9_PAUSES)


def _boundaries(durations: list[int]) -> list[int]:
    edges, elapsed = [], 0
    for duration in durations[:-1]:
        elapsed += duration
        edges.append(elapsed)
    return edges


def test_phrases_split_at_punctuation_and_mark_sentence_ends() -> None:
    phrases = st.phrases("Buy now, pay later. Check: the date; then act")
    assert [phrase.text for phrase in phrases] == [
        "Buy now,",
        "pay later.",
        "Check:",
        "the date;",
        "then act",
    ]
    assert [phrase.sentence_end for phrase in phrases] == [False, True, False, False, False]


def test_pauses_anchor_phrase_boundaries_and_extra_pauses_fall_between_words() -> None:
    timing = _p9_timing()
    words = [item.word for item in timing.words]
    assert words == P9_SCRIPT.split()
    # 17 of 18 punctuation boundaries have a real pause; "many buy now," was spoken through.
    assert len(timing.boundary_pauses) == 17
    assert words.index("many") + 2 not in timing.boundary_pauses
    for index, pause in timing.boundary_pauses.items():
        assert timing.words[index].end_ms == pause.start_ms
        assert timing.words[index + 1].start_ms == pause.end_ms
    # The unpunctuated pause after "pay later" is placed in a word gap, never inside a word.
    extra = P9_PAUSES[1]
    assert not any(item.start_ms < extra.start_ms < item.end_ms for item in timing.words)
    assert any(item.end_ms == extra.start_ms for item in timing.words)
    assert all(a.end_ms <= b.start_ms for a, b in zip(timing.words, timing.words[1:], strict=False))


def test_recommendation_reproduces_the_hand_computed_p9_pause_midpoints() -> None:
    recommendation = st.recommend_scene_durations(_p9_timing(), P9_BEATS)
    assert recommendation["durations_ms"] == P9_V2_DURATIONS
    assert sum(recommendation["durations_ms"]) == P9_DURATION
    assert {item["source"] for item in recommendation["boundaries"]} == {"matched_pause_midpoint"}


def test_recommendation_requires_excerpts_that_concatenate_to_the_script() -> None:
    with pytest.raises(ValueError, match="concatenate exactly"):
        st.recommend_scene_durations(_p9_timing(), P9_BEATS[:-1])


def _fits(text: str) -> bool:
    return MediaService.caption_fits(text, MediaService.SOCIAL_CAPTION_PROFILE)


def test_caption_fit_follows_the_renderer_two_line_layout() -> None:
    # Calibrated against Production 9 v2 frames: the first line rendered on one line, the
    # second wrapped; a cue may use two such lines but never three.
    assert _fits("Buy now, pay later just got grown-up rules.")
    assert _fits("many buy now, pay later deals")
    assert not _fits("the provider has to check you can afford it.")


def test_p9_cues_split_only_at_pauses_sentence_ends_or_length() -> None:
    timing = _p9_timing()
    boundaries = _boundaries(P9_V2_DURATIONS)
    groups = st.group_cues(timing, P9_SCRIPT, boundaries, _fits)
    cues = st.build_caption_cues(timing, P9_SCRIPT, boundaries, _fits)
    texts = [cue["text"] for cue in cues]
    assert " ".join(texts) == P9_SCRIPT
    assert texts[0] == "Buy now, pay later just got grown-up rules."
    assert "many buy now, pay later deals" in texts
    assert len(cues) == 19
    words = P9_SCRIPT.split()
    for index, (first, last, reason) in enumerate(groups):
        assert reason in {"pause", "sentence end", "scene change", "length", "end"}
        if reason == "pause":
            gap = timing.words[last + 1].start_ms - timing.words[last].end_ms
            assert gap >= st.SPLIT_PAUSE_MS
        if reason == "length":
            # A length split only where the two neighbouring cues cannot share one cue.
            following = groups[index + 1]
            assert not _fits(" ".join(words[first : following[1] + 1]))
    for cue, (first, _last, _reason) in zip(cues, groups, strict=True):
        # Never ahead of the first spoken word (and so never before the end of a pause).
        assert cue["start_ms"] >= timing.words[first].start_ms
        assert _fits(cue["text"])
        assert not any(cue["start_ms"] < boundary < cue["end_ms"] for boundary in boundaries)
    assert all(
        a["end_ms"] + st.CUE_GAP_MS <= b["start_ms"] for a, b in zip(cues, cues[1:], strict=False)
    )
    # Scene-final cues end in the pause at or before the scene change.
    assert cues[0]["end_ms"] <= boundaries[0]


def test_cues_reach_the_readable_minimum_only_into_silence() -> None:
    text = "Stop. Then check the lender carefully today."
    timing = st.estimate_word_timings(text, 4000, [Silence(300, 1400)])
    first, second = st.build_caption_cues(timing, text, [], _fits)
    assert first["text"] == "Stop."
    # Spoken for 300 ms, held into the following silence to reach the readable minimum.
    assert first["end_ms"] - first["start_ms"] == st.CUE_MIN_MS
    assert first["end_ms"] + st.CUE_GAP_MS <= second["start_ms"] == 1400
    tight = st.estimate_word_timings(text, 4000, [Silence(300, 500)])
    first, second = st.build_caption_cues(tight, text, [], _fits)
    assert first["end_ms"] == second["start_ms"] - st.CUE_GAP_MS
    assert first["end_ms"] - first["start_ms"] < st.CUE_MIN_MS


def test_a_scene_change_inside_continuous_speech_does_not_split_the_phrase() -> None:
    timing = st.estimate_word_timings("Check the lender carefully today.", 3000, [])
    mid_phrase = round(timing.words[2].start_ms + 50)
    cues = st.build_caption_cues(timing, "Check the lender carefully today.", [mid_phrase], _fits)
    assert [cue["text"] for cue in cues] == ["Check the lender carefully today."]


def test_commas_and_pauses_permit_but_do_not_force_a_split() -> None:
    text = "Buy now, pay later deals."
    continuous = st.estimate_word_timings(text, 2000, [])
    assert [cue["text"] for cue in st.build_caption_cues(continuous, text, [], _fits)] == [text]
    paused = st.estimate_word_timings(text, 2400, [Silence(800, 1200)])
    assert [cue["text"] for cue in st.build_caption_cues(paused, text, [], _fits)] == [text]
    # A scene change in the pause does end the cue there.
    split_by_scene = st.build_caption_cues(paused, text, [1000], _fits)
    assert [cue["text"] for cue in split_by_scene] == ["Buy now,", "pay later deals."]


def test_without_any_pause_evidence_the_same_builder_estimates_every_boundary() -> None:
    timing = st.estimate_word_timings(P9_SCRIPT, P9_DURATION, [])
    assert timing.boundary_pauses == {}
    cues = st.build_caption_cues(timing, P9_SCRIPT, [], _fits)
    assert " ".join(cue["text"] for cue in cues) == P9_SCRIPT
    assert all(_fits(cue["text"]) for cue in cues)
    assert cues[-1]["end_ms"] <= P9_DURATION
    assert st.timing_evidence(timing)["matched_phrase_boundaries"] == 0


def test_cue_builder_rejects_timings_for_a_different_script() -> None:
    with pytest.raises(ValueError, match="approved script"):
        st.build_caption_cues(_p9_timing(), "Different words.", [], _fits)
