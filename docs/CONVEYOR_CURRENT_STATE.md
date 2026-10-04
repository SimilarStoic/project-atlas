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
- After post-acquisition founder narration authorization (a recorded action; the frozen request is unchanged; at most one
  narration call per run), the verified local full suite is **361 passed, 0 skipped, 0 failed**.
- Repository CI is restored to green for Ruff lint, Black formatting, and pytest. Verify the current run live when its
  result matters.
- The SHA-256 `97FF9F4B37766A98BE3C94506D5E45A399648B070DEAC686CA25EF755B29EDE2` is a historical
  pre-Migration-28 verification checkpoint. Migration 28 and legitimate Production #7-era writes changed the
  protected runtime afterward; do not treat that hash as its current value.

The founder-rejected, non-canonical v028 prototype scripts were intentionally removed from active `scripts/` after
preservation. Their exact source bytes and representative visual evidence are stored outside the repository at
`D:\ConveyorOS\archives\experiments\similarstoic\rejected-v028\2026-09-01\`. The tracked
[rejected-v028 evidence index](evidence/experiments/REJECTED_V028_PROTOTYPES.md) records their disposition. Do not
restore them or treat them as production tooling merely because historical evidence exists.

## Current production status

**SimilarStoic is production-worthy now.** The founder-approved public-production-quality baseline is
`output/production-tests/next-private-production/next-private-production.mp4` (SHA-256
`FE99094664FF2F3514BC4D66485FD24BDD2A63591811F98EE6C89DF0DC566B3A`, 38.720 seconds). This local artifact is the
creative-treatment reference, not a publication authorization or a scene library. Future videos must use new topics,
scripts, and scenes through the same production method recorded in
[`SIMILARSTOIC_CREATIVE_CALIBRATION.md`](SIMILARSTOIC_CREATIVE_CALIBRATION.md#founder-approved-production-method),
not reuse this video's content.

Fundamental visual tweaking is complete. Continue to improve character continuity without sacrificing expressive
variation, generate enough meaningful narration-driven scene changes to sustain engagement, and preserve factual
sources with appropriate publication-flow attribution. These are continuing quality improvements, not blockers and
not reasons to redesign the approved visual treatment or restart architecture experimentation. The successful eight
beats over approximately 39 seconds are evidence for useful density, not a universal beat-count rule.

The approved MP4 was assembled outside Conveyor's canonical production path: its eight images came from Conveyor's
generation service against a scratch database copy, it reuses the Production #7 attempt-2 Daniel narration, and its
final assembly procedure was not preserved. Canonical v2 has since reproduced the approved method offline from the
preserved beats and narration (Phase 1 replay, reaching `private_founder_review_ready`). That replay is technical
evidence, not founder acceptance of a new production.

Preserved evidence:

- approved baseline: `D:\ConveyorOS\evidence\similarstoic\approved-production-baseline\2026-10-03-v1\`
  (backup `D:\ConveyorBackups\approved-production-baseline\2026-10-03-v1\`);
- Phase 1 replay: `D:\ConveyorOS\evidence\similarstoic\phase1-replay\`;
- production DB backup (post-Migration-28, pre-Claude-implementation):
  `D:\ConveyorBackups\post-migration-28-pre-claude-implementation-2026-10-03\`.

Conveyor already models research provenance through `ResearchPack`, `Claim`, `Source`, `ClaimEvidence`, and
`ScriptClaimSet`. The bounded remaining integration is to project the sources supporting a production's approved
script claims into publishing-package source/credit metadata; extend those existing structures rather than inventing
a second sourcing subsystem.

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

Do not reopen P6 merely to make it pass. Production #7 and its experiments supplied later private evidence; the
founder-approved baseline above is the current creative authority.

P6 evidence included halos/edge defects, long static stretches, weak background semantic support, repeated poses and
hamster blocking, a ghost circle, character drift, a pronunciation issue, and a repeated ending. Narration was the
strongest component. These findings explain learned rules. Production #5 v4 remains historical accepted evidence;
the founder-approved `next-private-production.mp4` identified above is the current creative baseline.

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
- `static_character.py` is tested but currently has no production caller.

Do not delete or modify these areas merely because they are bounded or incomplete. Resolve each through a separately
authorized implementation phase.

## Canonical v2 fidelity and safeguards

Canonical v2 previously could not render full-frame beats acceptably: its compositor forward-maps source pixels, so
upscaling a 941x1672 generated image to the 1080x1920 frame left about 24% of pixels unwritten (a visible grid).
This is fixed by:

- a versioned scene adapter, `managed-image-to-rgba-v2`, that resamples full-frame variants to exactly 1080x1920
  with bit-exact FFmpeg Lanczos scaling and records the scale method in derived-asset metadata (derived raster IDs
  are versioned so pre-fix rasters are never reused);
- a production guard that rejects any layer mapping requiring upscale and requires full-frame layers at exact 1:1;
- a pre-encode compositor coverage gate: every composited frame must have zero unwritten alpha pixels.

New persistent snapshots freeze render profile `similarstoic-vertical-v3`: libx264 CRF 18, preset medium, yuv420p,
1080x1920 at 30 fps, AAC 192k mono 48 kHz, faststart. Existing `similarstoic-vertical-v2` behaviour is unchanged:
v1 AssetSelection snapshots and older persistent snapshots keep their historical encoding.

v2 production requests now:

- require an explicit boolean `narration_authorized`, frozen into the request digest; narration fails closed before
  any synthesizer call when it is not `true`;
- treat `forecast.image_calls` as a frozen per-run ceiling counted per recorded provider generation call, including
  failed calls (`forecast.narration_calls` must be 1);
- check generation authority before any provider call and the persisted execution provenance after each call; a
  mismatched execution counts as a call but is never admitted as an acquisition;
- require full-frame integrated beats to carry the request's character authority, while non-full-frame
  characterless entities remain allowed.

Acquisition review and retry:

- Rejected raw images can be reacquired within the same production run.
- Acquisition reviews are round-scoped and bound to the exact asset reviewed, and previously passed variants are
  never regenerated.
- Rejected and retried generation attempts continue to count toward the frozen image-call ceiling.
- Narration does not begin until every currently active variant has a passing acquisition review.

Full-frame aspect admission:

- Full-frame generated results are checked against the approved 9:16 shape immediately after generation.
- A source more than 0.5% relative error from 9:16 is technically rejected before founder review. The rejected
  attempt still counts toward the image-call ceiling, is never presented as an active founder-review asset, and only
  the affected variant is regenerated.
- The assembly-time full-frame aspect check remains as defense in depth.

Automated cell QA claims only persistent-aggregate verification and compositor coverage
(`conveyor-automated-cell-v2`); perceptual final-frame quality remains human review.

Canonical post-narration retiming (`retime`, also `POST /api/v2/productions/{run}/retime`):

- It is available only from `qa_review_pending`, or after a failed whole-video QA (`failed` at stage `qa`).
- Caller-supplied per-beat durations must sum exactly to the persisted narration duration.
- The approved images, scene states and narration are reused, with zero provider calls.
- Outputs are versioned, and all prior snapshots, renders and reviews are preserved.
- The newest successful render is the current render; later human whole-video QA binds to it.
- Retime is refused after a founder decision, or once any render of the run has been packaged.
- A failed retime has no recovery path yet.

Explicit claim-timed citation overlays are supported.

- They come only from an optional `citations` request field. Each citation has a scene, a label of 24 characters or
  fewer, and source IDs drawn from the script's frozen ScriptClaimSet. They are frozen in the request digest and are
  never inferred.
- Each citation is bound to one Scene, rendered small in the upper-right safe area only while that Scene is on screen,
  and carried through retime with its timing recomputed.
- Productions without citations render exactly as before.

## Schema authority

Application schema authority is the `schema_migrations` table with contiguous versions **1 through 28**. The current
maximum application migration is **28**. Migration 28 adds only append-only production-run events, cross-stage
evidence, QA-review outcomes and founder-review decisions; existing generation, persistent-scene, narration and media
tables remain authoritative for their artifacts.

`PRAGMA user_version = 0` does not mean that no application migrations exist. `PRAGMA schema_version = 203` is
SQLite's internal schema-cookie counter, not the Conveyor application migration version.

Migrations 25–27 remain immutable historical provenance. Migration 28 is current application schema authority and was
applied to the protected production runtime on 1 October 2026 after a dedicated pre-migration backup. Subsequent
authorized Production #7-era activity produced legitimate runtime writes; the old pre-migration hash is historical.

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
- QA automation improvements and the `static_character.py` production-integration decision remain future bounded
  work;
- broader evidence/work-directory cleanup and multi-channel expansion remain future bounded work;
- no compatibility junction is authorized;
- no schema cleanup migration is authorized;
- Production #7-era private work occurred and informed the founder-approved production baseline; and
- provider calls, spend, application startup, publication, and runtime mutation require separate authorization.

Phase 1 (canonical v2 fidelity) and Phase 1B (acquisition retry rounds and aspect admission) are complete. Remaining
gaps are:

- recipe binding, including moving the full-frame character requirement into the channel recipe;
- source-credit projection;
- character continuity;
- scene density;
- speech-aligned beat timing;
- ceiling counting of generation calls that raise before acquisition evidence is persisted. This covers both a paid
  provider call that raises before evidence is recorded, and a provider call that returns an asset but whose
  post-provider technical inspection or probe raises before evidence is recorded;
- image size on reference-conditioned calls: a configured image size may be recorded in provenance but is not sent
  on reference-conditioned image-edit calls, so those calls use the provider's default size;
- initial beat timing is estimated before narration exists and may require a post-narration retime;
- narration word timestamps are not persisted, so captions are not fully speech-aligned;
- packaging does not yet require the current, founder-accepted render.

Each requires separate authorization.

Update this file deliberately whenever accepted current operational truth changes. Do not turn it into a chronological
diary; move superseded detail to historical/provenance records and keep this document usable as a fresh-agent entry
point.
