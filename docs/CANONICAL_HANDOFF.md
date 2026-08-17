# Project Atlas — Canonical Handoff and Governance

## Purpose and authority

This document is the durable cross-chat re-grounding guide for Project Atlas. GitHub is the canonical
repository of truth. The founder is product owner and final product and acceptance authority. ChatGPT works
with the founder as product architect, roadmap interpreter, milestone designer, and architecture steward.
Codex is a bounded repository inspection and implementation agent; it must not independently decide product
architecture, roadmap changes, milestone boundaries, domain semantics, or final technical direction.

The canonical roadmap in [ROADMAP.md](../ROADMAP.md) is static by default. Neither a new chat, incomplete
conversation memory, implementation convenience, nor an inferred better sequence may change phases, reorder
direction, reinterpret commitments, remove requirements, add objectives, or treat deferred or unspecified
work as approved.

A roadmap or specification change becomes canonical only when the founder explicitly approves it with
ChatGPT, it is explicitly identified as such a change, canonical GitHub documentation is deliberately
updated, the change is reviewed and accepted, and that update is committed and pushed. Until then, the
existing GitHub roadmap and specification remain authoritative.

## Current accepted checkpoint

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

SimilarStoic Core v3 remains the current accepted visual baseline, and CharacterReferenceSet v1 remains
unchanged. **v0.15 — Persistent Idea Gate** is the
latest accepted implementation milestone; v0.14 remains its historical accepted predecessor. **Phase 2 —
Content Operating Model is the current ACTIVE roadmap phase, with accepted v0.15 implementation and
defined/authorized but unimplemented v0.16**, under founder + ChatGPT design/implementation stewardship.
This authorizes only those bounded specifications, not all Phase 2 scope or later-phase engines.

## Accepted end-to-end target operating model

Atlas is intended to become an approximately **95% automated content operating system**. The target is not to
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

## Approved Phase 2 operating-model specification

Phase 2 is **ACTIVE**. Its bounded v0.15 implementation is accepted; all remaining Phase 2 scope remains
unimplemented. Atlas uses **sparse human gates and rich
machine readiness checks**: human approval concentrates at meaningful judgement boundaries, while intermediate
stages progress automatically only when explicit quality, evidence and provenance requirements pass. Human
judgement and machine readiness are distinct; neither may silently substitute for the other.

The target founder gates are version-specific operating concepts, not approved database/workflow entities:

- **Idea Gate:** Proceed, Reject or Steer an opportunity based on relevant/audience value, timeliness,
  discovery context, risk/uncertainty and Atlas's recommendation; it is not ResearchPack approval.
- **Editorial Gate:** Approve, Revise, Reject or intentionally select an alternative editorial package of
  Title, Hook, Angle and Script with relevant evidence/risk context. Approval allows that specific proposition
  and version to progress subject to later readiness; it is not technical final-video approval. Where paid
  external production is contemplated, it also authorizes a bounded maximum spend for that proposition; this
  remains one linked Editorial Gate judgement, not a fourth routine founder gate.
- **Learning Gate:** accept, reject, limit, seek more evidence for, or override evidence-backed, scoped,
  reversible and historically attributable learning/adaptations. It must not silently alter brand, roadmap,
  audience, risk policy or governance.

No paid external production spend may occur without prior human authorization of a bounded envelope tied to
the approved editorial proposition. Approval authorizes a maximum, not a target: Atlas should spend less when
it can still meet the required quality, brand, evidence and risk floor. If meeting that floor would exceed the
ceiling, Atlas must stop and escalate rather than overspend or silently lower the quality requirement.

The eventual Editorial Gate production/spend proposal should make its exact editorial lineage and maximum
request understandable, with estimated total and stage/provider cost where available, expected quality,
meaningful lower-cost alternatives and trade-offs, recommended/premium rationale, and qualified expected
commercial or strategic upside. It must distinguish measured evidence, modelled expectation and speculation;
projected return is never guaranteed justification. Illustrative economy/recommended/premium labels are not
fixed future enums or a required number of choices.

Atlas seeks the lowest-cost feasible path that clears the approved quality, brand, evidence and risk floor.
Provider, model, attempt count and workflow should be optimized before any quality bar changes; premium is not
automatically better and cheapest is not automatically preferred. Within a future authorized envelope Atlas
may spend less, but sufficient remaining budget is required before paid external work begins. It must not
silently overspend or use open-ended retries. Exceptional extra spend or material risk requires a new human
authorization/exception path.

