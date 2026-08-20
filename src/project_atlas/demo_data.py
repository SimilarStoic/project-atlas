"""Explicitly local demo data for the Conveyor MVP UI shell.

This module models the UI's future-facing concepts without representing a
production repository, workflow engine, research service, or AI integration.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TopicOpportunity:
    """A proposed topic shown in the Discover experience."""

    id: str
    topic: str
    score: int
    why_now: str
    viewer_benefit: str
    suggested_angle: str
    evidence_quality: str
    risk: str
    portfolio_relevance: str
    visual_potential: str
    pillar: str


OPPORTUNITIES: tuple[TopicOpportunity, ...] = (
    TopicOpportunity(
        id="uk-isa-rules",
        topic="The ISA allowance reset: what to do before 5 April",
        score=92,
        why_now="The end of the UK tax year is approaching and ISA questions are rising.",
        viewer_benefit=(
            "A clear, practical checklist for protecting tax-efficient investing capacity."
        ),
        suggested_angle="The 15-minute ISA decision tree before the deadline.",
        evidence_quality="High · HMRC and GOV.UK",
        risk="Medium",
        portfolio_relevance="Fills a core UK wealth-planning gap",
        visual_potential="High",
        pillar="Keep More of What You Earn",
    ),
    TopicOpportunity(
        id="credit-utilisation",
        topic="Why a paid-off credit card can still affect your score",
        score=88,
        why_now=(
            "Community questions show persistent confusion about utilisation and statement dates."
        ),
        viewer_benefit="Helps viewers understand a common, low-stakes credit misconception.",
        suggested_angle="Your credit card has two clocks—and one matters more than you think.",
        evidence_quality="High · Experian, Equifax, TransUnion",
        risk="Low",
        portfolio_relevance="Builds depth in the credit fundamentals cluster",
        visual_potential="High",
        pillar="Build & Protect Wealth",
    ),
    TopicOpportunity(
        id="salary-sacrifice",
        topic="Salary sacrifice versus a pay rise at £60k",
        score=86,
        why_now=(
            "The £60k tax threshold remains a high-interest planning question for UK professionals."
        ),
        viewer_benefit="Explains a useful trade-off without presenting personalised advice.",
        suggested_angle="The invisible 60% tax trap—then the one lever that can change it.",
        evidence_quality="High · HMRC and MoneyHelper",
        risk="High",
        portfolio_relevance="Strong bridge between tax, pension and career content",
        visual_potential="Medium",
        pillar="Keep More of What You Earn",
    ),
    TopicOpportunity(
        id="ai-workflow",
        topic="Three AI workflows that make a junior analyst more valuable",
        score=83,
        why_now="AI adoption is moving from curiosity to practical workplace expectations.",
        viewer_benefit="Provides immediately useful ways to build career leverage.",
        suggested_angle="Don't ask AI to do your job—use it to make your judgment compound.",
        evidence_quality="Medium · employer and industry research",
        risk="Low",
        portfolio_relevance="Expands the skills and income pillar",
        visual_potential="High",
        pillar="Increase Income & Leverage",
    ),
    TopicOpportunity(
        id="energy-grid",
        topic="The quiet infrastructure behind the AI boom",
        score=80,
        why_now=(
            "Demand for data-centre power makes grids and energy infrastructure newly relevant."
        ),
        viewer_benefit="Connects a headline trend to the systems and businesses behind it.",
        suggested_angle="AI needs electricity first: the overlooked layer of the boom.",
        evidence_quality="Medium · regulatory and company sources",
        risk="Medium",
        portfolio_relevance="Adds a technology-and-opportunity perspective",
        visual_potential="High",
        pillar="Spot the Next Opportunity",
    ),
    TopicOpportunity(
        id="lifestyle-inflation",
        topic="The £300 lifestyle upgrade that becomes a £100k decision",
        score=77,
        why_now="Evergreen decision-making topic with strong audience resonance.",
        viewer_benefit="Makes opportunity cost tangible without shaming viewers.",
        suggested_angle="Small subscriptions are not the problem—the default life is.",
        evidence_quality="Medium · illustrative calculations",
        risk="Low",
        portfolio_relevance="Balances practical finance with behavioural content",
        visual_potential="High",
        pillar="Think & Decide Better",
    ),
)


CONTENT_ITEM: dict[str, Any] = {
    "id": "content-isa-deadline",
    "title": "The ISA allowance reset: what to do before 5 April",
    "status": "Human review",
    "lifecycle": [
        "Discover",
        "Research",
        "Angle",
        "Script",
        "Automated QA",
        "Human review",
        "Approval",
    ],
    "target_audience": "UK professionals, 24–35, building wealth alongside a full-time income",
    "pillar": "Keep More of What You Earn",
    "risk": "Medium · tax guidance requires date-sensitive review",
    "research_summary": (
        "Research Pack v0.3 consolidates current ISA allowance rules, transfer guidance "
        "and deadline timing from HMRC and GOV.UK. Two wording checks remain open."
    ),
    "claim_count": 12,
    "source_count": 6,
    "selected_angle": "The 15-minute ISA decision tree before the deadline.",
    "script": (
        "If you have spare cash before 5 April, the question is not simply ‘should I invest?’ "
        "It is whether you are about to lose a tax-year opportunity you cannot get back."
    ),
    "scene_plan": (
        "Hamster at a calm kitchen table with a sling bag, sorting four labelled envelopes. "
        "A tax-year calendar appears; the decision tree builds one branch at a time."
    ),
    "qa": [
        {"label": "Claim verification", "state": "Passed"},
        {"label": "Freshness check", "state": "Needs review"},
        {"label": "Audio-only comprehension", "state": "Passed"},
        {"label": "Visual fact check", "state": "Passed"},
    ],
}


ACTIVITY: tuple[dict[str, str], ...] = (
    {"time": "09:42", "text": "Research Pack v0.3 updated with current ISA guidance."},
    {"time": "09:18", "text": "Six demo opportunities ranked for founder review."},
    {"time": "Yesterday", "text": "Credit-content knowledge gap flagged for development."},
)


def opportunity_payload() -> list[dict[str, Any]]:
    """Return serialisable, explicitly demo-only topic opportunities."""

    return [asdict(opportunity) for opportunity in OPPORTUNITIES]


def content_payload() -> dict[str, Any]:
    """Return the serialisable, explicitly demo-only content workspace item."""

    return CONTENT_ITEM


def chat_reply(message: str) -> str:
    """Provide deterministic local replies; no model or external service is used."""

    normalized = message.lower()
    if "tomorrow" in normalized:
        return (
            "For tomorrow, I would prioritise the ISA allowance reset. It has the strongest "
            "combination of timeliness, UK viewer benefit and primary-source evidence."
        )
    if "why" in normalized and "recommend" in normalized:
        return (
            "The recommendation is driven by a 92 opportunity score: deadline proximity, "
            "clear viewer action and high-quality HMRC/GOV.UK evidence."
        )
    if "gap" in normalized and "credit" in normalized:
        return (
            "Demo knowledge map: credit utilisation, statement timing and credit-report myths "
            "are useful gaps. We have no published demo items in that cluster yet."
        )
    if "60k" in normalized:
        return (
            "For someone earning £60k, lead with the decision context: salary sacrifice can "
            "affect taxable income, but the content should explain trade-offs rather than give "
            "personalised advice."
        )
    return (
        "This is a local Conveyor demo. Try asking about tomorrow's topic, the recommendation, "
        "credit-content gaps, or making the £60k angle more relevant."
    )
