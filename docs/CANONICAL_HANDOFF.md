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

## Current implementation state

**v0.19 — Editorial-Angle-Authorized ContentPiece Initiation** is the latest accepted implementation milestone.
**v0.18 — Readiness-Authorized Editorial Angle Initiation** is its historical accepted predecessor. Migration 15
is canonical and migrations extend through 1–15. Phase 2 remains ACTIVE / INCOMPLETE and later phases remain
unactivated. No successor after v0.19 is selected: no v0.20, Editorial Draft Package slice or migration 16 is
authorized. Its implementation was committed and pushed at
`32812e6793d9b06632ebffd82504cd8810c2ab3d` (`feat: initiate ContentPieces from Ready EditorialAngles`). Founder
acceptance confirms Black 26.3.1, Ruff, 88 pytest tests and `git diff --check` passed. A fresh
session must verify the live GitHub checkpoint before acting.

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

SimilarStoic Core v3 remains the current accepted visual baseline, and CharacterReferenceSet v1 remains
unchanged. **v0.19 — Editorial-Angle-Authorized ContentPiece Initiation** is the latest accepted implementation
milestone; v0.18 is its historical accepted predecessor. **Phase 2 — Content Operating Model is the current
ACTIVE / INCOMPLETE roadmap phase, with accepted v0.15 through v0.19 implementations and no selected successor**,
under founder + ChatGPT design/implementation stewardship. This does not authorize all Phase 2 scope or later-phase
engines.

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
migrations extend through 1–15. No milestone after v0.19 is selected.

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

**Status: ACCEPTED IMPLEMENTATION CHECKPOINT.** v0.19 is the latest accepted Phase 2 milestone. v0.18 is its
historical accepted predecessor, migration 15 remains the latest canonical migration, Phase 2 remains ACTIVE /
INCOMPLETE, and no successor after v0.19 is selected. Founder acceptance covers implementation commit
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
publishing, analytics, Learning Gate implementation and orchestration. No milestone after v0.19 is selected.

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

The latest accepted Phase 2 implementation is **v0.19 — Editorial-Angle-Authorized ContentPiece Initiation**.
Its bounded persistence/API contract is accepted; **v0.18 — Readiness-Authorized Editorial Angle Initiation** is
its historical accepted predecessor. No successor after v0.19 is selected. Material detail beyond its approved
boundary returns to founder + ChatGPT.

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
3. optional core scene/expression exemplars; and
4. mandatory post-generation visual QA.

| Role class | Verified tracked asset | Dimensions | SHA-256 | Approved use |
| --- | --- | --- | --- | --- |
| CORE IDENTITY REFERENCE | `assets/visual-references/core-mascot/identity/9a9ccdc1-b948-45d1-a375-fc36d4e3bdc2.png` | 1448x1086 | `11332518cdace450f8e432fe8cb3558ea2374cf0273f94973912e914cee66956` | Preferred primary isolated core-mascot grounding asset. |
| CORE IDENTITY REFERENCE | `assets/visual-references/core-mascot/identity/a5564bd0-51d2-4713-82c1-42138f12a8dc.png` | 1448x1086 | `d3acb16af30b9a5aca29e92e2e8f19d7b5a21df4b8e572de054756ca23321cc4` | Preferred primary/supplementary core-only multi-pose grounding asset. |
| CORE IDENTITY REFERENCE | `assets/visual-references/core-mascot/identity/fa86fc7a-9006-4478-b5a2-371ba65cf06e.png` | 1536x1024 | `eb4eeab20550da110183819c51cd7710d067f63156ea1a1ef2e4f6c0f21b1f46` | Approved supplementary core-only specification/identity grounding; not preferred as sole grounding input. |
| CORE SCENE / EXPRESSION EXEMPLAR | `assets/visual-references/core-mascot/scenes/a3e484f6-8c69-4b89-8592-dd8671563b65.png` | 1448x1086 | `27ff66e34a8649a22c649a5593c93d0532cd176cf69dafb61bc19a1d2e1eb85a` | Supplementary flowchart/explaining pose, expression, composition and context. |
| CORE SCENE / EXPRESSION EXEMPLAR | `assets/visual-references/core-mascot/scenes/e2a608fa-267b-4e7b-b7e8-0065699dd13f.png` | 1448x1086 | `24dc9fd6367d6f7c4f9731b12bd1b7e7376edf7870ecee0a8ac066699363ff65` | Supplementary growth-chart/surprised-expression pose, composition and context. |
| CORE SCENE / EXPRESSION EXEMPLAR | `assets/visual-references/core-mascot/scenes/42ee8538-a4ff-4ca5-8b00-0044ef90207e.png` | 1448x1086 | `95ad2c8a75b7ce798eb315d1c84d34571bb1a44ace1922b141bdb2173fdfae4f` | Supplementary reading/thinking pose, expression, composition and context. |

The three identity assets contain no supporting hamster model and are the only core-mascot identity inputs in this
manifest. The scene/expression exemplars are supplementary only: their whiteboards, charts, books, tables, chairs,
diagrams and any other props are scene context, never mascot identity features.

Supporting-character references must live in separate per-character directories. Identity references from different
recurring characters must never be pooled. A recurring supporting character must receive its own isolated approved
reference(s) before stable reuse. Generated images never become approved references automatically; founder + ChatGPT
approval is required before an image can be added as a character reference.

This canonizes the tracked reference assets and reference-grounded generation requirements only. It does not
implement image-conditioning/reference-passing code or automated QA, create supporting-character entities, define a
supporting roster, create a milestone or authorize a later phase. Those implementation details remain separately
designed and authorized work.

#### Flat-colour and outline contract

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

`data/atlas.db` is ignored local/runtime/demo state, not canonical GitHub truth. A current local runtime DB may
contain zero CharacterReferenceSets, Assets or GenerationExecutions; that does not rewrite accepted canonical
history. The canonically accepted `character-reference-set-similarstoic-hamster-core-v1` version `1` contains the
founder-approved Asset `asset-9a02b4cb416744a994965e2e1f2f0c33` version `9`, SHA-256
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

## Required operating method

> DEFINE → DESIGN WITH FOUNDER / CHATGPT → BOUNDED CODEX TASK → IMPLEMENT LOCALLY → VALIDATE → REVIEW → FIX REGRESSIONS → FINAL ACCEPTANCE → COMMIT → PUSH → NEXT MILESTONE

**v0.19 — Editorial-Angle-Authorized ContentPiece Initiation** is the latest accepted implementation checkpoint.
Its implementation was validated, committed and pushed at
`32812e6793d9b06632ebffd82504cd8810c2ab3d`. No successor after v0.19 is selected; its immediate next action is
founder + ChatGPT design and selection of the next bounded milestone. Any scope beyond v0.19 requires a new
explicit founder + ChatGPT decision.

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

Do not invent a successor milestone after v0.19. The final Title/Hook domain model, final Script-to-Claim
architecture, EditorialAngle versioning/revalidation semantics, final Editorial Gate persistence shape, final
machine editorial-QA model, final Research Readiness evaluator implementation, Phase 4 automation design, later
publishing architecture, Learning persistence/automation and detailed financial implementation remain unresolved
or deferred. Each requires founder + ChatGPT design and explicit canonical authorization before implementation.
