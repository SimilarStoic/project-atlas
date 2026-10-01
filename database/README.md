# Database

Current operational and schema truth resolves through
[Conveyor Current State](../docs/CONVEYOR_CURRENT_STATE.md).

Conveyor uses governed SQLite persistence with source-defined, transactionally applied migrations in
`src/project_atlas/persistence.py`. Application schema authority is the `schema_migrations` table. Source migrations
are contiguous from **1 through 27**, and the current maximum application migration is **27**.

`PRAGMA user_version` is not the application migration authority. `PRAGMA schema_version` is SQLite's internal
schema-cookie counter, not the Conveyor application migration number. Migrations 25 and 26 are immutable historical
provenance; Migration 27 is the current application schema authority. Do not rewrite a deployed migration or create a
cleanup migration merely to reconcile documentation.

The active production database is selected explicitly through the fail-closed process environment established by
dot-sourcing `scripts/set_conveyor_environment.ps1` from the repository. The `ATLAS_DB_PATH` name is temporary
technical compatibility, not active product branding. Working-directory-relative databases are development
fallbacks, not production runtime authority.

For a read-only production audit, do not instantiate `AtlasRepository` or other application code: repository
construction can apply migrations or seed data. Database access, migration, backup, restore, and runtime mutation each
require a separately bounded procedure.

`database/migrations/` remains available for documentation or future migration assets; the current implementation is
source-defined.
