# Conveyor Current State

## Authority and purpose

This document is the single current operational authority for Conveyor. It records the state from which a fresh
agent should resume and the boundaries that prevent historical material from being mistaken for current instruction.

When current documentation conflicts, resolve current truth through this file. `README.md` is an onboarding map,
`ROADMAP.md` is strategy and future sequencing, and `CURRENT_STATUS.md` plus `docs/CANONICAL_HANDOFF.md` are historical
provenance. Design notes and evidence records remain authoritative for their bounded subjects only when they do not
conflict with this operational snapshot.

This checkpoint describes state; it does not authorize application execution, provider calls, spend, publication,
migration, or new production work.

## Product identity

**Conveyor** is the long-term production operating system/platform. It is continuously developed to support multiple
channels and products.

**SimilarStoic** is Conveyor's first autonomous pilot channel and flagship proving ground. SimilarStoic owns its
channel-specific editorial, visual, audience, and creative decisions. It does not define or own Conveyor itself.

**Project Atlas** is the historical development name for the system that evolved into Conveyor. Preserve that name in
historical records and in technical compatibility identifiers that have not yet undergone their bounded migration.
The Python package/import name `project_atlas`, the class name `AtlasRepository`, and `ATLAS_*` environment variables
remain valid technical identifiers for now; they are not current product branding. Do not rename them opportunistically.

## Current repository and runtime layout

The intended active Windows layout is:

```text
D:\ConveyorOS\
  source\
    Conveyor\
  runtime\
    ConveyorRuntime\
  channels\
    SimilarStoic\
  evidence\
  archives\
  docs\
  temp\

D:\ConveyorBackups\
```

Active source is `D:\ConveyorOS\source\Conveyor`. Active runtime is
`D:\ConveyorOS\runtime\ConveyorRuntime`. The SimilarStoic channel root is
`D:\ConveyorOS\channels\SimilarStoic`. `D:\ConveyorBackups` stays outside `ConveyorOS` as the independent recovery
boundary.

The former active roots `D:\ProjectAtlas` and `D:\ConveyorRuntime` no longer exist. Those strings may remain in
historical provenance, but they are not startup instructions. Do not recreate them or add compatibility junctions.
The post-relocation `.venv` was rebuilt fresh.

At the repository level:

- `src/project_atlas/` contains the current compatibility-named Python application packages.
- `tests/` contains automated tests and support.
- `scripts/` contains bounded operational and development automation.
- `database/` documents persistence and migration history.
- `docs/` contains this authority plus bounded architecture, policy, creative, and historical records.
- `assets/` contains tracked project assets; production runtime assets and media belong under the runtime root.

## Runtime environment contract

In each new PowerShell process intended for production operation, establish the runtime contract by dot-sourcing:

```powershell
. .\scripts\set_conveyor_environment.ps1
```

The script derives the approved layout from its own repository location, validates every required path, resolves the
repository-bundled FFmpeg/FFprobe pair, fails closed on missing or ambiguous paths, and sets these process-level values:

- `ATLAS_DB_PATH`
- `ATLAS_ASSET_STORAGE_ROOT`
- `ATLAS_MEDIA_STORAGE_ROOT`
- `ATLAS_FFMPEG_PATH`
- `ATLAS_FFPROBE_PATH`

The `ATLAS_*` prefix is temporary technical compatibility, not active product identity. Do not fall back to
working-directory-relative `data/atlas-local.db`, `data/assets`, or `data/media` for production. Do not use a system
`PATH` FFmpeg as an implicit production substitute.

The protected production database SHA-256 recorded below is a verification checkpoint, not a permanent runtime
contract. Legitimate future production operations may change it; never embed it in startup code or use it as a reason
to reject an authorized future database change.

## Current Git and verification checkpoint

The active repository is expected to be clean on `main`. Before consequential Git operations, fresh agents must inspect
the working tree and index and verify current `HEAD`, `origin/main`, and live remote `main` directly. Exact current
commit SHAs and GitHub Actions run IDs are volatile verification results, not permanent operational truth.

- The immutable rollback/reference checkpoint is the pre-cleanup tag `pre-conveyor-cleanup-2026-09-30` at
  `f17ab0cf89bc99a95bcfb4a9d28d31d8fc2d0fa3`.
- The relocated full offline suite originally passed **316 tests**.
- After the narration CI repair and its regression test, the verified full suite contains **317 passing tests**.
- Repository CI is restored to green for Ruff lint, Black formatting, and pytest. Verify the current run live when its
  result matters.
- The protected runtime database checkpoint SHA-256 is
  `97FF9F4B37766A98BE3C94506D5E45A399648B070DEAC686CA25EF755B29EDE2`.

