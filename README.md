# Project Atlas

> Working title — a scalable Python application platform.

Project Atlas is deliberately at the foundation stage. The repository provides a production-oriented structure, development tooling, and operational scaffolding; application and business logic will be added in future milestones.

## Technology baseline

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency and environment management
- Ruff and Black for code quality and formatting
- pytest for testing
- Docker and Docker Compose for reproducible runtime environments
- GitHub Actions for continuous integration

## Quick start

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Create the local environment and install development dependencies:

   ```bash
   uv sync --all-groups
   ```

3. Run the quality checks:

   ```bash
   uv run ruff check .
   uv run black --check .
   uv run pytest
   ```

## Repository layout

```text
src/project_atlas/  Application package (kept intentionally minimal for now)
tests/              Test suite, mirroring the source package when added
config/             Version-controlled, non-secret configuration templates
database/           Schema, migrations, and database tooling
scripts/            Repeatable developer and operational scripts
docs/               Architecture, decisions, and contributor documentation
assets/             Static design and project assets
logs/               Local runtime logs (not committed)
```

See [PROJECT.md](PROJECT.md) for project conventions and [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow.

## Container workflow

Build the development image:

```bash
docker compose build
```

The compose definition is intentionally a scaffold until Atlas gains a runnable service.

## Run the MVP UI shell

Start the local, dependency-free demo interface:

    uv run python -m project_atlas

Then open http://127.0.0.1:8000 in a browser. The MVP uses local demo data only;
it does not call AI services, research sources, publishing platforms, or analytics services.

## Status

Foundation only. No business logic, domain models, or externally exposed application behavior has been implemented.
