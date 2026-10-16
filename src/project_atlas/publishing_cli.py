"""Founder-gated on-demand publishing commands.

    python -m project_atlas.publishing_cli <command> ...

``status`` reads the database with ``mode=ro``. Every live command (``prepare``, ``approve``,
``reconcile-scheduled``) refuses unless the database SHA-256 equals ``--expect-db-sha256``,
rehearses on a temporary copy first (no YouTube call: the observation adapter is blocked, so a
rehearsal validates preconditions and wiring only), then takes a verified backup and runs.
``--dry-run`` stops after the rehearsal.

The publication itself is not a CLI command: the founder confirms the exact scheduled upload on
the loopback YouTube upload screen, and that confirmation is the publication authorization.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from project_atlas.production_backup import database_sha256, verified_backup
from project_atlas.publishing_credits import SourceCreditError, source_credits
from project_atlas.publishing_state import ON_DEMAND_SERIES, ON_DEMAND_TIMING

REHEARSAL_NOTE = (
    "Rehearsal on a temporary copy: it validates preconditions and wiring only; no YouTube call "
    "was made."
)


class CliError(RuntimeError):
    """A refused operation; the runtime was not changed."""


class RehearsalObservationBlocked(RuntimeError):
    """The rehearsal reached the point where a real run would observe YouTube."""


class _BlockedAdapter:
    """Stands in for YouTube during rehearsals: every capability refuses."""

    def __getattr__(self, name: str) -> Any:
        def refuse(*_args: Any, **_kwargs: Any) -> Any:
            raise RehearsalObservationBlocked(f"rehearsal: a live run would call YouTube ({name})")

        return refuse

    def authenticated_channel(self) -> str:
        from project_atlas.publishing_state import TARGET_CHANNEL

        return TARGET_CHANNEL


def _paths(args: argparse.Namespace) -> tuple[Path, Path]:
    db = Path(args.db or os.environ.get("ATLAS_DB_PATH", ""))
    media = Path(args.media or os.environ.get("ATLAS_MEDIA_STORAGE_ROOT", ""))
    if not str(db) or not db.is_file() or not str(media) or not media.is_dir():
        raise CliError("Database or media path missing; dot-source set_conveyor_environment.ps1.")
    return db, media


def _service(db: Path, media: Path, adapter: Any) -> Any:
    from project_atlas.media import LocalMediaStorage
    from project_atlas.persistence import AtlasRepository
    from project_atlas.publishing import PublishingService

    repository = AtlasRepository(db)
    return PublishingService(repository, LocalMediaStorage(media), adapter)


@contextlib.contextmanager
def _rehearsal(db: Path, media: Path) -> Iterator[Any]:
    root = Path(tempfile.mkdtemp(prefix="conveyor-publishing-rehearsal-"))
    try:
        source = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
        try:
            copy = sqlite3.connect(root / "conveyor.db")
            with copy:
                source.backup(copy)
            copy.close()
        finally:
            source.close()
        shutil.copytree(media / "final", root / "media" / "final", dirs_exist_ok=True)
        service = _service(root / "conveyor.db", root / "media", _BlockedAdapter())
        try:
            yield service
        finally:
            service.repository.close()
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _live(args: argparse.Namespace, label: str, operation, live_adapter=None) -> dict[str, Any]:
    db, media = _paths(args)
    actual = database_sha256(db)
    if actual != args.expect_db_sha256:
        raise CliError(f"Database SHA-256 is {actual}, not {args.expect_db_sha256}; unchanged.")
    report: dict[str, Any] = {"command": label, "db_sha256_before": actual}
    with _rehearsal(db, media) as service:
        try:
            result = operation(service)
            report["rehearsal"] = {"note": REHEARSAL_NOTE, "error": None, "result": result}
        except RehearsalObservationBlocked as blocked:
            report["rehearsal"] = {
                "note": REHEARSAL_NOTE,
                "error": None,
                "stopped_at": str(blocked),
            }
        except Exception as error:  # noqa: BLE001 - reported, nothing live has run
            report["rehearsal"] = {
                "note": REHEARSAL_NOTE,
                "error": f"{type(error).__name__}: {error}",
            }
            report["mode"] = "refused-by-rehearsal"
            return report
    if args.dry_run:
        report["mode"] = "dry-run"
        return report
    report["backup"] = verified_backup(db, Path(args.backup_root), f"pre-publishing-{label}")
    if database_sha256(db) != actual:
        raise CliError("The database changed during the backup; nothing was written.")
    service = _service(db, media, live_adapter() if live_adapter else _BlockedAdapter())
    try:
        report["live"] = {"result": operation(service)}
    finally:
        service.repository.close()
    report["mode"] = "live"
    report["db_sha256_after"] = database_sha256(db)
    return report


def cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    db, _media = _paths(args)
    connection = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        migration = connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        packages = [
            dict(row)
            for row in connection.execute(
                "SELECT id, pilot_slot, version, final_media_artifact_id, artifact_digest, "
                "package_digest FROM publishing_packages WHERE pilot_key = ? ORDER BY pilot_slot",
                (ON_DEMAND_SERIES,),
            )
        ]
        for package in packages:
            package["decisions"] = [
                dict(row)
                for row in connection.execute(
                    "SELECT id, sequence, decision FROM publication_gate_decisions "
                    "WHERE package_id = ? ORDER BY sequence",
                    (package["id"],),
                )
            ]
            package["operations"] = [
                dict(row)
                for row in connection.execute(
                    "SELECT o.id, o.action_kind, (SELECT kind FROM publication_operation_events e "
                    "WHERE e.operation_id = o.id ORDER BY sequence DESC LIMIT 1) AS last_event "
                    "FROM publication_operations o WHERE o.package_id = ?",
                    (package["id"],),
                )
            ]
            package["receipts"] = [
                dict(row)
                for row in connection.execute(
                    "SELECT id, public_at FROM publication_receipts WHERE package_id = ?",
                    (package["id"],),
                )
            ]
    finally:
        connection.close()
    return {"db_sha256": database_sha256(db), "schema_version": migration, "on_demand": packages}


def _manifest(service: Any, artifact_id: str, slot: int, metadata: dict[str, Any]) -> dict:
    run_id = service.founder_accepted_run(artifact_id)
    credits = source_credits(service.repository, run_id)
    body = metadata.get("description_body")
    if not isinstance(body, str) or not body.strip():
        raise CliError("metadata.description_body is required.")
    allowed = {
        "title",
        "description_body",
        "tags",
        "language",
        "category",
        "caption_artifact",
        "cover_choice",
        "compliance",
        "audience",
    }
    if set(metadata) - allowed:
        raise CliError(f"Unsupported metadata fields: {sorted(set(metadata) - allowed)}.")
    return {
        "title": metadata["title"],
        "description": body.rstrip() + "\n\n" + credits["text"],
        "tags": metadata.get("tags", []),
        "language": metadata["language"],
        "category": metadata.get("category"),
        "caption_artifact": metadata["caption_artifact"],
        "cover_choice": metadata["cover_choice"],
        "compliance": metadata["compliance"],
        "audience": metadata["audience"],
        "private_first": True,
        "transfer_route": "api",
        "release_route": "api",
        "publication_timing": dict(ON_DEMAND_TIMING),
        "pilot_slot": slot,
    }


def cmd_prepare(args: argparse.Namespace) -> dict[str, Any]:
    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))

    def operation(service: Any) -> dict[str, Any]:
        manifest = _manifest(service, args.artifact, args.slot, metadata)
        package = service.prepare_package(
            args.package_id, ON_DEMAND_SERIES, args.slot, 1, args.artifact, manifest
        )
        return {
            "package_id": package.id,
            "package_digest": package.package_digest,
            "artifact_digest": package.artifact_digest,
            "source_credits": package.manifest["source_credits"]["text"],
        }

    return _live(args, f"prepare-{args.package_id}", operation)


def cmd_approve(args: argparse.Namespace) -> dict[str, Any]:
    def operation(service: Any) -> dict[str, Any]:
        package = service.repository.get_publishing_package(args.package_id)
        if package.package_digest != args.package_digest:
            raise CliError("The package digest differs from the one the founder approved.")
        decision = service.approve_package(
            args.decision_id, args.package_id, args.founder_actor, args.comment
        )
        return {"decision_id": decision.id, "package_digest": decision.package_digest}

    return _live(args, f"approve-{args.package_id}", operation)


def cmd_reconcile(args: argparse.Namespace) -> dict[str, Any]:
    def adapter():
        from project_atlas.youtube_adapter import YouTubeReadOnlyObservationAdapter
        from project_atlas.youtube_consent import ConsentRegistry, YouTubeGovernance

        db, _media = _paths(args)
        root = Path(__file__).resolve().parents[2]
        from project_atlas.persistence import AtlasRepository

        governance = YouTubeGovernance(
            ConsentRegistry(Path(args.consent_state), root), AtlasRepository(db)
        )
        return YouTubeReadOnlyObservationAdapter.from_client_config(
            Path(args.client_config), root, governance
        )

    def operation(service: Any) -> dict[str, Any]:
        receipt = service.reconcile_scheduled_publication(
            args.receipt_id, args.status_id, args.publication_id
        )
        return {"receipt_id": receipt.id, "public_at": receipt.public_at}

    return _live(args, f"reconcile-{args.publication_id}", operation, live_adapter=adapter)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m project_atlas.publishing_cli")
    sub = parser.add_subparsers(dest="command", required=True)

    def paths(p):
        p.add_argument("--db")
        p.add_argument("--media")

    def live(p):
        paths(p)
        p.add_argument("--expect-db-sha256", required=True)
        mode = p.add_mutually_exclusive_group(required=True)
        mode.add_argument("--dry-run", action="store_true")
        mode.add_argument("--backup-root")

    p = sub.add_parser("status", help="read-only on-demand publishing state")
    paths(p)
    p = sub.add_parser("prepare", help="create an on-demand package with projected credits")
    live(p)
    p.add_argument("artifact")
    p.add_argument("--package-id", required=True)
    p.add_argument("--slot", type=int, required=True)
    p.add_argument("--metadata", required=True)
    p = sub.add_parser("approve", help="record the founder's package approval")
    live(p)
    p.add_argument("package_id")
    p.add_argument("--package-digest", required=True)
    p.add_argument("--decision-id", required=True)
    p.add_argument("--founder-actor", required=True)
    p.add_argument("--comment")
    p = sub.add_parser("reconcile-scheduled", help="receipt after observed public state")
    live(p)
    p.add_argument("publication_id")
    p.add_argument("--receipt-id", required=True)
    p.add_argument("--status-id", required=True)
    p.add_argument("--client-config", required=True)
    p.add_argument("--consent-state", required=True)
    return parser


COMMANDS = {
    "status": cmd_status,
    "prepare": cmd_prepare,
    "approve": cmd_approve,
    "reconcile-scheduled": cmd_reconcile,
}


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    for name in list(os.environ):
        if name.endswith("_API_KEY"):
            del os.environ[name]  # no model provider key is ever needed here
    try:
        report = COMMANDS[args.command](args)
    except (CliError, SourceCreditError) as error:
        print(json.dumps({"refused": str(error)}, indent=1), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=1, default=str, ensure_ascii=False))
    if report.get("mode") == "refused-by-rehearsal":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
