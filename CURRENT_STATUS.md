# Project Atlas — Current Status

## Last Updated

12 August 2026

## Current Phase

**Phase 1 — Product & Business Definition**

## Overall Status

🟡 Product definition continues. Atlas v0.1 through v0.7 are complete and pushed.

The technical foundation is complete and the repository is safely stored on GitHub.

The bounded Atlas v0.8 Generation Execution Foundation is implemented locally and awaiting review.

The v0.1 UI baseline, v0.2 persistent discovery foundation and v0.3 research and evidence foundation are implemented and safely stored on GitHub.

Atlas v0.8 implements the approved synchronous bridge from one persistent executable AssetSpec to
one immutable GenerationExecution and, on success, one immutable Asset. No further v0.8 implementation
beyond this bounded foundation has been approved.

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

`447c7c4657444119f5bc9fab77248f5aeb2f841b feat: add asset specification and asset foundation`

Branch:

`main`

Remote:

`origin https://github.com/SimilarStoic/project-atlas.git`

Working tree:

Clean at the v0.7 checkpoint; local `main` matched `origin/main`.

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

## Atlas v0.8 Local Implementation

**Project Atlas v0.8 â€” Generation Execution Foundation** is implemented locally and awaiting review,
commit and push.

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

Finance remains a major centre of gravity, an important commercial foundation, a core source of high-intent content and central to the SimilarStoic identity. The expanded territory extends the finance-centred strategy; it does not replace finance.

Relevant territory may include money, wealth and investing; work, careers and income; time; behaviour and psychology; life strategy; status and consumption; relationships and social decisions where relevant; energy and attention; mental models; modern adulthood; financial independence; and broader economic ideas made personally understandable.

These are strategic examples, not a final Atlas Pillar taxonomy.

## Editorial Inclusion Test

> Does understanding this help someone make better decisions about their money, work, time or future?

If yes, the idea may belong within SimilarStoic. SimilarStoic must not drift into generic self-improvement merely because a subject is popular or clickable.

Life design connected to money, time or work; psychology of consumption/status; careers/income; and financial relationships are potentially strong fits. Generic fitness advice with no meaningful connection is generally outside the intended territory.

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

Workflow stages should be independently addable, removable, reorderable and configurable where practical. The fixed MVP workflow must not become a permanent hard-coded constraint.

Short-form, long-form, newsletters and company deep dives should be able to reuse the same underlying knowledge/content system.

V1 business rules should be configurable without code where practical, including audience, geography, pillars, topic preferences/scoring, duration, editorial direction, source/freshness/risk requirements, approval rules, US-comparison rules, personal-perspective/CTA rules, visual rules, cadence, cost limits and automation level per stage.

Protected safety, security and integrity constraints are not ordinary configuration. Configuration must be versioned and auditable so historical content retains its production context.

## Cost Tracking & Development Stack

Cost tracking is a first-class requirement. The planned system links AI/API operations to content pieces where possible and eventually tracks usage, model/provider, research/writing/QA/narration/visual/rendering costs, total cost per item, spend over time, unit economics and revenue versus production cost.

Configurable monthly and per-content budget targets and alerts are required.

GPT + Codex are the current primary AI/development stack. Claude or another coding agent is not a dependency or requirement. This is a tooling choice, not an architectural lock-in; provider abstraction remains possible where practical.

---

# Current Phase 1 Work

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
- Atlas v0.8 Generation Execution foundation (local, awaiting review/commit/push)

Remaining before Phase 1 is complete:
- Final production-ready brand identity
- Final production-ready mascot visual specification
- Final Phase 1 acceptance review

---

# Next Step

Next:

> **Review the bounded Atlas v0.8 Generation Execution Foundation, then commit and push if approved.**

Implemented direction through v0.8:

v0.8 adds GenerationExecution provenance between an AssetSpec and any generated Asset; manual and
imported Assets remain valid without that nullable provenance.

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
