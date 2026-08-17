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

## Current immediate continuation

The approved next activity is **Phase 1 visual-evidence execution on accepted v0.14**. This is **not v0.15**
and does not create a new implementation milestone.

The approved sequence is:

1. Establish an isolated review environment.
2. Create a fresh v0.14 review database.
3. Bootstrap exactly two legitimate hamster reference candidates.
4. Stop at Human Gate A.
5. Founder and ChatGPT visually review the candidates.
6. Select zero, one, or more candidates.
7. Explicitly create CharacterReferenceSet v1 from any selected eligible Assets.
8. Generate grounded review evidence after that approval.
9. Make the Phase 1 visual-acceptance decision.

No reference set is created automatically.

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
- Pop culture is light seasoning. Original exaggerated reaction and freeze-frame comedy may use older animated
  timing mechanisms as inspiration, without copying protected characters, artwork, frames, or compositions.
- SimilarStoic Core v2 remains a provisional visual baseline: sparse, light, hand-drawn visual grammar.
  Material future style changes require new immutable versions.

## Deferred scope

Do not infer approval for neutral CharacterProfile-owned candidate studies, automatic reference selection,
similarity scoring, visual QA automation, style-reference grounding, generic approval/lifecycle models,
queues, retries, batch semantics, cost tracking, rendering, animation, audio production, publishing,
analytics, cloud systems, or agents.
