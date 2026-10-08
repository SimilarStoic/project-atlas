"""Pre-synthesis Script preflight: advisory, deterministic, never a Script rewrite."""

from __future__ import annotations

import pytest

from project_atlas import narration, script_preflight
from project_atlas.narration_verification import spoken_figures

# Production 10's founder-approved figure and coverage sentences, and the B1 spoken rewrite.
P10_FIGURE = "Ofgem puts a typical Direct Debit household at £1,723 a year — £60 more."
P10_COVERAGE = "It only covers default tariffs: around 20 million households, including prepayment."
B1_FIGURE = (
    "Take a typical household paying by Direct Debit. Ofgem puts it at £1,723 a year. "
    "That's £60 more."
)
C2_QUOTE = (
    "The energy price cap protects around 22 million households on default tariffs by limiting "
    "the maximum rates and standing charges that energy suppliers can charge."
)
C5_QUOTE = (
    "Overall number of domestic households* on Standard Variable Tariffs (SVT) – 'around 20 "
    "million' of which: New no. of SVT PPM customers – 'around 5 million'"
)


def _claim_set(*quotes: tuple[str, str], claims: tuple[str, ...] = ()) -> dict:
    return {
        "frozen_claims": [{"id": f"claim-{i}", "text": text} for i, text in enumerate(claims)],
        "frozen_claim_evidence": [
            {"claim_id": claim_id, "source_id": "S1", "reference": quote, "notes": ""}
            for claim_id, quote in quotes
        ],
    }


def _codes(findings: list[dict]) -> list[str]:
    return [item["code"] for item in findings]


def test_every_finding_is_advisory_editorial_evidence() -> None:
    findings = script_preflight.number_findings(P10_COVERAGE, _claim_set(("C2", C2_QUOTE)))
    findings += narration.speakability_findings(P10_FIGURE, "similarstoic-daniel-v2")
    findings += script_preflight.repetition_findings("Save the spare change. Save the spare cash.")
    assert findings
    for item in findings:
        assert item["blocking"] is False
        assert item["requires_editorial_judgement"] is True
        assert item["severity"] == "warning"
        assert item["rule_version"]


def test_figures_use_the_completeness_normalization() -> None:
    assert spoken_figures("It rose 4% to £1,723 for around 20 million homes.") == [
        ["four", "percent"],
        ["one", "thousand", "seven", "hundred", "twenty", "three", "pounds"],
        ["twenty", "million"],
    ]
    assert spoken_figures("No digits here, only twenty words.") == []


def test_p10_crossed_category_is_flagged_with_its_source_pairing() -> None:
    [finding] = script_preflight.number_findings(
        P10_COVERAGE, _claim_set(("C2", C2_QUOTE), ("C5", C5_QUOTE))
    )
    assert finding["code"] == "SCRIPT_NUMBER_QUALIFIER_MISMATCH"
    evidence = finding["evidence"]
    assert evidence["figure"] == "twenty million"
    assert "default" in evidence["script_qualifiers"]
    assert {
        (item["qualifier"], item["source_figure"]) for item in evidence["crossed_pairings"]
    } >= {("default", "twenty two million")}
    assert [item["claim_id"] for item in evidence["source_contexts"]] == ["C5"]


def test_correctly_qualified_figures_produce_no_finding() -> None:
    script = "It covers around 22 million households on default tariffs."
    assert script_preflight.number_findings(script, _claim_set(("C2", C2_QUOTE))) == []


def test_a_figure_with_no_qualifier_in_common_is_flagged() -> None:
    script = "About 22 million renters moved house."
    [finding] = script_preflight.number_findings(script, _claim_set(("C2", C2_QUOTE)))
    assert finding["code"] == "SCRIPT_NUMBER_QUALIFIER_MISMATCH"
    assert finding["evidence"]["crossed_pairings"] == []


def test_unquoted_and_unsourced_figures_are_distinguished() -> None:
    claim_set = _claim_set(("C1", "No figures in this quote."), claims=("Prices rose 4%.",))
    assert _codes(script_preflight.number_findings("Prices rose 4% this year.", claim_set)) == [
        "SOURCED_NUMBER_WITHOUT_QUOTE"
    ]
    assert _codes(script_preflight.number_findings("Prices rose 9% this year.", claim_set)) == [
        "SCRIPT_NUMBER_NOT_IN_FROZEN_EVIDENCE"
    ]
    assert _codes(script_preflight.number_findings("Prices rose 9%.", None)) == [
        "SCRIPT_NUMBER_NOT_IN_FROZEN_EVIDENCE"
    ]


def test_nearby_phrase_repetition_is_reported_once_and_distant_repetition_is_not() -> None:
    near = "Check the standing charge first. Then check the standing charge again."
    [finding] = script_preflight.repetition_findings(near)
    assert finding["code"] == "SCRIPT_PHRASE_REPETITION"
    assert finding["evidence"]["phrase"] == "check the standing charge"
    assert finding["evidence"]["sentence_indices"] == [0, 1]
    within = "The cap went up and the cap went up again."
    assert script_preflight.repetition_findings(within)[0]["evidence"]["sentence_indices"] == [0]
    distant = (
        "Check the standing charge first. Then read the meter. Then call the supplier. "
        "Finally check the standing charge."
    )
    assert script_preflight.repetition_findings(distant) == []
    # Rhetorical function-word structure ("the more you") is not a content repetition.
    assert script_preflight.repetition_findings("The more you use, the more you pay.") == []


def test_daniel_speakability_flags_the_p10_figure_sentence_but_not_the_b1_rewrite() -> None:
    codes = _codes(narration.speakability_findings(P10_FIGURE, "similarstoic-daniel-v2"))
    assert codes == [
        "SPEAKABILITY_MULTIPLE_FIGURES",
        "SPEAKABILITY_FIGURE_JOINED_BY_DASH_OR_COLON",
    ]
    assert narration.speakability_findings(B1_FIGURE, "similarstoic-daniel-v2") == []
    [colon] = narration.speakability_findings(P10_COVERAGE, "similarstoic-daniel-v2")
    assert colon["code"] == "SPEAKABILITY_FIGURE_JOINED_BY_DASH_OR_COLON"
    assert colon["evidence"]["narrator_profile_id"] == "similarstoic-daniel-v2"
    # A hyphenated word is not a dash join.
    assert (
        narration.speakability_findings("A price-cap rise of 4%.", "similarstoic-daniel-v2") == []
    )


def test_daniel_fixed_terms_and_long_sentences_are_flagged() -> None:
    [term] = narration.speakability_findings(
        "Buy now, pay later is everywhere.", "similarstoic-daniel-v2"
    )
    assert term["code"] == "SPEAKABILITY_FIXED_TERM_PUNCTUATION"
    assert term["evidence"]["term"] == "Buy now, pay later"
    long_sentence = " ".join(["word"] * 29) + "."
    [long] = narration.speakability_findings(long_sentence, "similarstoic-daniel-v2")
    assert long["code"] == "SPEAKABILITY_LONG_SENTENCE"
    assert long["evidence"]["word_count"] == 29
    assert (
        narration.speakability_findings(" ".join(["word"] * 28) + ".", "similarstoic-daniel-v1")
        == []
    )


def test_speakability_rules_belong_to_the_narrator_brand(monkeypatch) -> None:
    monkeypatch.setattr(narration, "SPEAKABILITY_RULES", {})
    assert narration.speakability_findings(P10_FIGURE, "similarstoic-daniel-v2") == []
    with pytest.raises(ValueError, match="Unknown narrator profile"):
        narration.speakability_findings(P10_FIGURE, "someone-else-v1")
