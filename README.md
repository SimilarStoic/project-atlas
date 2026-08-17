# Project Atlas

> Working title — a scalable Python application platform.

Project Atlas is a local, dependency-free editorial control interface and durable
SQLite foundation for SimilarStoic. It implements through v0.14, including reference-grounded
character generation and an explicit first-reference bootstrap operation. Later workflow, research
automation and production systems remain deferred.

For the canonical repository checkpoint, cross-chat re-grounding procedure, and roadmap-governance protocol,
see [docs/CANONICAL_HANDOFF.md](docs/CANONICAL_HANDOFF.md).

Atlas is a composable, evolvable system: implementation-specific pipeline components remain replaceable behind
stable boundaries, while accepted changes preserve historical provenance through additive/versioned evolution.
Core domain/provenance invariants remain deliberately governed rather than casually replaced. SimilarStoic's
brand scope extends beyond finance to useful explanatory subjects, and its sparse visual baseline may use
occasional original contrasting break-frame/still devices as a signature creative mechanism.

The canonical future financial-control boundary distinguishes a durable **Cost Ledger** for actual operating
spend, a durable **Revenue Ledger** for money earned from already contemplated monetisation sources, and an
**Economics / Control Centre** that may derive financial views and guardrails from them. Audience/content
analytics remains separate, though it may inform unit economics. This is conceptual only: no financial schema,
ledger, integration, formula, threshold, enforcement or automation implementation is present or authorized.
Future financial records must preserve provenance, provider independence and immutable historical execution
semantics. Paid external production will eventually require prior founder authorization of a bounded maximum
spend envelope tied to the approved editorial proposition. Atlas should spend less when it can still clear the
required quality, brand, evidence and risk floor; it must stop and escalate rather than exceed that ceiling or
silently lower the floor. This is a future operating principle, not financial or spend-authorization
implementation.

Atlas's approved end-state is an approximately **95% automated content operating system**, not a human-free
system. Routine execution should progressively automate around founder judgement at three target gates: Idea
(opportunity approval/steering), Editorial (title, hook, angle, script, evidence/risk and revision decisions
plus bounded paid-production spend authorization) and Learning (performance, hypotheses, adaptations and
available economics context). These are operating-model direction only, not workflow/database entities. The
durable v0.1–v0.14 chain from Opportunity through Asset is a foundation; later phases extend it through
publication, platform performance, analytics,
revenue/economics, learning and future content decisions. Implementation milestones remain subordinate to the
canonical roadmap and must not redefine it.

Phase 2 is now the **active** roadmap phase. v0.16 Authorized Research Initiation is the latest accepted
implementation milestone; v0.15 Persistent Idea Gate remains its historical accepted predecessor, and the
remaining Phase 2 scope is not implemented. Its approved
operating-model direction keeps sparse version-specific founder gates (Idea, Editorial and Learning) distinct from rich machine readiness
evidence. The editorial chain should
progress automatically only when explicit quality, evidence and provenance requirements pass; exceptions,
rather than normal work, interrupt automation. This is not a generic mutable workflow model or an approved
schema. Production/publication, Learning, financial-control and orchestration records remain with their later
phase boundaries.

Future Editorial Gate proposals may compare feasible production options and explain expected quality,
capability, risk and cost trade-offs, including qualified—not guaranteed—commercial or strategic upside.
Quality is a floor: Atlas optimizes cost inside it, never by silently degrading it. Authorized ceilings govern
paid external spend only; an overspend requires human escalation, while the exact financial-control mechanics
remain deferred.

The first approved implementation direction is immutable Idea Gate review snapshots and immutable Idea Gate
decisions for mutable Opportunities: Proceed, Reject or Steer with optional founder direction and preserved
history. A decision applies to the exact snapshot reviewed, has no automatic research/workflow side effect, and
does not reuse `Opportunity.status` or approval flags. This direction is now defined as
**v0.15 — Persistent Idea Gate**, the latest accepted Phase 2 implementation milestone. It adds only
immutable snapshot/decision provenance, a narrow domain-qualified API and minimal Discover interaction
through additive migration 12; v0.14 remains the historical accepted predecessor.
The approved spend-authorization direction is not part of this first Idea Gate implementation slice.

