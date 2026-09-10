# Conveyor — Current Status

## Last Updated

10 September 2026 — Multi-authority visual-generation implementation is synchronized at
`1284e344b376e550b0a06ee79e79e9ae478b96c2`. Production #5 v3 establishes the reference-driven scene-generation
method as the intended SimilarStoic default and reached approximately 85–90% of desired public-launch quality. Its
artifact remains **MIXED / TARGETED FINAL REPAIR** and acceptance is on hold while bounded v4 precision cleanup is
active. Exact v1–v3 artifacts and immutable evidence remain preserved. Productions #2–#4 remain accepted.

## Current State — Read This First

The canonical [SimilarStoic Visual-Production Vocabulary](docs/SIMILARSTOIC_VISUAL_VOCABULARY.md) defines the compact
acting, environment, prop/effect, composition, reuse and break-frame design language for future visual work. It adds no
runtime architecture and authorizes no production or generation.

The [multi-authority visual-generation design](docs/MULTI_AUTHORITY_VISUAL_GENERATION.md) specifies the smallest
provider-neutral bridge from those approved visual-DNA authorities to scene-specific generation. The local
implementation preserves `VisualStyleProfile`, `CharacterProfile` and `CharacterReferenceSet`; Migration 24 adds typed,
digest-backed non-character authorities plus immutable per-execution recipe provenance; composition remains
guidance/local assembly rather than a new executable asset type. The persistent runtime is migrated and the minimum
approved authorities are materialized, but this implementation is not canonical until its pending commit is reviewed
and pushed.

The [post-production quality-cycle note](docs/QUALITY_CYCLE_20260902.md) records the reviewed continuity findings and
[evidence manifest](docs/QUALITY_CYCLE_20260902_MANIFEST.json). Production #1's original Hazel, Marin v2 and presentation
proofs remain founder-rejected for final quality. The later 18.03-second audiovisual integration proof is accepted: it
combined approved stills with restrained motion, idea-led cuts, subordinate speech-aligned captions and complete
narration. OpenAI `gpt-4o-mini-tts-2025-12-15` / Marin is the **PROVISIONAL ACCEPTED PRODUCTION BASELINE**,
not the permanent SimilarStoic narrator. The earlier GPT Image 2 full-scene reference-board method failed, while the later isolated-character
method passed: founder + ChatGPT accepted
`assets/visual-references/core-mascot/poses/core-v3-umbrella-resistance-acting-pose-v1.png` as the first approved
secondary acting-pose reference. Founder + ChatGPT subsequently selected
`assets/visual-references/environments/style/similarstoic-default-scene-language-v1.png` as the approved environment
style / default-scene-language reference. The primary Core v3 identity reference and approved acting pose remain
unchanged. Static integration and its bounded refinement both passed; the exact approved result is tracked as
`assets/visual-references/compositions/grammar/similarstoic-static-composition-grammar-v1.png`. Founder + ChatGPT also
accepted the calm sorting acting pose, indoor environment example and portrait composition example #2. **Static
visual-production method demonstrated successfully across two materially different scene types:** outdoor/high-action
storm and calm indoor/explanatory sorting. Founder + ChatGPT have now also accepted the “things in your hands” acting
pose, abstract reach-boundary environment and balanced composition example #3. This establishes a third bounded static
capability—abstract explanatory metaphor without text-dependent meaning—without claiming universal repeatability.
Founder + ChatGPT have also accepted the first rare special break-frame example: a hand-drawn gross-up close-up for
“One Notification, End of Days,” tracked at
`assets/visual-references/break-frames/examples/similarstoic-hand-drawn-gross-up-notification-v1.png`. It is bounded
evidence for a comedic interruption mode and does not replace or alter ordinary identity, acting-pose, environment or
composition authority.

