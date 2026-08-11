# Contributing to Project Atlas

## Before you start

- Discuss changes that introduce a new service, persistence technology, public interface, or major dependency before implementation.
- Keep pull requests focused. Separate refactors from behavior changes where practical.
- Do not commit secrets, generated runtime logs, local databases, or virtual environments.

## Local setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
uv sync --all-groups
```

## Required checks

Run these commands before opening a pull request:

```bash
uv run ruff check .
uv run black --check .
uv run pytest
```

To apply formatting and safe lint fixes locally:

```bash
uv run black .
uv run ruff check --fix .
```

## Code and test conventions

- Place production code in `src/project_atlas/`.
- Place tests in `tests/`, using names that mirror the package under test.
- Name tests for observable behavior, not implementation details.
- Keep imports and module dependencies directional; avoid circular imports.
- Update documentation and configuration templates whenever a change affects them.

## Pull requests

Include a concise summary, the reason for the change, validation performed, and any deployment or migration implications. CI must pass before merge.
