# Controlled Publishing and Performance Learning Loop

## Decision and boundary

Productions #2–#5 are founder-accepted. Production #5 v4 also satisfies the reference-driven visual-generation proof.
Controlled YouTube pilot-readiness is **PASS**, while public launch remains unauthorized. Uninstructed OpenAI
`gpt-4o-mini-tts-2025-12-15` / Marin is the provisional production-development narrator baseline, not the permanent
narrator. Narrator quality remains passage-dependent; no tested instruction is a universal production default, and
further Stage-1 experimentation is paused pending new explicit founder authority. Publishing accepted Production #5
must not regenerate its narration. This document retains
the approved design for a later smallest controlled loop that can publish an exact accepted artifact, observe real
audience behaviour and apply conservative evidence to later content decisions:

> idea → research → script → production → founder final review → controlled publication → performance ingestion →
> interpretation → learning applied to future content

This document remains design authority. Source Migration 25 now contains the separately authorized **offline**
publishing/learning persistence foundation, validated with a test-only fake adapter. A separately authorized
identity-only OAuth preflight now uses the minimum YouTube read-only scope and has resolved the sole authenticated
channel exactly to `UC1cX-OTF9-LZeNo5TaFgrgQ`; its refresh token is protected by Windows Credential Locker and remains
outside Git/provenance. The offline
foundation still implements no live upload, publication, metric collection or autonomous optimiser; the verified
persistent runtime remains at Migration 24. Accepted Production #5 v4 may later become the first live-loop item only after live
integration and exact publication authority are separately accepted. Readiness PASS authorizes no upload or
publication. Production #6 must not begin.
The [controlled pilot architecture](CONTROLLED_YOUTUBE_PILOT_ARCHITECTURE.md) governs external-action safety,
manual routes, operation evidence, analytics coverage and API-data retention; this design does not override it.

## Pilot platform scope

