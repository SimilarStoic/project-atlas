"""Verified SQLite backup of the production database, taken before any live runtime write.

A copy is made with SQLite's backup API from a read-only connection and accepted only when the
copy passes integrity and foreign-key checks and holds exactly the same rows as the source,
table by table (row counts and a content digest). No application code opens either database.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

_LABEL = re.compile(r"[a-z0-9][a-z0-9_.-]{0,99}")


class BackupError(RuntimeError):
    """The backup could not be taken or did not verify; nothing else may proceed."""


def database_sha256(database: Path) -> str:
    return sha256(Path(database).read_bytes()).hexdigest()


def table_fingerprint(connection: sqlite3.Connection) -> dict[str, tuple[int, str]]:
    """Per table: row count and a digest of every row (order-independent)."""

    result = {}
    for (name,) in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ):
        rows = sorted(repr(row) for row in connection.execute(f'SELECT * FROM "{name}"'))
        result[name] = (len(rows), sha256("\n".join(rows).encode("utf-8")).hexdigest())
    return result


def verified_backup(
    database: Path, backup_root: Path, label: str, *, timestamp: datetime | None = None
) -> dict[str, Any]:
    """Back up ``database`` into ``backup_root/<label>-<YYYYmmdd-HHMMSS>/`` and verify it."""

    database, backup_root = Path(database), Path(backup_root)
    if not _LABEL.fullmatch(label):
        raise BackupError(f"Backup label {label!r} must be a lowercase safe name.")
    if not database.is_file():
        raise BackupError(f"Database {database} does not exist.")
    sidecars = sorted(path.name for path in database.parent.glob(f"{database.name}-*"))
    if sidecars:
        raise BackupError(f"Refusing: SQLite sidecar files present {sidecars}.")
    stamp = (timestamp or datetime.now()).strftime("%Y%m%d-%H%M%S")
    folder = backup_root / f"{label}-{stamp}"
    try:
        folder.mkdir(parents=True, exist_ok=False)
    except FileExistsError as error:
        raise BackupError(f"Backup folder {folder} already exists.") from error
    target = folder / database.name
    source = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        copy = sqlite3.connect(target)
        try:
            with copy:
                source.backup(copy)
        finally:
            copy.close()
        check = sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True)
        try:
            integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
            violations = len(check.execute("PRAGMA foreign_key_check").fetchall())
            identical = table_fingerprint(check) == table_fingerprint(source)
            migration = check.execute(
                "SELECT MAX(version), COUNT(*) FROM schema_migrations"
            ).fetchone()
        finally:
            check.close()
    finally:
        source.close()
    if integrity != "ok" or violations or not identical:
        raise BackupError(
            f"Backup verification failed (integrity={integrity}, foreign_key_violations="
            f"{violations}, content_identical={identical}); {target} is not a valid backup."
        )
    return {
        "backup": str(target),
        "backup_sha256": database_sha256(target),
        "source_sha256": database_sha256(database),
        "integrity": integrity,
        "foreign_key_violations": violations,
        "content_identical": identical,
        "schema_migrations": {"max": migration[0], "count": migration[1]},
    }