Phase 1 is complete; Phase 2 remains ACTIVE / INCOMPLETE; v0.27 remains the latest named accepted implementation.
Production #2, **Why a paid-off credit card can still affect your score**, completed the existing governed lifecycle
and is accepted. Its exact brief and acceptance record are in
[Production #2 — Bounded Design](docs/PRODUCTION_2_DESIGN.md). This acceptance did not itself select v0.28, authorize a
successor milestone or rig, or promote rejected `ad52ab3` material.

Production #3, **The £300 monthly upgrade that quietly adds up to £72,000 over 20 years**, also completed the governed
lifecycle and is accepted. Its exact design and acceptance record are in
[Production #3 — Bounded Design](docs/PRODUCTION_3_DESIGN.md). The direct nominal arithmetic remains
`£300 × 12 × 20 = £72,000`; no return, inflation or wealth outcome is implied.

Production #4, **Three AI workflows that make a junior analyst more valuable**, completed the same governed lifecycle
and is accepted. Its exact design, execution and acceptance record are in
[Production #4 — Design and Acceptance](docs/PRODUCTION_4_DESIGN.md). It promises no career outcome, requires human
verification of important output and keeps sensitive information out of unapproved tools.

The production-method validation objective is **PASSED**, while public-launch quality is **NOT YET PASSED**. Production
#5 establishes **REFERENCE-DRIVEN DYNAMIC SCENE GENERATION: PASS**, while both exact v1 and v2 final artifacts remain
**MIXED / REVISE** and **ACCEPTANCE: HOLD**. V3 is the only active correction. It must repair physical cable topology,
make the grid-connection queue self-explanatory, preserve scene richness, use materially larger stable captions, keep the
camera static by default and pass actual full-frame plus phone-scale vision review before a new founder gate.
Marin remains usable for development but narrator quality is **PROVISIONAL / UPGRADE REQUIRED BEFORE OR DURING
LAUNCH-QUALITY FINALIZATION**. The active envelope after v2 is `$6.43 / $10` with `$3.57` remaining.

[Controlled Publishing and Performance Learning Loop](docs/PUBLISHING_AND_LEARNING_LOOP.md) separately defines a
YouTube Shorts-only pilot, one founder gate for the exact external publication action, and append-only performance and
learning provenance. It is synchronized design authority only: no platform implementation, API call, publication,
publishing migration or Production #5 execution has occurred.

The [minimum repeatable production cadence](docs/SIMILARSTOIC_PRODUCTION_CADENCE.md) targets one
founder-review-ready short per five working days with work in progress limited to one. It automates routine selection,
research/editorial preparation, production mechanics and QA while retaining final artifact, canon, publication,
exceptional spend and architecture decisions at founder gates. Routine productions may use the active `$10` quality
envelope without separate per-production spend gates. Stop before exceeding the envelope, or when remaining authority
falls below `$2` while further paid work would be useful.

The source-of-truth order is: **(1) current GitHub `main`; (2) canonical tracked documentation; (3) source,
migrations and tests; (4) verified persistent runtime; (5) verified local experimental/review evidence;
(6) continuity handoff; (7) chat recollection.** Founder is
final authority for product direction, architecture, quality acceptance, milestone selection, destructive actions and
push. ChatGPT is product architect, specification steward and anti-drift reviewer; Codex is the bounded inspection,
implementation, testing and validation agent. Governing principle: **CHANGE WITHOUT REBUILD**.

### Current canonical state and historical pre-reconciliation context

- **Base before this publishing/learning design candidate:** local `main` and `origin/main` both resolved to
  `48c79b7216e4793b1d9d7dfcb939aeebaf3038c6`, ahead/behind `0 / 0`, with the tracked tree clean. Rejected
  `ad52ab38ad32f97b933099ef98a32dc8fd268662` remains preserved separately and is not an ancestor of this candidate.
  The earlier 2 September synchronization recorded `f44f65b` with ahead/behind `0 / 0` immediately before its
  documentation commit; that remains historical checkpoint context. Phase 2 is ACTIVE /
  INCOMPLETE; v0.27 remains the latest named accepted implementation milestone; source and verified runtime migrations
  are contiguous through 24 in the pending implementation candidate. The post-v0.27 changes do not imply acceptance
  of v0.28 or a successor milestone.
- **Historical pre-reconciliation context:** remote `origin/main` was
  `5220320ef81e422dec338b8410ad80b5491c0f31`, with Migration 21 then latest. Local `HEAD` was
  `2358f244b48db9cae49e0a0bc8b1ec9ce0525811`, four commits ahead and zero behind, before founder review and the
  authorized push. That candidate history comprised:
  `5396247` deterministic static mascot production path; `c1b2638` generated narration provenance; `cf3b1a4` local
  narration recovery; `2358f24` OpenAI narration refinement / Migration 23.

Historical accepted-checkpoint text below remains historical context. It does not override this current reconciliation.

## Persistent Runtime and Production #1

The selected persistent runtime is outside Git at `D:\ConveyorRuntime\conveyor.db`, `assets\`, and `media\`.
`D:\ConveyorRuntime` is a workstation convention, not a hardcoded requirement; the portable contract remains
`ATLAS_DB_PATH`, `ATLAS_ASSET_STORAGE_ROOT`, `ATLAS_MEDIA_STORAGE_ROOT`, `ATLAS_FFMPEG_PATH`, and
`ATLAS_FFPROBE_PATH`. No runtime data is tracked.

SQLite `integrity_check` is `ok`; migrations 1–24 are contiguous. Migration 22 adds generated narration provenance
and immutable terminal `NarrationGenerationExecution` history. Migration 23 truthfully permits `openai_tts` alongside
`local_system_speech`. Migration 24 adds immutable multi-authority visual-reference persistence and direct generation
execution lineage. These post-v0.27 changes do not create a v0.28 milestone.

**Production #1 did occur through the persistent Conveyor lifecycle.** Its technical/end-to-end trial is completed,
but its production-quality acceptance is **FAILED / NOT ACCEPTED**. The approved Script/content was broadly
acceptable; neither original media artifact nor the later presentation proof is accepted as final SimilarStoic
channel quality.

- Hazel baseline `final-media-artifact-similarstoic-control-v1-hazel-desktop-v1`: SHA-256
  `ae326e5722f5d361d6cf0b382e454639cdcca2ec7899439af0839e92cba621ef`, 45.168 s. It worked technically, but founder
  found the narration robotic, visuals static, captions dominant, and engagement weak.
- OpenAI/Marin refinement `final-media-artifact-similarstoic-control-v1-refined-openai-marin-v2`: SHA-256
  `e26f386e10d4a443247f98801ed48592876ca67a4af0e180864fdc392956ec7e`, 34.400 s. Its narration was materially more
  natural, but it was not accepted as a unique permanent SimilarStoic voice; the mascot remained too static and the
  typography, captions, scenes and backgrounds were not engaging enough.

`Microsoft Hazel Desktop` is technically functional but founder-rejected for robotic quality. OpenAI
`gpt-4o-mini-tts` / `marin` created the immutable narration execution
`narration-generation-similarstoic-control-v1-openai-marin-attempt-1` and narration SHA-256
`648c1be676cd6a68731844a9fc9676116b32f23f316ac7e6d0379af005e74486`. Custom-voice capability was inspected
read-only and was unavailable through the configured endpoint/account; no consent recording or founder voice was
uploaded, and no custom voice was created.

The flattened mascot was the Production #1 visual reference. Later facial-overlay, deterministic motion, layered
reconstruction and rig experiments were founder-rejected/non-canonical: no canonical rig exists, the flattened source
proved insufficient for high-quality programmatic reconstruction, and the static-character presentation is not the
accepted final SimilarStoic identity standard. No v0.28 milestone is selected.

Production #2 has **completed and passed founder + ChatGPT final quality review**. The mutable
`credit-utilisation` Opportunity is `accepted` and records the accepted artifact identity while the immutable render
and artifact rows preserve their exact at-render review state. Governed lineage includes research pack
`research-pack-similarstoic-credit-utilisation-v1`, Script `script-similarstoic-credit-utilisation-v1`, VisualPlan
`visual-plan-similarstoic-credit-utilisation-v1`, input snapshot
`final-media-input-snapshot-similarstoic-production-2-v1` and final artifact
`final-media-artifact-similarstoic-production-2-founder-review-v1`. The runtime-managed MP4 has SHA-256
`ea7f490c046eb424624fb5147d84e792dff561af76f345ecc1ca068c5f7a5493`; it is 48.120 seconds, 1080×1920,
30 fps H.264/AAC. Exact narration completeness is 126/126 words and all 32 caption cues use final-master speech
alignment. Six-scene visual continuity passed. The MP4 remains managed runtime/ignored review evidence rather than a
tracked repository binary.

Production #3 has **completed and passed founder + ChatGPT final quality review**. The mutable
`lifestyle-inflation` Opportunity is `accepted`; immutable render and artifact rows preserve exact at-render history.
Governed lineage includes research pack `research-pack-similarstoic-lifestyle-inflation-v1`, Script
`script-similarstoic-lifestyle-inflation-v1`, VisualPlan `visual-plan-similarstoic-lifestyle-inflation-v1`, narration
`narration-asset-similarstoic-production-3-marin-v1`, input snapshot
`final-media-input-snapshot-similarstoic-production-3-v1` and final artifact
`final-media-artifact-similarstoic-production-3-founder-review-v1`. The runtime-managed MP4 has SHA-256
`8153d42cc006e79ddbd90502f2f9be3a0d4a7b6fe6226c01657a50bd65145dd4`; it is 48.450 seconds, 1080×1920,
30 fps H.264/AAC. Exact narration completeness is 126/126 canonical words and 130/130 normalized spoken tokens; all
21 semantic caption cues use final-duration speech alignment. Six-scene visual continuity and full decode passed.

Production #4 has **completed and passed founder + ChatGPT final quality review**. The mutable `ai-workflow`
Opportunity is `accepted`; immutable render and artifact rows preserve exact at-render history. Governed lineage ends
at `final-media-artifact-similarstoic-production-4-founder-review-v1`. The runtime-managed MP4 has SHA-256
`a9a15ec24be9ed11df601c61a6dd5ff5e42a983b81449fc2dffefe795c7118ac`; it is 65.400 seconds, 1080×1920,
30 fps H.264/AAC. Exact normalized narration completeness is 144/144 words; all 21 semantic caption cues use final-audio
alignment. Six-scene identity, visual, editorial and technical QA passed. Its bespoke auditor pose remains production
evidence rather than a new reusable canonical authority.

Founder + ChatGPT accepted the local audiovisual integration proof at
`D:\ProjectAtlas\work\similarstoic-audiovisual-proof-20260909\founder-review\similarstoic-audiovisual-integration-proof-v1.mp4`,
SHA-256 `1267f9c05c3431ee2d71fe73433f318efc9bfb935616a13fd56593500f7d55ca`, 18.03 seconds, 1080×1920 H.264/AAC.
This acceptance proves the validated static language can support restrained motion, idea-led cuts, subordinate captions
aligned to actual speech and complete narration while preserving identity. It does not make all future videos ready.
Marin is accepted for current production development only; permanent narrator identity remains open and replaceable.

`D:\ProjectAtlas\data\atlas.db` is protected legacy/local historical state, distinct from the runtime, with verified
SHA-256 `5B414FBE03BF86765FFCB095715B12F3CCDBC064E797552C41D140E6B6B3320E`.

The isolated acting-pose experiment established the approved secondary pose. Subsequent separated-environment tests
rejected a detailed cinematic street, then calibrated a sparse hand-drawn direction across Candidates 1–4. Founder +
ChatGPT selected Candidate 4 as the environment style/default-scene-language reference and Candidate 3 as useful
untracked evidence for the viable lower-detail pole. Candidate 4 is approximately the upper normal detail boundary for
an ordinary scene; it is not mandatory reusable scenery, a universal background or a permanent provider selection.
The visual method now consists of canonical identity authority, approved acting-pose references, approved Default Scene
Language, approved environment examples, approved composition grammar, approved composition examples and a distinct
rare special break-frame example. The separated
method has passed across outdoor/high-action storm, calm indoor sorting and abstract explanatory metaphor. Production
#5 v1 added `$1.2855625` conservative/calculable exposure through five image calls, two TTS calls and four Whisper calls,
bringing the active `$10` envelope to `$5.68` used and `$4.32` remaining. Production #2 added `$0.781255` conservative exposure, rounded to `$0.79`: three successful image calls,
one successful and one failed-transfer TTS call, and two Whisper calls covering 90 provider-reported seconds. No exact
provider-reported dollar charge was returned. Production #3 added `$0.0170125`, rounded to `$0.02`, through one Marin
TTS call and one 49-second Whisper alignment; its six visuals used approved assets and local composition at zero image
provider cost. Production #4 added `$0.557925`, rounded to `$0.56`, through two image calls, three TTS calls and five
Whisper calls covering 262 provider-reported seconds; rejected and diagnostic attempts remain included. No response
returned an actual dollar charge. The break-frame
sequence rejected machinery/cinematic, rough-cartoon and photoreal gross-up directions before the accepted hand-drawn
gross-up; canonicalization added `$0` provider spend. This is bounded evidence, not universal repeatability or a new
architecture.

## Exact Next Action

Review and push the validated Migration 24 multi-authority visual-generation implementation candidate. Production #5
remains reserved and must not start until this implementation is accepted, pushed and synchronized. Publishing and
learning persistence remains unimplemented and will use the next available migration, currently expected to be 25.
No external publication, Production #5 execution, Production #6, v0.28 or rig is part of this candidate.

The [quality-cycle note](docs/QUALITY_CYCLE_20260902.md) also qualifies spend estimates and the reference-set ID reused
across separate database histories. Use database + member + digest, not the set ID alone, when reporting provenance.

The bounded Atlas v0.9 Visual Style Control Foundation, v0.10 Visual Style Fidelity Refinement, v0.11
Character Continuity Foundation, v0.12 Canonical Character Reference Foundation, v0.13 Reference-Grounded
Character Generation, and v0.14 Explicit Character Reference Bootstrap are complete and pushed. The
founder-approved Phase 1 visual baseline is SimilarStoic Core v3; v2 remains historical and immutable.

The v0.1 UI baseline, v0.2 persistent discovery foundation and v0.3 research and evidence foundation are implemented and safely stored on GitHub.

Atlas v0.8 through v0.14 are complete and pushed. Conveyor now has immutable, versioned character identity,
canonical visual-reference foundations, reference-grounded character generation, and explicit first-reference
bootstrap alongside the founder-approved SimilarStoic Core v3 visual-style baseline.

## Current Product Identity

**Conveyor** is the current engine, project and operating-system identity. **Project Atlas** is the historical/legacy
project name. **SimilarStoic** remains the outward-facing channel, editorial brand and mascot world: **SimilarStoic by
Conveyor**. Legacy Atlas technical identifiers remain intentionally preserved for compatibility, including
`project_atlas`, `project-atlas`, `Atlas*`, `ATLAS_*`, `data/atlas.db`, `atlas_recommendation`, API routes and the
GitHub repository/remote name. Historical Project Atlas records remain historical truth and are not rewritten. This
rename creates no implementation milestone and does not change schema, migrations, package namespace, environment
variable names, DB path, API routes, GitHub repository name, or successor state.

---

# Completed

## Accounts & Infrastructure

- SimilarStoic Gmail created
- SimilarStoic GitHub account created
- Private `project-atlas` GitHub repository created
- Project located at `D:\ProjectAtlas`
- Git for Windows installed
- Git repository initialised
- `main` branch established
- GitHub remote configured
- Initial commit created
- Initial commit pushed to GitHub

## Historical v0.14 Git Checkpoint

Current commit:

`516884b8fab0a29e8e82973d684be1ae8a08bff6 feat: add character reference bootstrap`

Branch:

`main`

Remote:

`origin https://github.com/SimilarStoic/project-atlas.git`

Working tree:

Clean at the accepted v0.14 checkpoint; local `main` matched `origin/main` at acceptance.

Validated state:

- Ruff passed.
- Black `--check` passed.
- pytest: **75 passed** at the accepted v0.14 checkpoint.
- `git diff --check` passed.
- SQLite migrations: **1–11**.

## Atlas v0.18 Checkpoint

**Project Atlas v0.18 — Readiness-Authorized Editorial Angle Initiation** is the accepted implementation
checkpoint.

- v0.18 is the historical accepted predecessor to v0.19; v0.17 is its historical accepted predecessor.
- Migration 15 is canonical; SQLite migrations extend through **1–15**.
- An EditorialAngle can be created under one exact explicitly supplied `Ready` ResearchReadinessAssessment through
  immutable direct provenance: **this EditorialAngle was initiated under this exact Ready
  ResearchReadinessAssessment.**
- Historical/demo/legacy Angles retain null provenance without backfill, and low-level legacy creation remains
  compatible.
- Readiness is neither current/latest state nor consumed; one Ready assessment may support multiple Angles, and
  later reassessments do not rewrite prior provenance.
- Existing same-ResearchPack Claim-link semantics remain unchanged; no frozen Claim matching, automatic
  ContentPiece/Script creation, `Opportunity.status` mutation, workflow state or UI was introduced.
- Validation passed: **86 tests passed**; Ruff, Black `--check`, and `git diff --check` passed.
- Phase 2 remains ACTIVE / INCOMPLETE; Phase 1 remains complete, later phases remain unactivated, and no successor
  after v0.19 is selected.

## v0.19 Accepted Checkpoint

**v0.19 — Editorial-Angle-Authorized ContentPiece Initiation** is the accepted implementation checkpoint. It adds
the deliberate lifecycle edge: explicit creation of a
ContentPiece from one exact eligible Opportunity-owned EditorialAngle that already carries its exact immutable
`Ready` ResearchReadinessAssessment provenance. The lifecycle path requires exact Opportunity/Angle
lineage, non-null provenance, exact existing `Ready` assessment, and internally consistent assessment →
ResearchPack → Angle → Opportunity lineage; it must not select latest/current/any Ready or substitute an
assessment.

Legacy/demo/seed null-provenance Angles remain valid and unmodified but are ineligible for this path; existing
low-level ContentPiece creation remains compatible. The existing immutable ContentPiece → EditorialAngle reference
provides the durable chain to readiness: no duplicate assessment reference or migration 16 was added. One eligible
Angle may initiate multiple ContentPieces; no consumption/current/latest/progressed state,
upstream revalidation, UI, editorial package, Title/Hook/Script, Editorial Gate, provider call, production,
publishing, analytics or orchestration is included. The API is
`POST /api/opportunities/{opportunity_id}/content-pieces`.

- Founder + ChatGPT acceptance is granted for implementation commit
  `32812e6793d9b06632ebffd82504cd8810c2ab3d`.
- Validation passed: Black 26.3.1 `--check`, Ruff, **88 pytest tests**, and `git diff --check`.
- v0.25 — Operational Visual Production Inputs is the latest accepted implementation milestone; v0.24 is its accepted
  historical predecessor. Migration 20 is latest, migration 21 is absent, and no successor after v0.25 is selected.

## v0.20 Accepted Checkpoint

**v0.20 — Readiness-Lineage-Preserving Script Initiation** is the accepted implementation checkpoint. It adds one
deliberate lifecycle edge:
an eligible ContentPiece → one complete immutable Script version. Eligibility is derived only from durable
ContentPiece → EditorialAngle → exact `Ready` ResearchReadinessAssessment → ResearchPack → Opportunity lineage;
it does not record a lifecycle marker, add readiness provenance to Script or ContentPiece, select another Ready
assessment, or revalidate research. The repository allocates each new Script version as immutable history from
existing versions, while low-level Script creation remains compatible.

The narrow API is `POST /api/content-pieces/{content_piece_id}/scripts`, accepting only Script ID, narration text
and optional metadata. It rejects caller version/readiness/lineage overrides and invalid provenance. No migration,
Title/Hook, Script-to-Claim, QA/Gate, workflow, UI, VisualPlan, production, publishing, analytics or orchestration
is included. v0.25 — Operational Visual Production Inputs is the latest accepted successor; v0.24 is its accepted
historical predecessor. Migration 20 is latest, migration 21 is absent, and no successor after v0.25 is selected.
Validation passed: Black 26.3.1 `--check`, Ruff, **90 pytest tests**, and `git diff --check`.

- Implementation commit: `8dd8ecb7c22eb73b60b7d65853fbf11635d2188c`.
- Initial documentation commit: `4ddab9749c2159ad7a9801f0af1d5365046ac793`.

## v0.21 Accepted Checkpoint

**v0.21 — Editorial Draft Package Foundation** adds durable, append-only `TitleOption` and `HookOption` records
for one eligible ContentPiece, plus immutable `EditorialPackageSnapshot` records that freeze one explicitly supplied
TitleOption, HookOption and exact Script version from that same ContentPiece. `ContentPiece.working_title` remains
unchanged compatibility data: it is neither backfilled nor synchronized with TitleOptions.

Each dedicated creation path reuses the exact durable ContentPiece → EditorialAngle → `Ready`
ResearchReadinessAssessment → ResearchPack → Opportunity eligibility chain. No readiness reference is duplicated on
the new records. Migration 16 is additive only: it adds `title_options`, `hook_options` and
`editorial_package_snapshots`, restrictive foreign keys and history indexes, with no backfill or current/selected
state. The API exposes ContentPiece-scoped create/history routes and narrow record retrieval routes.

v0.21 excludes package approval, current/latest/selected semantics, Script-to-Claim, editorial QA/Gate, workflow,
UI, production, publishing, analytics, Learning and orchestration. It is accepted. No successor after v0.21 is
selected. Validation passed: Black 26.3.1 `--check`, Ruff, **93 pytest tests**, and `git diff --check`.

- Implementation commit: `4e36cf6cfabe7e6dbe99e54804653edeec277d9a`.
- Initial documentation commit: `46a1a59e4ec857f953240d4d9b7a9c33c1cb3f8d`.

## v0.22 Accepted Checkpoint

**v0.22 — Closed Script Claim Provenance Foundation** adds one closed immutable `ScriptClaimSet` for an exact
immutable Script, with zero or more immutable `ScriptClaimLink` Claim identities. An empty set is valid and differs
from no set; no membership can later be appended, removed or replaced. Correction is represented by a new immutable
Script version with its own set.

Creation validates the exact existing Script → ContentPiece → EditorialAngle → `Ready`
ResearchReadinessAssessment → ResearchPack → Opportunity lineage. Every supplied Claim must belong to that exact
Angle's ResearchPack, appear in that exact assessment's `frozen_evidence_state`, and be linked to the Angle at
declaration time. Reads resolve the linked identities only against that frozen historical Claim/evidence state; live
Claim, Source, ClaimEvidence and Angle-link changes do not rewrite closed provenance.

Migration 17 is additive only: `script_claim_sets` and `script_claim_links` with restrictive foreign keys, one set
per Script and unique per-set Claim membership. It adds no readiness, ResearchPack, Angle, evidence or snapshot copy;
it leaves Script initiation and EditorialPackageSnapshot semantics unchanged. The API is
`POST`/`GET /api/scripts/{script_id}/claim-set`. v0.22 excludes ranges/segments, ClaimEvidence links, QA/Gate,
approval/workflow, UI, production, publishing, analytics, Learning and orchestration.

v0.22 is accepted. v0.21 is its historical accepted predecessor. Acceptance covers implementation commit
`346ddd76d19c8520541f77db4dda7853e8e8a5ed` and pending-state documentation commit
`3947ae34fb345a5cf6cb16423194a2b21d1d67c5`. v0.25 — Operational Visual Production Inputs is the latest accepted
implementation milestone; v0.24 is its accepted historical predecessor. Migration 20 is latest, migration 21 is
absent, and Phase 2 remains ACTIVE / INCOMPLETE. Validation passed: Black 26.3.1 `--check`, Ruff,
**96 pytest tests**, and `git diff --check`.

## v0.23 Accepted Checkpoint

**v0.23 — Deterministic Editorial Readiness Assessment** is the accepted implementation checkpoint. It adds one
immutable, additive `EditorialReadinessAssessment` for one exact
`EditorialPackageSnapshot`, preserving provenance by reference through the package's exact TitleOption, HookOption,
Script and closed ScriptClaimSet to the upstream frozen Ready research evidence. It does not duplicate package text,
Claims, evidence, sources or readiness IDs.

The server derives the outcome and structured findings using evaluator
`deterministic-editorial-readiness` version `v1` and assessment schema version 1. The sole blocking policy is a
missing ScriptClaimSet: it persists `NotReady` with `SCRIPT_CLAIM_SET_MISSING`. A closed empty set is a valid complete
zero-Claim declaration and may be `Ready`; a valid populated set resolves only through exact frozen provenance.
Broken package or provenance state remains an integrity error and never becomes a synthetic `NotReady` record. No
risk, freshness or verification-status blocking policy is defined.

Migration 18 adds only `editorial_readiness_assessments`, its restrictive package FK and package-history index, with no
backfill, current/latest/superseded pointer, finding table, score, provider/model or Gate/spend schema. The narrow API
is `POST`/`GET /api/editorial-package-snapshots/{snapshot_id}/readiness-assessments` and
`GET /api/editorial-readiness-assessments/{assessment_id}`. No subjective/model QA, Editorial Gate, UI, production,
publishing, analytics, Learning, financial behavior or orchestration is included.

Founder acceptance covers implementation commit `01eeafd78c0e5a81f9dc5442d9404ca8a25b55b9` and pending-state
documentation commit `64e5da9183d9a0fe1492e6968f266f26abd4538c`. Validation passed: Black 26.3.1 `--check`, Ruff,
**99 pytest tests**, and `git diff --check`. v0.25 — Operational Visual Production Inputs is the latest accepted
successor; v0.24 is its accepted historical predecessor. Migration 20 is latest; migration 21 is absent. Phase 2
remains ACTIVE / INCOMPLETE and no successor after v0.25 is selected.

## v0.25 Accepted Checkpoint

**v0.25 — Operational Visual Production Inputs** is ACCEPTED. v0.24 is its accepted historical predecessor; Phase 2
remains ACTIVE / INCOMPLETE; no successor after v0.25 is selected.

The existing mutable Scene and AssetSpec models are reused, but dedicated authoring requires a VisualPlan whose
immutable `visual_plan_gate_provenance` resolves through an exact `Approve` `EditorialGateDecision` and its exact
`Ready` package lineage. Historical/demo low-level operations remain compatible and are not backfilled. Scenes and
AssetSpecs remain editable until a later final-media milestone; v0.25 creates no production snapshot.

Manual/no-cost image import is first-class. The server accepts bounded PNG, JPEG or WebP bytes, validates their
declared format, writes a new managed copy, derives its immutable per-AssetSpec version and SHA-256 digest, and records
server-derived `imported` provenance. Arbitrary external paths, caller versions, digests, managed paths and source kinds
are not production inputs. Registered managed imported and generated image content remains safely retrievable only by
Asset ID.

Migration 20 adds only additive immutable `asset_selections`: exact AssetSpec, exact Asset, optional exact
CharacterReferenceSet and creation time, with restrictive foreign keys and history/reverse lookup indexes. There is no
current/latest/best/active/ranking state and multiple historical selections remain valid. Imported character Asset
selections require a caller-supplied exact CharacterReferenceSet matching the AssetSpec CharacterProfile; imported
non-character selections carry none. Generated Assets preserve their GenerationExecution provenance and cannot receive
a manual reference-set override. No ReferenceSet membership is created or changed.

The narrow API adds Gate-qualified Scene and AssetSpec create/list/update routes, raw managed Asset import under an
AssetSpec, Asset history/content retrieval, and immutable AssetSelection create/list/get routes. v0.25 does not add
narration, captions, timing, rendering, MP4 output, manifests, QA, provider changes, paid production, spend/cost,
workflow, UI, publishing, analytics, Learning or successor scope. Founder acceptance covers implementation commit
`065e10bc6e36bf009f54fbce9a0135ef0cae9273` and pending-state documentation commit
`67500b338ecb959177b131ece2f59b9b11fb327c`. Ruff passed, **107 pytest tests** passed and `git diff --check` passed;
Black 26.3.1 formatting equivalence across the 10 repository Python files passed through the accepted in-process API
check after the documented Windows CLI worker-process hang.

## v0.24 Accepted Checkpoint

**v0.24 — Editorial Gate + Approved VisualPlan Initiation** is accepted. It adds immutable, additive
`EditorialGateDecision` history over one exact immutable
`EditorialPackageSnapshot` and one explicitly supplied exact `Ready` `EditorialReadinessAssessment`. The only
outcomes are `Approve`, `Revise` and `Reject`; there is no current/latest/selected/superseded state. Multiple
decisions may exist for a package or assessment.

Only an exact `Approve` decision may deliberately initiate a VisualPlan. The dedicated path derives the exact
ContentPiece and Script from the approved package, creates the VisualPlan and its additive
`visual_plan_gate_provenance` record atomically, and accepts no caller lineage override. It does not consume the Gate
decision or automatically create Scenes, AssetSpecs, GenerationExecutions or Assets. Historical/demo and low-level
VisualPlans remain compatible without Gate provenance and are not backfilled.

Migration 19 adds only `editorial_gate_decisions`, `visual_plan_gate_provenance`, restrictive foreign keys and
history/reverse lookup indexes; migration 20 was added later for v0.25 and migration 21 is absent. The narrow API is
`POST`/`GET /api/editorial-package-snapshots/{snapshot_id}/gate-decisions`,
`GET /api/editorial-gate-decisions/{decision_id}`, and
`POST /api/editorial-gate-decisions/{decision_id}/visual-plans`.

The implementation commit is `34acdcfc3b3d523a3eb4a00af6ae7d768669444b`; the pending-state documentation commit
is `ae993dae6732a2cb456f57e3d070cd315c77a30b`. Validation passed: Black 26.3.1 formatting equivalence across 10
repository Python files via an in-process API check; the documented Black CLI could not terminate in this Windows host
because of a process-runtime hang. Ruff passed, **102 pytest tests** passed, and `git diff --check` passed. Gate approval authorizes
visual planning only. v0.24 adds no new Title/Hook or Script-to-Claim lifecycle work, machine editorial QA, paid
production, spend/cost authorization, provider/generation work, final media, Scene/AssetSpec lifecycle expansion,
publishing, UI, workflow, analytics or successor scope. Phase 2 remains ACTIVE / INCOMPLETE and no successor after
v0.24 is selected.

## Atlas v0.2 Checkpoint

**Project Atlas v0.2 — Persistent Discovery Foundation** is complete and pushed.

- The v0.1 UI baseline is preserved.
- Subjects are persistent.
- Opportunities are persistent.
- Opportunity/Subject relationships are persistent.
- SQLite persistence, explicit migrations and a repository layer are established.
- No generic Topics model was introduced.
- Pillars remain deliberately deferred.

## Atlas v0.3 Checkpoint

**Project Atlas v0.3 — Research & Evidence Foundation** is complete and pushed.

- A versioned ResearchPack belongs to one Opportunity.
- Claims are version-specific and belong to one ResearchPack.
- Sources are reusable Atlas-wide records, deduplicated by exact URL.
- ClaimEvidence records Source provenance for Claims, including stance, reference and notes.
- Claim fields persist recognised type, risk, freshness and review semantics without numeric
  truth, confidence, source-authority or evidence-strength scores.
- One persistent ISA ResearchPack is seeded for the existing Content Workspace item only.
- The Content Workspace now reads that persisted research read-only; angle, script, scene plan
  and QA remain on their local demo-data path.
- Research policies, AI research, agents, scripts, workflow, publishing, production and
  analytics remain deferred.

## Atlas v0.4 Checkpoint

**Project Atlas v0.4 — Editorial Angle Foundation** is complete and pushed.

- EditorialAngle belongs to one Opportunity and references one ResearchPack from that same
  Opportunity.
- Each Angle persists a working title, thesis, audience promise, framing, ordered intended
  takeaways and extension metadata; it has no version, status, score, selection or approval fields.
- EditorialAngleClaim records a Claim's `core` or `supporting` role for an Angle. Repository
  validation rejects Claim/Angle links across ResearchPacks.
- Two distinct persistent ISA Angles are idempotently seeded for the existing v1 ISA ResearchPack.
- The Content Workspace reads persistent research and a deterministic persistent EditorialAngle
  with linked Claims; script, scene plan, QA, production and workflow remained deferred at v0.4.
- No workflow state, AI angle generation, publishing, production or analytics
  has been introduced.

## Atlas v0.5 Checkpoint

**Project Atlas v0.5 — Content Piece + Script Foundation** is complete and pushed.

- ContentPiece belongs to one Opportunity and derives from one EditorialAngle from that same
  Opportunity. Its Opportunity/Angle provenance is immutable after creation.
- Script belongs to one ContentPiece and stores complete narration text. Versions are unique per
  ContentPiece, immutable after creation, and the latest is derived by highest version number.
- One persistent ISA video ContentPiece and one immutable Script v1 are idempotently seeded from
  the deterministic ISA EditorialAngle and existing demo narration.
- The Content Workspace reads persistent Research, EditorialAngle, ContentPiece and latest Script
  narration. Scene Plan and QA remained demo-backed at this checkpoint; workflow, production,
  publishing and analytics remain deferred.
- No visual-plan, scene, QA, approval, workflow, publishing, production or AI-generation
  persistence was introduced in v0.5.

## Atlas v0.6 Checkpoint

**Project Atlas v0.6 — Visual Plan + Scene Foundation** is complete and pushed.

- VisualPlan belongs to one ContentPiece and one exact immutable Script version from that same
  ContentPiece. Its ContentPiece/Script provenance is immutable after creation.
- Scene belongs to one VisualPlan, uses an ordered unique sequence within that plan, and retains a
  human-readable narration excerpt only; Script narration remains authoritative and audio-complete.
- One persistent ISA VisualPlan and three ordered Scenes are idempotently seeded from the existing
  kitchen-table, envelopes, tax-year calendar and decision-tree demo direction.
- The Content Workspace reads persistent VisualPlan and Scene data; the compatibility Scene Plan
  display derives from persistence. QA remains demo-backed.
- Asset generation, production, workflow, publishing, analytics, AI visual planning and agents
  remain deferred.

## Atlas v0.7 Checkpoint

**Project Atlas v0.7 — Asset Specification + Asset Foundation** is complete and pushed.

- AssetSpec belongs to one Scene and stores an asset type, purpose, description, canonical
  provider-neutral generation prompt, optional continuity key and extension metadata. Its Scene
  provenance is immutable after creation.
- Asset belongs to one AssetSpec and records an immutable versioned registered output with a storage
  path, media type, source kind and metadata. There is no current, selected, approved, generated or
  workflow state.
- Five persistent ISA AssetSpecs are idempotently seeded across the three existing Scenes: kitchen
  environment, hamster sorting envelopes, tax-year calendar, decision-tree graphic and hamster
  reaction. No Asset outputs are seeded.
- The Content Workspace now reads persistent AssetSpecs and registered Assets beneath persisted
  Scenes. QA remains demo-backed.
- Provider integration, asset generation jobs, production, workflow, publishing, analytics and agents
  remain deferred.

## Atlas v0.8 Checkpoint

**Project Atlas v0.8 â€” Generation Execution Foundation** is complete and pushed.

- GenerationExecution records one immutable terminal synchronous generator attempt with exactly
  `succeeded` or `failed` outcome, a frozen AssetSpec snapshot, normalized Atlas generation input and
  generic generator/provider/model/request provenance.
- A successful operation atomically creates one GenerationExecution and one linked immutable Asset;
  generated Asset versions remain scoped to AssetSpec. Failed executions create no Asset.
- Assets remain broader than generated outputs: manual/imported Assets retain nullable execution
  provenance.
- OpenAI is the first replaceable Image API adapter behind an Atlas-owned generator boundary. Keys are
  environment-configured and never persisted; generated files are stored under Atlas-managed local storage.
- No execution or Asset is seeded, and startup never invokes generation. Queues, retries, batch generation,
  QA, approval, rendering, workflow, production, publishing, analytics and agents remain deferred.

## Atlas v0.9 Checkpoint

**Project Atlas v0.9 Visual Style Control Foundation** is complete and pushed.

- VisualStyleProfile is immutable and versioned, with no editor or active/current/selected state. The
  deterministic SimilarStoic Core v1 seed preserves sparse, light, hand-drawn editorial direction without
  duplicating that brand guidance into AssetSpecs.
- Atlas-owned deterministic PromptComposer resolves profile-wide and matching AssetSpec-type rules before
  the AssetSpec's concrete generation requirement. Provider adapters receive only the composed prompt in a
  provider-neutral GenerationInput v2.
- New executions retain exact resolved style provenance in GenerationInput v2 and a restrictive direct
  GenerationExecution-to-VisualStyleProfile lineage. Existing v0.8 GenerationInput v1 rows remain readable
  with null profile lineage.
- `ATLAS_VISUAL_STYLE_PROFILE_ID` selects an immutable profile ID; an unset value now uses SimilarStoic Core
  v3. V2 remains selectable and historical.
  CharacterProfile identity, canonical visual references, StyleBible/reference-image continuity, profile
  editing, QA, workflow, production and publishing remain deferred at this checkpoint.

## Atlas v0.10 Checkpoint

**Project Atlas v0.10 — Visual Style Fidelity Refinement** is complete and pushed as a provisional
visual-style baseline.

- SimilarStoic Core v2 is seeded beside the preserved immutable SimilarStoic Core v1 profile; no
  migration was required.
- V2 retains the sparse, light, one-idea and asset-decomposition rules from v0.9 while strengthening
  visibly hand-drawn dark-line language: organic uneven lines, simplified imperfect forms, mostly
  white/unfilled space and only an optional restrained flat block accent colour; tonal shading and
  textured fills are explicitly avoided.
- The deterministic default is v2. `ATLAS_VISUAL_STYLE_PROFILE_ID` can still explicitly select v1.
  Existing v1 executions and their GenerationInput v2 snapshots remain unchanged.
- V2 is the current text-guided production baseline, not the final SimilarStoic visual identity. Further
  art-direction refinement remains intentionally deferred; a future immutable profile version may
  supersede v2, and reference-grounded style fidelity may be explored later if justified.
- Style-reference images, canonical visual-reference continuity, profile editing, QA, workflow, production,
  publishing and other future style architecture remain deferred.

## Phase 1 Visual Style Synchronization

Human Gate A approved generated Asset `asset-9a02b4cb416744a994965e2e1f2f0c33` (version 9;
SHA-256 `eaf0af82fe98120613793465f94029a72ae13a79f8e3e258d265e88fa47c450b`) for the existing
SimilarStoic Hamster Core v1 CharacterProfile. The approved visual specification is represented by new
immutable SimilarStoic Core v3; v2 remains unchanged, historical and selectable.

- V3 retains the sparse, mostly light, dark hand-drawn, imperfect, no-gradient/no-tonal-shading language.
- For the canonical recurring hamster only, it permits warm tan/orange inner ears, nose and
  paws/hands/feet, while retaining a mostly white/light body, large hamster-like ears, long whiskers,
  simple alert eyes, minimal fur detail and crude average-adult-from-memory drawing quality.
- The signature crossbody sling/man-bag alone may use flat green, blue, orange, yellow, red and black with
  a dark-gray strap. General scene colour remains restrained; the exception does not permit arbitrary
  highly multicoloured scene elements.
- The deterministic fallback profile is v3; `ATLAS_VISUAL_STYLE_PROFILE_ID` can explicitly select any
  immutable seeded version. No schema migration or new domain concept was required.

Phase 1 visual acceptance is closed with **PASS WITH DEFERRED VISUAL REFINEMENT**. The Human Gate A Asset
is the sole immutable member of CharacterReferenceSet v1; two reference-grounded review executions then
succeeded across the approved sorting and reaction Scene AssetSpecs. No further generation is authorized.

The non-blocking deferred refinement is specifically residual AI-clean or overly competent professional
illustration finish. Future work may increase believable human-drawn imperfection and reduce overly smooth,
confident contours, but must preserve the approved hamster identity, proportions, large-ear/long-whisker
cues, warm tan/orange accents, multi-colour sporty sling-bag, dark-gray strap and reference-set continuity.
It is not permission to redesign the hamster.

Accepted immutable evidence:

- Human Gate A reference Asset `asset-9a02b4cb416744a994965e2e1f2f0c33`, version 9, SHA-256
  `eaf0af82fe98120613793465f94029a72ae13a79f8e3e258d265e88fa47c450b`.
- CharacterReferenceSet `character-reference-set-similarstoic-hamster-core-v1`, version 1, contains exactly
  position 1 → that approved Asset.
- Grounded sorting evidence: `generation-execution-dd25dc1388b04eef8d4f32ee06ec7807` →
  `asset-76c02a603d0e4a69955b51633c1e13ce`, version 1, SHA-256
  `a12735798ad1c294849eaeab3796a080a8a27ec54335917048d1c5132f427577`.
- Grounded reaction evidence: `generation-execution-f1900a2b32634a36b0b53244474259ce` →
  `asset-c989501ad83e4c9da668218c3179fb9c`, version 10, SHA-256
  `ce0438980ae2f9c8015e63046805d70cc58d9789daa29671c28ac5dc1243e95b`.

VisualStyleProfile v3 remains the current accepted baseline. At this Phase 1 visual-acceptance checkpoint, no
v0.15 or post-Phase-1 milestone had been selected.

## Current Founder + ChatGPT Visual-Specification Clarification

This current clarification tightens the existing approved mascot contract; it does not rewrite the historical
v0.14 record or create a new milestone, CharacterReferenceSet, VisualStyleProfile, schema or implementation scope.
The current core mascot identity is governed jointly by the immutable
`character-reference-set-similarstoic-hamster-core-v1` reference asset and this current founder + ChatGPT-approved
visual-refinement contract. The set contains only the approved Asset/version/SHA recorded above. Where this
clarification deliberately tightens future depiction requirements beyond the literal original v1 pixels—more
prominent rounded ears and whiskers, broad/soft hamster-like face, toothless mouths, fixed bag panel/layout rules,
flat-colour rendering and mandatory consistency QA—it governs future conforming depictions without mutating,
replacing or rewriting the historical reference asset. CharacterReferenceSet v2, replacement and silent substitution
are not authorized; absence of runtime rows or bytes does not change that rule.

The main mascot must remain unmistakably hamster-like, never mouse-like: broad soft rounded face/muzzle, compact
rounded hamster-native body, visibly large rounded ears (slightly more prominent than v1 when pose allows), long
distinct whiskers beyond the muzzle, alert dark eyes, mostly white/light body, warm tan/orange inner ears/nose/paws,
minimal/no fur detail and crude hand-drawn anatomy. Expression may change eyes, brows, mouth, gesture and posture,
but never identity, ear scale, whiskers, proportions, core colouring or bag design. All mouths are simple and
toothless: teeth, dental detail, duplicate mouth lines, malformed inner-mouth shapes, inconsistent lips and extra
mouth anatomy are non-conforming.

Only the core mascot wears the fixed genuinely crossbody sling bag: dark-gray strap, dark/black zipper band and
outline, red/orange upper strip, green upper/central panel, blue lower-left panel, yellow lower-right panel, the
approved curved silhouette, fixed panel adjacency/colour ordering, and consistent visible zipper/pull treatment.
Supporting hamsters may vary as believable hamster types but remain secondary, never wear the bag and never duplicate
the full core identity. A small recurring set of supporting hamster models may be established and reused across
scenes and videos; each model's hamster type/colour pattern, body shape, size/scale, facial characteristics and
other stable secondary traits must remain consistent once established. One-off background hamsters may vary within
the approved language only if they do not become or imitate an established recurring model. Hamsters use
direct-transition flat block colours and simple sparse dark, hand-drawn,
slightly imperfect outlines: gradients, shading, painterly blending, fur texture/detail, cross-hatching, glossy
highlights, AI-clean rendering, missing/duplicate/stray contours and extra anatomy are prohibited.

Established recurring characters must use approved visual reference assets/models as concrete image/reference
grounding whenever the generation mechanism supports it; they must not be materially reconstructed or reinterpreted
from prose alone when an approved reference exists. The current mascot is jointly governed by the immutable
CharacterReferenceSet v1 asset, current founder + ChatGPT-approved written refinement contract and mandatory visual
QA; deliberate written refinements beyond literal v1 pixels govern only those refinements, while the reference
governs the rest of the concrete appearance. The same rule applies to recurring supporting models. One-off background
hamsters need no persistent reference unless they later become recurring. Generated images never become approved
references automatically: only founder + ChatGPT-approved visual exemplars may do so.

Appearance in a group scene, comparison sheet, specification sheet or other multi-character visual does not by itself
establish a supporting hamster as a recurring character or approved identity model. A recurring supporting character
exists only after explicit founder + ChatGPT approval and approval of its own isolated character-specific visual
reference.

Every generated visual containing the core mascot—including production, infographic, roadmap, presentation,
internal-documentation, demo and decorative graphics—requires review against v1 and the character, bag and
flat-colour contracts before use. Any material inconsistency must be corrected, regenerated or rejected and must
fail closed if consistency cannot be established. This mandatory review/rejection requirement is canonical now; its
technical mechanism remains unspecified, and automated character-consistency-QA architecture/implementation remains
deferred. When a supporting hamster represents an established recurring model, review must also confirm its
established colour pattern, body shape, scale and distinguishing facial/character traits; material drift is
non-conforming and must be corrected, regenerated or rejected.

Reference grounding is not acceptance by itself. A generation materially deviating from the approved reference +
written contract—including proportions, bag geometry/colour placement, whiskers, ear size, mouth anatomy, outlines,
shading/gradients, core colours or supporting-character model—is non-conforming. If an approved reference is
unavailable to a process expected to generate a recurring character, it must fail closed rather than silently
approximate the character from text and treat the output as canonical or publishable. This does not choose
refined-exemplar storage, implement image-conditioning/reference passing, automated QA or supporting-character
entities; all such technical enforcement remains deferred.

### Verified current core-mascot visual-reference checkpoint

The approved current-depiction references are now durable, Git-tracked bytes under
`assets/visual-references/core-mascot/`. They supplement the immutable historical CharacterReferenceSet v1 anchor and
the current founder + ChatGPT-approved visual-refinement contract; they do not alter v1, create v2, alter
VisualStyleProfile v3, or add runtime implementation.

- **CORE IDENTITY REFERENCES:**
  - Preferred primary isolated grounding: `identity/9a9ccdc1-b948-45d1-a375-fc36d4e3bdc2.png` (1448x1086;
    SHA-256 `11332518cdace450f8e432fe8cb3558ea2374cf0273f94973912e914cee66956`).
  - Preferred primary/supplementary multi-pose grounding: `identity/a5564bd0-51d2-4713-82c1-42138f12a8dc.png`
    (1448x1086; SHA-256 `d3acb16af30b9a5aca29e92e2e8f19d7b5a21df4b8e572de054756ca23321cc4`).
  - Supplementary core-only specification/identity grounding, not preferred as sole input:
    `identity/fa86fc7a-9006-4478-b5a2-371ba65cf06e.png` (1536x1024; SHA-256
    `eb4eeab20550da110183819c51cd7710d067f63156ea1a1ef2e4f6c0f21b1f46`).
- **CORE SCENE / EXPRESSION EXEMPLARS:**
  - Flowchart/explaining: `scenes/a3e484f6-8c69-4b89-8592-dd8671563b65.png` (1448x1086; SHA-256
    `27ff66e34a8649a22c649a5593c93d0532cd176cf69dafb61bc19a1d2e1eb85a`).
  - Growth-chart/surprised expression: `scenes/e2a608fa-267b-4e7b-b7e8-0065699dd13f.png` (1448x1086; SHA-256
    `24dc9fd6367d6f7c4f9731b12bd1b7e7376edf7870ecee0a8ac066699363ff65`).
  - Reading/thinking: `scenes/42ee8538-a4ff-4ca5-8b00-0044ef90207e.png` (1448x1086; SHA-256
    `95ad2c8a75b7ce798eb315d1c84d34571bb1a44ace1922b141bdb2173fdfae4f`).

The identity references are the primary grounding inputs and contain no supporting hamster model. Scene/expression
exemplars are supplementary only: their whiteboards, charts, books, tables, chairs and other props are scene context,
never identity features, and they cannot override identity references or the written contract. Core-mascot generation
remains reference-grounded and subject to mandatory post-generation QA. Supporting characters require separate,
isolated per-character approved references before stable reuse; cross-character identity pooling is prohibited.
Generated images do not become approved references automatically. Automated reference selection, image-conditioning
and QA remain deferred; no runtime implementation has been added.

## Atlas v0.11 Checkpoint

**Project Atlas v0.11 — Character Continuity Foundation** is complete, accepted, committed and pushed.

- CharacterProfile is an immutable, versioned canonical identity boundary. SimilarStoic Hamster Core v1 is
  seeded as the approved recurring hamster identity, separate from VisualStyleProfile visual-language rules.
- Character AssetSpecs may reference a CharacterProfile; the two canonical seeded hamster AssetSpecs do so.
  `continuity_key` remains non-authoritative grouping metadata, not a canonical identity mechanism.
- Atlas-owned prompt composition freezes complete CharacterProfile identity provenance in GenerationInput v3.
  GenerationExecution retains direct restrictive CharacterProfile lineage and an execution-time AssetSpec
  snapshot, so later AssetSpec relationship changes do not alter historical meaning.
- At the v0.11 checkpoint, Atlas used prompt-only image generation. Canonical visual-reference Asset
  relationships, reference-image/image-edit conditioning and guaranteed cross-generation visual consistency
  did not yet exist.
- Source-attribution/citation work and Script-to-Claim/evidence provenance remain future work, alongside QA,
  workflow, production, publishing and broader automation systems.

## Atlas v0.12 Checkpoint

**Project Atlas v0.12 — Canonical Character Reference Foundation** is complete, accepted, committed and
pushed.

- CharacterReferenceSet is an immutable, versioned visual-reference selection for one exact
  CharacterProfile. It has one-or-more ordered immutable Asset members, with no mutable current, best or
  approved state.
- Newly generated managed Assets receive immutable SHA-256 byte provenance. Existing historical Assets may
  retain null digests; reference selection requires an existing supported managed image whose bytes match its
  stored digest.
- The founder can review eligible generated hamster Assets by safe Asset-ID image serving and explicitly
  create immutable canonical reference sets. Historical set versions and their original Asset/execution
  provenance remain preserved.
- Canonical-reference selection sits beside the production chain rather than changing it:
  ContentPiece → Script → VisualPlan → Scene → AssetSpec → GenerationExecution → Asset.
- At the v0.12 checkpoint, Atlas remained prompt-only. Reference consumption and execution lineage were
  introduced by v0.13; neutral CharacterProfile-owned studies and guaranteed cross-generation consistency
  remain deferred.

## Atlas v0.13 Checkpoint

**Project Atlas v0.13 — Reference-Grounded Character Generation** is complete, accepted, committed and
pushed.

- Normal character generation resolves the highest CharacterReferenceSet version for the exact
  CharacterProfile, freezes its ordered Asset/digest/media/position provenance in GenerationInput v4, and
  verifies managed reference bytes before the provider request.
- Grounded character requests use the adapter's ordered multipart image-edit path; prompt-only requests
  retain the ordinary image-generation path. Reference bytes remain runtime-only.
- GenerationExecution retains direct CharacterReferenceSet lineage. Missing sets, invalid references, and
  missing provider configuration remain pre-provider failures with no execution or Asset.

## Atlas v0.14 Checkpoint

**Project Atlas v0.14 — Explicit Character Reference Bootstrap** is complete, accepted, committed and pushed.

- A separate explicit operation can generate the first eligible Scene-owned character Asset for an exact
  CharacterProfile only while that profile has no CharacterReferenceSet.
- Bootstrap uses the existing non-reference GenerationInput v3 representation and provider path. It creates
  no reference set or mutable candidate state.
- Once any exact-profile CharacterReferenceSet exists, bootstrap is rejected before provider invocation;
  ordinary character generation continues to require grounded references.

---

# Product Decisions Completed

## Audience

20–35-year-old ambitious people who want:
- Financial literacy
- Wealth
- A better life
- Greater independence

Young professionals and beginners alike.

## Promise

> Understand how to build wealth without spending hours researching it.

## Territory

> MONEY + WORK + BEHAVIOUR + LIFE STRATEGY

> Understand money. Understand yourself. Build a better life.

SimilarStoic is not restricted to finance. Finance remains a major centre of gravity, an important commercial
foundation, a core source of high-intent content and central to the SimilarStoic identity, but is not required
for every piece. The expanded territory extends the finance-centred strategy; it does not replace finance.

Relevant territory may include finance and economics; work and careers; time, psychology, behaviour and
incentives; decision-making; society and social behaviour; life strategy; status and consumption; relationships
and social decisions; energy and attention; mental models; modern adulthood; financial independence; and useful
explanations of how systems or other parts of the world work. The editorial purpose is to make useful parts of
the world understandable and entertaining for the target audience.

These are strategic examples, not a final Conveyor Pillar taxonomy.

## Editorial Inclusion Test

> Does understanding this help the audience understand or make better decisions about money, work, behaviour,
> psychology, incentives, society, time, future, decision-making, or an important system or phenomenon?

If yes, the idea may belong within SimilarStoic. SimilarStoic must not drift into generic motivation or
self-improvement without substantive explanatory value, miscellaneous trivia without meaningful relevance or
insight, or random entertainment that does not fit the brand's explanatory purpose.

Life design connected to money, time or work; psychology of consumption/status; careers/income; and financial
relationships are potentially strong fits.

## Long-Term Transformation

Help viewers build a compounding portfolio of:
- Knowledge
- Skills
- Opportunities
- Investment understanding
- Better decision-making

Ultimately:
> Better decisions → greater wealth → greater independence.

## Personality

Relaxed, knowledgeable Gen-Z friend.

Confident, approachable, humorous and relatable without becoming a guru or sacrificing substance.

## Content Pillars

The current editorial portfolio themes guide strategy but do not define the final persistent Conveyor Pillar taxonomy.

1. Build & Protect Wealth
2. Keep More of What You Earn
3. Increase Income & Leverage
4. Spot the Next Opportunity
5. Think & Decide Better

## Conveyor Domain Distinction

- **Pillars** are strategic portfolio organisation.
- **Subjects** are reusable concepts and knowledge domains.
- **Opportunities** are specific editorial possibilities and may involve multiple Subjects.

These concepts must not be collapsed into one generic Topic model. The final Pillar taxonomy and its relationships remain deliberately deferred.

## Geography

UK-first, Western-focused, globally aware.

UK examples lead.

US comparisons are included briefly when useful.

## Content Mix

Initial target:
- 35% evergreen
- 25% current/news
- 25% opportunities/trends
- 15% actionable/personal

## Creative Format

Mascot-led hybrid animation.

Classic hamster as the canonical mascot, with a small everyday crossbody/sling bag as its signature accessory.

The hamster should feel like an ordinary young adult: relaxed, curious, intelligent, relatable and occasionally cheeky—not a finance guru, corporate mascot or generic human with a hamster head.

Controlled variations such as small, large, squishy and exaggerated are allowed while retaining the canonical identity.

Core rule:

> The narrator explains. The hamster illustrates.

> **THE COMPLETE VIDEO MUST BE UNDERSTANDABLE FROM AUDIO ALONE.**

Visuals may enhance, entertain, reinforce, provide humour and provide metaphor; they must not contain information required to understand the explanation. This remains a hard requirement for future script, scene and visual-planning architecture.

## Narration

One consistent AI narrator voice.

Natural, warm, conversational, confident, relaxed and slightly witty.

The narrator is not visually present.

Never robotic, corporate, patronising or excessively theatrical. Audio quality, pronunciation, pacing and processing require their own QA process.

## Short-form

Primary:
- 30–90 seconds
- TikTok
- Instagram Reels
- YouTube Shorts

Initial publishing target:

> One high-quality short per day.

Long-form:
- 2–5 minutes initially
- 8–15+ minutes later

## Topic Philosophy

Viewer-first.

Topics should be:
- Relevant
- Timely
- Useful
- Substantive
- Visually interesting

Topic discovery draws from current events, community signals, trends, evergreen knowledge gaps and existing content.

Community sources are not authoritative evidence.

Conveyor produces a curated daily shortlist of 5–10 opportunities. Initially Conveyor proposes and the founder
approves or steers; research begins only after approval.

## Editorial Integrity

Top priority.

Official/primary sources should be preferred.

Important claims should be corroborated where appropriate.

Current information must be checked for freshness.

Facts, interpretation and opinion must be distinguished.

Unverified claims must not be published as facts.

Structured Research Packs precede scripting. They identify contradictions, uncertainty and outdated information, and distinguish facts, interpretations and forecasts.

The v0.3 Research & Evidence Foundation supports different claim/statement types, provenance,
source relationships, verification states and freshness requirements. It does not assume every
statement has the same evidence burden or hard-code a narrow financial-news workflow.

For example, current ISA rules need current authoritative, jurisdiction-aware financial/tax evidence and strong freshness checks. Behavioural, life-strategy and philosophical pieces may combine economic evidence, behavioural/psychological research, statistics, academic or expert sources, calculations, illustrative examples and editorial interpretation.

## Actionable Content

Where appropriate:

> "Here's what I'd do."

Personal perspective should be distinguished from personalised financial advice.

Higher-risk financial content requires additional review.

## Monetisation

Long-term diversified strategy:
- Platform revenue
- Sponsorships
- Affiliates
- Own digital products
- Software/tools
- Potential financial products/services subject to regulatory requirements

Editorial independence is non-negotiable.

---

# Content Operating Model Decisions

## Research, Angles & Scripts

Official/primary sources are the foundation of factual claims; important claims are independently corroborated proportionately to their importance and risk. High-risk financial content requires human review.

Generate multiple angles from verified research. Select for viewer relevance, benefit, curiosity, timeliness, substance, evidence, emotional resonance, visual potential, portfolio value and brand fit. Evidence quality is a minimum gate, not simply another score.

Generate hooks after the underlying angle/story. Hooks must not misrepresent, exaggerate or manufacture urgency.

Create a structured content package—not only a script—with narration, scene plan, hamster direction, source/claim mapping, a relevant US comparison where useful, and an appropriate CTA/action. “Here's what I'd do” is used only where genuinely useful and stays distinct from personalised financial advice.

Narration must be understandable as audio without visuals; visuals enhance rather than carry essential information. Pop-culture references can be used as analogies or references, but production must not depend on copyrighted footage or characters.

## QA, Production & Approval

Script QA requires claim-by-claim verification, meaning preservation against the Research Pack, editorial/compliance review, visual fact checking, audio-only comprehension and freshness checks for current/changeable claims.

Material unsupported or inaccurate claims block publication. Substantive factual corrections must be surfaced, not silently hidden.

Videos are built from reusable illustrated assets and layered scenes, not single-pass generative video. Maintain canonical hamster assets, expressions, environments and props. Generate numerical charts/data visualisations programmatically from verified data.

Narration is the master timeline. Use evolving illustrated scenes: major idea/location/concept changes trigger major scene changes; minor background movement is optional and purposeful. Use simple baseline animation, exaggerated character states and occasional highly detailed hero frames; hero frames are visual peaks, not the default.

Signature original break-frame/still devices may occasionally interrupt the normal sparse visual grammar to
land a joke, dramatize an event, make an explanatory point or metaphor, convey a feeling, or make a concept
memorable. They may be unusually detailed, exaggerated, uncanny, absurd, dramatically over-serious, visually
intense or stylistically contrasting; the contrast may itself be part of the comedy or explanation. They are
not the default treatment. Classic SpongeBob-era/older animated-comedy timing may inspire the mechanism, but
no protected characters, artwork, frames, compositions, dialogue, backgrounds or franchise-specific visual
identity may be copied.

Final production QA includes technical, audio, factual, visual and brand-consistency checks; audio-only comprehension; caption/text accuracy; and chart/data accuracy.

Initially every video requires human approval before publication. Automation may increase only after demonstrated reliability. Preserve research, sources, scripts, assets and version history for published content.

## Distribution, Analytics & Learning

Initial platforms remain YouTube Shorts, TikTok and Instagram Reels. Create once and adapt intelligently for each platform. One high-quality short per day is the initial target, not a mandatory quota.

Collect reach, retention, engagement, audience and eventually commercial metrics where available. Link performance to topic, pillar, angle, hook, format, visual approach and other attributes to improve future content.

Do not optimise purely for views or compromise editorial integrity and brand trust. Comments can become topic/content signals but are not factual evidence.

Maintain a knowledge map of covered subjects and outstanding knowledge gaps so the content system progressively learns from its own history.

---

# Architecture Milestone

## Knowledge + Content Intelligence

Conveyor is specified as a structured knowledge + content intelligence system, not merely a content archive:

> Pillars (portfolio) → Subjects (knowledge) → Opportunities → Research → Sources → Claims → Scripts → Scenes/Assets → Publications → Performance → Audience Signals → Learnings → Future Opportunities/Angles

Claims retain appropriate provenance, verification/freshness information, applicability context and risk metadata. Previously researched knowledge may be reused after appropriate freshness validation.

Pillars remain strategic portfolio organisation, Subjects remain reusable knowledge domains, and Opportunities remain specific editorial possibilities. This documentation does not define the final Pillar taxonomy.

Community/forum/social sources remain audience/topic signals and are distinct from authoritative factual evidence. The knowledge system will eventually support portfolio-gap analysis and identify coverage that needs development or updating.

## MVP Scope & User Interface

The planned MVP focuses on:

> Discover → Human Topic Selection/Steering → Research → Angle → Script → Automated QA → Human Review → Approval

Its success criterion is a trustworthy, production-ready SimilarStoic content package with minimal manual management.

Automated video production, automated publishing and advanced analytics are later phases.

The planned core screens are:

- **Command Centre** — strongest opportunities, attention-needed content, Conveyor activity, important knowledge/source changes, lightweight performance and Conveyor Chat access.
- **Discover / Opportunities** — 5–10 opportunities with relevance, why-now context, viewer benefit, suggested angle, evidence quality, risk, portfolio relevance and visual potential.
- **Content Workspace** — lifecycle, research, claims, sources, angle, script, visual plan, QA state and approval controls.
- **Conveyor Chat** — natural-language questions, steering and eventually actions.

The interface prioritises decisions and exceptions over unnecessary technical complexity.

## Modular, Configurable Architecture

The architecture follows a “change without rebuild” principle: data, capabilities, workflows, configuration and interface remain loosely coupled.

Conveyor is a composable pipeline. Providers, research engines, model/provider adapters, narration/audio and
image/visual providers, production stages, rendering components, publishing integrations, analytics
integrations and other implementation-specific pipes should be replaceable behind stable boundaries, explicit
inputs/outputs, loose coupling and preserved provenance. Replacing one pipe must not require reconstructing
the end-to-end system solely because an underlying implementation changes.

Workflow stages should be independently addable, removable, reorderable and configurable where practical. The fixed MVP workflow must not become a permanent hard-coded constraint.

Short-form, long-form, newsletters and company deep dives should be able to reuse the same underlying knowledge/content system.

V1 business rules should be configurable without code where practical, including audience, geography, pillars, topic preferences/scoring, duration, editorial direction, source/freshness/risk requirements, approval rules, US-comparison rules, personal-perspective/CTA rules, visual rules, cadence, cost limits and automation level per stage.

Protected safety, security and integrity constraints are not ordinary configuration. Configuration must be versioned and auditable so historical content retains its production context.

Accepted phases, milestones, specifications, profiles and implementation choices remain evolvable after
acceptance. Prefer additive changes, immutable new versions, explicit future selection and durable provenance
that preserves which historical outputs used which version; do not destructively rewrite accepted historical
records merely because the current design evolves. Core domain/provenance invariants remain stable by default:
ownership/provenance relationships, historical preservation, immutable/versioned reference semantics,
execution semantics and established domain meaning require explicit founder + ChatGPT architecture/
specification approval, deliberate canonical synchronization, review, acceptance, commit and push to change.

## Cost Tracking & Development Stack

Cost tracking is a first-class requirement. The planned system links AI/API operations to content pieces where possible and eventually tracks usage, model/provider, research/writing/QA/narration/visual/rendering costs, total cost per item, spend over time, unit economics and revenue versus production cost.

Configurable monthly and per-content budget targets and alerts are required.

### Approved future financial-control conceptual boundary

Future financial control distinguishes a durable **Cost Ledger** for actual operating spend, a durable
**Revenue Ledger** for money earned from already contemplated monetisation sources, and an **Economics /
Control Centre** that may derive profitability, unit economics, revenue-versus-production-cost, budgets,
alerts, trends, efficiency and financial guardrails. Cost and revenue records may attribute through existing
content/pipeline provenance where appropriate; mutable aggregate totals must not be embedded in immutable
GenerationExecution history.

Audience/content analytics remains separate: views, retention, engagement and follower/subscriber growth may
inform unit economics, but analytics is not the Revenue Ledger. Detailed ledger schema, revenue ingestion and
attribution rules, metric formulas, thresholds, enforcement, kill switches, escalation and founder-exception
semantics remain unspecified. Financial-control implementation remains deferred; no financial entities,
tables, integrations or automation guardrails have been created.

Phase 3 will own future cost/budget/control architecture; Phase 7 may provide publication/platform data,
Phase 8 owns separate performance/commercial metrics, Phase 9 may later consume financial limits, and Phase
10 may consume business/economic outcomes. No new phase or activation is implied.

GPT + Codex are the current primary AI/development stack. Claude or another coding agent is not a dependency or requirement. This is a tooling choice, not an architectural lock-in; provider abstraction remains possible where practical.

---

# Phase 1 Completion

Completed:
- Audience
- Promise
- Territory
- Personality
- Content pillars
- Geography
- Content mix
- Editorial philosophy
- Creative format
- Narration approach
- Publishing strategy
- Monetisation direction
- Content operating model
- Topic discovery, research and source-verification standards
- Angle, hook and content-package requirements
- Script QA and final-production QA
- Mascot identity, animation and visual-production principles
- Distribution, analytics and learning model
- Initial human approval rule
- Knowledge + content intelligence model
- Hybrid dashboard + conversational control model
- MVP editorial-intelligence scope and core screens
- Modular, configuration-first architecture principles
- Cost-tracking requirements and current development-stack choice
- Atlas v0.1 editorial control interface baseline
- Atlas v0.2 persistent discovery foundation
- Finance-centred editorial expansion to money, work, behaviour and life strategy
- Editorial inclusion test and explicit Pillars / Subjects / Opportunities distinction
- Atlas v0.3 Research & Evidence persistence foundation
- Atlas v0.4 Editorial Angle persistence foundation
- Atlas v0.5 Content Piece + Script persistence foundation
- Atlas v0.6 Visual Plan + Scene persistence foundation
- Atlas v0.7 Asset Specification + Asset persistence foundation
- Atlas v0.8 Generation Execution foundation
- Atlas v0.9 Visual Style Control foundation
- Atlas v0.10 Visual Style Fidelity Refinement
- Atlas v0.11 Character Continuity Foundation
- Atlas v0.12 Canonical Character Reference Foundation
- Atlas v0.13 Reference-Grounded Character Generation
- Atlas v0.14 Explicit Character Reference Bootstrap
- Phase 1 visual acceptance: **PASS WITH DEFERRED VISUAL REFINEMENT**
- Final production-ready SimilarStoic brand identity: **APPROVED**
- Formal Phase 1 acceptance and closure: **APPROVED**

Phase 1 closure status:

- Phase 1 is formally closed.
- Visual evidence review remains accepted with **PASS WITH DEFERRED VISUAL REFINEMENT**.
- Residual AI-clean/professional illustration finish is deferred visual refinement, not a Phase 1 blocker.
- No successor milestone or phase transition is implied, selected or active.

---

# Canonical End-to-End Target Operating Model

Conveyor is intended to become an approximately **95% automated content operating system**: routine execution is
progressively automated, while founder interaction concentrates where practical at an **Idea Gate**
(opportunity approval/steering), an **Editorial Gate** (title, hook, angle, script, evidence/risk review and
revision decisions) and a **Learning Gate** (performance, hypotheses, proposed adaptations and available
economics context). These are target operating-model gates, not approved workflow/database entities.

The established v0.1–v0.14 chain—Opportunity → Research Pack / Claims / Sources / Evidence → Editorial Angle
→ ContentPiece → Script → VisualPlan → Scene → AssetSpec → GenerationExecution → Asset—is durable
foundation, not a complete operating system. The approved direction extends it toward Publication → platform
performance → Analytics → Revenue/Economics → Learning → future content decisions. Automation must apply to
proven workflows only; it must not automate uncertainty merely because automation is technically possible.

Phase 2 is **ACTIVE**: it is the current roadmap phase under founder + ChatGPT design/implementation
stewardship. Activation does not authorize all Phase 2 scope or later-phase engines. **v0.16 — Authorized
Research Initiation** is a historical accepted implementation predecessor; v0.18 — Readiness-Authorized Editorial
Angle Initiation and v0.20 — Readiness-Lineage-Preserving Script Initiation are historical accepted predecessors.
v0.25 — Operational Visual Production Inputs is the latest accepted implementation milestone; v0.24 — Editorial Gate
+ Approved VisualPlan Initiation is its accepted historical predecessor. Later phases retain their defined
roles for technical architecture, research, content intelligence, production, distribution, analytics/learning,
automation and scale; no later phase is activated.

# Approved Phase 2 Operating-Model Specification

Phase 2 now has approved specification direction and is active. Its narrow v0.15 implementation is accepted;
remaining scope is unimplemented. Conveyor uses sparse human gates and rich machine readiness:
human judgement is distinct from readiness evidence, neither may
silently substitute for the other, and intermediate work should progress automatically only when explicit
quality, evidence and provenance requirements pass.

The target gates are **Idea** (Proceed / Reject / Steer an opportunity), **Editorial** (Approve / Revise /
Reject / intentional alternative selection for a Title/Hook/Angle/Script package) and **Learning** (review
evidence-backed, scoped, reversible performance/economics adaptations). They are version-specific future
decision concepts, not database entities or a generic mutable workflow state.

Where paid external production is contemplated, the Editorial Gate also contains the linked founder judgement
of the maximum spend Conveyor may use for that approved proposition. It is a bounded ceiling, not a spend target,
and does not create a fourth routine founder gate. Conveyor should choose the lowest-cost path that still clears
the approved quality, brand, evidence and risk floor; it must stop and escalate rather than exceed the ceiling
or silently lower that floor. A future production/spend proposal may explain lineage, estimated cost and
breakdown, quality/cost/risk trade-offs, alternatives, premium rationale, and qualified commercial/strategic
upside. Estimates must distinguish evidence, modelling and speculation.

The approved first half is Opportunity → Idea Gate → Research → machine research-readiness → Editorial Angle
→ ContentPiece → Title/Hook/Script development → machine editorial QA → Editorial Gate. The target second
half is Editorial package → Editorial Gate approval + bounded spend authorization → production within the
authorized envelope → machine production/brand/risk QA → publication readiness → automatic publishing unless
an exception occurs → analytics/economics → machine learning interpretation → Learning Gate. Overspend is a
financial exception requiring human escalation, not a routine fourth gate. The existing initial human
publication approval remains until reliability is demonstrated.

Opportunities remain mutable discovery records. The first approved Idea Gate implementation direction requires
an immutable review snapshot of exactly the presented Opportunity context and an immutable, additive decision
specific to that snapshot. Proceed / Reject / Steer and optional founder direction are durable history, not
`Opportunity.status`, approval booleans, generic Decision/Approval state or automatic research/orchestration
side effects. A material re-presentation creates a new snapshot/decision history. This is now defined as
**v0.15 — Persistent Idea Gate**: the accepted first Phase 2 implementation milestone, using additive
migration 12.

**v0.16 — Authorized Research Initiation** is now the historical accepted predecessor to v0.17. It provides
deliberate creation of Opportunity-owned
ResearchPack versions under an immutable, nullable direct IdeaGateDecision provenance reference: Proceed and
Steer qualify, Reject never does, and snapshot/pack Opportunity lineage must match exactly. Historical packs
remain valid without fabricated provenance; Steer direction remains canonical on IdeaGateDecision and is
consumed by reference. The separate initiation action has no automatic research/job/queue/provider/readiness/
workflow/automation effect, no consumed/current authorization state and no `Opportunity.status` mutation.
Migration 13, repository/API/UI implementation and tests are canonical; v0.16 remains the historical accepted
predecessor. v0.16 itself implies no scope beyond its accepted boundary.

**Research Readiness semantics are canonically accepted.** They define additive, immutable,
versioned assessments of an exact frozen ResearchPack Claim/Source/ClaimEvidence state, not mutable workflow
state and not a founder gate. Every assessment must preserve the assessed evidence snapshot, Ready /
NeedsMoreResearch / Blocked outcome, findings/reasons, assessment schema and policy/check versions, timestamp
and producer/implementation provenance. ResearchPack ID/version alone is insufficient because Claims,
Sources and ClaimEvidence may change later. Multiple assessments remain additive with no persisted
current/latest/superseded pointer; later evidence requires a new assessment. Migration 14 and the controlled
API are canonical; no UI, evaluator/producer, research automation or EditorialAngle progression implementation
exists. A Ready assessment does not automatically create editorial records.

**v0.17 — Persistent Research Readiness** is a historical accepted implementation predecessor to v0.18. Migration
15 is canonical and migrations extend through 1–15. v0.17 is limited to one immutable
ResearchReadinessAssessment table with a server-built,
deterministically ordered, schema-versioned frozen ResearchPack/Claim/Source/ClaimEvidence payload; exact
Ready / NeedsMoreResearch / Blocked outcomes; structured findings; policy/check, schema and producer
provenance; additive history; and controlled create/list/get API reads. It has no UI, evaluator, mutable
current/latest state, backfill, automation or later-phase behavior.

**v0.18 — Readiness-Authorized Editorial Angle Initiation** is the accepted implementation checkpoint and latest
accepted Phase 2 milestone: deliberate creation of an Opportunity-owned EditorialAngle under one exact supplied
immutable `Ready` ResearchReadinessAssessment, using a
direct immutable `research_readiness_assessment_id` reference. The reference is nullable for historical/demo/legacy
Angles, required only on the dedicated lifecycle path, and means only that the Angle was initiated under that exact
Ready assessment—not that mutable Angle content remains perpetually validated. Existing low-level Angle creation
remains compatible, with no backfill or global readiness requirement. The lifecycle validates Opportunity →
ResearchPack and assessment → same ResearchPack lineage; it rejects missing, cross-lineage, NeedsMoreResearch and
Blocked input. No latest/current selection, consumption, readiness mutation, frozen Claim matching, ContentPiece,
Script, `Opportunity.status` mutation, workflow entity, provider call, UI or Phase 5 automation is authorized.
Migration 15 remains canonical for the nullable restrictive FK and lineage index. Migrations extend through 1–20.
v0.25 — Operational Visual Production Inputs is the latest accepted implementation milestone; v0.24 — Editorial Gate
+ Approved VisualPlan Initiation is its accepted historical predecessor. Migration 20 is latest and no successor after
v0.25 is selected.

Phase 2 defers production/publication records to Phases 6/7, Learning Gate persistence to Phase 8, financial
guardrail records to future financial implementation, and orchestration to Phase 9. No gate/readiness tables,
generic approval state, Script-to-Claim architecture, queues, production, publishing, analytics, financial
systems or automation have been created.

The future Cost Ledger, Revenue Ledger and Economics / Control Centre remain the financial-control boundary;
analytics remains separate and immutable GenerationExecution history cannot carry later-changing aggregate
totals. Future learning may compare authorized/actual spend, production choices, quality and performance or
revenue outcomes where available, without allowing profit signals to silently redefine editorial strategy.
This spend direction concerns paid external spend only; remaining accounting, reservation, thresholds,
enforcement, proposal schema and negligible/internal-cost treatment remain unspecified.

## v0.26 Accepted Checkpoint

**v0.26 — Narrated Final Media Production** is **ACCEPTED**. v0.25 is its accepted historical predecessor. Founder
acceptance covers implementation commit `deb88cda96b1b3989f37a525db5b6555849611db` and pending-state documentation
commit `18c9fe5154154e90aedeff81199a94cc85f6a6dd`. At the v0.26 acceptance checkpoint, Migration 21 was latest and
Migration 22 was absent. Phase 2 remains ACTIVE / INCOMPLETE; no successor after v0.26 was selected at that checkpoint.

The implemented durable lifecycle is: exact accepted v0.25 visual-production lineage → immutable Script-owned managed
`NarrationAsset` → immutable `FinalMediaInputSnapshot` → terminal `RenderExecution` → immutable managed
`FinalMediaArtifact` → delegated manual production QA and manual publication handoff. Narration is bounded manual WAV,
MP3 or M4A import only; multiple takes are retained with no current/latest take and no TTS. A snapshot requires the
exact Gate-authorized VisualPlan, exact Script and NarrationAsset, every ordered current Scene exactly once, one exact
AssetSelection per Scene, frozen managed Asset SHA-256/reference provenance, exact timing, deterministic captions and
fixed render settings.

Local FFmpeg/FFprobe render synchronously to 1080×1920, 30fps H.264/AAC MP4 with static, slow-zoom-in or
slow-zoom-out motion, cuts or fixed 250ms crossfades, and burned deterministic captions. Crossfade overlap is internal
and never changes the caller-facing frozen duration. Each attempt is terminal `succeeded` or `failed`; multiple
explicit attempts are retained, failures create no artifact, and successful artifacts retain managed bytes, SHA-256
and FFprobe technical validation for safe exact retrieval. The narrow API provides narration import/list/get/content,
snapshot create/get, synchronous render create/get, and artifact get/content routes without caller-controlled paths,
digests, duration, render profile or FFmpeg arguments.

Validation: Ruff passed, **114 pytest tests** passed, `git diff --check` passed, and real repository-domain FFmpeg /
FFprobe proof exercised a two-Scene crossfade/caption render at 1080×1920, 30/1 fps, H.264/AAC and exact 2000ms
duration with matching retrieved SHA-256 bytes. Black 26.3.1 in-process equivalence checked 12 Python files with
`would_change=0`; the Windows CLI worker/process completion behavior remains a host-runtime exception. v0.26 adds no
TTS, paid-provider activation, cost/spend, publishing or publication records, queues/workers, production UI,
analytics/Learning, generic workflow engine or new founder Gate.

## v0.27 — First-Run Operability Bridge (Accepted Checkpoint)

**v0.27 — First-Run Operability Bridge** is **ACCEPTED**. Founder acceptance covers implementation commit
`8dd10ef793ac44c25107f02ba4b6bb5c333cf500` and pending-state documentation commit
`cb5fb1593827e6f7f0943973e86d992ea10dccf5`. v0.26 is its accepted historical predecessor. It adds only thin HTTP ingress over
existing repository semantics: Opportunity creation; ResearchPack-scoped Claim creation; reusable Source creation;
ClaimEvidence linking/upsert; and eligible EditorialAngle–Claim linking. This closes the early first-run research and
editorial ingress gaps without workflow state, research automation or generic CRUD.

It also adds one deliberate imported-reference lifecycle: qualifying managed imported character Assets may form an
immutable ordered `CharacterReferenceSet` through an explicit CharacterProfile-scoped route. Every member must be an
imported managed Asset from a Gate-authorized character AssetSpec with the exact CharacterProfile and verified
SHA-256 bytes. No AssetSelection is required before bootstrap; the resulting set can then satisfy existing imported
character AssetSelection provenance. Generated-reference requirements remain unchanged, no current/latest/best
reference state exists, and no provider, cost/spend, production trial or visual-canon change is introduced.

Later canonical Migration 22 adds only generated-narration provenance; Phase 2 remains ACTIVE / INCOMPLETE. Validation passed: Ruff,
**117 pytest tests**, `git diff --check`, and Black 26.3.1 in-process equivalence across 12 Python files with
`would_change=0`; the Windows Black CLI worker/process completion behavior remains a host-runtime exception. No
successor after v0.27 is selected.

# Next Step

Reference-grounded generation and explicit first-reference bootstrap are complete through v0.14. Phase 1 is
formally closed: the final production-ready SimilarStoic brand identity is **APPROVED**, and the visual
decision remains **PASS WITH DEFERRED VISUAL REFINEMENT** under the immutable SimilarStoic Core v3 baseline.
Phase 2 remains active and incomplete. v0.27 — First-Run Operability Bridge is the latest named accepted implementation
milestone; current canonical source/runtime migrations are through 23. Production #1 has occurred as a
technical/end-to-end trial but is not accepted final quality. Reconciliation is complete; the next product action
requires a new founder + ChatGPT decision.
The roadmap remains governed by canonical GitHub documentation and the explicit change protocol in
[docs/CANONICAL_HANDOFF.md](docs/CANONICAL_HANDOFF.md).

The first approved implementation direction remains immutable Idea Gate review snapshots plus immutable Idea
Gate decisions. The accepted v0.15 implementation adds its narrow persistence, API and minimal Discover
interaction through migration 12, without changing deferred scope. Editorial Gate spend authorization is a future
production/financial-control direction and is not part of that first slice.

Neutral CharacterProfile candidate generation, guaranteed cross-generation consistency, Generic AssetLibrary,
imported/manual reference ingestion, named reference roles, similarity scoring, automated character-consistency
QA, generic approval/current/best state, provider registry, queues/workers/batching, animation/rendering,
publishing, analytics, compliance, source attribution/citations and exact Script-to-Claim/evidence work remain
deferred.

Implemented direction through v0.14: v0.8 adds GenerationExecution provenance between an AssetSpec and any
generated Asset; v0.9 adds immutable VisualStyleProfile provenance and deterministic prompt composition;
v0.11 adds immutable CharacterProfile identity provenance; v0.12 adds immutable, ordered,
digest-backed CharacterReferenceSet selection; v0.13 consumes verified references; v0.14 adds explicit
first-reference bootstrap without changing normal grounded-generation semantics. Manual and imported Assets
remain valid without execution provenance, but cannot be canonical references.

> Opportunity → Research Pack → Claims → Sources / Evidence → verification / provenance → Editorial Angle → ContentPiece → Script → VisualPlan → Scenes → AssetSpecs → GenerationExecution → Assets

The final Pillar taxonomy, configurable research rules, scoring system and broader evidence policy
remain intentionally unsettled. v0.3 does not implement those later decisions.

## Development Method

> DEFINE → DESIGN WITH USER → BOUNDED CODEX TASK → IMPLEMENT LOCALLY → VALIDATE → REVIEW → FIX REGRESSIONS → COMMIT → PUSH → NEXT MILESTONE

This is the established method for preserving **change without rebuild**.

---

# Important Project Rule

No AI agent should assume missing decisions.

If a product/business decision materially affects:
- Brand
- Audience
- Editorial direction
- Monetisation
- Risk
- Quality

The agent should ask the founder rather than inventing a decision.

Technical implementation decisions may be made autonomously where they do not materially alter the approved product specification.