Use **YouTube Shorts only** for the first pilot. Do not cross-post the pilot to TikTok, Instagram or another platform.
One platform removes cross-platform audience and metric-definition confounds while the loop itself is unproven.
The intended pilot is initially **three** controlled public items, at no more than **one per week**. One item is an
observation, not proof of audience or product fit. Production #5 v4, SHA-256
`c35e8e6211ae9bf7bfeb694ec6dbec3c69d822862729d9d9f4440d50028ea2bd`, has no identified pilot-quality
veto and is the prospective first item. The intended target is [`@Similar-stoic`](https://www.youtube.com/@Similar-stoic),
channel ID `UC1cX-OTF9-LZeNo5TaFgrgQ`. Founder access to that exact channel in Studio is confirmed, and the 16
September 2026 read-only OAuth preflight independently resolved the sole authenticated channel to that exact ID.
Token validity, handle, public channel lookup and Studio access alone remain insufficient. This identity PASS grants
no mutation or publication authority.

YouTube is the strongest initial fit because:

- current SimilarStoic masters are vertical and under three minutes, which YouTube classifies as Shorts;
- the YouTube Data API supports upload plus `private`, `unlisted` and `public` privacy states, and supports scheduled
  publication while a video is private;
- the YouTube Analytics API exposes views/engaged views, watch time, average view duration, average view percentage,
  likes, comments, shares, subscribers gained and time-normalized audience-retention data;
- a private-first upload permits processing and metadata verification before the approved public transition.

Current official capability references:

- [YouTube videos resource and privacy/scheduling states](https://developers.google.com/youtube/v3/docs/videos)
- [YouTube video upload](https://developers.google.com/youtube/v3/docs/videos/insert)
- [YouTube Analytics metrics](https://developers.google.com/youtube/analytics/metrics)
- [YouTube Analytics dimensions and elapsed-video retention](https://developers.google.com/youtube/analytics/dimensions)
- [Three-minute YouTube Shorts eligibility](https://support.google.com/youtube/answer/15424877?hl=en)
- [YouTube custom thumbnails](https://support.google.com/youtube/answer/72431)

TikTok and Instagram remain later platform adapters. Do not add them until the YouTube loop has at least three
comparable public items with complete seven-day snapshots and no material attribution or control failure.

## Exact publishing package

Conveyor prepares one immutable, platform-specific package for one exact accepted `FinalMediaArtifact`. The package
contains:

- target platform and exact channel/account identity;
- final-media artifact ID, SHA-256, duration and media path;
- exact title, description and final public caption;
- restrained tags/hashtags and `en-GB` language/locale;
- `Education` category where the channel/API reports it as available;
- audience/compliance declarations, including whether any platform disclosure is required;
- a separate timed caption file derived from the accepted final-audio alignment, while keeping burned-in captions;
- one 9:16 cover image derived from an accepted video frame, its digest and fallback frame timestamp;
- intended privacy transition, publication timestamp and `Europe/London` timezone;
- approved transfer route, approved API/manual public-transition route, pilot slot and bounded manual execution window
  where applicable;
- package version, digest and creation timestamp.

The title states the useful proposition without manufacturing urgency. The description gives one concise explanation,
lists material sources when the episode makes factual claims, and identifies SimilarStoic. Use at most three relevant
hashtags; do not treat hashtag volume as a discovery strategy.

The cover follows the Production #4 lesson: the hamster and visual metaphor remain primary. Labels or numbers may
support the image, but the cover must not become a slide, checklist or text card. If the API/account cannot set the
9:16 custom thumbnail reliably, use the recorded fallback frame through YouTube Studio and preserve that choice in the
publication record.

## Controlled upload and publication workflow

1. **Local package:** produce and validate the exact publishing package without contacting YouTube.
2. **Founder publication gate:** before platform transfer, founder approves the exact artifact and package digests,
   target channel, public proposition, declarations, privacy transition, transfer/public-transition routes, pilot slot
   and publication time/timezone or bounded manual window in one immutable decision. Readiness and accepted render
   status are not publication authority. A changed proposition requires new authority.
3. **Private upload:** only after that approval, transfer the verified approved MP4 as `private` through the approved
   API or Studio route; never upload directly as public. Reserve durable operation identity before external mutation.
4. **Remote verification:** wait for successful processing, then verify remote video identity, duration, privacy,
   title, description, caption availability, cover result and target channel. A mismatch fails closed.
5. **Public transition:** when remote verification passes, Conveyor may perform or reconcile the exact approved
   eligible `private → public` transition at the approved time. It may use verified private-video scheduling where
   specifically approved. Studio execution is recorded as a human action, not a Conveyor API action.
6. **Publication receipt:** after independently observing public state, preserve platform video ID, URL, actual public
   publication timestamp and its source/precision, package/approval/action linkage and retainable response evidence
   before metric ingestion begins. Private upload time is not public publication time.

The default pilot slot is **Tuesday at 18:30 Europe/London**, once per week. Hold that slot for the first three pilot
publications to reduce timing variance. If the exact slot cannot be met, keep the item private and move to the next
explicitly recorded pilot slot; do not publish immediately merely to preserve cadence.

`Draft` means a local immutable package with no platform transfer. `Private` is the default uploaded pre-publication
state. `Unlisted` is not part of the default path and requires an explicit reason because link access can escape the
review group. `Public` is permitted only by the exact founder publication decision above. During the pilot, no standing
approval or automatic-public default replaces that decision.

An unverified YouTube API service may cause an uploaded video to be **locked private**. Unlike an ordinary eligible
private upload, that lock cannot necessarily be undone with a Studio public click. Current guidance requires re-upload
through a verified API service or YouTube's own app/site. Therefore an explicitly approved **Studio private upload**
is a controlled fallback, alongside Studio private-to-public transition for an eligible ordinary private video.
Preserve a blocked API-upload object; never automatically create a replacement that could duplicate it. Reconcile
outcome and obtain an explicit recovery decision. [YouTube private-lock guidance](https://support.google.com/youtube/answer/7300965?hl=en).

Local idempotency does not guarantee remote exactly-once execution. Durable deterministic operation reservation and
append-only events distinguish intended, approved, attempted, uncertain, remotely identified and observed outcomes.
An ambiguous upload is `outcome_unknown` (or equivalent), **not failure**; no replacement upload is permitted until
reconciliation establishes safety. Protected resumable-session state is separate from ordinary provenance, and
YouTube's acknowledged byte range governs resumption. The narrow adapter and explicit local CLI/service execution
model are defined in the [architecture authority](CONTROLLED_YOUTUBE_PILOT_ARCHITECTURE.md).

## Minimum performance ingestion

Collect aggregate, content-level signals only. Do not collect viewer identities or raw personal data. Use append-only
snapshots at approximately **24 hours, 72 hours, 7 days and 28 days** after actual publication. Store the observation
time, nominal checkpoint and due time, actual collection time, requested and returned platform coverage, metric
availability/maturity, API definition/version where available, retainable response digest and missing-data reason.
These are **collection checkpoints**, not guarantees of exact 24h/72h/7d/28d analytics coverage. YouTube reports by
platform periods and may return only through the latest date for which all requested metrics are available.
Unavailable or immature values are **not zero**. [Analytics query coverage](https://developers.google.com/youtube/analytics/reference/reports/query).

### Core signals

| Signal | Decision use |
| --- | --- |
| `engagedViews` and `views` | Reach context and the number of viewers who continued beyond the first frame; preserve both because Shorts definitions can differ. |
| `estimatedMinutesWatched` | Total attention earned; interpret with reach. |
| `averageViewDuration` and `averageViewPercentage` | Pacing and length fit. |
| `audienceWatchRatio` by `elapsedVideoTimeRatio` | Hook hold, scene-level drops, payoff hold and rewatch spikes. |
| likes, comments and shares | Raw platform secondary-resonance observations, interpreted cautiously at low counts. |
| `subscribersGained` | Raw platform high-value audience-fit observation, interpreted cautiously at low counts. |

Impressions and click-through rate are optional diagnostics when the API provides a relevant surface-specific value;
they are not primary Shorts-feed metrics. Saves are not part of the YouTube pilot because no reliable equivalent is
assumed. Comment text is not ingested by default; founder does not review routine comments or dashboards. A later
moderation/qualitative design is required before storing comment content.

When available, map returned time-normalized retention points to the accepted final-media timeline and scene
boundaries. This allows an observed drop or rewatch to be associated with the actual hook, visual beat, claim, payoff
or CTA without claiming causation from one curve or assuming a complete 100-point series.
Do not create engagement, conversion or composite metrics from YouTube API Data by default. Current policy requires
the applicable additional-derived-metrics permission, which is not established for Conveyor. Preserve supported raw
platform metrics and distinct authored qualitative interpretations.
[YouTube Developer Policies](https://developers.google.com/youtube/terms/developer-policies) and
[additional derived-metric policy](https://developers.google.com/youtube/terms/derived-metrics-policy).

Append-only **Conveyor-authored** provenance does not authorize permanent storage of raw YouTube API Data. Authorized
statistics may be retained while current consent and required periodic checks remain valid; other API Data requires
refresh/deletion as applicable, and revocation/deletion requests must be honored. Provider payloads and prohibited
disguised hashes/tombstones must be removable without rewriting permissible authored history. Exact retention controls
remain an implementation task. [YouTube API-data policies](https://developers.google.com/youtube/terms/developer-policies).

## End-to-end attribution

Every platform observation must resolve through immutable identifiers and digests:

> Opportunity → ResearchPack / Claims / Sources → EditorialAngle → title/hook → Script/version → VisualPlan →
> FinalMediaInputSnapshot → FinalMediaArtifact → PublishingPackage → founder PublicationGateDecision →
> PublicationOperation / events → PlatformPublication → PublicationStatusSnapshot → PublicationReceipt →
> PerformanceSnapshot → LearningAssessment / supporting observations → later LearningApplication / content decision

The publishing package freezes exactly what was intended. The publication record freezes where and when it actually
appeared. Performance snapshots preserve later-changing platform totals as observations rather than mutating the
artifact or publication history. A learning assessment names every snapshot and content feature it compares. When a
learning changes a later Opportunity, hook, Script, duration, visual treatment, payoff or CTA, that later record cites
the assessment ID and describes the bounded change.

## Persistence conclusion and additive source migration

Runtime migrations 1–24 preserve the chain from Opportunity through accepted `FinalMediaArtifact` and visual-reference
authority provenance. By themselves they contain no
durable publishing package, publication approval, platform-publication identity, performance snapshot or learning
assessment tables. JSON in existing metadata could hold a temporary note, but it cannot safely represent append-only
platform state and repeated metric observations without blurring immutable provenance.

Additive **source Migration 25** now implements the offline publishing/learning persistence needed before any live
loop. It has not been applied to the verified persistent runtime and this design does not authorize live integration.
The source foundation covers these concepts:

- immutable `PublishingPackage` tied to one `FinalMediaArtifact`;
- immutable `PublicationGateDecision` tied to the exact package and founder decision;
- durable `PublicationOperation` and append-only `PublicationOperationEvent` for external action and uncertainty;
- stable `PlatformPublication` identity tied to one package and target account;
- append-only `PublicationStatusSnapshot` and actual-publication `PublicationReceipt`;
- append-only `PerformanceSnapshot` records;
- immutable/versioned `LearningAssessment` with exact supporting-observation links, plus an explicit record when a
  future content decision applies it.

Provider adapters, OAuth/credential storage, retry policy, quota handling, schema fields, uniqueness rules and
transaction semantics belong to the later implementation design. Credentials must never be stored in provenance JSON
or Git. Exact SQL DDL is not canonized by this conceptual list. Existing final-media history remains unchanged.

## Conservative learning rules

Hard rule: **automate proven learning, not noise**.

| Evidence tier | Minimum interpretation | Allowed effect |
| --- | --- | --- |
| One-off observation | One item, an immature snapshot, very low exposure or a major confound. | Record only; fix an objective technical failure, but make no strategy change. |
| Weak evidence | Two comparable items or one mature item with a clear but unreplicated pattern. | Create a hypothesis and design a future comparison; do not change canonical strategy. |
| Repeated pattern | At least three comparable public items with complete seven-day snapshots, the same directional effect and no dominant topic/timing confound. | Adjust a routine, reversible production choice for a bounded trial and record the reason. |
| Strong enough for consequential review | Normally at least five comparable items spanning two topic families or two deliberate replications, with a material stable effect and mature snapshots. | Recommend a brand/editorial/cadence change to founder; do not apply it automatically. |

Counts are floors, not proof. Confidence also depends on engaged-view volume, effect size, retention-curve stability,
metric maturity, platform-definition changes and confounds such as topic, publication time, length, cover, external
traffic or a changed CTA. Zero likes or subscribers at tiny reach is absence of evidence, not negative audience fit.

Examples of admissible hypotheses include repeated retention loss under the same intro structure, stable response to a
hook family, topic-family differences, duration effects, a visual device aligned with retention change, payoff hold or
CTA effect. Do not infer the cause from correlation alone. Change one main variable where practical, preserve the
comparison set and evaluate the result after the same observation window.

Conveyor summarizes each mature cycle for the founder as: **what happened; why it probably happened; confidence; main
confounds; and the smallest recommended change**. Founder review is required only for consequential brand/editorial or
strategy change, not routine metric inspection.

## Cadence during the pilot

Keep the existing **one founder-review-ready short per five working days** production pace and publish no more than one
pilot Short per week. Do not optimize for volume. Each item receives 24-hour and 72-hour observations before the next
public item and a seven-day snapshot before its result influences another production. The 28-day snapshot updates the
historical assessment without blocking the next weekly item.

After at least three public pilot items have complete seven-day snapshots, review loop reliability, publication errors,
metric completeness and the first cross-item hypotheses. A move toward one high-quality Short per day requires proven
publishing reliability and repeated learning evidence; this document does not authorize that acceleration.

## Human gates and stop conditions

Founder involvement during the pilot is limited to:

- founder-operated OAuth/account authorization setup;
- the exact final external publication approval;
- the authorized Studio action if manual execution is selected, or an explicit recovery decision if another upload
  might duplicate an uncertain or API-locked remote object;
- consequential brand/editorial or strategy changes supported by performance evidence;
- new spend authorization where the active envelope requires it.

Stop at BLOCKER for wrong-account risk, missing approval/provenance, unavailable public transition, material platform
policy ambiguity, unknown upload success, duplicate-publication risk, corrupt metric attribution or evidence that
cannot be reconstructed. Stop at SPEND GATE under the
existing envelope rules. Routine package generation, private processing checks, aggregate metric ingestion, confidence
assessment and bounded reversible recommendations do not create founder gates once their implementation is authorized.

Current conservative narrator Stage-1 exposure is `$0.19694332 / $0.50`, with `$0.30305668` unspent. The active
quality envelope is `$7.62694332 / $10` used and `$2.37305668` remaining. Remaining budget is not spending
authorization. This documentation design uses no provider or platform call.
