# Conveyor Business and Vendor Strategy

## Status and authority

This document is **CANONICAL BUSINESS-STRATEGY AUTHORITY** for Conveyor / SimilarStoic.

It governs build-vs-buy, provider selection, external SaaS/API use, cost discipline, portability and commercial investment decisions. It does not itself authorize any provider integration, subscription, spend, architecture change, production, publication or milestone. Those remain subject to the existing founder + ChatGPT decision and implementation gates.

The governing engineering/product principle remains **CHANGE WITHOUT REBUILD**. This document extends that principle to vendors and commercial capability choices.

## Core business principle

Conveyor should use the combination of internal capability and external providers that produces the best business outcome for SimilarStoic, subject to a hard quality floor and without creating unnecessary dependency.

> **Quality is non-negotiable. Cost efficiency is mandatory. Vendor loyalty is not.**

> **Build differentiated intelligence; integrate commodity capability when it makes business sense.**

> **Do nothing merely because it is possible. Every addition must improve quality, economics, speed, reliability, learning or strategic capability enough to justify itself.**

Conveyor is not required to own every underlying model, renderer, crawler, scheduler, analytics transport or infrastructure component. It should own the durable state, decision logic, provenance, quality standards, business rules and SimilarStoic-specific intelligence that make the operating system valuable.

External products may be used when they materially improve the product or economics. They must be treated as replaceable capability providers rather than permanent structural dependencies wherever practical.

## Quality before cheapness

Cost efficiency must never be achieved by lowering the accepted SimilarStoic quality bar.

A cheaper option is preferable only when it meets the required quality, reliability, provenance and strategic constraints. If a more expensive provider or tool produces a materially better accepted product, saves substantial founder/engineering time, increases reliable throughput, improves learning or supports materially stronger revenue/profit, the higher cost may be the better business decision.

Conversely, an inexpensive tool that adds complexity, weakens quality, creates lock-in or saves little useful work is not automatically cost-effective.

The objective is not minimum spend. The objective is **maximum sustainable business value for acceptable cost without sacrificing product quality**.

## Investment and scale

Recurring software/provider cost should be judged against the value it enables, not against an arbitrary preference for low monthly spend.

A combined provider/tool stack costing hundreds of pounds per month can be a sound investment if it reliably supports substantially greater high-quality output, saves material labour, accelerates learning, improves revenue generation or increases profit enough to justify the cost.

As SimilarStoic scales, decisions should increasingly use metrics such as:

- cost per accepted production;
- cost per published production;
- founder hours saved;
- engineering/maintenance time avoided;
- accepted-production throughput;
- provider retry/failure rate;
- revenue per production and per month;
- gross contribution / margin after production-tool costs;
- payback period for recurring tools or infrastructure;
- reliability and operational risk;
- measurable quality uplift.

Raw subscription price alone is not an adequate decision metric.

## Build vs integrate decision rule

For each required capability, first define the capability Conveyor must control. Do not begin from an assumption that Conveyor must build the implementation itself.

Evaluate external integration and internal build against the same criteria:

1. **Quality** — does it meet or exceed the accepted SimilarStoic quality bar?
2. **Business economics** — what is the true cost, including subscription/API spend, engineering, maintenance, retries and human attention?
3. **Strategic differentiation** — is this capability part of Conveyor's defensible intelligence or commodity infrastructure?
4. **Portability** — can the provider be replaced without rebuilding unrelated Conveyor systems or losing durable state?
5. **Scale economics** — does buying remain sensible at expected volume, or does internalizing become materially better later?
6. **Reliability and control** — does the option reduce operational risk and give enough control over output, provenance and failure handling?
7. **Security/privacy/compliance/licensing** — are data use, credentials, rights and commercial terms compatible with Conveyor / SimilarStoic?
8. **Evidence of value** — is the option being adopted because it demonstrably improves an outcome, rather than because the capability is novel or available?

Choose the option with the best overall business case. Revisit the decision when market prices, provider quality, scale, reliability or product requirements materially change.

## Provider-neutral capability architecture

Where practical, Conveyor should define narrow internal capability contracts and keep provider-specific implementation behind them.

Examples include:

- discovery / trend and audience-signal sources;
- frontier-model / reasoning providers;
- search and research providers;
- image / visual generation;
- design and rendering;
- speech synthesis / narration;
- transcription / alignment;
- publishing and scheduling;
- analytics / performance-data ingestion.

The existence of an external provider does not require using it. The existence of an internal implementation does not require retaining it forever.

A provider should be replaceable when a cheaper, higher-quality, more reliable or strategically superior option becomes available, subject to bounded validation before switching.

The desired change path is:

> **change provider -> validate quality and economics -> update the bounded adapter/configuration -> continue operating**

not:

> **change provider -> rebuild Conveyor**

## What Conveyor should own

Conveyor should preferentially own the durable, differentiated parts of the operating system, including:

- canonical project and production state;
- SimilarStoic editorial and brand canon;
- research/evidence and claim provenance;
- content and quality gates;
- accepted visual authorities and production vocabulary;
- narrator-quality requirements and accepted narrator identity/configuration provenance;
- spend governance and cost evidence;
- exact artifact lineage and hashes;
- publication authority and package identity;
- performance-learning rules and durable learning evidence;
- provider-selection logic where multiple providers are viable.

External services may perform commodity or specialist execution beneath those controls when that is the stronger business choice.

## No integration for its own sake

Conveyor must not become a collection of SaaS integrations or AI features.

Every integration, subscription, API, internal subsystem or automation must justify itself by improving one or more of:

- accepted output quality;
- cost efficiency;
- production speed / throughput;
- founder or engineering time;
- reliability;
- strategic capability;
- learning quality;
- revenue or profit potential.

If an integration cannot establish a credible benefit, do not add it.

Existing third-party products discovered during research or ordinary use should be treated as **candidate capabilities to evaluate**, not as implied roadmap commitments.

## Current application

This strategy does not change the current canonical product objective. **SimilarStoic narrator naturalness remains the next focused pre-launch objective.**

The narrator experiment should follow the same business principle: evaluate the strongest suitable providers, preserve provider-neutral provenance and CHANGE VOICE WITHOUT REBUILD, spend only what is justified by the quality question, and do not adopt a provider merely because it offers a feature.

Production #6, publishing implementation, Migration 25 and unrelated capability integrations remain outside this business-strategy canonicalization unless separately authorized.

## Founder authority

The founder remains final authority for product direction, consequential commercial commitments, quality acceptance, exceptional spend, provider lock-in decisions and public actions.

ChatGPT remains product architect / roadmap and specification steward and should carry this business principle into future build-vs-buy, vendor, architecture and cost recommendations.

Codex or another implementation agent may inspect or implement only bounded decisions already authorized through the existing governance process; it must not independently select a vendor, expand scope, purchase a service or reinterpret this strategy as authorization to integrate new products.
