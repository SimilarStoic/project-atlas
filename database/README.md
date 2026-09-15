# Database

This directory is reserved for database documentation, schema assets, and migration history. Conveyor currently uses
governed SQLite persistence with source-defined, transactionally applied migrations in
`src/project_atlas/persistence.py`; canonical source and verified persistent runtime are contiguous through
**Migration 24**. Migration 24 is operational for multi-authority visual-reference provenance.
**Migration 25 is absent** and remains separately governed; this documentation reconciliation does not create or
authorize it.

`database/migrations/` is retained for documentation or future migration assets; the current migration implementation is
source-defined. Do not modify migrations that have been deployed to a shared environment.
