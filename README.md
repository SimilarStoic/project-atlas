# Project Atlas

> Working title — a scalable Python application platform.

Project Atlas is a local, dependency-free editorial control interface and durable
SQLite foundation for SimilarStoic. It implements the v0.1-v0.10 scope;
later workflow,
research automation and production systems remain deferred.

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

Pillars, generic Topics, final-title and hook models, ScriptSection and ContentPackage
persistence, AI research, agents, research policies, workflows, publishing,
production and analytics remain deferred.

## Content piece and script persistence

Atlas v0.5 adds the smallest durable bridge from an EditorialAngle to a concrete
deliverable and its complete audio-first narration:

- A **ContentPiece** belongs to one Opportunity and derives from one EditorialAngle
  from that same Opportunity. Its provenance is immutable; format key, working title
  and metadata remain editable.
- A **Script** belongs to one ContentPiece and stores one complete narration body.
  Script versions are unique per ContentPiece and immutable after creation; the latest
  version is derived from the highest version number, not a persisted current-state flag.

Startup idempotently seeds one ISA video ContentPiece from the deterministic ISA
EditorialAngle and one Script v1 using the existing demo narration. The Content
Workspace now reads the persistent ContentPiece and latest Script narration read-only.
Scene plan and QA remain demo-backed; workflow, production, publishing and analytics
remain deferred.

## Visual plan and scene persistence

Atlas v0.6 adds the smallest durable bridge from one exact immutable Script version
to its visual production blueprint:

- A **VisualPlan** belongs to one ContentPiece and references one Script from that
  same ContentPiece. Its ContentPiece/Script provenance is immutable; visual direction
  and metadata remain editable.
- An ordered **Scene** belongs to one VisualPlan. Its `narration_excerpt` is a
  human-readable locator only: the Script remains the authoritative, complete
  audio-first narration. Scene sequence is unique within its VisualPlan; editable
  scene detail never moves it to another plan.

Startup idempotently seeds one ISA VisualPlan for the seeded ContentPiece and
Script v1, with three ordered Scenes migrated from the existing kitchen-table,
calendar, envelopes and decision-tree direction. The Content Workspace now reads
the persistent VisualPlan and Scenes read-only; its compatibility `scene_plan`
display is derived from those records. QA remains demo-backed.

This preserves the SimilarStoic rule that the complete video is understandable
from audio alone: visuals clarify, reinforce and provide metaphor, but do not
replace essential narration. Asset generation, production, publishing, workflow,
analytics and agents remain deferred.

## Asset specification and asset persistence

Atlas v0.7 adds the smallest durable bridge from a persisted Scene to its required
visual ingredients and registered outputs:

- An **AssetSpec** belongs to one Scene. It records an open-ended asset type, purpose,
  description, canonical provider-neutral generation prompt, optional continuity key
  and extension metadata. Its Scene provenance is immutable; the requirement detail
  remains editable.
- An **Asset** belongs to one AssetSpec. Versions are unique per AssetSpec and immutable
  after creation; each records only a storage path, media type, source kind and metadata.
  There is no current, selected, approved, generated or workflow state.

Startup idempotently seeds five ISA AssetSpecs across the existing three Scenes: a
kitchen-table environment and hamster sorting envelopes, a tax-year calendar, and a
decision-tree graphic plus hamster reaction. It deliberately seeds no Asset outputs.
The Content Workspace now reads persisted AssetSpecs and their registered Assets
read-only beneath each Scene. QA remains demo-backed.

## Generation execution foundation

Atlas v0.8 adds one synchronous image-generation operation for one persisted, executable
AssetSpec. A terminal immutable **GenerationExecution** freezes the AssetSpec snapshot and
normalized provider-neutral input actually used, then retains generic generator/provider/model/request
provenance and success or failure details. A success atomically registers exactly one immutable Asset;
manual/imported Assets remain valid without execution provenance.

OpenAI is the first replaceable Image API adapter, configured through `OPENAI_API_KEY` and
`ATLAS_OPENAI_IMAGE_MODEL`; no API secret is persisted. Generated files are stored safely below the
configurable `ATLAS_ASSET_STORAGE_ROOT` (default `data/assets/`). Startup performs no generation and
seeds zero executions and zero Assets. Queues, retries, batch generation, QA, approval, rendering,
workflow, production, publishing, analytics and agents remain deferred.

## Visual style control foundation

Atlas v0.9 adds a durable visual-style layer between an **AssetSpec** and its
provider-neutral **GenerationInput**. An immutable, versioned **VisualStyleProfile**
stores reusable SimilarStoic visual direction; it has no editor, selected/current state
or provider-specific fields. One idempotently seeded `SimilarStoic Core` v1 profile
requires a sparse hand-drawn or line-drawn editorial style, predominantly light
backgrounds, restrained detail and colour, one dominant visual idea, and no invented
written material unless the AssetSpec requires it.

Atlas-owned deterministic prompt composition resolves profile-wide and matching
AssetSpec-type rules (`environment`, `character`, `prop`, or `graphic`) before the
concrete persisted AssetSpec requirement. Styled runs persist `GenerationInput` v2 with
only the resolved style rules, while retaining a direct GenerationExecution-to-profile
lineage. Existing v0.8 `GenerationInput` v1 history remains readable unchanged.

Environment AssetSpecs describe only the setting/background layer. Character, prop and
graphic requirements remain separate production assets for later composition.

Atlas v0.10 adds immutable `SimilarStoic Core` v2 alongside the preserved v1 profile.
V2 strengthens the hand-drawn rendering language—organic dark linework, simplified forms, mostly
white/unfilled space, and no colour unless a single restrained flat block accent is helpful—while
avoiding tonal shading, textured fills and polished digital-illustration finish. It retains v0.9's
sparse, light, decomposed composition rules. The active immutable
profile is configured with `ATLAS_VISUAL_STYLE_PROFILE_ID`, falling back deterministically to v2;
v1 remains selectable. No schema migration was required: both profile versions are idempotent seed
data, and existing executions retain their frozen v1 lineage unchanged.

SimilarStoic Core v2 is the current text-guided production baseline, not the final SimilarStoic visual
identity. Further visual art direction remains intentionally deferred; a future immutable profile version
may supersede v2, and reference-grounded style fidelity may be considered later if justified. Existing v1
and v2 GenerationExecutions retain their original frozen style provenance.

Style-reference images, Character entities and continuity, profile editing, QA, workflow and production
systems remain deferred.

## Status

v0.1 UI shell, v0.2 persistent discovery, v0.3 Research & Evidence persistence,
v0.4 Editorial Angle persistence, v0.5 Content Piece + Script persistence, and
v0.6 Visual Plan + Scene persistence are complete and pushed. v0.7 Asset Specification +
Asset persistence, v0.8 Generation Execution, and v0.9 Visual Style Control are complete and
pushed. v0.10 Visual Style Fidelity is complete and pushed as a provisional visual-style baseline. Later
Atlas systems remain out of scope.
