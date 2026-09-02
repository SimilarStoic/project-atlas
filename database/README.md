# Database

This directory is reserved for database documentation, schema assets, and migration history. Conveyor currently uses
governed SQLite persistence with source-defined, transactionally applied migrations in
`src/project_atlas/persistence.py`; the canonical source and verified runtime are contiguous through Migration 23.
Migration 24 is absent and unauthorized.

`database/migrations/` is retained for documentation or future migration assets; the current migration implementation is
source-defined. Do not modify migrations that have been deployed to a shared environment.
