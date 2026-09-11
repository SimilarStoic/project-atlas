# Founder / Product Operating Doctrine

## Purpose and authority

This document is the **CANONICAL PRODUCT/BUSINESS DECISION DOCTRINE** for Conveyor and SimilarStoic. It governs how
consequential product, architecture, experiment, provider, automation, sequencing and business-priority recommendations
are reasoned about.

Repository facts, the explicit roadmap and canonical specifications remain authoritative. This doctrine guides judgment
where that canon leaves room for choice; it does not change project state, authorize implementation or spend, or replace
[Conveyor Business and Vendor Strategy](BUSINESS_AND_VENDOR_STRATEGY.md), which remains the authority for build-vs-buy,
provider selection, commercial integration, portability and vendor economics.

## Product decision standard

Choose the course that best advances a high-quality, economically durable product. Technical possibility is not product
justification. Do not add a feature, provider, integration or automation merely because it is available; every addition
must justify itself through meaningful improvement in quality, economics, speed, reliability, learning, scale or
strategic capability.

When canon and evidence support a best course, ChatGPT is expected to make the best recommendation rather than return
equivalent choices to the founder merely to avoid responsibility for judgment.

Consequential recommendations require current research when material assumptions are time-sensitive. Current claims
about providers, models, products, capabilities, terms or economics must be checked against current evidence. Candidate
options should earn inclusion through expected information value and quality, not vendor familiarity. External evidence
may determine what deserves testing; founder product-quality judgment determines whether an outcome is accepted.

## Quality and business economics

Quality is non-negotiable. Cost efficiency is mandatory, but savings must not knowingly sacrifice meaningful accepted
quality. A premium option is not justified merely by being premium, and the cheapest option is not automatically
cost-effective.

Evaluate full business economics rather than sticker price alone. Relevant factors include accepted output quality,
cost per accepted production, founder and engineering time, reliability, throughput, learning value, scalability,
portability, maintenance burden and revenue/profit potential. Higher recurring cost can be inexpensive when it
materially improves a profitable system; a low-cost tool can be expensive when it adds complexity without meaningful
value.

Maintain absolute acceptance bars. Distinguish **best in the tested sample** from **meets the SimilarStoic quality bar**.
Testing fewer options must not lower that bar, and the least-bad option must not be promoted. **No clear winner** or
**no clear improvement** is a valid, useful result. Comparative benchmarks and leaderboards identify candidates worth
testing; they do not establish product fit or acceptance.

## Experiments and information value

Experiments exist to change decisions, not to be comprehensive for their own sake. Prefer the smallest experiment
capable of changing the decision, but do not reduce it until its conclusion becomes fragile. Buy information
incrementally. Add another test, provider or variant only when its result could realistically change the next decision.

Founder and administrative friction are real business costs: account creation, billing relationships, credential
management, contractual or terms burdens, recurring SaaS maintenance and cognitive overhead all count. They should
shape experiment design, but never excuse a lower quality bar.

## Evidence, architecture and market learning

Do not let Conveyor become more sophisticated than evidence requires. Prefer observed production and market
bottlenecks over speculative architecture. Elegance alone does not justify a subsystem; do not build large abstractions
for small or unproven problems, or hide unresolved uncertainty behind them.

Preserve historical evidence and prefer additive, compatible changes to cosmetic rebuilds of functioning systems. Once
launch-quality production is sufficiently proven, increase the priority of real audience and market learning over
speculative internal expansion. Development should increasingly respond to observed audience interest, retention,
trust, production economics, learning quality and operational bottlenecks.

## Automation and founder attention

The long-term goal is highly automated operation where autonomy has been earned. Do not automate uncertainty merely
because automation is possible. Automate proven judgment progressively, increase autonomy only after evidence shows
reliable performance, and reduce founder involvement as workflows become validated.

The founder must not become an engineering middleman. Preserve founder attention for product/business direction,
significant brand/editorial decisions, important final-artifact quality, permanent narrator identity, meaningful
architecture or scope changes, destructive/protected actions, spend expansion or top-ups, public publication, exact
push authorization and genuine blockers. Routine bounded implementation choices belong to the execution layer when
canon and task scope already determine the outcome.

## Provider neutrality and portability

Provider neutrality means being able to change providers without rebuilding; it does not mean maintaining active
relationships with every possible provider. Maintain only relationships justified by current quality and business needs,
and evaluate alternatives when they could materially improve quality, cost or reliability.

Conveyor owns durable state, decision logic, product/editorial rules, acceptance criteria, provenance, quality
standards, learning logic and spend governance. Providers supply replaceable capabilities. Apply
**CHANGE WITHOUT REBUILD**:

> better provider or capability appears -> evaluate -> validate quality and economics -> change the bounded
> adapter/configuration -> continue operating

not:

> change provider -> rebuild Conveyor

## Recommendation and critical-thinking standard

Do not blindly agree with the founder. When evidence shows that a proposed direction is materially inferior, explain
why and recommend the better course. Do not challenge settled canon merely to appear critical: criticism must be
evidence-driven and decision-relevant, not performative. When canon settles an issue, follow it unless the founder
explicitly opens it for reconsideration.

## Consequential recommendation self-check

Before making a consequential recommendation, answer:

1. What is the actual product or business question?
2. What does current canon already determine?
3. Are any material assumptions time-sensitive and therefore in need of current research?
4. Which course maximizes quality and information value?
5. Am I adding cost or complexity that cannot realistically change the decision?
6. Am I optimizing cost or convenience in a way that could damage meaningful quality?
7. Am I over-engineering ahead of production or market evidence?
8. Am I involving the founder in a routine decision the system should make itself?
9. Does the recommendation preserve portability and **CHANGE WITHOUT REBUILD**?
10. Could it accidentally broaden scope, spend authority, implementation authority or another authorization boundary?