Opportunities remain mutable discovery records. Idea Gate authority must therefore apply to an immutable review
snapshot of exactly what the founder judged, not only to evolving current Opportunity state. The conceptual
snapshot freezes reviewable Opportunity identity, title, summary, why-now context, relevant Subject context,
score/ranking if presented, Atlas recommendation/explanation, material risk/uncertainty and review
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

Any scope beyond the accepted v0.15 and now-defined v0.16 boundaries requires a new explicit founder + ChatGPT
decision. Material ambiguity about semantics, migration scope, history, API meaning, founder decision meaning
or deferred scope must return to founder + ChatGPT rather than be inferred.

### v0.16 — Authorized Research Initiation

v0.16 is the defined and authorized next Phase 2 implementation milestone, but is not implemented or
accepted; v0.15 remains the latest accepted milestone and migrations remain 1–12 until implementation.
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
needs; it does not alter ResearchPack ownership/version uniqueness or other existing domain records. The full
acceptance requirements, implementation boundary and ambiguity-return rule are canonical in
[ROADMAP.md](../ROADMAP.md) under **v0.16 — Authorized Research Initiation**. Once this definition is
reviewed, committed and pushed, Codex is authorized to implement only that bounded specification.

The approved first half is Opportunity → Idea Gate → Research → machine research-readiness → Editorial Angle
→ ContentPiece → Title/Hook/Script development → machine editorial QA → Editorial Gate. Research readiness is
a machine boundary for proposed content/material claims, with conceptual Ready / Needs-more-research / Blocked
meanings only; the final evidence schema and Script-to-Claim architecture remain deferred. Editorial QA must
eventually establish research/claim support, uncertainty/freshness treatment, evidence-supported non-
overpromising editorial content, audio-first meaning preservation, territory/tone, surfaced risk and
provenance.

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
No post-Phase-1 milestone or further generation is authorized or implied.

## Mandatory fresh-chat protocol

Absence from current ChatGPT or Codex memory is never evidence that a Project Atlas requirement does not
exist. A new ChatGPT conversation must first reconcile:

1. the latest canonical GitHub state;
2. the latest accepted checkpoint;
3. this canonical handoff/re-grounding document;
4. a fresh Codex Repository Grounding Audit; and
5. a fresh Codex Complete Project Atlas Specification Map.

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

## Required operating method

> DEFINE → DESIGN WITH FOUNDER / CHATGPT → BOUNDED CODEX TASK → IMPLEMENT LOCALLY → VALIDATE → REVIEW → FIX REGRESSIONS → FINAL ACCEPTANCE → COMMIT → PUSH → NEXT MILESTONE

The governing principle is **CHANGE WITHOUT REBUILD**.

Every newly accepted milestone or checkpoint must refresh canonical status, repository documentation when
semantics changed, checkpoint metadata, this cross-chat handoff, and the fresh-chat startup instructions.
Every future handoff must direct the next chat to repeat this repository-grounding process.

## Architectural rules to preserve

- Migrations are additive and historical records are preserved.
- A VisualPlan owns Scenes; a Scene owns AssetSpecs; environment Assets remain background-only.
- `CharacterProfile`, `VisualStyleProfile`, and `AssetSpec` are separate concepts. No generic Topic model is
  introduced.
- CharacterReferenceSets are immutable and versioned. They have no mutable current, best, or selected state.
- Ordinary character generation requires reference grounding. v0.14 bootstrap is explicit and available only
  before the first CharacterReferenceSet for the exact CharacterProfile.
- One real provider attempt produces one immutable terminal GenerationExecution. A pre-provider failure
  produces no execution; a failed provider attempt produces a failed execution and no Asset; success produces
  an execution and at most one Asset.
- Atlas is a composable pipeline: providers, research engines, adapters, narration/audio and image/visual
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
  Atlas must optimize cost within the required quality, brand, evidence and risk floor, stop/escalate before an
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
- Atlas remains audio-first. Do not introduce premature agents, cloud infrastructure, queues, publishing, or
  analytics.

## Canonically accepted creative/product decisions synchronized at v0.14

These are accepted product decisions synchronized into the repository at this checkpoint, not claims about
historical implementation dates:

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
