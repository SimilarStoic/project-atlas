# Conveyor — Project Guide

## Purpose

Conveyor is the long-term production operating system/platform. SimilarStoic is its first autonomous pilot channel and
flagship proving ground; SimilarStoic owns its channel-specific editorial and creative decisions but does not define or
own Conveyor. Project Atlas is the historical development name.
This repository starts with durable engineering boundaries so new capabilities can be added without turning the
codebase into a monolith.

## Architectural principles

- Keep domain and business rules independent of frameworks, transport layers, and infrastructure.
- Prefer small, cohesive modules with explicit interfaces.
- Make dependencies point inward: delivery and infrastructure code may depend on the application core, never the reverse.
- Treat configuration, observability, migrations, and tests as first-class concerns.
- Add dependencies intentionally and document significant architectural choices in `docs/decisions/`.

## Source layout

The `src/` layout prevents tests and local commands from accidentally importing an uninstalled working copy. The
legacy compatibility package name remains `project_atlas`; the product rename does not change it.

As the system grows, organize code by bounded capability rather than by one global technical layer. A future capability can own its application, domain, and infrastructure concerns while sharing only deliberately stable abstractions.

## Directory responsibilities

| Directory | Responsibility |
| --- | --- |
| `src/project_atlas/` | Production Python packages |
| `tests/` | Automated tests and test support |
| `config/` | Safe defaults and configuration templates; never credentials |
| `database/` | Migration history, schema assets, and database documentation |
| `scripts/` | Idempotent development and operational automation |
| `docs/` | Architecture, runbooks, decisions, and design notes |
| `assets/` | Non-code project assets |
| `logs/` | Local-only runtime output |

## Quality baseline

- Format code with Black.
- Lint with Ruff; use `ruff check --fix` only after reviewing the resulting diff.
- Test with pytest before opening a pull request.
- Keep CI and local commands aligned through `pyproject.toml`.
- Use type annotations for new public interfaces; add a type-checking tool when the first production module makes it valuable.

## Configuration and secrets

Configuration should be typed and validated when application configuration is introduced. Commit only templates and non-sensitive defaults. Put secrets in environment variables or the chosen deployment secret manager; do not commit `.env` files.

## Documentation expectations

Current operational truth resolves through `docs/CONVEYOR_CURRENT_STATE.md`. Record decisions that affect multiple
modules, deployment, persistence, security, or public interfaces in `docs/decisions/`. Keep bounded setup and
operational instructions consistent with the current authority.