The founder-rejected, non-canonical v028 prototype scripts were intentionally removed from active `scripts/` after
preservation. Their exact source bytes and representative visual evidence are stored outside the repository at
`D:\ConveyorOS\archives\experiments\similarstoic\rejected-v028\2026-09-01\`. The tracked
[rejected-v028 evidence index](evidence/experiments/REJECTED_V028_PROTOTYPES.md) records their disposition. Do not
restore them or treat them as production tooling merely because historical evidence exists.

## Current production status

**Production #5 v4 remains the accepted artifact baseline.**

**Production #6 was completed as a private diagnostic production cycle. It mechanically exercised the current
Conveyor production path and produced useful evidence, but failed founder creative acceptance and was not approved
for publication. Its failures informed subsequent generalized production rules. P6 is closed as diagnostic evidence,
not accepted/publicly released.**

The status distinctions are:

| Question | P6 status |
| --- | --- |
| Mechanically executed | Yes |
| Founder creatively accepted | No |
| Published | No |
| Lessons retained and generalized | Yes |
| Closed as diagnostic evidence | Yes |

Do not reopen P6 merely to make it pass. No Production #7 work has begun at this checkpoint.

P6 evidence included halos/edge defects, long static stretches, weak background semantic support, repeated poses and
hamster blocking, a ghost circle, character drift, a pronunciation issue, and a repeated ending. Narration was the
strongest component. These findings explain learned rules; they do not replace Production #5 v4 as the accepted
artifact baseline.

## Creative operating rules

The current generalized creative rules are:

- Use a sparse, light, hand-drawn visual language with deliberate imperfection.
- Preserve generous white or off-white negative space.
- Avoid generic polished corporate, vector, or cartoon appearance.
- Avoid gradients, painterly shading, glossy dimensional rendering, and unnecessary surface detail.
- Preserve the recognizable Core v3 hamster with its crossbody bag.
- **THE NARRATOR EXPLAINS. THE HAMSTER ILLUSTRATES.**
- Make movement and visual change follow meaning rather than arbitrary time intervals.
- Treat captions as part of composition, not an overlay afterthought.
- Review the complete video at normal speed, at phone scale, before acceptance.
- Persistence does not mean stillness.
- Stale states, ghost markers, repeated endings, and other residual visual state are unacceptable.

Quality must be judged at the stage that owns the defect:

- At **raw-world acquisition**, judge source-world/style quality, semantic action support, believable scale and world
  logic, and crisp intentional source edges.
- At **actor-fit/final-composite**, judge actor, object, and composite edge quality separately.
- If softness appears only during placement, scaling, compositing, or rendering, localize the defect to that stage
  instead of regenerating otherwise strong source art.

## Pipeline model

Conveyor's high-level pipeline is:

```text
brief
→ script
→ visual beats
→ canonical characters/worlds
→ controlled animation/state
→ narration
→ captions
→ render
→ QA
→ publish
→ learn
```

Core reliability has three dimensions: creative/product quality, reproducibility/control, and audience progression.

> A perfectly persistent boring video is still a bad product.

Generation may be stochastic. Accepted production state must be deterministic and reproducible.

## Current mechanical foundation

The repository has mechanically established:

- the Persistent Scene Model;
- exact inheritance and admitted lineage;
- resolved scene state flowing into render;
- exact SimilarStoic Core mascot performance reuse from the three founder-approved tracked acting poses, with
  deterministic background extraction and no automatic character-regeneration fallback;
- caption integration;
- the Daniel narration path; and
- deterministic accepted production state.

These mechanisms are foundations, not proof of creative quality or end-to-end autonomous readiness. Mechanical
persistence does not guarantee a compelling, semantically active, publication-ready product.

## Known pipeline boundaries

The following limitations remain operationally important:

- The legacy v1 `AssetSelection` snapshot path still has HTTP ingress and is not dead.
- Persistent-scene v2 has an explicit canonical HTTP lifecycle under `/api/v2/productions`. It starts from an
  approved `VisualPlan` plus semantic world/entity/variant intent, performs managed acquisition, pauses for raw-world
  review, adapts approved images into provenance-linked scene rasters, persists world/admission/state lineage, uses
  approved narration, captions and rendering, and then pauses for whole-video review before it can become
  `private_founder_review_ready`.
- `WHOLE_VIDEO_QA_PROFILE` and related QA profile structures are largely metadata and human-review contracts; their
  existence is not proof of fully automated semantic creative QA. The v2 lifecycle records automated bounded cell
  evidence and explicit human acquisition/whole-video outcomes without treating either as founder acceptance.
- The initial Core mascot performance pack covers umbrella resistance, sorting/decisions, and selective effort on
  reachable objects. A different required semantic performance must stop with `CORE MASCOT PERFORMANCE MISSING` and
  enter a separately bounded acquisition/approval step; current coverage is intentionally not a complete pose pack.

Do not delete or modify these areas merely because they are bounded or incomplete. Resolve each through a separately
authorized implementation phase.

## Schema authority

Application schema authority is the `schema_migrations` table with contiguous versions **1 through 28**. The current
maximum application migration is **28**. Migration 28 adds only append-only production-run events, cross-stage
evidence, QA-review outcomes and founder-review decisions; existing generation, persistent-scene, narration and media
tables remain authoritative for their artifacts.

`PRAGMA user_version = 0` does not mean that no application migrations exist. `PRAGMA schema_version = 203` is
SQLite's internal schema-cookie counter, not the Conveyor application migration version.

Migrations 25–27 remain immutable historical provenance. Migration 28 is current application schema authority. The
protected production runtime was intentionally not opened or migrated during implementation verification; applying
Migration 28 there requires the separately authorized production-runtime transition before the lifecycle is used.

For read-only database auditing, do not instantiate application repository code: repository construction can apply
migrations or seed data. Use an explicitly read-only method under a separately authorized audit procedure.

## SimilarStoic's role

SimilarStoic is where Conveyor's generalized capabilities are first exercised against a real channel. Its accepted
creative language, narrator choices, audience strategy, and editorial rules are channel-specific evidence that can
improve Conveyor. They must not hard-code SimilarStoic ownership into the platform or turn its creative preferences
into universal rules for every future channel.

The strategic direction remains a useful, evidence-led explanatory channel spanning money, work, behaviour, and life
strategy. Current detailed channel strategy lives in bounded SimilarStoic documents and `ROADMAP.md`; current
operational status always resolves here.

## Historical and evidence policy

Preserve knowledge that explains why the system exists while removing its ability to confuse current operation.
Evidence can be conceptually classified as:

- accepted;
- rejected;
- experiments;
- archives; or
- disposable.

This classification is not authorization to move or delete evidence. Historical documents retain their original
claims as provenance. Their current-looking language must be read in the context of their dated snapshot and the
historical notice at the top of the file.

The [rejected SimilarStoic v028 prototype evidence](evidence/experiments/REJECTED_V028_PROTOTYPES.md) is a bounded
historical record of non-canonical experiments, not active production tooling.

## Safe starting procedure for a fresh agent

1. Read this document before treating any other status or handoff file as current.
2. Confirm the repository is `D:\ConveyorOS\source\Conveyor`, expect a clean working tree unless the authorized task
   deliberately creates changes, and inspect `git status` without altering it.
3. Do not restore the rejected v028 prototypes into active `scripts/`; consult their
   [evidence index](evidence/experiments/REJECTED_V028_PROTOTYPES.md) only when historical context is relevant.
4. For authorized production operation in a new PowerShell process, dot-source
   `scripts/set_conveyor_environment.ps1` and inspect the five resolved values.
5. Fail closed if the structure or required runtime paths differ; do not recreate legacy roots or accept relative
   production fallbacks.
6. Do not open the production database through application code merely to inspect it.
7. Before any consequential action, identify the exact authorization boundary: code, migration, provider, spend,
   production, publication, evidence movement, and Git operations are separate decisions.
8. Use `ROADMAP.md` for future direction, bounded design documents for their subjects, and historical snapshots only
   for provenance.

Reading or dot-sourcing the environment script does not itself authorize starting Conveyor.

## Current cleanup and migration boundaries

At this checkpoint:

- source/runtime relocation is complete;
- the durable runtime environment contract and storage-path normalization are complete;
- documentation authority consolidation and final reconciliation are complete;
- CI restoration is complete;
- rejected-v028 prototype preservation and disposition are complete;
- Git working-tree cleanup is complete;
- the `project_atlas` technical rename, `AtlasRepository` rename, and `ATLAS_*` compatibility migration remain future
  bounded work;
- the legacy v1 `AssetSelection` ingress remains available and unchanged while canonical v2 production uses its
  explicit `/api/v2/productions` lifecycle;
- QA automation improvements and expansion of the approved Core mascot performance pack remain future bounded work;
- broader evidence/work-directory cleanup and multi-channel expansion remain future bounded work;
- no compatibility junction is authorized;
- no schema cleanup migration is authorized;
- no Production #7 work has begun; and
- provider calls, spend, application startup, publication, and runtime mutation require separate authorization.

Update this file deliberately whenever accepted current operational truth changes. Do not turn it into a chronological
diary; move superseded detail to historical/provenance records and keep this document usable as a fresh-agent entry
point.
