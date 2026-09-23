# Database

This directory is reserved for database documentation, schema assets, and migration history. Conveyor currently uses
governed SQLite persistence with source-defined, transactionally applied migrations in
`src/project_atlas/persistence.py`. Source-defined migrations are contiguous through **Migration 26**. Migration 26
adds `inworld_tts` to the narration-execution constraint without reinterpreting historical rows, using the established
transactional table-rebuild pattern. Separately authorized persistent migration 25 -> 26 completed on 22 September
2026 with a verified SQLite backup and preserved historical business data. The
[23 September reconciliation](../CURRENT_STATUS.md#verified-pilot-and-runtime-state--23-september-2026) verified
migrations 1–26, integrity `ok`, zero FK violations and the unchanged post-migration hash. No migration was performed
by that read-only audit. Do not use auto-migrating/seeding repository construction for inspection. Migration 24
is the multi-authority visual-reference foundation; Migration 25 is the additive controlled-publishing/learning
persistence foundation. Migration 25 is now active in the verified persistent runtime after a byte-for-byte Migration
24 backup, with integrity and foreign keys clean and all earlier historical table contents unchanged. The protected
legacy database remains untouched. This adds no OAuth credentials, upload, publication or runtime mutation authority.

With no `ATLAS_DB_PATH`, ordinary local repository construction uses portable `data/atlas-local.db`; historical
repository `data/atlas.db` is an exact protected legacy artifact and construction refuses that target. The persistent
Conveyor runtime remains selected explicitly by its environment configuration.

`database/migrations/` is retained for documentation or future migration assets; the current migration implementation is
source-defined. Do not modify migrations that have been deployed to a shared environment.
