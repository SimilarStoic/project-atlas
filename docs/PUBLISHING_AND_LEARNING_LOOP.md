# Controlled Publishing and Performance Learning Loop

## Decision and boundary

Productions #2, #3 and #4 are founder-accepted. The production-method validation objective is therefore **SATISFIED**.
The next validation target is the smallest controlled loop that can publish an exact accepted artifact, observe real
audience behaviour and apply conservative evidence to later content decisions:

> idea → research → script → production → founder final review → controlled publication → performance ingestion →
> interpretation → learning applied to future content

This document is design authority only. It implements no platform API, credential, publication, metric collection,
Production #5, migration or autonomous optimiser. Migration 24 remains unauthorized. Production #5 is reserved as the
**FIRST LIVE-LOOP VALIDATION PRODUCTION** and must not begin until the publishing/learning implementation and exact pilot
authority are separately accepted. Production #6 must not begin.

## Pilot platform scope

Use **YouTube Shorts only** for the first pilot. Do not cross-post the pilot to TikTok, Instagram or another platform.
One platform removes cross-platform audience and metric-definition confounds while the loop itself is unproven.

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
- [Three-minute YouTube Shorts eligibility](https://support.google.com/youtube/answer/15424877)
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
2. **Founder publication gate:** founder approves the exact artifact digest, package digest, target channel, public
   title/description/cover, privacy transition and publication time in one decision.
3. **Private upload:** only after that approval, upload the approved MP4 as `private`; never upload directly as public.
4. **Remote verification:** wait for successful processing, then verify remote video identity, duration, privacy,
   title, description, caption availability, cover result and target channel. A mismatch fails closed.
5. **Public transition:** when remote verification passes, Conveyor may perform the exact approved `private → public`
   transition at the approved time. It may use YouTube's private-video scheduling field when available and verified.
6. **Publication receipt:** preserve platform video ID, URL, actual publication timestamp, package/approval linkage and
   the platform response digest before metric ingestion begins.

The default pilot slot is **Tuesday at 18:30 Europe/London**, once per week. Hold that slot for the first three pilot
publications to reduce timing variance. If the exact slot cannot be met, keep the item private and move to the next
explicitly recorded pilot slot; do not publish immediately merely to preserve cadence.

`Draft` means a local immutable package with no platform transfer. `Private` is the default uploaded pre-publication
state. `Unlisted` is not part of the default path and requires an explicit reason because link access can escape the
review group. `Public` is permitted only by the exact founder publication decision above. During the pilot, no standing
approval or automatic-public default replaces that decision.

An unverified YouTube API project may restrict API uploads to private viewing. Implementation must discover this before
the pilot. If public API transition is unavailable, the founder may perform the final public action in YouTube Studio
against the same approved package; Conveyor records the resulting platform identity and timestamp. Do not weaken the
gate or use another platform as a workaround.

## Minimum performance ingestion

Collect aggregate, content-level signals only. Do not collect viewer identities or raw personal data. Use append-only
snapshots at approximately **24 hours, 72 hours, 7 days and 28 days** after actual publication. Store the observation
time, metric window, API definition/version where available, raw response digest and missing-data reason.

### Core signals

| Signal | Decision use |
| --- | --- |
| `engagedViews` and `views` | Reach context and the number of viewers who continued beyond the first frame; preserve both because Shorts definitions can differ. |
| `estimatedMinutesWatched` | Total attention earned; interpret with reach. |
| `averageViewDuration` and `averageViewPercentage` | Pacing and length fit. |
| `audienceWatchRatio` by `elapsedVideoTimeRatio` | Hook hold, scene-level drops, payoff hold and rewatch spikes. |
| likes, comments and shares | Secondary resonance signals, normalized by engaged views where possible. |
| `subscribersGained` | High-value audience-fit signal, normalized by engaged views and treated cautiously at low counts. |

Impressions and click-through rate are optional diagnostics when the API provides a relevant surface-specific value;
they are not primary Shorts-feed metrics. Saves are not part of the YouTube pilot because no reliable equivalent is
assumed. Comment text is not ingested by default; founder does not review routine comments or dashboards. A later
moderation/qualitative design is required before storing comment content.

Map the 100-point retention series to the accepted final-media timeline and scene boundaries. This allows a drop or
rewatch to be associated with the actual hook, visual beat, claim, payoff or CTA without claiming causation from one
curve.

## End-to-end attribution

Every platform observation must resolve through immutable identifiers and digests:

> Opportunity → ResearchPack / Claims / Sources → EditorialAngle → title/hook → Script/version → VisualPlan →
> FinalMediaInputSnapshot → FinalMediaArtifact → PublishingPackage → founder PublicationGateDecision →
> PlatformPublication → PerformanceSnapshot → LearningAssessment → future content decision

The publishing package freezes exactly what was intended. The publication record freezes where and when it actually
appeared. Performance snapshots preserve later-changing platform totals as observations rather than mutating the
artifact or publication history. A learning assessment names every snapshot and content feature it compares. When a
learning changes a later Opportunity, hook, Script, duration, visual treatment, payoff or CTA, that later record cites
the assessment ID and describes the bounded change.

## Persistence conclusion and future additive migration

Migrations 1–23 already preserve the chain from Opportunity through accepted `FinalMediaArtifact`. They contain no
durable publishing package, publication approval, platform-publication identity, performance snapshot or learning
assessment tables. JSON in existing metadata could hold a temporary note, but it cannot safely represent append-only
platform state and repeated metric observations without blurring immutable provenance.

A **future additive migration is justified before the first automated live-loop pilot**. Migration 24 is not authorized
or implemented by this design. The smallest future persistence proposal should cover these concepts:

- immutable `PublishingPackage` tied to one `FinalMediaArtifact`;
- immutable `PublicationGateDecision` tied to the exact package and founder decision;
- stable `PlatformPublication` identity tied to one package and target account;
- append-only `PublicationStatusSnapshot` and `PerformanceSnapshot` records;
- immutable `LearningAssessment` plus an explicit record when a future content decision applies it.

Provider adapters, OAuth/credential storage, retry policy, quota handling, schema fields, uniqueness rules and
transaction semantics belong to the later implementation design. Credentials must never be stored in provenance JSON
or Git. Existing final-media history remains unchanged.

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

- the exact final external publication approval;
- consequential brand/editorial or strategy changes supported by performance evidence;
- new spend authorization where the active envelope requires it.

Stop at BLOCKER for wrong-account risk, missing approval/provenance, unavailable public transition, material platform
policy ambiguity, corrupt metric attribution or evidence that cannot be reconstructed. Stop at SPEND GATE under the
existing envelope rules. Routine package generation, private processing checks, aggregate metric ingestion, confidence
assessment and bounded reversible recommendations do not create founder gates once their implementation is authorized.

Current quality-envelope state is `$4.39 / $10` used and `$5.61` remaining. This design used `$0` and made no provider
or platform call.
