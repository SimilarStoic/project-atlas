# Conveyor — Canonical Handoff and Governance

## Purpose and authority

This document is the durable cross-chat re-grounding guide for Conveyor. GitHub is the canonical
repository of truth. The founder is product owner and final product and acceptance authority. ChatGPT works
with the founder as product architect, technical decision-maker, roadmap interpreter, milestone designer,
architecture steward, bounded Codex task author, implementation reviewer and anti-drift guard. Codex is a
bounded repository inspection and implementation agent; it must not independently decide product architecture,
roadmap changes, milestone boundaries, domain semantics, successor sequencing, or final technical direction.

The canonical roadmap in [ROADMAP.md](../ROADMAP.md) is static by default. Neither a new chat, incomplete
conversation memory, implementation convenience, nor an inferred better sequence may change phases, reorder
direction, reinterpret commitments, remove requirements, add objectives, or treat deferred or unspecified
work as approved.

A roadmap or specification change becomes canonical only when the founder explicitly approves it with
ChatGPT, it is explicitly identified as such a change, canonical GitHub documentation is deliberately
updated, the change is reviewed and accepted, and that update is committed and pushed. Until then, the
existing GitHub roadmap and specification remain authoritative.

## Current canonical synchronisation state

### Current canonical snapshot

- Git checkpoint: `58c69ffad0bc5523c9a23ad25f5076aab0d330b0` — `production: accept SimilarStoic Production 5`.
- Phase 1 is complete; Phase 2 — Content Operating Model is **ACTIVE / INCOMPLETE**.
- Productions #2–#5 are accepted. Production #5 v4 is the accepted artifact, SHA-256
  `c35e8e6211ae9bf7bfeb694ec6dbec3c69d822862729d9d9f4440d50028ea2bd`; v1–v3 remain historical iteration evidence.
- Reference-driven dynamic SimilarStoic generation is **DEFAULT / ACCEPTED**. Approved visual references are generative
  DNA for new script-specific scenes, not a finite content inventory.
- Migrations 1–24 are contiguous. Migration 24 adds multi-authority visual-reference persistence; Migration 25 is
  absent. Publishing/learning is approved in design only and is not implemented.
- Public launch is unauthorized and Production #6 has not started.
- Marin is the provisional production-development baseline; the permanent narrator is unresolved. Narrator naturalness
  is the next focused pre-launch objective: **CHANGE VOICE WITHOUT REBUILD**.
- Active quality-envelope exposure is `$7.43 / $10`; `$2.57` remains.
- Founder owns final product, quality, spend, publication and push decisions; ChatGPT owns product architecture and
  canonical specification stewardship; Codex performs bounded inspection, implementation and validation.
- Governing principle: **CHANGE WITHOUT REBUILD**.

### Fresh-chat instruction

