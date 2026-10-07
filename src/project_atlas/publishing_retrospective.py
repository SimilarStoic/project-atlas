"""One-time recorder for founder-attested retrospective publications (P8 and P9).

The founder released Productions 8 and 9 manually in YouTube Studio, outside Conveyor. This
module records those already-public releases as truthful, founder-attested runtime provenance:
one package, one ``attest_external`` decision, one upload and one release operation (each a
single ``succeeded`` founder event), one founder-supplied platform identity and one attested
receipt per release. Nothing here contacts YouTube or any other provider, and nothing here
authorizes a new upload, observation or release.

Writes are all-or-nothing per release, idempotent on an exact rerun, and fail closed on any
partial or conflicting existing state. The live command takes a verified SQLite backup first.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from project_atlas.publishing_schema import (
    FOUNDER_ATTESTATION_SOURCE,
    RETROSPECTIVE_INTENT_SCHEMA,
    RETROSPECTIVE_RELEASE_POLICY,
)
from project_atlas.publishing_state import (
    TARGET_CHANNEL,
    canonical_json,
    digest,
    package_identity_digest,
    retrospective_release_week,
    safe_evidence,
    stamp,
)

PILOT_KEY = "similarstoic-youtube-external-reconciliation-v1"
ATTESTATION_REFERENCE = "docs/CONVEYOR_CURRENT_STATE.md#public-releases"
_ATTESTED_EVENT = {
    "method": "founder-attestation",
    "retrospective": True,
    "conveyor_reserved": False,
    "conveyor_dispatched": False,
}
# The preserved P9 publication files, as recorded in production-9/publish/SHA256-MANIFEST.txt.
P9_METADATA_SHA256 = {
    "title.txt": "7a64165132104aa1746e7a61717cf38336720fe54c6574a3bb7dd30de06f6dc1",
    "description.txt": "9f9e673d63d00303f5527d4c9a61c359c313c59fa222e95ad01e2e8cccf5fe77",
}

P8_TITLE = 'Your employer is offering "free money". Are you taking all of it?'
P8_DESCRIPTION = "\n".join(
    (
        "Workplace pensions in 30 seconds: what goes in, what your employer pays, and what to "
        "check on your payslip. UK rules, 2026–27.",
        "",
        "Sources:",
        "GOV.UK – Workplace pensions: what you, your employer and the government pay",
        "https://www.gov.uk/workplace-pensions/what-you-your-employer-and-the-government-pay",
        "",
        "The Pensions Regulator – Minimum contribution increases planned by law",
        "https://www.thepensionsregulator.gov.uk/en/business-advisers/automatic-enrolment-guide-"
        "for-business-advisers/minimum-contribution-increases-planned-by-law-phasing",
        "",
        "The Pensions Regulator – Earnings thresholds",
        "https://www.thepensionsregulator.gov.uk/en/employers/new-employers/im-an-employer-who-"
        "has-to-provide-a-pension/declare-your-compliance/ongoing-duties-for-employers/"
        "earnings-thresholds",
        "",
        "GOV.UK – Pension tax relief",
        "https://www.gov.uk/tax-on-your-private-pension/pension-tax-relief",
        "",
        "GOV.UK – Leaving your workplace pension scheme",
        "https://www.gov.uk/workplace-pensions/if-you-want-to-leave-your-workplace-pension-scheme",
        "",
        "MoneyHelper – What happens if you leave a job or opt out",
        "https://www.moneyhelper.org.uk/en/pensions-and-retirement/building-your-retirement-pot/"
        "what-happens-to-your-pension-money-and-benefits-when-you-leave-your-pension",
        "",
        "MoneyHelper – Contribution matching",
        "https://www.moneyhelper.org.uk/en/pensions-and-retirement/building-your-retirement-pot/"
        "contribution-matching",
        "",
        "MoneyHelper – How pension auto-enrolment works",
        "https://www.moneyhelper.org.uk/en/pensions-and-retirement/pensions-basics/"
        "automatic-enrolment-an-introduction",
        "",
        "General information only, not financial advice. Rules can change, so check your own "
        "scheme.",
        "",
        "Narration voice is AI-generated.",
        "",
        "#UKPersonalFinance #WorkplacePension #pensions",
    )
)


class RetrospectiveRecordError(ValueError):
    """The retrospective release cannot be recorded truthfully; nothing was written."""


@dataclass(frozen=True)
class RetrospectiveRelease:
    label: str
    production_run_id: str
    artifact_id: str
    artifact_sha256: str
    remote_id: str
    public_url: str
    timing: dict[str, Any]
    expected_week: str
    pilot_slot: int
    title: str
    description: str
    metadata_provenance: dict[str, Any]


def p8_release() -> RetrospectiveRelease:
    return RetrospectiveRelease(
        "P8",
        "production-8-attempt-2",
        "production-8-attempt-2-artifact-2",
        "6f2b248a14002efc1a2e39ba930efb442a5b7a2eb8e293e6924334379a95c000",
        "MbVZPnX_b_s",
        "https://youtube.com/shorts/MbVZPnX_b_s",
        {
            "mode": "retrospective",
            "timezone": "Europe/London",
            "precision": "second",
            "public_at": "2026-10-04T13:57:41+01:00",
        },
        "2026-W40",
        1,
        P8_TITLE,
        P8_DESCRIPTION,
        {
            "metadata_source": "founder-pasted from YouTube Studio 2026-10-07",
            "metadata_formatting": "line breaks reconstructed from chat-normalized paste",
        },
    )


def p9_release(publish_dir: Path) -> RetrospectiveRelease:
    """P9 metadata comes only from the preserved files, after their recorded SHA-256 checks."""

    text = {}
    for name, expected in P9_METADATA_SHA256.items():
        content = (Path(publish_dir) / name).read_bytes()
        if sha256(content).hexdigest() != expected:
            raise RetrospectiveRecordError(f"P9 {name} does not match its recorded SHA-256.")
        decoded = content.decode("utf-8")
        if not decoded.endswith("\n") or decoded.endswith("\n\n"):
            raise RetrospectiveRecordError(f"P9 {name} lacks its single file line terminator.")
        text[name] = decoded[:-1]
    return RetrospectiveRelease(
        "P9",
        "production-9-attempt-2",
        "production-9-attempt-2-artifact-3",
        "4c0a8bb23cff0ba8487f0ca0aa92950d60c100e75b63f463b1f6ea26f6b2132f",
        "Dd76ERbxg_w",
        "https://youtube.com/shorts/Dd76ERbxg_w",
        {
            "mode": "retrospective",
            "timezone": "Europe/London",
            "precision": "day",
            "public_date": "2026-10-05",
        },
        "2026-W41",
        2,
        text["title.txt"],
        text["description.txt"],
        {
            "metadata_source": "production-9/publish/title.txt and description.txt",
            "metadata_file_sha256": dict(P9_METADATA_SHA256),
            "metadata_formatting": "each file's single trailing line terminator removed",
        },
    )


def verify_preconditions(repository: Any, media_root: Path, release: RetrospectiveRelease) -> dict:
    """Fail closed unless the exact founder-accepted current render is the attested artifact."""

    connection = repository.connection
    latest = connection.execute(
        "SELECT status FROM production_run_events WHERE production_run_id = ? "
        "ORDER BY sequence DESC LIMIT 1",
        (release.production_run_id,),
    ).fetchone()
    if latest is None or latest["status"] != "founder_accepted":
        raise RetrospectiveRecordError(f"{release.label}: the production is not founder_accepted.")
    founder = connection.execute(
        "SELECT id, outcome FROM production_founder_reviews WHERE production_run_id = ?",
        (release.production_run_id,),
    ).fetchall()
    if len(founder) != 1 or founder[0]["outcome"] != "accepted":
        raise RetrospectiveRecordError(f"{release.label}: no accepted founder review.")
    reviews = connection.execute(
        "SELECT id, outcome, final_media_artifact_id FROM production_qa_reviews "
        "WHERE production_run_id = ? AND scope = 'whole_video' ORDER BY created_at, id",
        (release.production_run_id,),
    ).fetchall()
    if (
        not reviews
        or reviews[-1]["outcome"] != "passed"
        or reviews[-1]["final_media_artifact_id"] != release.artifact_id
    ):
        raise RetrospectiveRecordError(
            f"{release.label}: the latest whole-video QA is not a pass of the attested artifact."
        )
    renders = connection.execute(
        "SELECT id, final_media_artifact_id FROM production_run_evidence "
        "WHERE production_run_id = ? AND evidence_type = 'render'",
        (release.production_run_id,),
    ).fetchall()
    current = max(renders, key=lambda row: int(row["id"].rsplit(":", 1)[1]), default=None)
    if current is None or current["final_media_artifact_id"] != release.artifact_id:
        raise RetrospectiveRecordError(f"{release.label}: the artifact is not the current render.")
    artifact = connection.execute(
        "SELECT content_digest, storage_path FROM final_media_artifacts WHERE id = ?",
        (release.artifact_id,),
    ).fetchone()
    if artifact is None or artifact["content_digest"] != release.artifact_sha256:
        raise RetrospectiveRecordError(f"{release.label}: stored artifact SHA-256 differs.")
    stored = Path(media_root) / artifact["storage_path"]
    if not stored.is_file() or sha256(stored.read_bytes()).hexdigest() != release.artifact_sha256:
        raise RetrospectiveRecordError(f"{release.label}: managed artifact bytes differ.")
    if retrospective_release_week(release.timing) != release.expected_week:
        raise RetrospectiveRecordError(f"{release.label}: attested time is not in its week.")
    return {
        "founder_review_id": founder[0]["id"],
        "whole_video_review_id": reviews[-1]["id"],
        "render_evidence_id": current["id"],
    }


def _rows(release: RetrospectiveRelease, lineage: dict, founder_actor: str) -> dict[str, dict]:
    """Every row this release needs, keyed by table, without timestamps."""

    package_id = f"publishing-package-{PILOT_KEY}-slot-{release.pilot_slot}-v1"
    manifest = {
        "release_policy": RETROSPECTIVE_RELEASE_POLICY,
        "pilot_slot": release.pilot_slot,
        "transfer_route": "manual",
        "release_route": "manual",
        "publication_timing": release.timing,
        "route": "youtube_studio",
        "remote_id": release.remote_id,
        "public_url": release.public_url,
        "title": release.title,
        "description": release.description,
        **release.metadata_provenance,
        "production_run_id": release.production_run_id,
        "founder_review_id": lineage["founder_review_id"],
        "whole_video_review_id": lineage["whole_video_review_id"],
        "attestation_reference": ATTESTATION_REFERENCE,
    }
    safe_evidence(manifest)
    package_digest = package_identity_digest(
        PILOT_KEY,
        release.pilot_slot,
        1,
        None,
        release.artifact_id,
        release.artifact_sha256,
        TARGET_CHANNEL,
        manifest,
    )
    decision_id = f"{package_id}:founder-attestation"
    timing_key = "public_at" if release.timing["precision"] == "second" else "public_date"
    intents = {
        "upload": {
            "schema": RETROSPECTIVE_INTENT_SCHEMA,
            "action": "founder uploaded the exact artifact in YouTube Studio",
            "route": "youtube_studio",
            "artifact_digest": release.artifact_sha256,
            "upload_time": "not recorded",
        },
        "release": {
            "schema": RETROSPECTIVE_INTENT_SCHEMA,
            "action": "the video became public through YouTube Studio",
            "route": "youtube_studio",
            "pilot_slot": release.pilot_slot,
            timing_key: release.timing[timing_key],
            "precision": release.timing["precision"],
        },
    }
    operations, events = {}, {}
    for kind, intent in intents.items():
        key = digest(
            {
                "schema": "retrospective-publication-operation-v1",
                "package_digest": package_digest,
                "gate_decision_id": decision_id,
                "action_kind": kind,
                "execution_mode": "manual",
                "intent": intent,
            }
        )
        operation_id = f"publication-operation-{key}"
        operations[operation_id] = {
            "operation_key": key,
            "package_id": package_id,
            "gate_decision_id": decision_id,
            "action_kind": kind,
            "execution_mode": "manual",
            "intent_json": canonical_json(intent),
            "intent_digest": digest(intent),
        }
        events[f"{operation_id}:1"] = {
            "operation_id": operation_id,
            "sequence": 1,
            "kind": "succeeded",
            "actor": founder_actor,
            "evidence_json": canonical_json(_ATTESTED_EVENT),
            "provider_evidence_json": None,
            "provider_evidence_digest": None,
            "provider_purged_at": None,
        }
    upload_id, release_id = list(operations)
    publication_id = f"platform-publication-{operations[upload_id]['operation_key']}"
    receipt_facts = {
        "publication_id": publication_id,
        "package_digest": package_digest,
        "gate_decision_id": decision_id,
        "release_operation_key": operations[release_id]["operation_key"],
        "public_at": release.timing[timing_key],
        "timestamp_source": FOUNDER_ATTESTATION_SOURCE,
        "timestamp_precision": release.timing["precision"],
        "execution_mode": "manual",
        "remote_id": release.remote_id,
    }
    return {
        "publishing_packages": {
            package_id: {
                "pilot_key": PILOT_KEY,
                "pilot_slot": release.pilot_slot,
                "version": 1,
                "predecessor_id": None,
                "final_media_artifact_id": release.artifact_id,
                "artifact_digest": release.artifact_sha256,
                "platform": "youtube",
                "channel_id": TARGET_CHANNEL,
                "pilot_week": release.expected_week,
                "manifest_json": canonical_json(manifest),
                "package_digest": package_digest,
            }
        },
        "publication_gate_decisions": {
            decision_id: {
                "package_id": package_id,
                "package_digest": package_digest,
                "sequence": 1,
                "decision": "attest_external",
                "founder_actor": founder_actor,
                "transfer_route": None,
                "release_route": None,
                "timing_json": canonical_json(release.timing),
                "comment": f"Founder attests this release happened outside Conveyor; "
                f"see {ATTESTATION_REFERENCE}.",
            }
        },
        "publication_operations": operations,
        "publication_operation_events": events,
        "platform_publications": {
            publication_id: {
                "package_id": package_id,
                "upload_operation_id": upload_id,
                "platform": "youtube",
                "channel_id": TARGET_CHANNEL,
                "remote_id": release.remote_id,
                "binding_digest": digest(
                    {
                        "remote_id": release.remote_id,
                        "channel_id": TARGET_CHANNEL,
                        "package_digest": package_digest,
                        "operation_key": operations[upload_id]["operation_key"],
                        "evidence": {"method": "founder-attestation"},
                    }
                ),
                "identity_source": "founder_manual",
                "provider_purged_at": None,
            }
        },
        "publication_receipts": {
            f"publication-receipt-{PILOT_KEY}-slot-{release.pilot_slot}": {
                "publication_id": publication_id,
                "package_id": package_id,
                "gate_decision_id": decision_id,
                "release_operation_id": release_id,
                "public_status_id": None,
                "execution_mode": "manual",
                "channel_id": TARGET_CHANNEL,
                "pilot_week": release.expected_week,
                "public_at": release.timing[timing_key],
                "timestamp_source": FOUNDER_ATTESTATION_SOURCE,
                "timestamp_precision": release.timing["precision"],
                "first_public_observed_at": None,
                "receipt_digest": digest(receipt_facts),
                "provider_purged_at": None,
            }
        },
    }


# Insertion order respects foreign keys; timestamps are the only columns not compared.
_TABLE_ORDER = (
    "publishing_packages",
    "publication_gate_decisions",
    "publication_operations",
    "publication_operation_events",
    "platform_publications",
    "publication_receipts",
)
_TIMESTAMPS = {
    "publishing_packages": ("created_at",),
    "publication_gate_decisions": ("created_at",),
    "publication_operations": ("created_at",),
    "publication_operation_events": ("created_at",),
    "platform_publications": ("identified_at",),
    "publication_receipts": ("created_at",),
}


def _week_occupied(connection: sqlite3.Connection, week: str) -> bool:
    """Any non-failed public operation or receipt already holds this channel ISO week."""

    if connection.execute(
        "SELECT 1 FROM publication_receipts WHERE channel_id = ? AND pilot_week = ?",
        (TARGET_CHANNEL, week),
    ).fetchone():
        return True
    rows = connection.execute(
        "SELECT o.id, o.action_kind, o.intent_json FROM publication_operations o "
        "JOIN publishing_packages p ON p.id = o.package_id "
        "WHERE p.channel_id = ? AND p.pilot_week = ?",
        (TARGET_CHANNEL, week),
    ).fetchall()
    for row in rows:
        last = connection.execute(
            "SELECT kind, evidence_json FROM publication_operation_events "
            "WHERE operation_id = ? ORDER BY sequence DESC LIMIT 1",
            (row["id"],),
        ).fetchone()
        failed = last is not None and (
            last["kind"] == "failed"
            or (
                last["kind"] == "reconciled"
                and json.loads(last["evidence_json"]).get("resolution") == "failed"
            )
        )
        public = row["action_kind"] == "release" or json.loads(row["intent_json"]).get(
            "privacy"
        ) in {"public", "unlisted"}
        if public and not failed:
            return True
    return False


def record_release(
    repository: Any,
    media_root: Path,
    release: RetrospectiveRelease,
    founder_actor: str = "founder",
) -> dict[str, Any]:
    """Record one founder-attested release atomically; an exact rerun writes nothing."""

    lineage = verify_preconditions(repository, media_root, release)
    expected = _rows(release, lineage, founder_actor)
    connection = repository.connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        present = {}
        for table in _TABLE_ORDER:
            for row_id, values in expected[table].items():
                row = connection.execute(
                    f"SELECT * FROM {table} WHERE id = ?", (row_id,)
                ).fetchone()
                if row is not None:
                    record = dict(zip(row.keys(), tuple(row), strict=True))
                    actual = {k: v for k, v in record.items() if k not in _TIMESTAMPS[table]}
                    actual.pop("id")
                    if actual != values:
                        raise RetrospectiveRecordError(
                            f"{release.label}: existing {table} row {row_id} conflicts with the "
                            "attested facts."
                        )
                present[(table, row_id)] = row is not None
        if all(present.values()):
            connection.rollback()
            return {"release": release.label, "written": 0, "state": "already recorded"}
        if any(present.values()):
            raise RetrospectiveRecordError(
                f"{release.label}: partial retrospective state exists; refusing to complete it."
            )
        if _week_occupied(connection, release.expected_week):
            raise RetrospectiveRecordError(
                f"{release.label}: {release.expected_week} is already occupied on this channel."
            )
        recorded_at = stamp()
        written = 0
        for table in _TABLE_ORDER:
            for row_id, values in expected[table].items():
                row = {"id": row_id, **values}
                for column in _TIMESTAMPS[table]:
                    row[column] = recorded_at
                columns = ", ".join(row)
                marks = ", ".join("?" for _ in row)
                connection.execute(
                    f"INSERT INTO {table} ({columns}) VALUES ({marks})", tuple(row.values())
                )
                written += 1
    except BaseException:
        connection.rollback()
        raise
    connection.commit()
    return {
        "release": release.label,
        "written": written,
        "state": "recorded",
        "rows": {table: sorted(expected[table]) for table in _TABLE_ORDER},
    }


# --- Live command: verified backup first, then migration 29 and the two records ---------------


def _table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    names = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        )
    ]
    return {
        name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in names
    }


def verified_backup(database: Path, backup_root: Path) -> dict[str, Any]:
    """SQLite backup-API copy with integrity, foreign-key and row-count verification."""

    database = Path(database)
    sidecars = sorted(path.name for path in database.parent.glob(f"{database.name}-*"))
    if sidecars:
        raise RetrospectiveRecordError(f"Refusing: SQLite sidecar files present {sidecars}.")
    folder = Path(backup_root) / (
        f"pre-migration-29-retrospective-publications-{datetime.now(UTC):%Y%m%d-%H%M%S}"
    )
    folder.mkdir(parents=True)
    target = folder / database.name
    source = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        copy = sqlite3.connect(target)
        with copy:
            source.backup(copy)
        copy.close()
        check = sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True)
        try:
            integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
            violations = len(check.execute("PRAGMA foreign_key_check").fetchall())
            same = _table_counts(source) == _table_counts(check)
        finally:
            check.close()
    finally:
        source.close()
    if integrity != "ok" or violations or not same:
        raise RetrospectiveRecordError(
            f"Backup verification failed (integrity={integrity}, fk={violations}, counts={same})."
        )
    return {
        "backup": str(target),
        "backup_sha256": sha256(target.read_bytes()).hexdigest(),
        "integrity": integrity,
        "foreign_key_violations": violations,
        "row_counts_match": same,
    }


def _record_all(database: Path, media_root: Path, publish_dir: Path, actor: str) -> list[dict]:
    from project_atlas.persistence import AtlasRepository

    repository = AtlasRepository(database)  # Applies migration 29 if the database lacks it.
    try:
        results = [
            record_release(repository, media_root, release, actor)
            for release in (p8_release(), p9_release(publish_dir))
        ]
        if repository.connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or (
            repository.connection.execute("PRAGMA foreign_key_check").fetchall()
        ):
            raise RetrospectiveRecordError("Post-record integrity or foreign-key check failed.")
        return results
    finally:
        repository.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m project_atlas.publishing_retrospective",
        description="Record the founder-attested P8/P9 releases (no provider access).",
    )
    parser.add_argument("command", choices=["record"])
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--media-root", required=True, type=Path)
    parser.add_argument("--p9-publish-dir", required=True, type=Path)
    parser.add_argument("--founder-actor", default="founder")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="rehearse on a temporary copy")
    mode.add_argument("--backup-root", type=Path, help="live: verified backup destination")
    args = parser.parse_args(argv)
    if args.dry_run:
        scratch = Path(tempfile.mkdtemp(prefix="retrospective-rehearsal-"))
        try:
            backup = verified_backup(args.db, scratch)
            rehearsal = Path(backup["backup"])
            results = _record_all(
                rehearsal, args.media_root, args.p9_publish_dir, args.founder_actor
            )
            rerun = _record_all(rehearsal, args.media_root, args.p9_publish_dir, args.founder_actor)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        report = {"mode": "dry-run", "results": results, "rerun": rerun}
    else:
        backup = verified_backup(args.db, args.backup_root)
        results = _record_all(args.db, args.media_root, args.p9_publish_dir, args.founder_actor)
        report = {"mode": "live", "backup": backup, "results": results}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
