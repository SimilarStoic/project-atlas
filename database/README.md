# Database

This directory is reserved for database documentation, schema assets, and migration history. Conveyor currently uses
governed SQLite persistence with source-defined, transactionally applied migrations in
`src/project_atlas/persistence.py`. Source-defined migrations are contiguous through **Migration 25**. Migration 24
is operational in the verified persistent runtime for multi-authority visual-reference provenance; Migration 25 is
the additive **offline** controlled-publishing/learning persistence foundation in source. This pass applied it only
to disposable test databases, not the protected legacy database or persistent runtime. It adds no OAuth credentials,
live YouTube adapter, upload, publication or runtime deployment authority.

With no `ATLAS_DB_PATH`, ordinary local repository construction uses portable `data/atlas-local.db`; historical
repository `data/atlas.db` is an exact protected legacy artifact and construction refuses that target. The persistent
Conveyor runtime remains selected explicitly by its environment configuration.

`database/migrations/` is retained for documentation or future migration assets; the current migration implementation is
source-defined. Do not modify migrations that have been deployed to a shared environment.