For findings reviewed on 8 September 2026, read [Production #1 quality-cycle continuity](QUALITY_CYCLE_20260902.md)
and its [evidence manifest](QUALITY_CYCLE_20260902_MANIFEST.json). They record proof rejection, incomplete Marin audio,
actual alignment, Cedar's relative preference/rejection, the failed full-scene image method, the successful isolated
acting-pose method, the approved separated environment/composition method, the accepted abstract scene and the first
approved hand-drawn gross-up break-frame, qualified spend and reference-set provenance. The synchronized parent
checkpoint for Production #5 acceptance is `144a201e6484ceec778d5fd8dee94bd2f935dc31`; Production #4, the controlled publishing/learning design and the
[multi-authority visual-generation architecture](MULTI_AUTHORITY_VISUAL_GENERATION.md) are synchronized. Migration 24
is operational. Production #5 v4 and reference-driven dynamic SimilarStoic generation are **ACCEPTED** as the default
visual-production method. Immutable v1–v4 evidence is preserved. Founder assessment places v4 at approximately 95% of
desired public-launch production quality; public launch remains unauthorized and narrator naturalness is the primary
remaining pre-launch quality track. Rejected experimental implementation remains excluded from canonical history.

For the current compact creative vocabulary governing acting categories, environment families, props/effects,
composition patterns, reuse, negative space and signature break-frames, read
[SimilarStoic Visual-Production Vocabulary](SIMILARSTOIC_VISUAL_VOCABULARY.md). It is design canon, not runtime
architecture or production authorization.

The multi-authority implementation preserves the working CharacterProfile/CharacterReferenceSet path and adds the
minimum typed, digest-backed non-character authority and execution-recipe provenance needed for new reference-driven
scenes. Migration 24 and the canonical runtime authority materialization are validated locally; no provider work was
performed.

Treat this document as continuity context, but verify repository facts through Codex where possible. Do not use later
chat recollection to override repository evidence. Do not push without explicit current founder authorization.

### Source of truth and authority

Use this precedence order: **(1) current GitHub `main`; (2) canonical tracked documentation; (3) source, migrations
and tests; (4) verified persistent runtime; (5) verified local experimental/review evidence;
(6) this continuity handoff; (7) chat recollection.** Founder is final
authority for product direction, architecture, editorial/quality acceptance, milestone selection, destructive actions
and final push. ChatGPT is product architect, roadmap/specification steward, anti-drift reviewer and bounded Codex
task author/reviewer. Codex is the bounded local inspection, implementation, testing and validation agent. Governing
principle: **CHANGE WITHOUT REBUILD**.

### Current canon and pre-reconciliation history

**Base before the publishing/learning design candidate:** local `main` and `origin/main` both resolve to
`48c79b7216e4793b1d9d7dfcb939aeebaf3038c6`, ahead/behind `0 / 0`, with the tracked tree clean. Founder-rejected
experimental `ad52ab38ad32f97b933099ef98a32dc8fd268662` remains preserved separately and is not promoted. The earlier
2 September synchronization recorded `f44f65b` with ahead/behind `0 / 0` before its documentation commit; that is
historical context.
Phase 2 is ACTIVE /
INCOMPLETE; v0.27 — First-Run Operability Bridge remains the latest named accepted implementation milestone, v0.26 is
its accepted predecessor, and no successor milestone is selected. Source and verified runtime migrations are contiguous
through 24 in the synchronized implementation: Migration 22 adds generated-narration provenance and
`local_system_speech` execution support; Migration 23 adds truthful `openai_tts` support; Migration 24 adds
multi-authority visual-reference persistence. These post-v0.27 changes do not constitute an accepted v0.28 milestone.

**Historical pre-reconciliation context:** `origin/main` was
`5220320ef81e422dec338b8410ad80b5491c0f31`, where Migration 21 was latest. Local `HEAD` was
`2358f244b48db9cae49e0a0bc8b1ec9ce0525811`, four commits ahead and zero behind, before founder review and the
authorized push. That local candidate history comprised:

1. `539624751f8de9317c01d3b32a2c5f4211459bd2` — deterministic static mascot production path.
2. `c1b26381ddf7d92ef7d3c4b0449c7f3e6e5eb0cb` — generated narration provenance / Migration 22.
3. `cf3b1a4cedc6ddfb5f405a8a82d9147b5f56d11e` — local narration production recovery.
4. `2358f244b48db9cae49e0a0bc8b1ec9ce0525811` — OpenAI narration refinement / Migration 23.

### Persistent runtime and migration distinction

The current persistent runtime is outside Git at `D:\ConveyorRuntime`: `conveyor.db`, `assets\`, and `media\`.
The runtime directory and its contents must not be committed. This is a workstation convention, not a hardcoded domain
requirement; portable configuration remains `ATLAS_DB_PATH`, `ATLAS_ASSET_STORAGE_ROOT`,
`ATLAS_MEDIA_STORAGE_ROOT`, `ATLAS_FFMPEG_PATH`, and `ATLAS_FFPROBE_PATH`.

`D:\ConveyorRuntime\conveyor.db` passed SQLite `integrity_check`; migrations 1–24 are contiguous. Migration 22 adds
generated narration provenance and immutable `NarrationGenerationExecution` records. Migration 23 adds truthful
`openai_tts` support alongside `local_system_speech`. Migration 24 adds immutable visual-reference authorities,
ordered managed-Asset members and direct generation-execution lineage. These post-v0.27 changes do not create a v0.28
milestone.

`D:\ProjectAtlas\data\atlas.db` is protected legacy/local historical state, separate from the runtime. It must not be
migrated, overwritten, moved, deleted or repurposed. Its verified SHA-256 is
`5B414FBE03BF86765FFCB095715B12F3CCDBC064E797552C41D140E6B6B3320E`.

### Production #1 exact status

Production #1 **did occur** through the persistent Conveyor lifecycle. Its technical/end-to-end trial is completed;
its production-quality acceptance is **FAILED / NOT ACCEPTED**. The Script/content was broadly acceptable, but neither
original artifact nor the later presentation proof is accepted as final SimilarStoic channel quality.

- Hazel baseline: `final-media-artifact-similarstoic-control-v1-hazel-desktop-v1`, SHA-256
  `ae326e5722f5d361d6cf0b382e454639cdcca2ec7899439af0839e92cba621ef`, duration 45.168 s. It was technically valid,
  but founder found narration robotic, visuals too static, captions too dominant and engagement weak.
- OpenAI/Marin refinement: `final-media-artifact-similarstoic-control-v1-refined-openai-marin-v2`, SHA-256
  `e26f386e10d4a443247f98801ed48592876ca67a4af0e180864fdc392956ec7e`, duration 34.400 s. Narration was materially
  more natural, but not accepted as a unique permanent SimilarStoic voice; the static mascot, typography/captions and
  scenes/backgrounds did not produce an accepted presentation identity.

`Microsoft Hazel Desktop` is technically functional but founder-rejected for robotic quality. OpenAI
`gpt-4o-mini-tts` / `marin` produced successful immutable execution
`narration-generation-similarstoic-control-v1-openai-marin-attempt-1` and narration SHA-256
`648c1be676cd6a68731844a9fc9676116b32f23f316ac7e6d0379af005e74486`. OpenAI custom-voice capability was inspected
read-only and was unavailable through the configured endpoint/account at that time. No consent recording or founder
voice recording was uploaded, and no custom voice was created.

Founder + ChatGPT later accepted the bounded audiovisual integration proof at
`D:\ProjectAtlas\work\similarstoic-audiovisual-proof-20260909\founder-review\similarstoic-audiovisual-integration-proof-v1.mp4`,
SHA-256 `1267f9c05c3431ee2d71fe73433f318efc9bfb935616a13fd56593500f7d55ca`, duration 18.03 seconds, 1080×1920,
H.264/AAC. It demonstrated that approved static compositions remain coherent under restrained push/pull, drift,
foreground effects, simple reveals and idea-led cuts. Its six compact caption cues came from actual final-audio word
timings, and all 45 words of the selected canonical excerpt were recovered from the mastered narration. It is materially
closer to publishable SimilarStoic quality than Hazel or Marin v2 without claiming automatic readiness for later videos.

OpenAI `gpt-4o-mini-tts-2025-12-15`, voice `marin`, is now the **PROVISIONAL ACCEPTED PRODUCTION-DEVELOPMENT
BASELINE**. It is good enough to continue production development but is not the permanent channel voice. Permanent
narrator identity remains open; a future founder-derived custom voice requires founder-provided recordings, explicit
consent and separately authorized provider work.

Narrator identity and TTS provider are separate concerns. Either may later change without rebuilding script, visual
plan, approved imagery, composition grammar, motion design or editorial structure. Any voice replacement requires new
narration audio, completeness transcription, actual speech alignment, caption timing, duration-dependent edit timing
and final rendering. Never reuse old timestamps; preserve provider, model, voice and reference/consent provenance.

### v0.28 and accepted Production #2

The flattened mascot source was used for Production #1. Later facial-overlay, deterministic motion, layered
reconstruction and animation-ready rig experiments were non-canonical and founder-rejected; the flattened source was
insufficient for high-quality programmatic reconstruction. No canonical rig exists, and the static-character
presentation is not accepted as the final SimilarStoic identity standard. No v0.28 milestone or Migration 24 exists.

Production #2, **Why a paid-off credit card can still affect your score**, completed the existing governed runtime
lifecycle from design checkpoint `9fbf807e0148a177ba86902922d17c4851a5e200` and passed founder + ChatGPT final
quality review. The mutable `credit-utilisation` Opportunity now records `accepted` status and the exact accepted
artifact identity. Immutable render and final-artifact rows remain unchanged as at-render history.

The lineage includes research pack `research-pack-similarstoic-credit-utilisation-v1`, Script
`script-similarstoic-credit-utilisation-v1`, VisualPlan `visual-plan-similarstoic-credit-utilisation-v1`, narration
`narration-asset-similarstoic-production-2-marin-v1`, input snapshot
`final-media-input-snapshot-similarstoic-production-2-v1`, render execution
`render-execution-similarstoic-production-2-founder-review-v1` and final artifact
`final-media-artifact-similarstoic-production-2-founder-review-v1`. The runtime-managed MP4 at
`D:\ConveyorRuntime\media\production-2\similarstoic-production-2-credit-utilisation-founder-review-v1.mp4` has
SHA-256 `ea7f490c046eb424624fb5147d84e792dff561af76f345ecc1ca068c5f7a5493`; it is 48.120 seconds,
1080×1920, 30 fps H.264/AAC. Full decode passed, all 126 Script words are present and all 32 captions derive from
final-master speech alignment. The UK-first claims preserve material geography and scoring-model distinctions.

Marin remains the **PROVISIONAL ACCEPTED PRODUCTION BASELINE** and permanent narrator identity remains replaceable.
Six-scene visual continuity passed. Current conservative envelope exposure is `$3.81`,
leaving `$6.19` of the authorized `$10`; Production #2 added `$0.781255` conservative exposure and no exact
provider-reported dollar charge. This acceptance creates no v0.28 milestone, Migration 24, rig or architecture change
and does not authorize Production #3.

### Minimum repeatable cadence and accepted Productions #3–#4

The proposed [minimum repeatable cadence](SIMILARSTOIC_PRODUCTION_CADENCE.md) limits work in progress to one and targets
one founder-review-ready short per five working days. Routine queue selection, source/evidence preparation, editorial
drafting, visual planning, asset decisions, narration/alignment, captions, rendering, QA, provenance and bounded fixes
run without separate founder interactions once exact design and spend authority exists. Consequential design/spend,
final artifact, canon, publication, roadmap, migration and architecture decisions remain founder-reviewed under the
existing gates.

[Production #3 — Bounded Design](PRODUCTION_3_DESIGN.md) records the completed and accepted low-risk evergreen piece:
**The £300 monthly upgrade that quietly adds up to £72,000 over 20 years**. The exact figure is nominal cash arithmetic
`£300 × 12 × 20`, without investment-return, inflation, borrowing-cost or wealth claims. The mutable
`lifestyle-inflation` Opportunity is `accepted`; immutable runtime lineage ends at final artifact
`final-media-artifact-similarstoic-production-3-founder-review-v1`.

The runtime-managed MP4 at
`D:\ConveyorRuntime\media\production-3\similarstoic-production-3-lifestyle-inflation-founder-review-v1.mp4` has
SHA-256 `8153d42cc006e79ddbd90502f2f9be3a0d4a7b6fe6226c01657a50bd65145dd4`; it is 48.450 seconds, 1080×1920,
30 fps H.264/AAC. Full decode, complete narration, final-duration caption timing and six-scene visual continuity passed.
Production #3 added `$0.0170125` conservative/calculable exposure, bringing the active envelope to `$3.83 / $10` with
`$6.17` remaining. Canonicalization added no provider call or spend. Marin remains provisional and replaceable.

### Accepted Production #4

[Production #4 — Design and Acceptance](PRODUCTION_4_DESIGN.md) records **Three AI workflows that make a junior
analyst more valuable**. The mutable `ai-workflow` Opportunity is `accepted`; immutable runtime lineage ends at final
artifact `final-media-artifact-similarstoic-production-4-founder-review-v1` while render and artifact rows preserve
their exact at-render `pending` metadata.

The runtime-managed MP4 at
`D:\ConveyorRuntime\media\production-4\similarstoic-production-4-ai-workflows-founder-review-v1.mp4` has SHA-256
`a9a15ec24be9ed11df601c61a6dd5ff5e42a983b81449fc2dffefe795c7118ac`; it is 65.400 seconds, 1080×1920,
30 fps H.264/AAC. Full decode, 144/144 normalized narration words, final-audio caption timing and six-scene quality
checks passed. Production #4 added `$0.557925` conservative/calculable exposure, bringing the active envelope to
`$4.39 / $10` with `$5.61` remaining. Canonicalization added no provider call or spend. Marin remains provisional.

Forward production lesson: labels, checklists and diagrams may support the action, but the hamster and visual metaphor
should remain the primary illustration whenever possible; avoid slide-deck or infographic drift. Production #4 remains
accepted without revision.

### Production #5 review state

Production #5 v4 and the Migration 24 reference-driven scene-generation path are **ACCEPTED**. The accepted exact MP4
has SHA-256 `c35e8e6211ae9bf7bfeb694ec6dbec3c69d822862729d9d9f4440d50028ea2bd`; preserve exact v1–v4 artifacts and immutable
lineage. The method is the SimilarStoic default: approved authorities are generative DNA for new script-specific scenes,
not a finite content inventory. Repair-don't-empty, connected topology, structural geometry, facial-expression and
occlusion/layer integrity, reuse-with-variation, semantic grounding, social-mobile-v3 captions, static-camera default
and full-resolution/normal/phone inspection remain mandatory. Founder accepted two non-blocking historical observations:
a small residual line beneath the mouth in one frame and one bag/table occlusion-depth inconsistency. Marin remains
provisional and replaceable. Final exposure is `$7.43 / $10` with `$2.57` remaining. Public launch is unauthorized;
Production #6, Migration 25, publishing implementation and publication remain absent.

### Controlled publishing and performance learning loop

Productions #2–#5 satisfy the current production-method validation objective. Narrator naturalness is the next focused
quality task. Publishing remains unauthorized; when separately authorized, the canonical candidate
[Controlled Publishing and Performance Learning Loop](PUBLISHING_AND_LEARNING_LOOP.md) selects YouTube Shorts as the
sole initial pilot platform, retains one founder decision for each exact public action and keeps the existing pace at no
more than one pilot Short per week.

The pilot uses local package preparation, founder approval of the exact artifact/package/account/time, private upload,
remote processing/metadata verification and only then the approved public transition. Core observations are engaged
views/views, watch time, average duration/percentage, the time-normalized retention curve, likes, comments, shares and
subscribers gained, captured append-only at approximately 24 hours, 72 hours, 7 days and 28 days. One item cannot change
strategy; repeated evidence across comparable items is required before even a bounded routine adjustment.

Current migrations 1–24 preserve provenance through `FinalMediaArtifact` and visual generation authorities, but have
no publishing-package, publication, performance-snapshot or learning-assessment persistence. A future additive
publishing migration is justified before an automated live pilot and will use the next available number, currently
expected to be 25. No platform API, credential or external publication has occurred.
Subsequent founder direction assigns Production
#5's immediate role as the reference-driven dynamic-scene/quality-uplift proof; only an accepted artifact may later
serve as the first live-loop item after publishing implementation and exact publication authority. Production #6 must
not begin.

### Approved secondary acting-pose reference

Founder + ChatGPT accepted
`assets/visual-references/core-mascot/poses/core-v3-umbrella-resistance-acting-pose-v1.png`, SHA-256
`a6ebaec876b40a7a89b22bca26e18ffa56d0709078498d3126946990c55e581e`, as **Core v3 — umbrella resistance acting
pose v1**, the first approved SimilarStoic acting-pose reference / pose-pack seed. It is a secondary pose/performance
reference showing approved physical deformation while the hamster remains recognizable. It does not replace the
primary identity authority at `assets/visual-references/core-mascot/identity/9a9ccdc1-b948-45d1-a375-fc36d4e3bdc2.png`
and does not establish a complete pose pack, rig, permanent provider choice or automatic acceptance of later outputs.

The accepted isolated-character method used GPT Image 2 edits with exact canonical tracked references directly and no
generated reference board. Candidate 1 preserved identity and acting but retained shading/vignette defects. Candidate
2 was the single defect-targeted refinement and passed founder review. The separate Leonardo Phoenix environment-only
attempt was rejected because it inserted an unwanted different hamster and umbrella. It is not promoted.

### Approved environment style and default scene language

Founder + ChatGPT selected Candidate 4 from the controlled environment calibration as the approved **environment
style / default-scene-language reference**. Its exact tracked copy is
`assets/visual-references/environments/style/similarstoic-default-scene-language-v1.png`, SHA-256
`989e0da7b273a42f0bf8c229c1510b904902b1eef3336e626705966e6048ccb2`. It defines the normal visual language of the
world around Core v3: predominantly warm white/off-white space, generous negative space, sparse composition, simple
imperfect hand-drawn outlines, restrained block colours, few useful props and only enough detail to establish location,
concept or action. Character, props and environment must appear to share one illustrator, without a stylistic seam.

Candidate 4 is approximately the upper normal detail boundary for an ordinary scene; untracked Candidate 3 shows a
viable lower-detail pole. Ordinary scenes may sit between them. Candidate 4 is a style reference, not mandatory reusable
scenery, a universal background, an environment pack or permanent provider selection. Predominantly flat colour allows
very subtle unobtrusive tonal variation, but obvious gradients, realistic or volumetric lighting, glossy rendering,
photorealistic shading, detailed materials and painterly texture remain rejected. Predominantly white/off-white is the
ordinary-scene default; night scenes, hero/break frames, intense moments, special diagrams and deliberate visual jokes
may later use purposeful exceptions.

Visual simplicity is a SimilarStoic brand choice first and a production-efficiency advantage second. It may improve
consistency, character/world matching, generation efficiency and reuse, but “simple on purpose” must never become
“cheap-looking”; quality remains authoritative over marginal cost savings.

Primary identity authority, approved acting-pose reference and environment-style reference remain distinct semantic
roles. The environment reference must inherit compatible line weight, complexity, colour treatment, shape language and
rendering density from Core v3, but it cannot define the hamster's identity or approved deformation.

### Approved static composition grammar

The zero-provider-spend static integration experiment and its bounded refinement both passed founder + ChatGPT review.
The exact refined frame is tracked at
`assets/visual-references/compositions/grammar/similarstoic-static-composition-grammar-v1.png`, SHA-256
`c6f933eddf7394ff3d00708650f7c1fa1df2f29ff8011e7ae4858653dd1f45d8`, as the first approved **composition-grammar
reference**. It demonstrates character-first hierarchy, subordinate context, deliberate warm-white/off-white negative
space, mobile-readable character scale, action-aware off-centre placement, minimal illustrative ground contact and
sparse environmental marks crossing the character plane without obscuring it.

Identity, acting-pose, environment-style and composition-grammar authorities remain distinct. The hard assembly rule is
that character, props, environment and compositing treatments appear to share one illustrator: avoid mismatched line
weight, density, shading, texture, perspective sophistication, colour treatment or polish. Negative space is active
design, and the target is simple on purpose rather than cheap-looking.

This approval validates the separated method for one static scene. The exact storm layout is not mandatory, no complete
scene pack exists, and repeatability across multiple scene types remains unproven. It creates no runtime Asset record,
Production #2, successor milestone, rig or video-production authority.

The separated method of stable approved pose assets plus independently sourced/generated environments and controlled
Conveyor composition is visually validated for this one scene, but is not accepted as expanded architecture. Working
cumulative experiment spend is `$24.107475`, leaving `$0.892525` under the existing cumulative `$25` authorization,
with the billing qualifications in the quality-cycle note unchanged.

### Historical pre-Production #5 gate — superseded

Before Migration 24 and Production #5 were accepted, the required gate was to review and synchronize the
multi-authority implementation before beginning Production #5. That gate is satisfied and is retained only as
chronology. Publishing/learning persistence remains unimplemented and, if separately authorized, will use the next
available migration number, currently expected to be 25. No platform call or external publication has occurred;
Production #6, a successor milestone, v0.28 and a rig remain absent/unauthorized.

Historical accepted-checkpoint detail below is retained as historical context; it does not supersede this current
canonical state.

### Current product identity

**Conveyor** is the current engine, project and operating-system identity. **Project Atlas** is the historical/legacy
project name. **SimilarStoic** remains the outward-facing channel, editorial brand and mascot world: **SimilarStoic by
Conveyor**. Legacy Atlas technical identifiers remain intentionally preserved for compatibility; historical Project
Atlas records remain historical truth and are not rewritten. This rename creates no implementation milestone and does
not change schema, migrations, package namespace, environment-variable names, DB path, API routes, GitHub repository
name, or successor state.

### Historical Phase 1 implementation checkpoint

**v0.14 — Explicit Character Reference Bootstrap**

- Commit: `516884b8fab0a29e8e82973d684be1ae8a08bff6`
- Subject: `feat: add character reference bootstrap`
- Acceptance state: migrations 1–11; 75 tests passed; Ruff, Black `--check`, and `git diff --check` passed.
- At acceptance, local `main == origin/main` and the working tree was clean.

## Current canonical product and roadmap state

**Phase 1 — Product & Business Definition is formally closed.** The founder-approved final
production-ready SimilarStoic brand identity is approved. The Phase 1 visual decision remains **PASS WITH
DEFERRED VISUAL REFINEMENT**: residual AI-clean/overly professional finish is non-blocking and does not
alter the approved hamster identity, colours, sling-bag treatment, proportions or CharacterReferenceSet
continuity.

SimilarStoic Core v3 remains the current accepted visual baseline. The historical CharacterReferenceSet v1 remains
unchanged within its original database history; the same ID has different members in the persistent runtime. See the
[database-qualified provenance finding](QUALITY_CYCLE_20260902.md#reference-set-provenance-qualification); do not
rewrite either history or treat the set ID alone as globally interchangeable.
**v0.27 — First-Run Operability Bridge** is the latest accepted implementation milestone; **v0.26 — Narrated Final
Media Production** is its accepted historical predecessor. **Phase 2 — Content Operating Model is the current ACTIVE /
INCOMPLETE roadmap phase, with accepted v0.15 through v0.27 implementations and no selected successor after v0.27**,
under founder + ChatGPT design/implementation stewardship. This does not authorize
all Phase 2 scope or later-phase engines.

## Accepted end-to-end target operating model

Conveyor is intended to become an approximately **95% automated content operating system**. The target is not to
remove human judgement: routine execution is progressively automated while founder interaction concentrates,
where practical, at three target operating-model gates. The **Idea Gate** covers review, approval, rejection,
steering and reprioritisation of explained candidate opportunities. The **Editorial Gate** covers founder
decisions on the prepared title, hook, angle, script, supporting research/evidence context, risk/uncertainty
notes, revisions and alternatives, plus bounded paid-production spend authorization where relevant. The
**Learning Gate** covers performance, evidence-backed hypotheses,
proposed adaptations and available economics context. These gates are not approved database or workflow-state
entities.

Automation may eventually operate between and around those gates across discovery, research, verification,
editorial work, visual planning, generation, narration/audio, rendering, quality control, publishing,
analytics, learning, scheduling, cost/revenue tracking, economics/control reporting and financial guardrails.
It must increase only after quality, provenance and operating behaviour are demonstrated: **automate proven
workflows; do not automate uncertainty merely because automation is technically possible.** Human review may
remain mandatory for high-risk claims, material factual uncertainty, sensitive/regulated subject matter,
exceptional spend, system-health/quality exceptions and other later-defined areas.

The existing durable foundation chain is:

> Opportunity → Research Pack / Claims / Sources / Evidence → Editorial Angle → ContentPiece → Script → VisualPlan → Scene → AssetSpec → GenerationExecution → Asset

This is not proof that the complete operating system is implemented. The approved direction extends toward
Publication → platform performance → analytics → revenue/economics → learning → future opportunity/content
decisions, without approving publication, analytics or financial schemas.

The phases retain their existing ordered roles: Phase 1 is complete product/business definition; active Phase 2
defines the human-led executable content lifecycle and its approved direction; Phase 3 provides the
technical substrate; Phases 4–8 add research, content intelligence, production, distribution and
analytics/learning capabilities; Phase 9 connects proven components toward the approximately 95% automated
target; and Phase 10 scales a proven system. No later phase is activated.

The current phase map is:

1. **Phase 1 — Product & Business Definition:** COMPLETE.
2. **Phase 2 — Content Operating Model:** ACTIVE / INCOMPLETE.
3. **Phase 3 — Technical Architecture:** NOT ACTIVE.
4. **Phase 4 — Research Engine:** NOT ACTIVE.
5. **Phase 5 — Content Intelligence:** NOT ACTIVE.
6. **Phase 6 — Video Production:** NOT ACTIVE.
7. **Phase 7 — Distribution:** NOT ACTIVE.
8. **Phase 8 — Analytics & Learning:** NOT ACTIVE.
9. **Phase 9 — Automation:** NOT ACTIVE.
10. **Phase 10 — Scale:** NOT ACTIVE.

## Approved Phase 2 operating-model specification

Phase 2 is **ACTIVE**. Its bounded v0.15 implementation is accepted; all remaining Phase 2 scope remains
unimplemented. Conveyor uses **sparse human gates and rich
machine readiness checks**: human approval concentrates at meaningful judgement boundaries, while intermediate
stages progress automatically only when explicit quality, evidence and provenance requirements pass. Human
judgement and machine readiness are distinct; neither may silently substitute for the other.

The target founder gates are version-specific operating concepts, not approved database/workflow entities:

- **Idea Gate:** Proceed, Reject or Steer an opportunity based on relevant/audience value, timeliness,
  discovery context, risk/uncertainty and Conveyor's recommendation; it is not ResearchPack approval.
- **Editorial Gate:** Approve, Revise, Reject or intentionally select an alternative editorial package of
  Title, Hook, Angle and Script with relevant evidence/risk context. Approval allows that specific proposition
  and version to progress subject to later readiness; it is not technical final-video approval. Where paid
  external production is contemplated, it also authorizes a bounded maximum spend for that proposition; this
  remains one linked Editorial Gate judgement, not a fourth routine founder gate.
- **Learning Gate:** accept, reject, limit, seek more evidence for, or override evidence-backed, scoped,
  reversible and historically attributable learning/adaptations. It must not silently alter brand, roadmap,
  audience, risk policy or governance.

No paid external production spend may occur without prior human authorization of a bounded envelope tied to
the approved editorial proposition. Approval authorizes a maximum, not a target: Conveyor should spend less when
it can still meet the required quality, brand, evidence and risk floor. If meeting that floor would exceed the
ceiling, Conveyor must stop and escalate rather than overspend or silently lower the quality requirement.

The eventual Editorial Gate production/spend proposal should make its exact editorial lineage and maximum
request understandable, with estimated total and stage/provider cost where available, expected quality,
meaningful lower-cost alternatives and trade-offs, recommended/premium rationale, and qualified expected
commercial or strategic upside. It must distinguish measured evidence, modelled expectation and speculation;
projected return is never guaranteed justification. Illustrative economy/recommended/premium labels are not
fixed future enums or a required number of choices.

Conveyor seeks the lowest-cost feasible path that clears the approved quality, brand, evidence and risk floor.
Provider, model, attempt count and workflow should be optimized before any quality bar changes; premium is not
automatically better and cheapest is not automatically preferred. Within a future authorized envelope Conveyor
may spend less, but sufficient remaining budget is required before paid external work begins. It must not
silently overspend or use open-ended retries. Exceptional extra spend or material risk requires a new human
authorization/exception path.

Opportunities remain mutable discovery records. Idea Gate authority must therefore apply to an immutable review
snapshot of exactly what the founder judged, not only to evolving current Opportunity state. The conceptual
snapshot freezes reviewable Opportunity identity, title, summary, why-now context, relevant Subject context,
score/ranking if presented, Conveyor recommendation/explanation, material risk/uncertainty and review
timestamp/provenance. This does not make Opportunity a fully versioned aggregate or approve fields/schema.

Idea Gate decisions are durable, immutable/additive and specific to one immutable snapshot. **Proceed**
authorizes that reviewed proposition into research/editorial development; **Reject** does not authorize it;
and **Steer** authorizes progression while preserving founder direction/comments for later work. They are
distinct from machine readiness and `Opportunity.status`. A future Proceed creates no ResearchPack, status
mutation, research job, queue, automation trigger or current workflow-stage change in its first implementation
slice. It must not introduce approval booleans, `Opportunity.current_decision`, generic Approval/universal
Decision entities, generic mutable workflow state, history overwrite or Opportunity mutation for direction.

Human authority applies to the exact immutable review representation judged. A material later Opportunity
change and re-presentation may create another snapshot and decision; both histories remain additive and
independently understandable.

### v0.15 — Persistent Idea Gate

v0.15 is the accepted first Phase 2 implementation milestone. It persists only
**IdeaGateReviewSnapshot** and **IdeaGateDecision**: explicit stable identity/provenance plus a schema-versioned
frozen payload of actually displayed Opportunity review context, and an immutable snapshot-specific founder
decision. Opportunity remains mutable. Visible Subject identity/slug/name/role freezes in the payload; no full
metadata dump, Opportunity versioning or normalized snapshot-Subject tables are authorized. Proceed/Reject/
Steer are the only outcomes; Steer requires non-empty preserved direction; one decision per snapshot is
enforced; and a later judgment uses a new snapshot.

Migration 12 is limited to those records, foreign keys, uniqueness,
outcome constraint and historical-read indexes. v0.15 provides create/get/list/history repository behavior,
separate snapshot then decision writes, domain-qualified API routes, and a minimal Discover/Command Centre
interaction that displays frozen material, persists the three outcomes and shows history. It has no public
update/delete/current/latest state, generic approval/workflow system, `Opportunity.status` reinterpretation,
ResearchPack/job/queue/readiness/automation effect, financial behavior or later-phase scope.

Its full acceptance requirements and exclusions are canonical in [ROADMAP.md](../ROADMAP.md): immutable
historical snapshots, readable frozen Subject context, each outcome, required Steer direction, additive second
review cycles, unchanged Opportunity semantics, compatible v0.1–v0.14 behavior, real API/UI proof, and passing
migration/repository/HTTP/UI/quality tests. Editorial Gate spend authorization remains outside v0.15.

Any scope beyond the defined v0.19 boundary requires a new explicit founder + ChatGPT
decision. Material ambiguity about semantics, migration scope, history, API meaning, founder decision meaning
or deferred scope must return to founder + ChatGPT rather than be inferred.

### v0.16 — Authorized Research Initiation

v0.16 is a historical accepted implementation predecessor to v0.18; v0.17 is the later historical accepted
predecessor and v0.15 remains an earlier historical accepted predecessor. Migration 13 remains canonical for its
bounded implementation, and migrations now extend through 1–15.
Its purpose is deliberate creation of Opportunity-owned ResearchPack versions under explicit qualifying Idea
Gate provenance, preserving Proceed/Steer founder authority and reference-only Steer direction without
research automation or workflow state. ResearchPacks retain Opportunity ownership and gain only an immutable,
nullable direct IdeaGateDecision provenance reference for the explicit lifecycle path. Historical/demo packs
remain valid, readable and unmodified with null provenance; no generic authorization/progression/workflow
model or fabricated backfill is authorized.

Only Proceed and Steer qualify; Reject must fail. The decision and its immutable review snapshot must exist,
and the snapshot must belong to the same Opportunity as the created pack. Founder Steer direction remains
authoritative only on IdeaGateDecision and is consumed by reference, never copied into ResearchPack state.

An Idea Gate decision remains authorization/provenance, not automatic orchestration: it does not create a
ResearchPack, start research, enqueue work, invoke a provider, mutate `Opportunity.status`, create readiness
or workflow state, or trigger automation. One qualifying decision may support multiple ResearchPack versions;
there is no consumed/current authorization state. Material Opportunity change requires a new snapshot/decision
before later research is treated as authorized. The v0.16 vertical slice is a dedicated qualifying repository
operation, a narrow Opportunity/ResearchPack-scoped POST endpoint, and a minimal Discover **Initiate Research**
interaction that collects existing pack inputs and displays the created pack/provenance. It excludes source or
Claim generation, research readiness/QA, queues/workers/providers, Editorial Gate, production, publication,
analytics/Learning, financial controls, Phase 4 research automation and Phase 9 orchestration.

Migration 13 is limited to the nullable direct provenance foreign key and its historical-protection/indexing
needs; it does not alter ResearchPack ownership/version uniqueness or other existing domain records. v0.16 is
accepted and implies no scope beyond its accepted boundary. The full acceptance requirements, implementation
boundary and ambiguity-return rule are canonical in
[ROADMAP.md](../ROADMAP.md) under **v0.16 — Authorized Research Initiation**.

The approved first half is Opportunity → Idea Gate → Research → machine research-readiness → Editorial Angle
→ ContentPiece → Title/Hook/Script development → machine editorial QA → Editorial Gate. Research readiness is
a machine boundary for proposed content/material claims, not a founder gate or a claim that a topic is fully
researched. Its approved design direction is additive, immutable, versioned assessments of an exact frozen
ResearchPack evidence state. A ResearchPack ID/version alone is insufficient because Claims, Sources and
ClaimEvidence may change after pack creation. Each assessment must retain a schema-versioned frozen snapshot of
the relevant ResearchPack, Claims, Sources, evidence relationships and freshness/as-of context; stable record
IDs preserve live-record provenance without creating a second mutable research source of truth.

The exact outcomes are **Ready**, **NeedsMoreResearch** and **Blocked**. Each assessment preserves its outcome,
findings/reasons, assessment schema version, policy/check version, timestamp and producer/implementation
provenance. Multiple assessments may coexist for one ResearchPack; evidence changes require a new assessment,
and earlier history remains immutable. No mutable current/latest/superseded readiness pointer or
`ResearchPack` readiness field is approved. v0.17 now implements its bounded readiness schema and controlled API;
it adds no UI, evaluator, provider call, research automation or founder
approval/override. A Ready assessment must not automatically create an EditorialAngle, ContentPiece or Script.
The approved lifecycle direction is explicit creation of an EditorialAngle under an exact supplied Ready assessment
with direct immutable initiation provenance. It is now canonically accepted as v0.18; the final Script-to-Claim
architecture and Editorial QA implementation remain deferred.

### Research and evidence quality canon

ResearchPacks precede scripting. Primary sources are preferred where appropriate; corroboration must be
proportional to risk, materiality and importance; and freshness matters. Conveyor must distinguish fact,
interpretation, opinion, forecast and illustration. Unsupported material claims must not silently progress.
ResearchReadinessAssessment persistence records immutable evidence-state assessments; it does not replace the
research-quality policy, and readiness is a machine boundary rather than founder approval. The final Phase 4
research evaluator and final Script-to-Claim architecture remain deferred; no scoring thresholds, universal
source-count rule, automated fact-check algorithm or evaluator design is implied.

### v0.17 — Persistent Research Readiness

v0.17 is a historical accepted implementation predecessor to v0.18. Migration 15 is canonical and migrations
extend through 1–15. v0.17 introduces only one immutable
ResearchReadinessAssessment table. The assessment belongs to one
ResearchPack and carries its own server/repository-built, deterministic, schema-versioned frozen evidence JSON;
no normalized snapshot aggregate, findings rows, generic readiness/workflow/approval entity or current/latest
state is authorized.

The frozen payload preserves the ResearchPack ID/version/summary/as-of context, relevant Claim fields,
relied-upon Source provenance and ClaimEvidence links in stable ID ordering with canonical JSON serialization.
Assessment records preserve Ready / NeedsMoreResearch / Blocked, structured findings, schema version,
policy/check version, producer kind/identifier/implementation version and time. They are create/get/list only:
multiple records may coexist, no backfill or readiness inference occurs, and corrections/reassessments are new
records. A caller supplies controlled assessment inputs while the server freezes canonical evidence; callers
cannot submit an arbitrary canonical snapshot.

The v0.17 API boundary is `POST /api/research-packs/{id}/readiness-assessments`, `GET
/api/research-packs/{id}/readiness-assessments` and `GET /api/research-readiness-assessments/{id}`. It requires
no UI, founder approval, evaluator, provider, job, queue or automation. It does not change ResearchPack status,
EditorialAngle, ContentPiece, Script, Title/Hook, Editorial Gate, progression authority, production,
publication, analytics/Learning, financial controls, Phase 4 research automation or Phase 9 orchestration.

### v0.18 — Readiness-Authorized Editorial Angle Initiation

**Status: HISTORICAL ACCEPTED IMPLEMENTATION CHECKPOINT.** v0.18 belongs to Phase 2 and is the historical
accepted predecessor to v0.19. v0.17 is its historical accepted predecessor; migration 15 is canonical and
migrations extend through 1–17. v0.25 — Operational Visual Production Inputs is the latest accepted implementation
milestone; v0.24 is its accepted historical predecessor. Migration 20 is latest, migration 21 is absent, and no
successor after v0.25 is selected.

Its purpose is deliberate creation of an Opportunity-owned EditorialAngle under one explicitly supplied immutable
`Ready` ResearchReadinessAssessment. The durable fact is direct immutable Angle → assessment initiation
provenance, conceptually `research_readiness_assessment_id`: **this Angle was initiated under this exact Ready
assessment**, not that a mutable Angle remains perpetually validated. The reference is nullable for
historical/legacy/demo Angles, required only on the new lifecycle path, and receives no backfill.

The dedicated operation is conceptually `create_editorial_angle_under_research_readiness(...)`: it takes the Angle,
Opportunity, ResearchPack and exact assessment IDs plus ordinary Angle fields. It validates the Opportunity,
ResearchPack, Pack → Opportunity lineage, assessment, exact `Ready` outcome and assessment → same-Pack lineage,
then creates one normal Angle and persists the exact reference. `NeedsMoreResearch`, `Blocked`, missing resources,
assessment/Pack mismatch and Pack/Opportunity mismatch fail. It must not infer latest/any Ready, consume/select or
mutate readiness, change `Opportunity.status`, generate/rank an Angle, invoke a provider, create ContentPiece or
Script, enqueue work, or create workflow state.

Existing low-level `create_editorial_angle(...)` remains compatible for legacy/seed/test use, including positional
callers; lifecycle readiness is not globally required. Normal editable Angle fields and Claim roles remain editable,
but the readiness reference cannot change through Angle edits and edits trigger no revalidation. One Ready may
support multiple Angles; later Ready, NeedsMoreResearch or Blocked assessments never rewrite or automatically
invalidate earlier provenance. Existing same-ResearchPack Claim-link validation remains; no frozen Claim matching,
Claim-role snapshotting or Script-to-Claim behavior is included.

The v0.18 vertical API is `POST /api/opportunities/{opportunity_id}/editorial-angles`, with explicit
`research_pack_id`, `research_readiness_assessment_id` and normal Angle fields. Its response exposes the direct
Angle/Opportunity/Pack/assessment provenance without duplicating frozen readiness evidence. Missing resources are
404-style; malformed or invalid lifecycle requests are 400-style under existing conventions. No UI is required or
authorized: this is not a founder gate and persistence/API proves the boundary without a premature manual workflow.

Migration 15 is canonical and is limited to the nullable direct reference on
`editorial_angles`, a restrictive FK and a lineage index. It must not change Angle versioning, ResearchPack,
ReadinessAssessment, Claim links, ContentPiece, Script, Title/Hook or Editorial Gate. The full v0.18 acceptance
criteria are canonical in [ROADMAP.md](../ROADMAP.md), including legacy compatibility, exact-Ready validation,
immutability, no-consumption/no-current state, multiple-Angle history, unchanged Claim boundary, no automatic
side effects, API proof and v0.1–v0.17 compatibility.

v0.18 excludes EditorialAngle versioning, frozen Angle snapshots, Claim-level revalidation, candidate generation or
ranking, LLM/provider calls, Phase 5 content intelligence, ContentPiece/Script/Title/Hook work, editorial QA/Gate,
jobs/queues/workers, Phase 9 orchestration, production, publishing, analytics/Learning and financial controls.
Phase 5 may later automate Angle generation and Phase 9 may later orchestrate progression; neither is included.
Material ambiguity about provenance meaning, lifecycle-only enforcement, legacy compatibility, exact qualification,
lineage validation, update immutability, Claim boundaries, API semantics or later phases returns to founder + ChatGPT.

### v0.19 — Editorial-Angle-Authorized ContentPiece Initiation

**Status: HISTORICAL ACCEPTED IMPLEMENTATION CHECKPOINT.** v0.25 — Operational Visual Production Inputs is the
latest accepted Phase 2 milestone. v0.24 is its accepted historical predecessor; migration 20 is latest,
migration 21 is absent, and Phase 2 remains ACTIVE / INCOMPLETE. Founder acceptance covers implementation commit
`32812e6793d9b06632ebffd82504cd8810c2ab3d`; Black 26.3.1, Ruff, 88 pytest tests and `git diff --check` passed.

Its purpose is the next smallest deliberate lifecycle edge:

> Ready ResearchReadinessAssessment → readiness-authorized EditorialAngle → explicitly initiated ContentPiece

v0.19 establishes deliberate creation of one ContentPiece from one exact eligible EditorialAngle. The operation must
receive explicit `opportunity_id`, explicit `editorial_angle_id`, and the existing ordinary ContentPiece fields. It
requires that the Opportunity and EditorialAngle exist; that the Angle belongs to that exact Opportunity; that the
Angle carries a non-null `research_readiness_assessment_id`; that this exact assessment exists and has outcome
`Ready`; and that assessment → ResearchPack → EditorialAngle → Opportunity lineage is internally consistent. It must
not select latest/current/any Ready assessment or substitute a different Ready assessment: the exact immutable
assessment already referenced by the Angle is the only relevant upstream provenance.

Legacy, demo and seed Angles with null readiness provenance remain valid historical/compatibility records, receive no
backfill or mutation, and are not eligible for this lifecycle path. Existing low-level ContentPiece creation may remain
available for existing compatibility, demo and test use; v0.19 must not globally reinterpret every ContentPiece as
requiring lifecycle eligibility.

The lifecycle-created fact means only: **this ContentPiece was deliberately initiated from this exact EditorialAngle,
whose own initiation was authorized under this exact immutable Ready ResearchReadinessAssessment provenance.** It
does not mean that the mutable Angle remains perpetually validated, Angle text is frozen, Claims were revalidated, the
Angle passed editorial QA, a current assessment was selected, the Angle or assessment was consumed, the ContentPiece
is production-ready, or an Editorial Gate passed. This is explicit lineage, not a generic workflow engine.

The durable chain is ContentPiece → EditorialAngle → ResearchReadinessAssessment. The existing immutable
ContentPiece → EditorialAngle provenance is sufficient: v0.19 adds no duplicate
`research_readiness_assessment_id` on ContentPiece and no migration 16.

One eligible EditorialAngle may initiate multiple ContentPieces. No consumption flag, current/latest ContentPiece,
one-use progression, generic progressed state or upstream revalidation is approved. Existing ContentPiece
Opportunity/Angle provenance remains immutable. Normal ContentPiece edits must not alter provenance, mutate or
revalidate the Opportunity, ResearchPack, assessment, Angle or sibling ContentPieces; later assessments must not
rewrite existing ContentPiece lineage.

The vertical API is `POST /api/opportunities/{opportunity_id}/content-pieces`, with `editorial_angle_id` and the
ordinary ContentPiece fields. Missing Opportunity and Angle use the existing 404 convention; wrong
Opportunity/Angle lineage, null readiness provenance, invalid/mismatched upstream lineage and non-Ready provenance
are 400-style failures. Success persists a ContentPiece under existing response conventions. No UI is authorized.

v0.19 excludes a full editorial package; Title; Hook; Script creation; Script-to-Claim relationships; EditorialAngle
versioning, snapshots, revalidation, generation or ranking; provider/model calls; research automation; readiness
evaluator; machine editorial QA; Editorial Gate; spend authorization; generic workflow/progression state; jobs,
queues or UI; image/visual generation; automated reference selection or visual-consistency QA; production,
publishing, analytics, Learning Gate implementation and orchestration. v0.20 is a separate accepted successor;
v0.19's accepted boundary remains unchanged.

The target second half is Editorial package → Editorial Gate approval + bounded spend authorization →
production within the authorized envelope → machine production/brand/risk QA → publication readiness →
automatic publishing unless an exception occurs → analytics/economics → machine learning interpretation →
Learning Gate → approved adaptations. Overspend is a financial exception requiring human escalation, not a
routine fourth gate. The existing initial human pre-publication approval rule remains until reliability is
demonstrated. Readiness failure is never silently bypassed, including through grounded-to-ungrounded fallback
or material output substitution.

Progression derives from existing domain records plus durable, version-specific decision history and readiness
evidence—not a generic mutable `WorkflowItem(status, approved, current_step)` source of truth. Substantive
versions require relevant re-evaluation; history remains additive. Phase 2 later needs only editorial-chain
decision/readiness/revision provenance. Production/publication readiness records remain for Phases 6/7,
Learning records for Phase 8, financial guardrails for future financial implementation, and orchestration for
Phase 9. No placeholder entities are approved.

The latest accepted Phase 2 implementation is **v0.25 — Operational Visual Production Inputs**; **v0.24 — Editorial
Gate + Approved VisualPlan Initiation** is its accepted historical predecessor. Material detail beyond the approved
boundaries returns to founder + ChatGPT.

### v0.20 — Readiness-Lineage-Preserving Script Initiation

**Status: HISTORICAL ACCEPTED IMPLEMENTATION CHECKPOINT.** v0.25 — Operational Visual Production Inputs is the
latest accepted Phase 2 milestone. v0.24 is its accepted historical predecessor; migration 20 is latest,
migration 21 is absent, Phase 2 remains ACTIVE / INCOMPLETE, and no successor after v0.25 is selected.

v0.20 adds one deliberate lifecycle edge: eligible ContentPiece → complete immutable Script version. Eligibility is
derived only from durable ContentPiece → EditorialAngle → exact `Ready` ResearchReadinessAssessment → ResearchPack
→ Opportunity lineage. The dedicated repository operation accepts ContentPiece ID, Script ID, narration text and
optional existing Script metadata; it derives version 1 or maximum existing version plus one from immutable history.
It neither accepts a caller version/readiness ID nor adds a lifecycle marker, current/latest state, duplicate
readiness FK, revalidation, mutation or consumption. Existing low-level Script creation remains compatible.

`POST /api/content-pieces/{content_piece_id}/scripts` accepts only `id`, `narration_text` and optional `metadata`.
Missing caller ContentPiece is 404-style; broken or non-Ready stored lineage is 400-style. No migration, Title/Hook,
editorial package, Script-to-Claim, QA/Gate, workflow, UI, VisualPlan, production, publishing, analytics, Learning,
orchestration, visual-canon or later-phase work is included.
Founder acceptance covers implementation commit `8dd8ecb7c22eb73b60b7d65853fbf11635d2188c`
(`feat: initiate Scripts from Ready ContentPieces`) and initial documentation commit
`4ddab9749c2159ad7a9801f0af1d5365046ac793` (`docs: record v0.20 script initiation pending acceptance`).
Validation passed: Black 26.3.1 `--check`, Ruff, 90 pytest tests and `git diff --check`.

### v0.21 — Editorial Draft Package Foundation

**Status: HISTORICAL ACCEPTED IMPLEMENTATION CHECKPOINT.** v0.25 — Operational Visual Production Inputs is the
latest accepted Phase 2 milestone. v0.24 is its accepted historical predecessor. Migration 20 is latest,
migration 21 is absent, Phase 2 remains ACTIVE / INCOMPLETE, and no successor after v0.25 is selected.

v0.21 adds immutable append-only TitleOption and HookOption alternatives for an eligible ContentPiece and frozen
EditorialPackageSnapshots that bind one exact TitleOption, HookOption and Script version from that same ContentPiece.
Creation reuses the ContentPiece's exact Ready lineage; readiness remains indirect and `working_title` remains
unsynchronized compatibility data. Migration 16 adds only the three approved tables, restrictive foreign keys and
history indexes, without backfill. ContentPiece-scoped create/list APIs and narrow GET retrieval are included.

v0.21 excludes selection/current/latest or approval state, Script-to-Claim, editorial QA/Gate, workflow, UI,
VisualPlan, production, publishing, analytics, Learning and orchestration. Founder acceptance covers implementation
commit `4e36cf6cfabe7e6dbe99e54804653edeec277d9a` and initial documentation commit
`46a1a59e4ec857f953240d4d9b7a9c33c1cb3f8d`; Black 26.3.1, Ruff, 93 pytest tests and `git diff --check` passed.

### v0.22 — Closed Script Claim Provenance Foundation

**Status: ACCEPTED IMPLEMENTATION CHECKPOINT.** v0.22 is a historical accepted Phase 2 milestone. v0.25 —
Operational Visual Production Inputs is the latest accepted Phase 2 milestone; v0.24 is its accepted historical
predecessor. Migration 20 is latest, migration 21 is absent, Phase 2 remains ACTIVE / INCOMPLETE, and no successor
after v0.25 is selected.

v0.22 adds one closed immutable ScriptClaimSet per exact immutable Script, with zero or more immutable
ScriptClaimLinks that store Claim identities only. A closed empty set is meaningful and distinct from no set; no
membership can later be appended, removed or replaced. Correcting provenance means creating a new immutable Script
version and closing its own set.

Creation derives the Script's existing ContentPiece → EditorialAngle → exact Ready assessment → ResearchPack →
Opportunity lineage. Every explicit Claim must belong to that exact Angle ResearchPack, occur in the exact assessment's
`frozen_evidence_state`, and be associated with the Angle at declaration time. Historical reads resolve linked IDs to
the frozen Claim/evidence representation from that assessment, never treating later mutable Claim or evidence data as
the Script's historical support. Later Angle-link edits do not rewrite a closed set.

Migration 17 adds only `script_claim_sets` and `script_claim_links`, restrictive foreign keys, uniqueness constraints
and a Claim lookup index, without backfill or duplicated readiness/evidence provenance. The narrow API is
`POST`/`GET /api/scripts/{script_id}/claim-set`; Script initiation and EditorialPackageSnapshot semantics remain
unchanged. v0.22 excludes ranges/segments, ClaimEvidence links, Claim snapshots, package Claim links, QA/Gate,
approval/workflow, UI, production, publishing, analytics, Learning and orchestration. Founder acceptance covers
implementation commit `346ddd76d19c8520541f77db4dda7853e8e8a5ed` and pending-state documentation commit
`3947ae34fb345a5cf6cb16423194a2b21d1d67c5`; Black 26.3.1 `--check`, Ruff, 96 pytest tests and `git diff --check`
passed.

### v0.23 — Deterministic Editorial Readiness Assessment

**Status: ACCEPTED IMPLEMENTATION CHECKPOINT.** v0.23 is a historical accepted Phase 2 milestone; v0.22 is its
historical accepted predecessor. v0.25 — Operational Visual Production Inputs is the latest accepted Phase 2
milestone; v0.24 is its accepted historical predecessor. Migration 20 is latest, migration 21 is absent, Phase 2
remains ACTIVE / INCOMPLETE, and no successor after v0.25 is selected.

v0.23 appends one immutable `EditorialReadinessAssessment` for an exact immutable `EditorialPackageSnapshot`.
Assessment provenance is resolved through the exact package TitleOption, HookOption, Script and ScriptClaimSet to
the existing exact upstream Ready research assessment's frozen evidence; it copies none of those inputs. Multiple
assessment records per package are allowed; there is no current/latest/superseded state.

The server alone derives outcome and structured findings using evaluator `deterministic-editorial-readiness` version
`v1` and assessment schema version 1. Its sole blocking policy is `SCRIPT_CLAIM_SET_MISSING`: no ScriptClaimSet
persists `NotReady` with a blocking error finding. A closed empty set is complete valid zero-Claim provenance and may
be `Ready`; a valid populated set must resolve exact frozen Claim/evidence/source representation. Broken package or
provenance state is an integrity error, not a persisted synthetic `NotReady`. v0.23 defines no blocking rule for
risk, freshness or verification status.

Migration 18 adds only `editorial_readiness_assessments`, a restrictive EditorialPackageSnapshot FK and package
history index, without backfill or duplicated package/research provenance. The narrow API is
`POST`/`GET /api/editorial-package-snapshots/{snapshot_id}/readiness-assessments` and
`GET /api/editorial-readiness-assessments/{assessment_id}`. No subjective/model QA, Editorial Gate, score, provider,
UI, spend, production, publishing, analytics, Learning or orchestration is included. Founder acceptance covers
implementation commit `01eeafd78c0e5a81f9dc5442d9404ca8a25b55b9` and pending-state documentation commit
`64e5da9183d9a0fe1492e6968f266f26abd4538c`. Validation passed: Black 26.3.1 `--check`, Ruff, 99 pytest tests and
`git diff --check`.

### v0.24 — Editorial Gate + Approved VisualPlan Initiation

**Status: ACCEPTED IMPLEMENTATION CHECKPOINT.** v0.24 is an accepted historical predecessor to v0.25; v0.23 is its
historical accepted predecessor. Migration 19 is historical, while migration 20 is latest; Phase 2 remains ACTIVE /
INCOMPLETE and no successor after v0.25 is selected.

v0.24 adds exact immutable `EditorialGateDecision` history over one supplied `EditorialPackageSnapshot` and one
supplied exact `Ready` `EditorialReadinessAssessment`. Outcomes are only `Approve`, `Revise` and `Reject`; records are
immutable and additive, may repeat for a package or assessment, and define no current/latest/selected/superseded or
workflow state. `Approve` authorizes deliberate visual planning only: it does not authorize paid production, spend,
providers, generation, production, publication or financial behavior.

Only an exact `Approve` decision may initiate a VisualPlan through the dedicated lifecycle. It derives the exact
ContentPiece and Script from the Gate decision's immutable package and atomically records additive
`visual_plan_gate_provenance`. It does not consume the Gate decision or automatically create Scenes, AssetSpecs,
GenerationExecutions or Assets. Historical/demo and low-level VisualPlans remain valid without Gate provenance and
are not backfilled. Migration 19 adds only `editorial_gate_decisions`, `visual_plan_gate_provenance`, restrictive FKs
and direct history/reverse lookup indexes. The API is `POST`/`GET
/api/editorial-package-snapshots/{snapshot_id}/gate-decisions`, `GET
/api/editorial-gate-decisions/{decision_id}`, and `POST
/api/editorial-gate-decisions/{decision_id}/visual-plans`.

v0.24 adds no new Title/Hook or Script-to-Claim lifecycle work, machine editorial QA, paid production, spend/cost
schema, provider/model or generation work, Scene/AssetSpec lifecycle work, UI, production, publishing, analytics,
Learning, orchestration or successor scope. Implementation commit:
`34acdcfc3b3d523a3eb4a00af6ae7d768669444b`. Pending-state documentation commit:
`ae993dae6732a2cb456f57e3d070cd315c77a30b`. Validation: Black 26.3.1 formatting equivalence passed across 10
repository Python files through an in-process API check; the documented Black CLI could not complete in this Windows
host because of a process-runtime hang. Ruff passed, **102 pytest tests** passed, and `git diff --check` passed.

### v0.25 — Operational Visual Production Inputs

**Status: ACCEPTED IMPLEMENTATION CHECKPOINT.** v0.25 is the latest accepted Phase 2 milestone; v0.24 is its
accepted historical predecessor. Migration 20 is latest, migration 21 is absent, Phase 2 remains ACTIVE / INCOMPLETE
and no successor after v0.25 is selected.

v0.25 operationalizes only visual inputs below an exact existing `Approve` Editorial Gate chain. Dedicated Scene and
AssetSpec create/list/update operations revalidate `VisualPlan → visual_plan_gate_provenance → Approve
EditorialGateDecision → exact Ready package` before ordinary mutable authoring. Scene/AssetSpec ownership remains
immutable and their existing editable fields remain editable. Historical/demo low-level operations continue without
backfill. `narration_excerpt` remains a locator, not timing authority, and no visual production snapshot exists.

Manual/no-cost import accepts bounded PNG, JPEG or WebP bytes only, validates their declared image signature, writes a
new immutable file below managed storage, derives the next AssetSpec-local version and SHA-256, and records the Asset
as `imported`. It never accepts an external filesystem path, caller-controlled version/digest/storage/source provenance
or unregistered content. Safe content resolution supports registered managed `generated` and `imported` image Assets
only.

Migration 20 adds only `asset_selections`: immutable additive rows holding one exact AssetSpec, one exact Asset, an
optional CharacterReferenceSet and timestamp, with restrictive FKs and history/reverse lookup indexes. No
current/latest/best/active/ranking/superseded state exists. Selection validates Gate-derived ownership, safe managed
bytes and matching SHA-256. An imported character Asset selection must explicitly name an exact CharacterReferenceSet
for the AssetSpec's CharacterProfile; imported non-character selections require null. Generated selections preserve
their GenerationExecution character/reference provenance and reject manual reference overrides. No reference-set
membership or visual canon changes occur.

The API adds dedicated Gate-qualified Scene and AssetSpec authoring, managed raw-byte Asset import, Asset history and
safe content retrieval, and immutable AssetSelection create/list/get. Provider generation is unchanged and optional.
There is no narration, captions, timing, render/timeline, MP4, final-media manifest, QA, paid production, spend/cost,
UI, workflow, publishing, analytics, Learning or successor work. Founder acceptance covers implementation commit
`065e10bc6e36bf009f54fbce9a0135ef0cae9273` and pending-state documentation commit
`67500b338ecb959177b131ece2f59b9b11fb327c`. Ruff passed, **107 pytest tests** passed and `git diff --check` passed;
Black 26.3.1 formatting equivalence passed for 10 repository Python files through the accepted in-process API check
after the documented Windows CLI worker-process hang.

### v0.26 — Narrated Final Media Production

**Status: ACCEPTED IMPLEMENTATION CHECKPOINT.** At its acceptance, v0.26 was the latest accepted Phase 2 milestone;
v0.25 is its accepted historical predecessor. Founder acceptance covers implementation commit
`deb88cda96b1b3989f37a525db5b6555849611db` and pending-state documentation commit
`18c9fe5154154e90aedeff81199a94cc85f6a6dd`. At the v0.26 acceptance checkpoint, Migration 21 was latest and
Migration 22 was absent. Phase 2 remains ACTIVE / INCOMPLETE and no successor after v0.26 was selected at that
checkpoint. This does not authorize a successor milestone.

The bounded lifecycle is `Approve EditorialGateDecision → Gate-authorized VisualPlan → exact Script → manual managed
NarrationAsset → FinalMediaInputSnapshot → RenderExecution → FinalMediaArtifact → delegated manual production QA /
manual publication handoff`. `NarrationAsset` supports managed manual WAV, MP3 and M4A import, one exact Script,
server-derived safe path/SHA-256/probed duration and immutable append-only history without current/latest semantics or
TTS. `FinalMediaInputSnapshot` freezes one exact approved VisualPlan/Script/NarrationAsset, every ordered current
Scene exactly once, one exact AssetSelection per Scene, current mutable Scene/AssetSpec render facts, managed Asset
digest/reference lineage, timing, deterministic caption cues and fixed settings.

Local FFmpeg/FFprobe synchronously renders vertical 1080×1920, 30fps H.264/AAC MP4 with static, slow-zoom-in and
slow-zoom-out motion, cuts, fixed 250ms crossfades and burned captions. Each crossfade extends only its internal source
and output is trimmed/capped to the frozen final duration. `RenderExecution` is immutable and terminal (`succeeded` or
`failed`), with multiple explicit attempts allowed; failed attempts retain bounded error facts and no artifact. Each
successful execution has at most one immutable safe managed `FinalMediaArtifact`, whose SHA-256 and FFprobe technical
validation are preserved and whose content resolves only by registered artifact ID.

The operational runtime dependency is a usable local FFmpeg/FFprobe pair resolved from `PATH` or explicit
`ATLAS_FFMPEG_PATH` and `ATLAS_FFPROBE_PATH`. It is not a bundled repository binary, provider integration,
paid-production authorization or cost/spend implementation.

The narrow HTTP surface provides narration import/list/get/content; snapshot create/get; synchronous render create/get;
and artifact get/content. It accepts no caller filesystem path, digest, duration, source kind, caption content, render
profile, codec, output path or FFmpeg argument. No provider TTS, paid production, cost/spend, publication record or
automation, queue/worker, production UI, analytics/Learning, generic workflow engine or new founder Gate is included.
Validation passed: Ruff, **114 pytest tests**, `git diff --check`, real repository-domain two-Scene crossfade/caption
FFmpeg/FFprobe proof and Black 26.3.1 in-process equivalence across 12 Python files (`would_change=0`). The documented
Windows Black CLI worker/process completion behavior remains a host-runtime exception.

### v0.27 — First-Run Operability Bridge

**Status: ACCEPTED IMPLEMENTATION CHECKPOINT.** v0.27 is the latest accepted milestone; v0.26 is its accepted
historical predecessor. Founder acceptance covers implementation commit `8dd10ef793ac44c25107f02ba4b6bb5c333cf500`
and pending-state documentation commit `cb5fb1593827e6f7f0943973e86d992ea10dccf5`. v0.27 adds only narrow HTTP
ingress over existing repository operations: Opportunity creation,
ResearchPack-scoped Claim creation, reusable Source creation, ClaimEvidence link/upsert and eligible
EditorialAngle–Claim linking. HTTP preserves server-owned path lineage, existing Source URL identity and current
server-built frozen research-readiness evidence; it does not introduce workflow state, generic CRUD, research
automation or writing generation.

The explicit `POST /api/character-profiles/{id}/reference-sets/imported` operation deliberately freezes an immutable
ordered CharacterReferenceSet from qualifying managed imported character Assets. Every member must match the exact
CharacterProfile, originate from a Gate-authorized character AssetSpec, be source kind `imported`, safely resolve below
managed storage and match its stored SHA-256. It requires no prior AssetSelection, creates no GenerationExecution or
provider call, and leaves generated-reference provenance intact. No current/latest/best reference state, visual QA,
paid provider, cost/spend, production trial, UI, renderer, publishing, analytics/Learning or successor scope is
added. Later canonical Migration 22 separately adds only generated-narration provenance; Phase 2 remains ACTIVE /
INCOMPLETE, and no successor after v0.27 is selected. Validation passed: Ruff, **117 pytest tests**, `git diff --check`, and Black 26.3.1
in-process equivalence across 12 Python files (`would_change=0`).

Future financial control retains the Cost Ledger, Revenue Ledger and Economics / Control Centre boundary;
analytics remains separate and immutable GenerationExecution history cannot carry later-changing aggregate
totals. Learning may eventually compare authorized and actual spend, production choices, quality, performance
and revenue/economics outcomes where available, including whether incremental spend delivered useful value.
Financial signals inform but must not automatically dominate the hierarchy of **quality/evidence/risk floor →
editorial and brand objective → cost efficiency → revenue/profit optimization**. The rule concerns paid
external spend only; reservation/accounting mechanics, negligible/internal-cost treatment, financial schemas
and enforcement remain unspecified.

The approved first implementation direction remains immutable Idea Gate review snapshots and immutable Idea
Gate decisions. Editorial Gate spend authorization is for later Editorial Gate, production and financial-control
milestones and is not part of that first slice.

## Roadmap direction and milestone governance

> Canonical GitHub roadmap → approved end-to-end operating vision → phase objectives/design boundaries → implementation milestones → bounded Codex implementation tasks

Roadmap phases define the approved product direction. Versioned implementation milestones are bounded delivery
increments within that direction and must not independently redefine product direction, phase ownership,
roadmap sequencing, domain semantics or deferred scope. Any such change requires explicit founder + ChatGPT
approval, canonical documentation synchronization, review, acceptance, commit and push.

## Phase 1 visual acceptance decision

The completed activity was **Phase 1 visual-evidence execution on accepted v0.14**. This is **not v0.15**
and did not create a new implementation milestone.

The completed sequence was:

1. Establish an isolated review environment.
2. Create a fresh v0.14 review database.
3. Bootstrap exactly two legitimate hamster reference candidates.
4. Stop at Human Gate A.
5. Founder and ChatGPT visually review the candidates.
6. Founder approved Human Gate A Asset `asset-9a02b4cb416744a994965e2e1f2f0c33` (version 9; SHA-256
   `eaf0af82fe98120613793465f94029a72ae13a79f8e3e258d265e88fa47c450b`) for the exact
   `character-profile-similarstoic-hamster-core-v1` CharacterProfile.
7. Synchronize that founder-approved visual specification through immutable SimilarStoic Core v3 while
   preserving v2 as immutable historical provenance.
8. Explicitly created CharacterReferenceSet v1 from the approved eligible Asset.
9. Generated reference-grounded review evidence after that approval.
10. Founder and ChatGPT accepted the Phase 1 visual-evidence decision: **PASS WITH DEFERRED VISUAL
    REFINEMENT**.

Phase 1 visual acceptance is closed with **PASS WITH DEFERRED VISUAL REFINEMENT**. The immutable
`character-reference-set-similarstoic-hamster-core-v1` v1 contains exactly the approved Asset at position 1.
Grounded evidence succeeded for `asset-spec-isa-scene-01-hamster-sorting-v1`
(`generation-execution-dd25dc1388b04eef8d4f32ee06ec7807`, Asset
`asset-76c02a603d0e4a69955b51633c1e13ce`, SHA-256
`a12735798ad1c294849eaeab3796a080a8a27ec54335917048d1c5132f427577`) and
`asset-spec-isa-scene-03-hamster-reaction-v1`
(`generation-execution-f1900a2b32634a36b0b53244474259ce`, Asset
`asset-c989501ad83e4c9da668218c3179fb9c`, SHA-256
`ce0438980ae2f9c8015e63046805d70cc58d9789daa29671c28ac5dc1243e95b`).

The non-blocking deferred refinement is specifically residual AI-clean or overly competent professional
illustration finish. Future refinement must increase believable human-drawn imperfection and reduce overly
smooth/confident contours while preserving the approved hamster identity, proportions, large-ear/long-whisker
cues, warm tan/orange accents, multi-colour sling-bag, dark-gray strap, and CharacterReferenceSet continuity.
No further Phase 1 visual/generation work is authorized merely by this Phase 1 acceptance record. This historical
visual boundary does not invalidate or limit the separately authorized Phase 2 milestones.

### Current founder + ChatGPT visual-specification clarification

This is a current approved clarification of the existing SimilarStoic hamster identity contract. It builds on,
but does not rewrite, the historical v0.14 visual-acceptance record. It creates no milestone, schema change,
CharacterReferenceSet version, VisualStyleProfile version, implementation authorization, or later-phase activation.

The current core mascot identity is governed jointly by the immutable
`character-reference-set-similarstoic-hamster-core-v1` reference asset and this current founder + ChatGPT-approved
visual-refinement contract. The set contains only the approved position-1 Asset
`asset-9a02b4cb416744a994965e2e1f2f0c33`, version 9, SHA-256
`eaf0af82fe98120613793465f94029a72ae13a79f8e3e258d265e88fa47c450b`. Where this clarification deliberately
tightens future depiction requirements beyond the literal original v1 pixels—including more prominent rounded ears,
more prominent whiskers, a broad/soft hamster-like face, toothless mouths, fixed bag panel/layout rules, flat-colour
rendering and mandatory consistency QA—it governs future conforming depictions without mutating, replacing or
rewriting that historical reference asset. CharacterReferenceSet v2, replacement, silent substitution, or a new
mascot identity is not authorized. SimilarStoic Core v3 remains unchanged as the accepted visual-language baseline.

The core mascot is unmistakably hamster-like, never mouse-like: a broad, soft, rounded hamster face/muzzle and a
compact, rounded hamster-native body. It retains both visibly large, rounded ears—deliberately slightly more
prominent than in the original v1 reference when pose allows—long distinct whiskers extending well beyond the
muzzle, simple alert dark eyes, a mostly white/light body, warm tan/orange inner ears, nose and paws/hands/feet,
minimal or no fur detail, and simple, slightly crude hand-drawn anatomy. It must not receive glossy mascot
rendering, polished AI-clean finish, species drift, accidental body-proportion change, or facial-identity drift.
Expression may vary broadly—happy, excited, curious, thoughtful, surprised, determined, concerned, worried,
frustrated, cheeky, vulnerable, overwhelmed, triumphant, or otherwise scene-appropriate—through eyes, brows where
used, mouth shape, gesture and posture only. It must not alter identity, ear scale, whisker length or presence,
face proportions, core colouring, sling-bag design or body proportions.

#### Toothless mouth rule

Closed, smiling, surprised/open, speaking/open and wide-cheerful mouths are permitted, but every core-mascot mouth
must remain simple and toothless. Visible white teeth, small front teeth, dental detail, duplicate mouth lines,
malformed inner-mouth shapes, inconsistent lips and extra mouth anatomy are non-canonical generation errors. An
image showing teeth is non-conforming and must be corrected, regenerated or rejected.

#### Fixed signature bag

Only the main core mascot wears the identity-defining signature sling/crossbody bag. It has a genuinely crossbody
placement, dark-gray strap, dark/black zipper band and dark outline, red/orange strip along its upper area, green
upper/central panel, blue lower-left panel, yellow lower-right panel, the same recognizable curved sling-bag
silhouette as the approved reference, the same panel adjacency and colour relationships, and consistent zipper/pull
treatment where visible. Perspective and pose may change the view, but must not redesign its panel arrangement,
colour ordering, silhouette, strap identity or zipper structure.

Supporting/background hamsters may use believable Syrian/golden-like, Russian dwarf-like, Roborovski-like or other
appropriate hamster colour/type variations. They remain hamster-like and secondary, must not duplicate the full
core identity, and never wear the signature bag. The mostly-white/light core identity plus the bag are reserved for
the main mascot. Supporting hamsters are not purely ad hoc background variations: a small recurring set of
secondary hamster models may be established and reused across scenes and videos. Each may have its own stable hamster
type/colour pattern, body shape, body size/scale, facial characteristics and other secondary-character traits. Once
defined, its established appearance is stable for future depictions of that same model; future generations must not
randomly redesign or re-randomize it. Recurring supporting models may differ materially from one another in colour,
size and shape, but remain secondary, never wear the core bag and never duplicate the full core identity. One-off
background hamsters may vary freely within the approved hamster visual language only if they neither become nor
imitate an already established recurring supporting model.

#### Approved visual model and reference grounding

Mascot and recurring supporting characters must not be reconstructed from text description alone when an approved
visual reference model exists. Text documentation defines visual rules, constraints, identity semantics and QA
requirements; approved visual reference assets define the concrete appearance of the character model.

For the core mascot, `character-reference-set-similarstoic-hamster-core-v1` remains the immutable historical
identity anchor, while the current founder + ChatGPT-approved refinement contract remains authoritative for deliberate
refinements beyond literal v1 pixels. Founder-approved refined exemplar images may serve as concrete visual
references for the current depiction standard. Future core-mascot generation should use an approved visual reference
asset as image/reference grounding whenever the generation mechanism supports it. The mascot must not be recreated
approximately from prose alone if an approved visual reference can be supplied; a text-only recreation that
materially reinterprets the model is non-conforming.

The same principle applies to recurring supporting hamster models: once established and approved, each model's
approved visual reference is its concrete identity reference for future depictions. Future depictions should be
reference-grounded from that approved model wherever technically possible, rather than randomly reconstructed or
reinterpreted from text alone. Its established colour pattern, body shape, scale, facial characteristics and other
visual traits remain stable across scenes and videos. One-off background hamsters need no persistent named/model
reference unless they later become established recurring characters.

Appearance in a group scene, comparison sheet, specification sheet or other multi-character visual does not by itself
establish a supporting hamster as a recurring character or approved identity model. A recurring supporting character
exists only after explicit founder + ChatGPT approval and approval of its own isolated character-specific visual
reference.

Current character identity is governed jointly by (1) its approved visual reference asset/model, (2) the applicable
founder-approved written visual contract and (3) mandatory post-generation visual QA. Where written refinement
deliberately tightens a historical reference image, the refinement governs that specific deliberate change while the
reference continues to govern the rest of the concrete appearance. Prose is not permission to redraw or reinterpret
unspecified details. A newly generated image never becomes an approved model reference automatically; only a founder
and ChatGPT-approved visual exemplar may become one.

Reference grounding does not itself make a generation accepted. Every depiction must still pass the mandatory visual
consistency QA below. If it introduces changed proportions, altered bag geometry or colour placement, missing or
shortened whiskers, changed ear size, teeth, incorrect mouth anatomy, missing/duplicate/stray outlines, new
shading/gradients, changed core colours, supporting-character drift or any other material deviation from the approved
reference plus written contract, it is non-conforming and must be corrected, regenerated or rejected. If an approved
visual reference is unavailable to a process expected to generate a recurring character, that process must not
silently approximate the character from text and treat the result as canonical or publishable: fail closed.

#### Current tracked core-mascot reference manifest and hierarchy

The approved current-depiction assets below are durable, Git-tracked reference bytes. They supplement the immutable
historical v1 anchor and current written refinement contract; they do not create CharacterReferenceSet v2, alter v1,
alter VisualStyleProfile v3, create a runtime entity, or implement reference-passing or automated QA.

Core-mascot generation uses this hierarchy:

1. approved isolated core identity reference(s);
2. the founder + ChatGPT-approved written visual-refinement contract;
3. optional approved secondary acting/pose references;
4. optional core scene/expression exemplars; and
5. mandatory post-generation visual QA.

| Role class | Verified tracked asset | Dimensions | SHA-256 | Approved use |
| --- | --- | --- | --- | --- |
| CORE IDENTITY REFERENCE | `assets/visual-references/core-mascot/identity/9a9ccdc1-b948-45d1-a375-fc36d4e3bdc2.png` | 1448x1086 | `11332518cdace450f8e432fe8cb3558ea2374cf0273f94973912e914cee66956` | Preferred primary isolated core-mascot grounding asset. |
| CORE IDENTITY REFERENCE | `assets/visual-references/core-mascot/identity/a5564bd0-51d2-4713-82c1-42138f12a8dc.png` | 1448x1086 | `d3acb16af30b9a5aca29e92e2e8f19d7b5a21df4b8e572de054756ca23321cc4` | Preferred primary/supplementary core-only multi-pose grounding asset. |
| CORE IDENTITY REFERENCE | `assets/visual-references/core-mascot/identity/fa86fc7a-9006-4478-b5a2-371ba65cf06e.png` | 1536x1024 | `eb4eeab20550da110183819c51cd7710d067f63156ea1a1ef2e4f6c0f21b1f46` | Approved supplementary core-only specification/identity grounding; not preferred as sole grounding input. |
| APPROVED SECONDARY ACTING-POSE REFERENCE | `assets/visual-references/core-mascot/poses/core-v3-umbrella-resistance-acting-pose-v1.png` | 1024x1536 | `a6ebaec876b40a7a89b22bca26e18ffa56d0709078498d3126946990c55e581e` | Core v3 umbrella-resistance pose/performance grounding used alongside a canonical identity reference; never the primary identity authority. |
| APPROVED SECONDARY ACTING-POSE REFERENCE | `assets/visual-references/core-mascot/poses/core-v3-sorting-decisions-acting-pose-v1.png` | 1024x1536 | `16eb2a1ec14e7ddccca7332f2cf2b8e0842d51f5ce7fb3d0b8d672d21f9605bf` | Calm/focused sorting and decision behavior with Core v3 identity and sling-bag continuity; never the primary identity authority. |
| APPROVED SECONDARY ACTING-POSE REFERENCE | `assets/visual-references/core-mascot/poses/core-v3-things-in-hand-acting-pose-v1.png` | 1024x1536 | `b61fe5512df30e50ebc421b23069eafb350016e8995a0afba0bb40c33757cc5e` | Calm selective effort on reachable tokens for abstract explanation; never the primary identity authority. |
| CORE SCENE / EXPRESSION EXEMPLAR | `assets/visual-references/core-mascot/scenes/a3e484f6-8c69-4b89-8592-dd8671563b65.png` | 1448x1086 | `27ff66e34a8649a22c649a5593c93d0532cd176cf69dafb61bc19a1d2e1eb85a` | Supplementary flowchart/explaining pose, expression, composition and context. |
| CORE SCENE / EXPRESSION EXEMPLAR | `assets/visual-references/core-mascot/scenes/e2a608fa-267b-4e7b-b7e8-0065699dd13f.png` | 1448x1086 | `24dc9fd6367d6f7c4f9731b12bd1b7e7376edf7870ecee0a8ac066699363ff65` | Supplementary growth-chart/surprised-expression pose, composition and context. |
| CORE SCENE / EXPRESSION EXEMPLAR | `assets/visual-references/core-mascot/scenes/42ee8538-a4ff-4ca5-8b00-0044ef90207e.png` | 1448x1086 | `95ad2c8a75b7ce798eb315d1c84d34571bb1a44ace1922b141bdb2173fdfae4f` | Supplementary reading/thinking pose, expression, composition and context. |

The three identity assets contain no supporting hamster model and are the only core-mascot identity inputs in this
manifest. The acting-pose reference demonstrates accepted deformation/performance but cannot define or replace
identity. The scene/expression exemplars are supplementary only: their whiteboards, charts, books, tables, chairs,
diagrams and any other props are scene context, never mascot identity features.

The separate approved environment-style authority is
`assets/visual-references/environments/style/similarstoic-default-scene-language-v1.png`, 1024x1536, SHA-256
`989e0da7b273a42f0bf8c229c1510b904902b1eef3336e626705966e6048ccb2`. It may ground ordinary-scene linework,
palette, shape language, rendering density, negative space and prop simplicity. It cannot ground hamster identity or
require reuse of the pictured street.

The approved indoor environment example is
`assets/visual-references/environments/examples/similarstoic-calm-indoor-sorting-scene-v1.png`, 1536x1024, SHA-256
`45a8fcf77d1ba6d1b85601e9eba9a05e0554df705d3399c083f23a7b523dba2a`. It demonstrates a successful calm indoor
application without replacing the Default Scene Language authority.

The approved abstract environment example is
`assets/visual-references/environments/examples/similarstoic-abstract-reach-boundary-scene-v1.png`, 1024x1536,
SHA-256 `c30a8e66321fe9b725d6646ca1639fc6b01e87da3035092a0765067eaf2458b5`. It demonstrates a sparse conceptual
space with reachable and out-of-reach working areas without replacing the Default Scene Language authority or becoming
a mandatory diagram template.

The separate approved composition-grammar authority is
`assets/visual-references/compositions/grammar/similarstoic-static-composition-grammar-v1.png`, 1024x1536, SHA-256
`c6f933eddf7394ff3d00708650f7c1fa1df2f29ff8011e7ae4858653dd1f45d8`. It demonstrates coherent assembly of
approved character and environment assets. It cannot define identity, acting performance or environment style, and it
is not a mandatory storm layout or proof of repeatability across scene types.

The second approved composition example is
`assets/visual-references/compositions/examples/similarstoic-static-composition-example-2-indoor-sorting-v1.png`,
1024x1536, SHA-256 `dae3ca8f2cd035a686fdbc87458bf280120ef0bf4e53ebb39c9fd3e422d933a7`.
**Static visual-production method demonstrated successfully across two materially different scene types:** outdoor /
high-action storm and calm indoor / explanatory sorting. This does not establish universal repeatability or create a
new architecture layer.

The third approved composition example is
`assets/visual-references/compositions/examples/similarstoic-static-composition-example-3-things-in-hand-v1.png`,
1024x1536, SHA-256 `a5c7664ffcc40a6decdba0dc1a5c793d5850b6ddb975131a7395dc712329e427`. Together with the approved
`core-v3-things-in-hand-acting-pose-v1.png`, it establishes a third bounded capability: abstract explanatory metaphor
without text-dependent meaning. It does not establish universal repeatability, mandate this layout, or create a new
architecture layer.

The first approved special break-frame example is
`assets/visual-references/break-frames/examples/similarstoic-hand-drawn-gross-up-notification-v1.png`, 1024x1536,
SHA-256 `c38e0af357b0beb35ded28e78739115a630ca68ea9f6249f37f5ff8dcbae185e`. It records a rare hand-drawn gross-up
close-up in which detail, expression, crop and disproportionate reaction create a comedic rupture. It is special-mode
evidence only: it cannot define identity, ordinary acting, Default Scene Language, ordinary environment detail or
ordinary composition grammar. The rejected machinery/cinematic, rough-cartoon and photoreal gross-up candidates remain
local experimental evidence and are not visual canon.

Supporting-character references must live in separate per-character directories. Identity references from different
recurring characters must never be pooled. A recurring supporting character must receive its own isolated approved
reference(s) before stable reuse. Generated images never become approved references automatically; founder + ChatGPT
approval is required before an image can be added as a character reference.

This canonizes the tracked reference assets and reference-grounded generation requirements only. It does not
implement image-conditioning/reference-passing code or automated QA, create supporting-character entities, define a
supporting roster, create a milestone or authorize a later phase. Those implementation details remain separately
designed and authorized work.

#### Flat-colour and outline contract

The following contract governs ordinary mascot production. The approved special break-frame may intensify hand-drawn
line detail and distortion within its narrow comedic role; it does not alter the ordinary contract.

All hamster characters use direct-transition flat block colours. Gradients, tonal or volumetric shading, painterly
blending, textured/detailed fur, cross-hatching, glossy highlights and polished AI-clean rendering are prohibited.
Outlines must be simple, sparse, dark, hand-drawn, slightly imperfect and sufficient to define anatomy clearly;
missing limb contours, duplicate contours, stray lines, extra anatomy and contradictory outlines are prohibited.
Line-count variation must not change the character model.

#### Mandatory consistency review; automation remains deferred

Every generated visual containing the core mascot—including production visuals, infographics, roadmap graphics,
presentations, internal-documentation graphics, demo illustrations and decorative uses—must be reviewed against
CharacterReferenceSet v1, this character contract, the bag contract and the flat-colour contract before it is
usable, production-ready, publishable or used as a project graphic. Review must confirm hamster-like identity and
stable proportions; sufficiently large rounded ears; long whiskers on all visible sides as appropriate; correct
eyes, nose, white/light body and warm tan/orange accents; correct limb/paw contours without missing, duplicate or
stray lines or extra anatomy; no malformed facial geometry or teeth; flat colours without shading/gradients; exact
bag geometry, panel layout, colour arrangement, dark-gray strap and visible zipper/pull treatment; supporting
hamsters without the bag; and expression variation without identity drift. When a supporting hamster represents an
already established recurring model, review must also confirm that its established colour pattern, body shape, scale
and distinguishing facial/character traits match that model's prior approved appearance.

Generation alone is not acceptance. Any material inconsistency is non-conforming and must be corrected,
regenerated or rejected; it must not silently progress downstream or to publication. If consistency cannot be
established confidently, fail closed. A recurring supporting hamster that has materially drifted from its established
model is likewise non-conforming and must be corrected, regenerated or rejected. This mandatory review/rejection
requirement is approved now. Its technical mechanism may later be manual, deterministic, model-based or hybrid;
automated character-consistency-QA architecture and implementation remain explicitly deferred until separately
authorized.

### Runtime DB / CharacterReferenceSet reconciliation

`D:\ProjectAtlas\data\atlas.db` is ignored legacy/local historical/demo state, not canonical GitHub truth and not the
persistent database selected for the first genuine production run. A current local runtime DB may contain zero
CharacterReferenceSets, Assets or GenerationExecutions; that does not rewrite accepted canonical history. The
canonically accepted `character-reference-set-similarstoic-hamster-core-v1` version `1` contains the founder-approved
Asset `asset-9a02b4cb416744a994965e2e1f2f0c33` version `9`, SHA-256
`eaf0af82fe98120613793465f94029a72ae13a79f8e3e258d265e88fa47c450b`.

Current migrations/schema do not seed or restore that accepted set automatically, and current bootstrap does not
reconstruct the original accepted review environment or bytes. This is a deferred runtime-restoration/bootstrap
reproducibility gap; it does not block Phase 2. Do not regenerate a replacement Asset, invent
CharacterReferenceSet v2, silently auto-create reference sets, or reopen VisualStyleProfile v3 acceptance because
of local runtime row counts.

## Mandatory fresh-chat protocol

Absence from current ChatGPT or Codex memory is never evidence that a Conveyor requirement does not
exist. A new ChatGPT conversation must first reconcile:

1. the latest canonical GitHub state;
2. the latest accepted checkpoint;
3. this canonical handoff/re-grounding document;
4. a fresh Codex Repository Grounding Audit; and
5. a fresh Codex Complete Conveyor Specification Map.

It must distinguish canonical GitHub truth, implemented-but-documentation-stale work,
accepted-but-not-yet-canonically-synchronized work, provisional work, deferred work, superseded work, and
genuinely unspecified decisions. Conflicts must be surfaced, not silently reconciled, before ChatGPT proposes
a milestone or architecture.

A new Codex conversation must perform fresh repository grounding from the latest canonical GitHub state and
this document before any architecture or milestone task. It must preserve the authority boundaries above,
inspect only the scope ChatGPT/founder provides, and report any conflict or missing decision rather than
inventing one.

A newly started ChatGPT or Codex session must treat the canonical roadmap and approved end-to-end target
operating model as authoritative current intent. It must not replace, reorder or reinterpret them merely
because detailed future-phase implementation remains unspecified. Missing detail requires a founder + ChatGPT
design decision, not invention by a fresh chat or Codex.

## Required operating method — single-pass milestone execution

> DEFINE → DESIGN WITH FOUNDER / CHATGPT → ONE BOUNDED CODEX EXECUTION PASS → FOUNDER / CHATGPT REVIEW → ACCEPTANCE / PUSH → NEXT DESIGN GATE

### Design gate

Founder + ChatGPT define and approve each milestone's purpose, product/domain semantics, consequential
persistence or architecture decisions, important schema semantics, explicit inclusions/exclusions and acceptance
boundary. Codex must not independently select a milestone, select a successor, or redefine those decisions.

### One Codex execution pass

Once that design is approved, one comprehensive Codex task authorizes routine local completion of the bounded
milestone: fresh repository/GitHub grounding; source, documentation, test and migration inspection; implementation
choices within the approved design; tests; an additive migration only where its already-authorized schema semantics
make it directly necessary; routine implementation, test, formatting and tooling diagnosis/fixes; validation;
canonical documentation that accurately records the locally completed work as pending founder acceptance/push where
appropriate; complete-diff review; removal of unrelated scope Codex introduced; and logical local commits.

Codex does not need a separate founder instruction for routine inspection, tests, Black/Ruff/pytest, formatting,
ordinary tooling diagnosis, an in-boundary regression fix, required documentation synchronization, diff review or
local commits.

### Escalation conditions

Codex must stop and return to founder + ChatGPT only for a genuine unresolved product/domain/design ambiguity;
materially different architecture or persistence semantics; schema meaning not already authorized; scope beyond the
milestone; a material canonical product-behaviour conflict; an unexpected dependency/repository/tooling problem
that cannot be routinely resolved; a validation defect whose fix changes product or architecture decisions; a
destructive/protected Git action; or remote divergence requiring merge, rebase or history decisions. Routine
failures are for Codex to diagnose and fix within the approved boundary.

### Founder review and push gate

Codex returns one consolidated review package: repository checkpoint; implemented design; migrations; exact files;
tests; validation; a complete or fully reviewable diff; local commits; Git state; deviations/risks; and explicit
milestone-boundary confirmation. Founder + ChatGPT review that package. For a normal milestone without an
unresolved design issue, founder interaction should normally reduce to explicit push authorization, which may also
constitute final acceptance when the package states what is being accepted. Founder + ChatGPT may explicitly keep
acceptance and push separate for a particular milestone.

### Protected actions

Codex must never independently push, force-push, rebase shared history, merge unexpected remote divergence, amend
already-pushed commits, reset/clean away work, select the successor milestone or expand into a later phase. Founder
remains final product, business, quality, scope and acceptance authority; founder + ChatGPT remain architecture,
specification, roadmap and milestone authority; Codex remains the bounded repository inspection and execution agent.

**v0.27 — First-Run Operability Bridge** is the latest accepted implementation checkpoint. **v0.26 — Narrated Final
Media Production** is its accepted historical predecessor. No successor after v0.27 is selected; any scope beyond
v0.27 requires a new explicit founder + ChatGPT decision.

The governing principle is **CHANGE WITHOUT REBUILD**.

Every newly accepted milestone or checkpoint must refresh canonical status, repository documentation when
semantics changed, checkpoint metadata, this cross-chat handoff, and the fresh-chat startup instructions.
Every future handoff must direct the next chat to repeat this repository-grounding process.

## Architectural rules to preserve

- Migrations are additive and historical records are preserved.
- A VisualPlan owns Scenes; a Scene owns AssetSpecs; environment Assets remain background-only.
- No fake Scenes are permitted.
- `CharacterProfile`, `VisualStyleProfile`, and `AssetSpec` are separate concepts. No generic Topic model is
  introduced.
- CharacterReferenceSets are immutable and versioned. They have no mutable current, best, or selected state.
- No persisted mutable current, latest, best or selected state is permitted unless founder + ChatGPT specifically
  approve that domain-specific state.
- Ordinary character generation requires reference grounding. v0.14 bootstrap is explicit and available only
  before the first CharacterReferenceSet for the exact CharacterProfile.
- One real provider attempt produces one immutable terminal GenerationExecution. A pre-provider failure
  produces no execution; a failed provider attempt produces a failed execution and no Asset; success produces
  an execution and at most one Asset.
- Conveyor is a composable pipeline: providers, research engines, adapters, narration/audio and image/visual
  providers, production stages, rendering components, publishing and analytics integrations, and other
  implementation-specific pipes remain replaceable behind stable boundaries, explicit inputs/outputs,
  loose coupling and preserved provenance. Replacing one pipe must not require rebuilding the whole loop.
- Future financial control distinguishes a durable Cost Ledger for actual operating spend, a durable Revenue
  Ledger for money earned from already contemplated monetisation sources, and an Economics / Control Centre
  that may derive financial views and guardrails from them. Analytics remains separate: performance metrics
  may inform unit economics, but analytics is not the Revenue Ledger. This is a conceptual boundary only;
  ledger schema, ingestion/attribution rules, metric formulas, thresholds, enforcement, kill-switch,
  escalation and founder-exception semantics remain unspecified. Financial records must preserve historical
  provenance through additive evolution, retain provider independence, and must not mutate immutable
  GenerationExecution records with later-changing aggregate totals. Existing execution/provider provenance is
  a future attribution anchor, not an approved financial record.
- Future financial guardrails may constrain automated spend through budget limits, provider/model caps,
  alerts, escalation, pausing and founder exception approval. Phase 3 owns future cost/budget/control
  architecture; Phase 7 may provide publication/platform data; Phase 8 owns separate performance/commercial
  metrics; Phase 9 may consume limits during automation; and Phase 10 may consume business/economic outcomes.
  No new phase, phase activation or implementation is implied.
- The future pre-spend rule is prior human authorization of a bounded maximum paid-external-production envelope
  tied to the exact approved editorial proposition. It is not a target spend or a fourth routine founder gate.
  Conveyor must optimize cost within the required quality, brand, evidence and risk floor, stop/escalate before an
  overspend, and never silently reduce quality or rely on open-ended retries. A future proposal must make
  lineage, cost/quality/risk alternatives and qualified—not guaranteed—upside intelligible. No authorization,
  proposal, ledger, production or enforcement entity is approved by this documentation.
- Accepted phases, milestones, specifications, profiles and implementation choices remain evolvable through
  additive changes, immutable new versions, explicit future selection and preserved historical provenance;
  accepted historical records are not destructively rewritten merely because the current design evolves.
- Core domain/provenance invariants remain stable by default. Changing ownership/provenance relationships,
  historical preservation, immutable/versioned reference semantics, execution semantics or established domain
  meaning requires explicit founder + ChatGPT architecture/specification approval, deliberate canonical
  synchronization, review, acceptance, commit and push.
- Conveyor remains audio-first. Do not introduce premature agents, cloud infrastructure, queues, publishing, or
  analytics.

## Current technical stack and deliberately absent architecture

The current stack is Python 3.12+, a stdlib HTTP server, static HTML/CSS/JS, SQLite, uv, pytest, Ruff, Black,
GitHub Actions and a Docker scaffold. Relevant environment variables are `ATLAS_DB_PATH`,
`ATLAS_ASSET_STORAGE_ROOT`, `ATLAS_VISUAL_STYLE_PROFILE_ID`, `OPENAI_API_KEY` and
`ATLAS_OPENAI_IMAGE_MODEL`.

Until their owning phases are explicitly authorized, do not introduce authentication, cloud deployment
architecture, queues/workers, scheduling, a generic provider registry, retry/batch orchestration,
production/rendering, publishing, analytics, agents, or financial implementation/cost monitoring.

## Canonically accepted creative/product decisions synchronized at v0.14

These are accepted product decisions synchronized into the repository at this checkpoint, not claims about
historical implementation dates:

- SimilarStoic serves ambitious 20–35-year-old young professionals and beginners: UK-first, with Western/global
  awareness. Its promise is: **“Understand how to build wealth without spending hours researching it.”**
  The tone is relaxed, knowledgeable, Gen-Z-friendly, clear, practical, witty and substantial—never guru-like,
  clickbait/hype-driven, corporate, or falsely certain.
- The recurring character is a recognisable classic hamster with young-professional relatability, a recurring
  sling/crossbody bag, and hamster-native behaviour.
- Scene-level personality may range across curious, thoughtful, relaxed, worried, frustrated, cheeky, cute,
  vulnerable, overwhelmed, triumphant, and absurdly dramatic.
- The narrator explains while the hamster illustrates; content must remain comprehensible from audio alone.
- SimilarStoic is not restricted to finance. It makes useful parts of the world understandable and entertaining
  for the target audience across finance, economics, work, careers, psychology, behaviour, incentives,
  decision-making, society, social behaviour, life strategy and useful explanations of systems or phenomena.
  Finance remains an important commercial/editorial pillar, but is not required for every piece. Generic
  motivation/self-improvement without explanatory value, miscellaneous trivia without meaningful relevance
  or insight, and random entertainment outside the explanatory purpose remain excluded.
- Pop culture is light seasoning. Signature original break-frame/still devices may deliberately interrupt the
  normal sparse grammar to land a joke, dramatize an event, make an explanatory point or metaphor, convey a
  feeling, or make a concept memorable. They may be unusually detailed, exaggerated, uncanny, absurd,
  dramatically over-serious, visually intense or stylistically contrasting; that contrast may itself carry the
  comedy or explanation. They are not the default treatment. Classic SpongeBob-era/older animated-comedy
  timing may inspire the mechanism, without copying protected characters, artwork, frames, compositions,
  dialogue, backgrounds or franchise-specific visual identity.
- SimilarStoic Core v2 remains immutable historical visual provenance. SimilarStoic Core v3 is the current
  founder-approved Phase 1 visual baseline: sparse, light, dark hand-drawn and deliberately imperfect,
  with no gradients, tonal shading, painterly/textured fill or polished AI-clean finish. The canonical
  recurring hamster is mostly white/light with warm tan/orange inner ears, nose and paws/hands/feet;
  it has large distinctive ears, long whiskers, simple alert eyes, minimal/no fur detail, and a crude
  average-adult-from-memory drawing quality. Its signature genuinely crossbody sling/man-bag may use flat
  green, blue, orange, yellow, red and black with a dark-gray strap. This narrowly scoped character and
  accessory exception does not relax restrained general scene colour. Material future style changes require
  new immutable versions.
- Phase 1 visual acceptance is closed with **PASS WITH DEFERRED VISUAL REFINEMENT**. The founder-approved
  Human Gate A Asset is the sole immutable member of CharacterReferenceSet v1, and grounded evidence across
  two scenes succeeded. VisualStyleProfile v3 remains the accepted baseline. Residual AI-clean/professional
  finish is a non-blocking future refinement only; it does not authorize a hamster redesign or further
  generation. At Phase 1 acceptance, no v0.15 or successor milestone was selected.

## Deferred scope

Do not infer approval for neutral CharacterProfile-owned candidate studies, automatic reference selection,
similarity scoring, visual QA automation, style-reference grounding, generic approval/lifecycle models,
queues, retries, batch semantics, financial-control implementation (including Cost/Revenue Ledger schema or
integrations), rendering, animation, audio production, publishing, analytics, cloud systems, or agents.

## Genuinely unspecified — founder + ChatGPT decision required

Do not invent a successor milestone after v0.22. Statement-level Script provenance, machine editorial-QA, Editorial
Gate persistence, EditorialAngle versioning/revalidation semantics, final Research Readiness evaluator
implementation, Phase 4 automation design, later publishing architecture, Learning persistence/automation and
detailed financial implementation remain unresolved or deferred. Each requires founder + ChatGPT design and explicit
canonical authorization before implementation.