**v0.16 — Authorized Research Initiation** is the latest accepted implementation milestone; v0.15 remains its
historical accepted predecessor. It provides deliberate creation of Opportunity-owned
ResearchPack versions under a nullable direct qualifying IdeaGateDecision reference: Proceed/Steer may qualify,
Reject cannot, snapshot/pack Opportunity lineage must match, historical packs remain valid with null
provenance, and Steer direction is consumed by reference. It authorizes no automatic research,
provider/queue orchestration, historical backfill or later-phase activation.

The approved next **design direction only** is durable Research Readiness assessment semantics. Assessments are
additive, immutable and versioned against an exact schema-versioned frozen ResearchPack evidence state, because
Claims, Sources and ClaimEvidence may change after a pack is created. They preserve Ready, NeedsMoreResearch or
Blocked; findings/reasons; policy/check and schema versions; time; and producer provenance. Readiness is a
machine boundary, not founder approval or mutable workflow state: it has no persisted current/latest pointer,
does not automatically create an EditorialAngle, and does not yet define how editorial progression is
authorized. No readiness schema, API, UI, assessment producer, research automation or successor milestone is
implemented.

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

Atlas v0.10 added immutable `SimilarStoic Core` v2 alongside the preserved v1 profile. V2 strengthens the
hand-drawn rendering language—organic dark linework, simplified forms, mostly white/unfilled space, and no
colour unless a single restrained flat block accent is helpful—while avoiding tonal shading, textured fills
and polished digital-illustration finish. It retains v0.9's sparse, light, decomposed composition rules.

Following Human Gate A during Phase 1 visual-evidence execution, immutable `SimilarStoic Core` v3 is the
founder-approved Phase 1 visual baseline. It preserves v2's sparse, light, deliberately imperfect,
no-gradient/no-tonal-shading grammar while specifying an amateur human-drawn recurring hamster: large
hamster-like ears, long whiskers, simple alert eyes, minimal or no fur detail, and a genuinely crossbody
signature sling/man-bag. The canonical hamster remains mostly white/light, with warm tan/orange inner ears,
nose and paws/hands/feet. Its bag alone may use flat green, blue, orange, yellow, red and black with a
dark-gray strap; general scene colour remains restrained. V2 remains immutable, historical and selectable.

The active immutable profile is configured with `ATLAS_VISUAL_STYLE_PROFILE_ID`, falling back
deterministically to v3; v1 and v2 remain selectable. No schema migration was required: all profile versions
are idempotent seed data, and existing GenerationExecutions retain their frozen style provenance. The
founder-approved Human Gate A Asset is the sole immutable member of CharacterReferenceSet v1. Grounded v4
review evidence then succeeded for the canonical sorting and reaction Scene AssetSpecs. Phase 1 visual
acceptance is closed with **PASS WITH DEFERRED VISUAL REFINEMENT**: the only non-blocking deficiency is a
residual AI-clean/overly competent professional finish. Any future refinement must preserve the approved
hamster identity, colour assignments, sling-bag language and reference-set continuity; it does not authorize
a redesign or a further generation. At that Phase 1 acceptance point, no v0.15 or successor milestone was
implied.

Provider reference-image conditioning, profile editing, QA, workflow and production systems remain deferred.

## Character continuity foundation

Atlas v0.11 adds an immutable, versioned **CharacterProfile** boundary for recurring-character identity.
The seeded `SimilarStoic Hamster Core` v1 profile is separate from VisualStyleProfile visual-language
guidance. Character AssetSpecs may reference a CharacterProfile; the two canonical seeded hamster
AssetSpecs do so, while `continuity_key` remains non-authoritative grouping metadata.

For character runs, Atlas-owned prompt composition freezes complete identity provenance in
`GenerationInput` v3. GenerationExecution retains direct CharacterProfile lineage and an execution-time
AssetSpec snapshot, so later AssetSpec relationship changes do not change historical meaning.

