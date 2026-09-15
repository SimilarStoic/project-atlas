# Controlled YouTube Pilot — Architecture Authority

Founder-approved canonical reconciliation, 15 September 2026. This record defines the smallest controlled
publishing and learning architecture for the initial SimilarStoic YouTube Shorts pilot. Source Migration 25 and a
provider-neutral offline persistence/lifecycle foundation were subsequently implemented under separate authority.
This record does not authorize OAuth credentials, a YouTube call or upload, or public publication.
The [publishing and learning design](PUBLISHING_AND_LEARNING_LOOP.md) supplies the editorial package, pilot cadence
and conservative learning rules; this record governs execution, external-action safety and evidence boundaries.

## Pilot and authority boundary

Controlled pilot-readiness is **PASS**. The intended channel is [`@Similar-stoic`](https://www.youtube.com/@Similar-stoic),
ID `UC1cX-OTF9-LZeNo5TaFgrgQ`; founder access to this exact channel in YouTube Studio is confirmed. Accepted
Production #5 v4, SHA-256 `c35e8e6211ae9bf7bfeb694ec6dbec3c69d822862729d9d9f4440d50028ea2bd`, is
the prospective first pilot item, with no identified pilot-quality veto. The pilot is YouTube Shorts only, initially
three controlled public items at no more than one per week. One item is an observation, not proof of product or
audience fit. Readiness PASS authorizes neither implementation nor transfer nor publication. Broad public launch,
Production #6 remains absent. Migration 25 exists in source/tests only, not in the verified persistent runtime.

Every item needs one **exact founder publication approval before platform transfer**. The frozen package and decision
bind the exact `FinalMediaArtifact` and SHA-256, package version/digest, platform and channel ID, public title,
description, relevant tags/hashtags, language/locale, caption artifact, cover/thumbnail choice, audience and
compliance declarations, private-first requirement, approved transfer and public-transition routes, pilot slot, and
approved publication time/timezone or bounded manual execution window. A changed proposition requires new approval;
safe retries of the same approved operation do not. Readiness, editorial or render acceptance is not publication
authority. Before any mutation, authenticated OAuth channel identity must independently resolve unambiguously to
`UC1cX-OTF9-LZeNo5TaFgrgQ`. A valid Google token, matching handle, public channel lookup or Studio access alone does
not prove API authority. Wrong or ambiguous channel fails closed.

## Minimal execution and conceptual persistence

For three items, use explicit local CLI/service operations backed by durable SQLite state. Long-running uploads and
polling do not run inside the existing synchronous `HTTPServer`; its initial publishing surface is read-only. Reserve
and record consequential operations in short DB transactions, then perform network I/O outside transactions. Use
bounded polling/retries and local concurrency protection. No general worker, queue or publishing scheduler is needed.
Keep the boundary extendable without building speculative infrastructure.

The separately authorized additive Migration 25 preserves these **semantics** in source, not in a deployed pilot:
immutable `PublishingPackage`; immutable/append-only `PublicationGateDecision`; durable
`PublicationOperation` and append-only `PublicationOperationEvent`; stable `PlatformPublication` remote identity;
append-only `PublicationStatusSnapshot`; actual public-publication `PublicationReceipt`; append-only
`PerformanceSnapshot`; immutable/versioned `LearningAssessment` with exact links to supporting observations; and an
explicit record when a later content decision applies an assessment. Exact keys, fields and constraints are encoded
in source Migration 25; its deployment and any real adapter remain separately gated. Existing migrations 1–24 and
production artifacts are unchanged.

Keep distinct what Conveyor **intended**, what the founder **approved**, what external action was reserved and
attempted, whether its outcome became **uncertain**, which remote object was identified, what remote state was
observed, whether/when it became public, what performance was measured, what interpretation was made, and whether
that learning influenced a later content decision. Never collapse these into one mutable publication row.

Conveyor owns package, authority, operation identity, lineage, remote-object linkage, observations, receipts and
learning. A narrow replaceable YouTube adapter owns OAuth integration, request/resource schemas, resumable-upload
mechanics, processing/privacy semantics, captions/thumbnail mechanics, analytics queries and YouTube error
classification: **CHANGE WITHOUT REBUILD**. Do not build a generic social-network framework.

## External-action recovery and Studio routes

**Local idempotency is not remote exactly-once execution.** Before a consequential mutation, reserve a deterministic
durable operation identity. Duplicate commands resolve or reconcile that operation instead of creating another
external action. An ambiguous upload outcome is not failure. If success cannot be established, block as
`outcome_unknown` (or equivalent) and reconcile before another upload. Never automatically restart a transfer where
doing so could create a duplicate remote video.

Resumable-upload session information is protected operational state, separate from ordinary provenance. Preserve
enough state securely to resume an interrupted upload using YouTube's **acknowledged byte range** as authority.
Tokens, authorization headers and raw session URLs belong neither in Git nor ordinary provenance. Exact protected
storage and recovery protocol are later implementation decisions. [YouTube resumable-upload protocol](https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol).

Studio execution is a first-class controlled route: both **approved Studio private upload** and, for an eligible
ordinary private video, **approved Studio private-to-public transition**. Record the manual action, founder attestation,
remote identity and subsequent independently observed state honestly; do not claim Conveyor performed the click.
An upload locked private because it came through an unverified API service cannot necessarily be released in Studio.
Current YouTube guidance requires re-upload through a verified API service or YouTube's own app/site. Preserve the
blocked remote object and seek an explicit recovery decision before any replacement upload. Do not infer authority
for a duplicate from the original package. [YouTube private-lock guidance](https://support.google.com/youtube/answer/7300965?hl=en).

Founder-operated OAuth 2.0 should use maintained Google OAuth libraries and only scopes needed for the current
capabilities: authenticated channel verification, aggregate analytics read and separately approved video/caption/
publication mutations. Client configuration, tokens and protected upload-session material remain outside Git and
ordinary provenance. Wrong channel, expired authorization or revoked consent stops mutation. OAuth is not implemented
by this document.

## Observation, retention and learning

Collect aggregate content-level observations at nominal checkpoints approximately 24 hours, 72 hours, 7 days and
28 days **after actual public publication**. These are collection checkpoints, not guarantees of exact elapsed-time
analytics coverage. Each `PerformanceSnapshot` distinguishes nominal checkpoint, due time, collection time,
requested coverage, returned coverage and each metric's availability/maturity. YouTube may return results only
through the latest reporting date for which requested metrics are available. Missing or immature data is **not zero**.
[Analytics query coverage](https://developers.google.com/youtube/analytics/reference/reports/query).

Preserve supported raw platform metrics and authored qualitative interpretation. Do not create custom engagement,
conversion or composite performance metrics from YouTube API Data unless the relevant additional-derived-metrics
permission has actually been obtained; none is established. No viewer identities, personal viewer data or routine
comment-text ingestion. [Developer policies](https://developers.google.com/youtube/terms/developer-policies) and
[additional derived-metric policy](https://developers.google.com/youtube/terms/derived-metrics-policy).

Append-only Conveyor-authored provenance does **not** grant indefinite retention of YouTube API Data. Authorized
statistics may be retained while consent remains valid and required periodic authorization/video checks occur;
other API Data needs refresh or deletion under applicable policy. Revocation and deletion requests create separate
deletion obligations. Future implementation must allow provider data to be removed, including disallowed disguised
hashes/tombstones, while retaining permissible authored audit evidence. This is an explicit policy exception to
ordinary immutability, not a complete legal-policy implementation. [YouTube API-data policies](https://developers.google.com/youtube/terms/developer-policies).

One public item remains an observation. Weak evidence may create a hypothesis; repeated comparable evidence is
required before bounded routine production changes. Consequential brand, editorial or cadence changes require
founder review. A later decision that actually applies a learning must cite its assessment and exact supporting
observations without rewriting historical production. Weak audience performance is learning, not a technical blocker.

## Deferred infrastructure and separate debt

This pilot currently justifies no general worker/queue, publishing cron framework, autonomous release,
multi-platform social abstraction, TikTok/Instagram adapters, enterprise secret system, webhook infrastructure,
comment ingestion/moderation, viewer-level data, ML optimiser, automatic strategy rewriting, distributed locks,
microservices or cloud orchestration.

This reconciliation corrects `database/README.md` drift about Migration 24. The older instructed-Marin source method
is separate technical debt to correct before any newly authorized production that invokes narration; unchanged
accepted Production #5 must not regenerate narration for publishing. Production #5's historical render-era
“approval pending” metadata remains untouched; its later canonical acceptance is linked additively, while
publication requires its own new exact founder decision. Uninstructed OpenAI `gpt-4o-mini-tts-2025-12-15` / Marin
remains the provisional production-development baseline, not the permanent narrator. No tested instruction is a
universal default; Stage-1 experimentation is paused and narrator quality remains passage-dependent.

Conservative Stage-1 exposure is `$0.19694332 / $0.50`; `$0.30305668` remains unspent. The active quality envelope
is `$7.62694332 / $10`; `$2.37305668` remains. Remaining budget is not spending authorization.

The first offline source implementation now exists. The next possible separately authorized step is live **read-only
OAuth/exact-channel preflight**, not upload or publication. This architecture document authorizes no live YouTube
action and no public publication.
