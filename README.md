# Project Atlas

> Working title — a scalable Python application platform.

Project Atlas is a local, dependency-free editorial control interface and durable
SQLite foundation for SimilarStoic. It deliberately implements only the approved
v0.1-v0.4 scope; later workflow, research automation and production systems remain deferred.

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

## Local persistence

Atlas now stores its first persistent application data in SQLite at
`data/atlas.db` by default. Set `ATLAS_DB_PATH` to use a different local database:

    $env:ATLAS_DB_PATH = 'C:\path\to\atlas.db'
    uv run python -m project_atlas

On startup, Atlas applies recorded SQLite schema migrations and then idempotently
seeds the six existing Discover opportunities. Existing local changes are never
overwritten by later startup seeding.

This foundation persists reusable **Subjects**, individual editorial
**Opportunities**, and their many-to-many relationships. The current Discover
`pillar` field remains display-only compatibility metadata; it is not a persisted
Pillar model.

## Research and evidence persistence

Atlas v0.3 adds a small, general Research & Evidence foundation:

- A versioned **ResearchPack** belongs to exactly one Opportunity. Versions are
  unique per Opportunity and the latest pack is the highest version number.
- Each **Claim** belongs to exactly one ResearchPack version and retains its text,
  claim type, risk level, freshness type, review state, notes and review timestamp.
- **Sources** are global reusable records, deduplicated by exact stored URL.
- **ClaimEvidence** records the Claim/Source relationship, including its stance,
  optional locator and editorial/research notes.

Recognised Claim semantics are factual, interpretive, illustrative and editorial;
low, medium and high risk; stable, date-sensitive and current freshness; and
unreviewed, in-review, supported, disputed and insufficient review states.
`supported` means assembled evidence is considered sufficient for the intended
editorial use at its review point, not that a claim is permanently true.

The persistence model deliberately has no numeric truth, confidence, source-authority
or evidence-strength scores. It also has no universal evidence policy: different
content domains can acquire appropriate requirements later without replacing this
foundation.

Startup seeds one persistent ISA ResearchPack for the existing Content Workspace
opportunity. It is idempotent and does not overwrite local changes. The Content
Workspace reads that persisted ResearchPack, Claims, Sources and ClaimEvidence
read-only.

## Editorial angle persistence

Atlas v0.4 adds the smallest durable bridge from Research & Evidence to editorial
development:

- An **EditorialAngle** belongs to one Opportunity and references one ResearchPack
  from that same Opportunity. It stores a provisional working title, thesis,
  audience promise, framing, ordered intended takeaways and extension metadata.
- **EditorialAngleClaim** records the `core` or `supporting` role of a Claim in an
  EditorialAngle. Repository validation requires every linked Claim to belong to
  the Angle's ResearchPack.

Startup idempotently seeds two distinct ISA EditorialAngles for the existing v1
ResearchPack: a deadline decision-tree framing and an ISA-transfer-process framing.
The Content Workspace now reads a deterministic persisted EditorialAngle and its
linked Claims while remaining read-only. Final publication titles, script/narration,
scene plans, QA, production and workflow remain demo-backed or deferred.

Pillars, generic Topics, final-title and hook models, script and content-package
persistence, AI research, agents, research policies, workflows, publishing,
production and analytics remain deferred.

## Status

v0.1 UI shell, v0.2 persistent discovery, v0.3 Research & Evidence persistence,
and v0.4 Editorial Angle persistence are implemented locally. Later Atlas systems
remain out of scope.
