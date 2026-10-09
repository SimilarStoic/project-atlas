"""Test support: record founder-attested approvals for reference images used by test fixtures."""

from __future__ import annotations

CRITERIA = {
    "linework": "PASS",
    "palette": "PASS",
    "depth": "PASS",
    "shadow": "PASS",
    "texture": "PASS",
    "richness": "PASS",
}


def approve_reference_images(repository, *asset_ids: str) -> None:
    """Approve each image once (the image doubles as its own review sheet in tests)."""

    for asset_id in asset_ids:
        history = repository.list_plate_approvals(asset_id)
        if history and history[-1].decision == "approved":
            continue
        repository.record_visual_plate_decision(
            f"test-approval-{asset_id}-{len(history) + 1}",
            asset_id,
            "approved",
            "founder",
            "test fixture approval",
            contact_sheet_asset_id=asset_id,
            criteria=dict(CRITERIA),
        )
