# Project Atlas — Current Status

## Last Updated

17 August 2026

## Current Phase

**Phase 2 — Content Operating Model (ACTIVE; v0.16 ACCEPTED)**

## Overall Status

🟢 Phase 1 is formally closed. Phase 2 is now the active roadmap phase under founder + ChatGPT
design/implementation stewardship; v0.16 is the latest accepted implementation milestone and v0.15 is its
historical accepted predecessor. v0.17 — Persistent Research Readiness is defined and authorized for bounded
implementation, but is not implemented or accepted. Remaining Phase 2 scope is not implemented. Atlas v0.1
through v0.7 are complete and pushed.

The technical foundation is complete and the repository is safely stored on GitHub.

The bounded Atlas v0.9 Visual Style Control Foundation, v0.10 Visual Style Fidelity Refinement, v0.11
Character Continuity Foundation, v0.12 Canonical Character Reference Foundation, v0.13 Reference-Grounded
Character Generation, and v0.14 Explicit Character Reference Bootstrap are complete and pushed. The
founder-approved Phase 1 visual baseline is SimilarStoic Core v3; v2 remains historical and immutable.

The v0.1 UI baseline, v0.2 persistent discovery foundation and v0.3 research and evidence foundation are implemented and safely stored on GitHub.

Atlas v0.8 through v0.14 are complete and pushed. Atlas now has immutable, versioned character identity,
canonical visual-reference foundations, reference-grounded character generation, and explicit first-reference
bootstrap alongside the founder-approved SimilarStoic Core v3 visual-style baseline.

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

## Git

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

These are strategic examples, not a final Atlas Pillar taxonomy.

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

The current editorial portfolio themes guide strategy but do not define the final persistent Atlas Pillar taxonomy.

1. Build & Protect Wealth
2. Keep More of What You Earn
3. Increase Income & Leverage
4. Spot the Next Opportunity
5. Think & Decide Better

## Atlas Domain Distinction

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

Atlas produces a curated daily shortlist of 5–10 opportunities. Initially Atlas proposes and the founder approves or steers; research begins only after approval.

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

Atlas is specified as a structured knowledge + content intelligence system, not merely a content archive:

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

- **Command Centre** — strongest opportunities, attention-needed content, Atlas activity, important knowledge/source changes, lightweight performance and Atlas Chat access.
- **Discover / Opportunities** — 5–10 opportunities with relevance, why-now context, viewer benefit, suggested angle, evidence quality, risk, portfolio relevance and visual potential.
- **Content Workspace** — lifecycle, research, claims, sources, angle, script, visual plan, QA state and approval controls.
- **Atlas Chat** — natural-language questions, steering and eventually actions.

The interface prioritises decisions and exceptions over unnecessary technical complexity.

## Modular, Configurable Architecture

The architecture follows a “change without rebuild” principle: data, capabilities, workflows, configuration and interface remain loosely coupled.

Atlas is a composable pipeline. Providers, research engines, model/provider adapters, narration/audio and
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

Atlas is intended to become an approximately **95% automated content operating system**: routine execution is
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
Research Initiation** is the latest accepted implementation milestone; v0.15 remains its historical accepted
predecessor. Later phases retain their defined roles for technical architecture, research, content intelligence,
production, distribution, analytics/learning, automation and scale; no later milestone or phase is activated.

# Approved Phase 2 Operating-Model Specification

Phase 2 now has approved specification direction and is active. Its narrow v0.15 implementation is accepted;
remaining scope is unimplemented. Atlas uses sparse human gates and rich machine readiness:
human judgement is distinct from readiness evidence, neither may
silently substitute for the other, and intermediate work should progress automatically only when explicit
quality, evidence and provenance requirements pass.

The target gates are **Idea** (Proceed / Reject / Steer an opportunity), **Editorial** (Approve / Revise /
Reject / intentional alternative selection for a Title/Hook/Angle/Script package) and **Learning** (review
evidence-backed, scoped, reversible performance/economics adaptations). They are version-specific future
decision concepts, not database entities or a generic mutable workflow state.

Where paid external production is contemplated, the Editorial Gate also contains the linked founder judgement
of the maximum spend Atlas may use for that approved proposition. It is a bounded ceiling, not a spend target,
and does not create a fourth routine founder gate. Atlas should choose the lowest-cost path that still clears
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

**v0.16 — Authorized Research Initiation** is now the latest accepted implementation milestone. It provides
deliberate creation of Opportunity-owned
ResearchPack versions under an immutable, nullable direct IdeaGateDecision provenance reference: Proceed and
Steer qualify, Reject never does, and snapshot/pack Opportunity lineage must match exactly. Historical packs
remain valid without fabricated provenance; Steer direction remains canonical on IdeaGateDecision and is
consumed by reference. The separate initiation action has no automatic research/job/queue/provider/readiness/
workflow/automation effect, no consumed/current authorization state and no `Opportunity.status` mutation.
Migration 13, repository/API/UI implementation and tests are canonical; migrations are now 1–13. v0.15 remains
the historical accepted predecessor. v0.16 itself implies no scope beyond its accepted boundary.

**Research Readiness semantics are approved design direction only.** They define additive, immutable,
versioned assessments of an exact frozen ResearchPack Claim/Source/ClaimEvidence state, not mutable workflow
state and not a founder gate. Every assessment must preserve the assessed evidence snapshot, Ready /
NeedsMoreResearch / Blocked outcome, findings/reasons, assessment schema and policy/check versions, timestamp
and producer/implementation provenance. ResearchPack ID/version alone is insufficient because Claims,
Sources and ClaimEvidence may change later. Multiple assessments remain additive with no persisted
current/latest/superseded pointer; later evidence requires a new assessment. No readiness entity, migration,
API, UI, producer, research automation or EditorialAngle progression rule is implemented. A Ready assessment
does not automatically create editorial records; how readiness may later authorize EditorialAngle progression
remains a separate design decision.

**v0.17 — Persistent Research Readiness** is the defined and authorized next Phase 2 implementation milestone.
It is not implemented or accepted; v0.16 remains latest accepted and migrations remain 1–13 until bounded
implementation. v0.17 is limited to one immutable ResearchReadinessAssessment table with a server-built,
deterministically ordered, schema-versioned frozen ResearchPack/Claim/Source/ClaimEvidence payload; exact
Ready / NeedsMoreResearch / Blocked outcomes; structured findings; policy/check, schema and producer
provenance; additive history; and controlled create/list/get API reads. It has no UI, evaluator, mutable
current/latest state, backfill, EditorialAngle linkage/progression, automation or later-phase behavior. No
successor after v0.17 is selected.

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

# Next Step

Reference-grounded generation and explicit first-reference bootstrap are complete through v0.14. Phase 1 is
formally closed: the final production-ready SimilarStoic brand identity is **APPROVED**, and the visual
decision remains **PASS WITH DEFERRED VISUAL REFINEMENT** under the immutable SimilarStoic Core v3 baseline.
Phase 2 is now active. v0.16 — Authorized Research Initiation is the latest accepted implementation milestone;
v0.15 remains its historical accepted predecessor.
v0.17 — Persistent Research Readiness is the defined and authorized bounded implementation milestone, not yet
implemented or accepted. It does not select a successor milestone.
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
