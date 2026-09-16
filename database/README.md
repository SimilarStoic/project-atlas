# Database

This directory is reserved for database documentation, schema assets, and migration history. Conveyor currently uses
governed SQLite persistence with source-defined, transactionally applied migrations in
`src/project_atlas/persistence.py`. Source-defined migrations are contiguous through **Migration 25**. Migration 24
is the multi-authority visual-reference foundation; Migration 25 is the additive controlled-publishing/learning
persistence foundation. Migration 25 is now active in the verified persistent runtime after a byte-for-byte Migration
24 backup, with integrity and foreign keys clean and all earlier historical table contents unchanged. The protected
legacy database remains untouched. This adds no OAuth credentials, upload, publication or runtime mutation authority.

With no `ATLAS_DB_PATH`, ordinary local repository construction uses portable `data/atlas-local.db`; historical
repository `data/atlas.db` is an exact protected legacy artifact and construction refuses that target. The persistent
Conveyor runtime remains selected explicitly by its environment configuration.

`database/migrations/` is retained for documentation or future migration assets; the current migration implementation is
source-defined. Do not modify migrations that have been deployed to a shared environment.
