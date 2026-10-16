"""Publication source credits projected from a production's approved claim provenance.

The credits come only from records Conveyor already keeps: the production run's VisualPlan ->
Script -> closed ScriptClaimSet -> each Claim's supporting ClaimEvidence -> Source. Nothing is
typed by hand and there is no parallel credit store. Missing attribution fails closed.
"""

from __future__ import annotations

from typing import Any

from project_atlas.publishing_state import digest

CREDITS_HEADING = "Sources:"
CREDITS_SCHEMA = "claim-provenance-credits-v1"


class SourceCreditError(ValueError):
    """A sourced claim lacks the attribution a publication must carry."""


def _year(value: str | None) -> str | None:
    if not isinstance(value, str) or len(value) < 4 or not value[:4].isdigit():
        return None
    return value[:4]


def source_credits(repository: Any, run_id: str) -> dict[str, Any]:
    """Credits for one production run: an ordered source list, its text block and digest."""

    run = repository.get_production_run(run_id)
    plan = repository.get_visual_plan(run.visual_plan_id)
    claim_set = repository.get_script_claim_set_for_script(plan.script_id)
    if claim_set is None:
        raise SourceCreditError(
            f"Script {plan.script_id} has no closed claim set, so its sources are unknown."
        )
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()
    for link in repository.list_script_claim_links(claim_set.id):
        rows = repository.connection.execute(
            "SELECT source_id FROM claim_evidence WHERE claim_id = ? AND stance = 'supports' "
            "ORDER BY source_id",
            (link.claim_id,),
        ).fetchall()
        if not rows:
            raise SourceCreditError(f"Claim {link.claim_id} has no supporting source.")
        for row in rows:
            source = repository.get_source(row["source_id"])
            missing = [
                name
                for name, value in (
                    ("title", source.title),
                    ("publisher", source.publisher),
                    ("url", source.url),
                    ("publication year", _year(source.publication_date)),
                )
                if not isinstance(value, str) or not value.strip()
            ]
            if missing:
                raise SourceCreditError(
                    f"Source {source.id} (claim {link.claim_id}) lacks required attribution: "
                    f"{', '.join(missing)}."
                )
            if source.id in seen:
                continue
            seen.add(source.id)
            sources.append(
                {
                    "source_id": source.id,
                    "author": (source.author or "").strip() or None,
                    "title": source.title.strip(),
                    "publisher": source.publisher.strip(),
                    "year": _year(source.publication_date),
                    "url": source.url.strip(),
                }
            )
    if not sources:
        raise SourceCreditError(f"Claim set {claim_set.id} declares no sourced claims.")
    lines = [CREDITS_HEADING]
    for item in sources:
        lead = f"{item['author']}. " if item["author"] else ""
        lines.append(
            f"- {lead}\"{item['title']}\". {item['publisher']}, {item['year']}. {item['url']}"
        )
    text = "\n".join(lines)
    if "<" in text or ">" in text:
        raise SourceCreditError("Source attribution contains characters YouTube rejects (< or >).")
    return {
        "schema": CREDITS_SCHEMA,
        "run_id": run_id,
        "script_claim_set_id": claim_set.id,
        "sources": sources,
        "text": text,
        "digest": digest({"sources": sources, "text": text}),
    }