At the v0.11 checkpoint, generation remained prompt-only. Atlas had no canonical visual-reference Asset
relationship, reference-image or image-edit conditioning, or guarantee that separately generated hamster
Assets would remain visually consistent. Canonical visual references and provider conditioning were later
bounded work.

## Canonical character reference foundation

Atlas v0.12 adds an immutable, versioned **CharacterReferenceSet** for one exact CharacterProfile. A set
contains one-or-more explicitly ordered existing generated character Assets and records the founder's
canonical visual-reference selection without mutable current, best or approved state. The existing
SimilarStoic Hamster Core v1 CharacterProfile remains the canonical seeded hamster identity.

New managed generated Assets receive a lowercase SHA-256 digest of their exact persisted bytes. Reference
selection requires that digest, a successful character GenerationExecution with matching CharacterProfile
lineage, and a safely resolvable supported managed image. The local UI can display eligible hamster Assets by
Asset ID and create/view immutable historical reference-set versions with Asset and execution provenance.

Reference selection sits beside, rather than changes, the production chain:

`ContentPiece → Script → VisualPlan → Scene → AssetSpec → GenerationExecution → Asset`

At the v0.12 checkpoint, reference selection did not yet condition provider requests. That limitation was
addressed by v0.13; the immutable ordered-set model remains unchanged.

## Reference-grounded character generation

Atlas v0.13 resolves the highest CharacterReferenceSet version for the exact CharacterProfile at input
construction time. It freezes that set's ordered Asset IDs, SHA-256 digests, media types and positions in
GenerationInput v4, reloads and verifies the exact managed bytes at provider time, and records direct
GenerationExecution-to-CharacterReferenceSet lineage. Prompt-only requests use OpenAI image generation;
grounded character requests use ordered multipart image edits. Reference bytes remain runtime-only.

Normal character generation remains reference-grounded: a missing exact-profile CharacterReferenceSet is a
pre-provider failure that creates neither GenerationExecution nor Asset.

## Explicit character reference bootstrap

Atlas v0.14 adds a separate, human-initiated bootstrap operation for the first eligible character Assets on
an exact CharacterProfile with no CharacterReferenceSet. Bootstrap only accepts an existing Scene-owned
character AssetSpec with CharacterProfile provenance and uses GenerationInput v3 with the existing
non-reference provider path. It creates ordinary generated Assets and executions, never a reference set or
mutable candidate state. Once any exact-profile CharacterReferenceSet exists, bootstrap is rejected before
provider invocation; ordinary generation continues to require grounded references.

## Status

v0.1 UI shell, v0.2 persistent discovery, v0.3 Research & Evidence persistence,
v0.4 Editorial Angle persistence, v0.5 Content Piece + Script persistence, and
v0.6 Visual Plan + Scene persistence are complete and pushed. v0.7 Asset Specification +
Asset persistence, v0.8 Generation Execution, and v0.9 Visual Style Control are complete and
pushed. v0.10 Visual Style Fidelity is complete and pushed as a provisional visual-style baseline. v0.11
Character Continuity Foundation, v0.12 Canonical Character Reference Foundation, and v0.13
Reference-Grounded Character Generation and v0.14 Explicit Character Reference Bootstrap are complete and
pushed. The verified checkpoint is `516884b8fab0a29e8e82973d684be1ae8a08bff6`
(`feat: add character reference bootstrap`), with 75 passing tests and migrations 1–11. The canonical
handoff records the formal closure of **Phase 1 — Product & Business Definition**: the final
production-ready SimilarStoic brand identity is **APPROVED**, while visual acceptance remains **PASS WITH
DEFERRED VISUAL REFINEMENT**. The residual AI-clean/overly professional finish is non-blocking and preserves
the approved hamster identity, colours, sling-bag treatment, proportions and reference continuity.
v0.16 — Authorized Research Initiation is the latest accepted implementation checkpoint; v0.15 remains its
historical accepted predecessor. Migrations are canonical through 13. Later Atlas
systems remain out of scope.
