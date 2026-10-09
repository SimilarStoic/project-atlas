"""Migration 30: founder-attested decisions on visual reference images (plate approval gate).

A newly generated or imported image may become a member of a visual reference authority, or be
used as a reference by a new production run, only while its latest decision is ``approved`` for
its exact SHA-256. Decisions are append-only and sequential per image; the latest governs, so a
later ``withdrawn`` or ``rejected`` decision makes the image ineligible again. Images that existed
as references before this gate and carry no decision fall back to an exact-hash historical
allowlist. Decisions are founder-attested records citing a traceable founder authorization; they
are not cryptographically authenticated. Agent review findings are evidence, never the decision.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

DECISIONS = ("approved", "rejected", "withdrawn")
ATTESTATION = "founder-attested"
CRITERION_RESULTS = ("PASS", "FAIL")

# Reference images that were already authority members before the gate, by exact asset ID and
# SHA-256. A fallback only for images with no decision record: once any decision exists for an
# image, its latest decision governs (including withdrawal).
HISTORICAL_ALLOWLIST = {
    # Canonical repository references (src/project_atlas/visual_authorities.py, 2026-09-10).
    "asset-visual-authority-default-scene-language-v1": (
        "989e0da7b273a42f0bf8c229c1510b904902b1eef3336e626705966e6048ccb2"
    ),
    "asset-visual-authority-environment-home-v1": (
        "45a8fcf77d1ba6d1b85601e9eba9a05e0554df705d3399c083f23a7b523dba2a"
    ),
    "asset-visual-authority-environment-abstract-v1": (
        "c30a8e66321fe9b725d6646ca1639fc6b01e87da3035092a0765067eaf2458b5"
    ),
    "asset-visual-authority-composition-grammar-v1": (
        "c6f933eddf7394ff3d00708650f7c1fa1df2f29ff8011e7ae4858653dd1f45d8"
    ),
    "asset-visual-authority-composition-example-indoor-v1": (
        "dae3ca8f2cd035a686fdbc87458bf280120ef0bf4e53ebb39c9fd3e422d933a7"
    ),
    "asset-visual-authority-composition-example-abstract-v1": (
        "a5c7664ffcc40a6decdba0dc1a5c793d5850b6ddb975131a7395dc712329e427"
    ),
    "asset-visual-authority-special-break-frame-v1": (
        "c38e0af357b0beb35ded28e78739115a630ca68ea9f6249f37f5ff8dcbae185e"
    ),
    # Founder-approved room anchors (founder_approval in each authority's metadata).
    "asset-production-8-office-anchor-v1": (
        "19d1ac7a7a0400b592f2666d400d4a11f9ac9b081317019b934a92929998391a"
    ),
    "asset-production-8-storeroom-anchor-v1": (
        "296dfd01de89dd4bb105be3321cd27e64262992f6ca62a8a6c6ef765fb3489f2"
    ),
    "asset-4b30cc2631964e3ea9ea87985ba434fc": (
        "3d854b2f8f97b47882833f580caab27dd9ac6068ab3da9ed668eeb2f972a40d2"
    ),
    "asset-3888589e5e684985949ff716f6fbe5c6": (
        "6ee6def1bee66265e65615ebd759117807f11be985e104c3def3b0dc02f67453"
    ),
}

MIGRATION_30 = (
    30,
    (
        """
        CREATE TABLE visual_plate_approvals (
          id TEXT PRIMARY KEY,
          plate_asset_id TEXT NOT NULL,
          plate_sha256 TEXT NOT NULL CHECK (length(plate_sha256) = 64),
          sequence INTEGER NOT NULL CHECK (sequence >= 1),
          decision TEXT NOT NULL CHECK (decision IN ('approved', 'rejected', 'withdrawn')),
          contact_sheet_asset_id TEXT NULL,
          contact_sheet_sha256 TEXT NULL
            CHECK (contact_sheet_sha256 IS NULL OR length(contact_sheet_sha256) = 64),
          criteria_json TEXT NOT NULL,
          exceptions_json TEXT NOT NULL,
          founder_actor TEXT NOT NULL CHECK (length(trim(founder_actor)) > 0),
          decision_reference TEXT NOT NULL CHECK (length(trim(decision_reference)) > 0),
          attestation TEXT NOT NULL CHECK (attestation = 'founder-attested'),
          notes TEXT NOT NULL,
          record_digest TEXT NOT NULL CHECK (length(record_digest) = 64),
          created_at TEXT NOT NULL,
          UNIQUE (plate_asset_id, sequence),
          CHECK ((contact_sheet_asset_id IS NULL) = (contact_sheet_sha256 IS NULL)),
          CHECK (decision <> 'approved' OR contact_sheet_asset_id IS NOT NULL),
          FOREIGN KEY (plate_asset_id) REFERENCES assets(id) ON DELETE RESTRICT,
          FOREIGN KEY (contact_sheet_asset_id) REFERENCES assets(id) ON DELETE RESTRICT
        )
        """,
        "CREATE INDEX idx_visual_plate_approvals_plate "
        "ON visual_plate_approvals (plate_asset_id, sequence)",
        """
        CREATE TRIGGER visual_plate_approvals_plate_digest BEFORE INSERT
        ON visual_plate_approvals
        WHEN NEW.plate_sha256 IS NOT (SELECT content_digest FROM assets
                                      WHERE id = NEW.plate_asset_id)
        BEGIN SELECT RAISE(ABORT, 'plate digest does not match its asset'); END
        """,
        """
        CREATE TRIGGER visual_plate_approvals_sheet_digest BEFORE INSERT
        ON visual_plate_approvals
        WHEN NEW.contact_sheet_asset_id IS NOT NULL
          AND NEW.contact_sheet_sha256 IS NOT (SELECT content_digest FROM assets
                                               WHERE id = NEW.contact_sheet_asset_id)
        BEGIN SELECT RAISE(ABORT, 'contact sheet digest does not match its asset'); END
        """,
        """
        CREATE TRIGGER visual_plate_approvals_sequence BEFORE INSERT
        ON visual_plate_approvals
        WHEN NEW.sequence <> 1 + COALESCE((SELECT MAX(sequence) FROM visual_plate_approvals
                                           WHERE plate_asset_id = NEW.plate_asset_id), 0)
        BEGIN SELECT RAISE(ABORT, 'plate decisions are sequential'); END
        """,
        "CREATE TRIGGER visual_plate_approvals_immutable_update BEFORE UPDATE "
        "ON visual_plate_approvals "
        "BEGIN SELECT RAISE(ABORT, 'visual_plate_approvals is immutable'); END",
        "CREATE TRIGGER visual_plate_approvals_immutable_delete BEFORE DELETE "
        "ON visual_plate_approvals "
        "BEGIN SELECT RAISE(ABORT, 'visual_plate_approvals is immutable'); END",
    ),
)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class VisualPlateDecision:
    """One immutable founder-attested decision on one exact reference image."""

    id: str
    plate_asset_id: str
    plate_sha256: str
    sequence: int
    decision: str
    contact_sheet_asset_id: str | None
    contact_sheet_sha256: str | None
    criteria: dict[str, str]
    exceptions: list[Any]
    founder_actor: str
    decision_reference: str
    attestation: str
    notes: str
    record_digest: str
    created_at: str


class VisualReferenceApprovalMixin:
    """Record and evaluate founder-attested decisions on visual reference images."""

    def record_visual_plate_decision(
        self,
        decision_id: str,
        plate_asset_id: str,
        decision: str,
        founder_actor: str,
        decision_reference: str,
        *,
        contact_sheet_asset_id: str | None = None,
        criteria: dict[str, str] | None = None,
        exceptions: list[Any] | None = None,
        notes: str = "",
    ) -> VisualPlateDecision:
        """Append the next decision for one image; earlier decisions stay as history.

        An ``approved`` decision must be bound to a review contact sheet asset and a
        per-criterion PASS/FAIL record. ``decision_reference`` cites the founder's own
        authorization (message and date); review findings are evidence only.
        """

        for label, value in (
            ("decision ID", decision_id),
            ("founder actor", founder_actor),
            ("decision reference", decision_reference),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Plate decision {label} must be non-empty text.")
        if decision not in DECISIONS:
            raise ValueError(f"Plate decision must be one of {', '.join(DECISIONS)}.")
        if not isinstance(notes, str):
            raise ValueError("Plate decision notes must be text.")
        criteria = {} if criteria is None else criteria
        exceptions = [] if exceptions is None else exceptions
        if not isinstance(criteria, dict) or any(
            not isinstance(key, str) or not key.strip() or value not in CRITERION_RESULTS
            for key, value in criteria.items()
        ):
            raise ValueError("Plate criteria must map criterion names to PASS or FAIL.")
        if not isinstance(exceptions, list):
            raise ValueError("Plate exceptions must be a list.")
        if decision == "approved" and (contact_sheet_asset_id is None or not criteria):
            raise ValueError(
                "An approved plate decision requires its review contact sheet and criteria."
            )
        plate = self.get_asset(plate_asset_id)
        if plate.content_digest is None:
            raise ValueError("A plate decision requires an immutable plate digest.")
        sheet_digest = None
        if contact_sheet_asset_id is not None:
            sheet = self.get_asset(contact_sheet_asset_id)
            if sheet.content_digest is None:
                raise ValueError("A plate decision requires an immutable contact sheet digest.")
            sheet_digest = sheet.content_digest
        sequence = 1 + len(self.list_plate_approvals(plate.id))
        record = {
            "id": decision_id.strip(),
            "plate_asset_id": plate.id,
            "plate_sha256": plate.content_digest,
            "sequence": sequence,
            "decision": decision,
            "contact_sheet_asset_id": contact_sheet_asset_id,
            "contact_sheet_sha256": sheet_digest,
            "criteria": criteria,
            "exceptions": exceptions,
            "founder_actor": founder_actor.strip(),
            "decision_reference": decision_reference.strip(),
            "attestation": ATTESTATION,
            "notes": notes,
        }
        with self.connection:
            self.connection.execute(
                "INSERT INTO visual_plate_approvals (id, plate_asset_id, plate_sha256, sequence, "
                "decision, contact_sheet_asset_id, contact_sheet_sha256, criteria_json, "
                "exceptions_json, founder_actor, decision_reference, attestation, notes, "
                "record_digest, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record["id"],
                    record["plate_asset_id"],
                    record["plate_sha256"],
                    sequence,
                    decision,
                    contact_sheet_asset_id,
                    sheet_digest,
                    _canonical(criteria),
                    _canonical(exceptions),
                    record["founder_actor"],
                    record["decision_reference"],
                    ATTESTATION,
                    notes,
                    sha256(_canonical(record).encode()).hexdigest(),
                    _now(),
                ),
            )
        return self.list_plate_approvals(plate.id)[-1]

    def list_plate_approvals(self, plate_asset_id: str | None = None) -> list[VisualPlateDecision]:
        """Read-only decision history, oldest first (optionally for one image)."""

        if plate_asset_id is None:
            rows = self.connection.execute(
                "SELECT * FROM visual_plate_approvals ORDER BY plate_asset_id, sequence"
            )
        else:
            rows = self.connection.execute(
                "SELECT * FROM visual_plate_approvals WHERE plate_asset_id = ? ORDER BY sequence",
                (plate_asset_id,),
            )
        return [
            VisualPlateDecision(
                row["id"],
                row["plate_asset_id"],
                row["plate_sha256"],
                row["sequence"],
                row["decision"],
                row["contact_sheet_asset_id"],
                row["contact_sheet_sha256"],
                json.loads(row["criteria_json"]),
                json.loads(row["exceptions_json"]),
                row["founder_actor"],
                row["decision_reference"],
                row["attestation"],
                row["notes"],
                row["record_digest"],
                row["created_at"],
            )
            for row in rows
        ]

    def reference_image_eligibility(self, asset_id: str) -> dict[str, Any]:
        """Whether one image may serve as a visual reference now, and on what basis."""

        asset = self.get_asset(asset_id)
        history = self.list_plate_approvals(asset.id)
        if history:
            latest = history[-1]
            eligible = latest.decision == "approved" and latest.plate_sha256 == (
                asset.content_digest
            )
            return {
                "asset_id": asset.id,
                "eligible": eligible,
                "basis": "founder_decision",
                "decision_id": latest.id,
                "decision": latest.decision,
            }
        allowlisted = HISTORICAL_ALLOWLIST.get(asset.id)
        eligible = allowlisted is not None and allowlisted == asset.content_digest
        return {
            "asset_id": asset.id,
            "eligible": eligible,
            "basis": "historical_allowlist" if eligible else "no_eligible_approval",
            "decision_id": None,
            "decision": None,
        }

    def require_eligible_reference_images(self, asset_ids: list[str], context: str) -> None:
        """Fail closed unless every image has an eligible approval."""

        refused = [
            item
            for item in (self.reference_image_eligibility(asset_id) for asset_id in asset_ids)
            if not item["eligible"]
        ]
        if refused:
            detail = ", ".join(
                f"{item['asset_id']} ({item['decision'] or item['basis']})" for item in refused
            )
            raise ValueError(
                f"{context}: reference images without an eligible founder approval: {detail}."
            )
