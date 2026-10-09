# SimilarStoic Public-Launch Creative Calibration

> **Bounded methodology with historical status notes.** This file preserves its calibration method and dated gates;
> it is not current production-status authority. Resolve current operation, including P6 status, through
> [`CONVEYOR_CURRENT_STATE.md`](CONVEYOR_CURRENT_STATE.md).

## Founder-approved production method

The founder-approved production-quality reference is
`output/production-tests/next-private-production/next-private-production.mp4` (38.720 seconds; SHA-256
`FE99094664FF2F3514BC4D66485FD24BDD2A63591811F98EE6C89DF0DC566B3A`). It is suitable for the public SimilarStoic
main channel, although this decision does not publish it. Recreate its ingredients and flow on new content; do not
reuse its exact topic, script, or scenes. Later static-mascot and persistence-heavy comparison tangents are not part
of this approved method.

### A. Reusable SimilarStoic production invariants

- Generate dynamic, integrated full-scene action illustrations in which the narrator explains and the hamster/world
  illustrate. Preserve expressive facial and pose variation, movement through the composition, meaningful
  scene-to-scene progression, and sparse warm off-white negative space.
- Resolve the default `VisualStyleProfile` `visual-style-profile-similarstoic-core-v4`, `CharacterProfile`
  `character-profile-similarstoic-hamster-core-v1`, latest exact-profile `CharacterReferenceSet`
  `character-reference-set-similarstoic-hamster-core-v2`, and global `VisualReferenceAuthority`
  `visual-reference-authority-similarstoic-global-illustration-v1`. Reference set v2 is the identity reference
  `asset-similarstoic-control-v1-reference-anchor` (SHA-256
  `11332518CDACE450F8E432FE8CB3558EA2374CF0273F94973912E914CEE66956`) followed by the approved multi-pose identity
  reference `asset-similarstoic-core-identity-multipose-a5564bd0` (SHA-256
  `D3ACB16AF30B9A5ACA29E92E2E8F19D7B5A21DF4B8E572DE054756CA23321CC4`); the global style reference is
  `asset-visual-authority-default-scene-language-v1` (SHA-256
  `989E0DA7B273A42F0BF8C229C1510B904902B1EEF3336E626705966E6048CCB2`). Existing generation resolution already
  selects these authorities; do not create a parallel canon or style-memory system. Runs frozen on core-v3 stay
  bound to it; they are not migrated or rebound.
- The executable visual and character grammar is `VisualStyleProfile` `visual-style-profile-similarstoic-core-v4`
  (seeded in `src/project_atlas/persistence.py`, composed into every generation prompt by `PromptComposer`). Do
  not restate its rules here or in production packages. Each beat's AssetSpec adds only the beat-specific action,
  setting and expression line.
- Authoring: give every character beat exactly one explicit expression line naming brows and mouth, for example
  `Expression: careful. Brows level, mouth: small closed neutral line.` The v4 expression rule makes that line
  authoritative. Expressive variation, including furrowed or angled-down brows, is valid when the line asks for it.
  Specify props that could carry markings (phones, calendars, signs) as plain or blank. Vary the hamster's position,
  pose and staging from beat to beat rather than repeating one framing.
- In v4, the `character` asset type means the canonical SimilarStoic full-scene character asset path. A future
  non-full-scene character asset (for example a layered sprite) needs a distinct asset type.
- At acquisition, judge every raw image for authority/style match, semantic action, believable scale/world logic,
  crisp intentional edges, forbidden text/humans, and obvious mascot drift in head/body ratio, torso/silhouette,
  face/ears, or bag. Reject a weak source before rendering; do not reject useful expressive variation.
- Use approved Inworld `inworld-tts-2` SYSTEM voice `Daniel`, `en-US`, balanced delivery, 48 kHz WAV, speaking rate
  1.0, normalization on, enhancement off, and word timestamps. The persisted direction is relaxed, intelligent,
  conversational, grounded, lightly amused, confident without selling, with understated humour and natural
  clause-level pauses; never announcer, corporate presenter, finance guru, advert, podcast intro, or hyperactive
  creator. Do not add, omit, or paraphrase script words.
- Timeline weights express semantic intent; the first candidate uses narration-aligned scene boundaries. Use
  purposeful transitions, mobile-readable captions, and the established render path. Review acquisition quality
  before assembly and the complete result before founder review.

#### A.1 Founder-validated findings (Productions 8–10)

Each finding is recorded once, with the single executable place that now enforces it. Topic-specific P9 content
(the BNPL shop and kitchen, exact beat wording) stays in section C.

| Finding (founder review) | Generalized rule | Enforcement point | Evidence |
| --- | --- | --- | --- |
| Beat images drifted between locations | A recurring location is generated from one approved environment anchor | `environment_family` `VisualReferenceAuthority` per location, resolved by `GenerationService` | P8 Attempt 2; P9 shop/home anchors |
| Off-aspect source images reached review | Full-frame sources are 9:16 before founder review; technical failures are reacquired automatically | Acquisition admission (`full_frame_aspect_error`) in `production.py` | P8 Phase 1B |
| Doubled or toothed mouths, contradictory expressions | One readable expression and one simple toothless mouth; the beat's expression line is authoritative | core-v4 character rules `expression`, `mouth` plus the per-beat expression line | P9 Attempt 1 beats 3, 4, 7, 8; Attempt 2 accepted |
| Doubled toes, malformed fingers | Clean paws with separate digits, clean toes | core-v4 `paws_and_feet` | P9 Attempt 1 beats 5, 8 |
| Strap stopping at the neck or missing | One continuous strap from shoulder to bag | core-v4 `strap` | P9 Attempt 1 beat 7; Attempt 2 round 1 beat 7 |
| Torso or legs stretched to reach furniture | Compact proportions; furniture and props sized to the hamster | core-v4 `proportions` | P9 Attempt 2 round 1 beats 2, 8 |
| Duplicated objects or features | No duplicated limbs, facial features or objects | core-v4 `duplication` | P9 Attempt 1 |
| One identity image under-constrained poses | Identity plus approved multi-pose reference | Latest `CharacterReferenceSet` (v2) | P9 Attempt 2 |
| Props invited readable digits, dates or lettering | No embedded text of any kind in generated source art; props stay allowed with blank or non-legible surfaces | core-v4 global avoid (unconditional text ban) and global `detail`; authoring asks for blank props | P9 handset, post box, calendar |
| Narration needed approval after images, but runs were frozen without it | A recorded founder action may authorize narration post-acquisition. Legacy requests take one call; delivery-policy requests freeze N = 1–3 automatic takes. New SimilarStoic runs default to `similarstoic-daniel-v2`, `similarstoic-sentence-delivery-v1` prefer, N = 3 | `authorize_narration`; new-run narration default in `start()` (`production.py`) | P9 Attempt 2; narration-tests 2026-10-07-sentence-delivery |
| Captions ran ahead of speech and across scene changes | Pause-aligned phrase captions from the exact narration | `speech_timing.py` via `create_persistent_scene_snapshot` | P9 render v3 |
| Estimated beat timing did not follow the narration | Scene boundaries at the pause ending each scene's narration excerpt (matched pause midpoint, else estimated word gap), applied to the first candidate for `scene_timing: narration-aligned-v1` runs (the default for new runs); later retimes remain founder-approved | `_ensure_snapshot` + `recommend_retime`/`retime` | P8 v2, P9 v2; P10 v1; P10-R2 artifact-2 |
| A provider network failure interrupted acquisition | A technical provider failure stops the run; resume needs explicit founder authorization | Lifecycle `failed` state and `resume` | P9 Attempt 2 beat 8 |
| A sourced figure was stated with a different category than its source ("default tariffs: around 20 million") | A Script figure's stated qualifier must match the frozen source quote; mismatches are flagged for editorial judgement before synthesis | Editorial Readiness evaluator v2 (`SCRIPT_NUMBER_QUALIFIER_MISMATCH`, `script_preflight.py`); Approve over findings needs a comment | P10 Script C5 |
| Full-frame review missed duplicated spouts and a malformed arm | New-run acquisition review inspects props, and limbs and strap for character beats, zoomed in and bound to the asset SHA-256 | v2 acquisition review contract in `review_acquisition` (`production.py`) | P10 acquisition review |
| The HOME post box was reused as an energy meter | Anchor fixtures keep their identity; any new object is drawn separately | Structured `fixtures` on the pinned `environment_family` authority, one deterministic prompt clause, and per-fixture attestation in the v2 review | P10 HOME beats |
| Same-room beats drifted in geometry and furniture scale | The same environment plus viewpoint locks room geometry, furniture scale and fixture placement | Frozen `environment_pins` with `viewpoint:<key>` plates in generation and the v2 `geometry_compared_with` set | P10 HOME beats |

Open finding (not yet a rule): with Daniel, a fixed term such as "Buy now, pay later" was voiced as separate
utterances (a pitch reset and an unpunctuated pause). The P10 Script contained no comma-bearing fixed term, so it was
not evaluated. Fixed terms on the narrator's list are now flagged before synthesis by the editorial readiness
evaluator v2. No speech-form change is implemented; captions and parity checks still derive from the approved
Script.

#### Environment plates

Room plates (character-free environment anchors) carry the same-illustrator treatment into every beat generated in
that room, so they meet the same standard as finished art.

- **Authoring rule.** A `viewpoint:<key>` member role selects a reference plate; it is never a camera instruction.
  Room-plate descriptions name topic-specific materials and objects, prescribe no camera angle, and use "plain" only
  for surfaces that must stay blank (no readable text). Beat props stay out of the plate.
- **Plate review gate.** Before founder approval, place each candidate plate on a contact sheet beside the approved
  P9 home and shop anchors and two approved baseline beats, and record PASS or FAIL for linework, palette, depth,
  shadow, texture and richness. A FAIL blocks proposal for approval. Fixture presence, no text and zoomed defect
  checks remain required in addition.
- **OPEN conflict (not resolved).** Core-v4 wording ("shading: no soft or tonal shading"; "textured colouring or
  fills" and "realistic depth rendering" under avoid) conflicts with the approved exemplars, which show soft cast
  shadows, material texture and room depth. Until a founder decision reconciles them, the approved exemplars listed
  under "Approved visual evidence" in [`CONVEYOR_CURRENT_STATE.md`](CONVEYOR_CURRENT_STATE.md) are the human
  quality benchmark.

### B. Useful production-shape defaults

- The approved evidence uses eight meaningful narration-led visual beats over 38.720 seconds. Treat this as a useful
  density reference, not a rigid duration or beat-count requirement.
- Its eight beat durations were weighted by semantic-clause word counts, with 250 ms crossfades at scene boundaries.
- Captions use `similarstoic-social-mobile-v3` styling (Arial Bold 92 at 1080x1920, at most two lines, warm light
  backing, safe lower/middle/upper placement changed only at scene boundaries). The approved reference used
  deterministic five-word chunks; canonical renders now use pause-aligned phrase captions
  (`pause-aligned-phrase-captions-v1`; see `CONVEYOR_CURRENT_STATE.md`). Provider word timestamps, once persisted,
  feed the same cue builder.
- The persisted image executions used `openai` / `gpt-image-2`, PNG output, and two reference images per request.
  Eight initial acquisitions passed; there were no retries. Provider/model choice remains provenance, not permission
  to spend or a mandate to generate unnecessary alternatives.
- The final render used repository-bundled FFmpeg 9.0.1: 1080x1920 at 30 fps, H.264 `libx264` CRF 18 / medium /
  `yuv420p`, AAC mono 48 kHz at 192 kbps, and fast-start packaging.

### C. Topic-specific evidence that is not reusable canon

The emergency-buffer topic, approved script, clause wording, boiler/bad-Tuesday example, savings destination and
first-step imagery, regular-saving chute, debt-leak ending, and all eight exact scenes belong only to this video.
Future productions must create new researched claims, scripts, semantic beats, and scene content while retaining the
method above.

Character continuity, sufficient narration-driven scene density, and factual source attribution remain continuing
improvements, not launch blockers. Research provenance already belongs in Conveyor's `ResearchPack`, `Claim`,
`Source`, `ClaimEvidence`, and `ScriptClaimSet`; the precise remaining integration is to carry the supporting sources
from an approved script claim set into publishing-package source/credit metadata. That is a bounded extension point
for Claude, not authority to introduce a new provenance subsystem or reopen the visual architecture.

The existing generation service already defaults to the approved visual-style and global-authority IDs and resolves
the latest exact-profile character reference set. The production-shape recipe above is not yet a first-class lifecycle
selector: a canonical v2 caller must still supply the narration-led `VisualPlan`, per-beat `AssetSpec` instructions,
and semantic timing explicitly. Claude's bounded operational integration point is to expose this recipe through the
existing production/lifecycle configuration while retaining these existing authority records and provenance models;
it is not a new canon, style-memory, or mascot subsystem.

## Entry-gate reconciliation — 23 September 2026

The [verified pilot/runtime record](../CURRENT_STATUS.md#verified-pilot-and-runtime-state--23-september-2026)
establishes the successful private systems-proof prerequisite from existing durable ledger evidence (Case A).
No duplicate events were appended. P5 v4 and package v2 are unchanged; the upload is reconciled, and its publication
approval has subsequently been revoked. The reserved-only and future-revocation wording below is historical.
Daniel remains approved. Cell 1 has separate bounded zero-spend execution authority, subject to asset/quality gates;
this does not approve any resulting cell or canonize a visual grammar. No production or public release is authorized.

Current narrator milestone, 22 September 2026: [Daniel is founder-approved for production](SIMILARSTOIC_PRODUCTION_NARRATOR.md)
after short-cell casting and independent longer generalisation. Narrator search below is historical methodology,
not an instruction to continue casting. Remaining calibration, production generation and public release are separately
authorized; this selection does not reopen visuals or approve a newly assembled production.

Founder-approved future methodology, 16 September 2026. Creative Calibration is the intended quality phase after
**successful exact private remote verification of Pilot Item #1**. This specification grants no experiment,
generation, provider, subscription, spend, production or publication authority.

Creative Calibration is not Production #6, not an ordinary full production and not automatically authorized by the
private pilot. Its purpose is to discover a repeatable SimilarStoic narrator and visual production grammar before
investing in an ordinary public full-video production.

## Entry gate and product sequence

Arrival of 22 September, an upload attempt, incomplete upload, ambiguous outcome, unverified remote object, metadata
mismatch or failed observation does not satisfy the entry gate. If exact private remote verification does not succeed,
the publishing-proof phase remains unresolved until separately reconciled.

> successful private systems proof → separately authorized creative calibration → stable narrator + visual grammar →
> public-launch master → exact founder quality review → separately authorized public release

## Creative north star

> Current SimilarStoic visual world + F-level narrator-performance quality + B/C visual thought-density + E
> scene-development mechanics + D recognisable crude charm + A explanatory depth

The [Creative Reference Set](SIMILARSTOIC_CREATIVE_REFERENCE_SET.md) governs those logical references and their
anti-copying boundary. The existing SimilarStoic hamster, art, backgrounds, visual-reference authorities and
same-illustrator coherence remain the visual foundation; F is a narrator-performance benchmark, not a visual target or
an identity to imitate.

**THE NARRATOR EXPLAINS. THE HAMSTER ILLUSTRATES.**

**THE COMPLETE VIDEO MUST BE UNDERSTANDABLE FROM AUDIO ALONE.**

The narrator carries the argument. The visuals continuously reinterpret it. Product shorthand: **fast-moving
illustrated SimilarStoic storytelling with excellent audio**—not “highly animated AI cartoons.”

## Attention and AI-quality doctrine

Legitimate attention mechanisms include curiosity, unresolved questions, progression, expectation/payoff, meaningful
visual novelty, pattern breaks, humour, surprise, momentum, narrator rhythm, deliberate pauses, intensity variation,
recurring devices, intermediate rewards and conceptual conclusions.

They do not authorize deception, rage bait, empty stimulation, manufactured urgency, misleading hooks, unsupported
claims, factual distortion, generic motivational filler or optimization for views at the expense of trust. Visual
change follows meaning, narrative structure, attention, rhythm and clarity; no universal cut interval is established.

**AI can be an implementation detail; it should not be the main thing the viewer notices.** AI assistance is not the
problem; generic, inconsistent, randomly generated, cheaply assembled or art-direction-free output is. Finished work
should feel intentional, coherent, recognisable and deliberate. Legal/platform disclosure duties remain authoritative.

## Primary integrated unit: final-quality cells

Use approximately **6–9 seconds of final-publication-quality output**, with natural spoken boundaries taking priority
over an exact duration. Save money by shortening representative evidence, not by lowering its quality.

Where relevant, a judged cell includes final-quality SimilarStoic artwork, the actual narrator candidate, intended
visual grounding, compositing, transitions, captions, timing and render quality, plus music/SFX only where they belong
in the intended product. Founder question: **Would I be happy if this exact quality appeared in the public video?**

Review cells holistically against applicable dimensions:

- narrator naturalness, clarity, rhythm, momentum, engagement and sustained listenability risk;
- SimilarStoic recognisability and preservation of hamster/art/background identity;
- visual thought-density and the effectiveness of scene changes versus mutations;
- spoken-idea clarity, audio-only completeness and visual reinforcement;
- charm, personality and humour where relevant;
- intentional rather than generic-AI appearance;
- caption integration and absence of distracting narration/visual defects;
- plausible sustainability for longer content.

Mark genuinely irrelevant dimensions **NON-APPLICABLE**. These are review dimensions, not an automatic weighted score.
Founder comparative judgement and explicit rationale remain primary unless a later bounded experiment predefines a
quantitative decision rule.

## P5 v4 visual non-regression gate

Production #5 v4 is the current accepted SimilarStoic **visual-production quality baseline** for Creative Calibration.
It remains the hard control condition until the founder explicitly replaces it with a better accepted baseline.

Calibration separates two layers:

- **Layer A — visual production quality:** authored-frame coherence, shared-illustrator treatment, character-world
  integration, physical integrity, [Character Model Continuity](SIMILARSTOIC_VISUAL_VOCABULARY.md#character-model-continuity-gate),
  structural [Persistent Scene Model](PERSISTENT_SCENE_MODEL.md) continuity where the cell deliberately uses a
  continuing world, appropriate richness, caption-profile identity and final composite quality.
- **Layer B — temporal/spatial grammar:** scene progression, composition turnover, persistent visual memory, mutation
  logic, pacing and related experimental variables.

Layer A is a hard prerequisite. Layer B strength cannot compensate for Layer A failure. A treatment is not a valid
final-publication-quality calibration candidate merely because it progresses better while looking visibly weaker than
the accepted baseline.

Where a judged sequence uses a persistent world, individually attractive frames cannot pass Layer A if established
objects, geometry, camera, scale, approved variant content or spatial relationships drift without an authorized cause.
Unchanged content must inherit exactly and adjacent changes must be explainable. This requirement does not force a
persistent-world model onto unrelated single frames.

Apply this gate to every meaningful final state of a final-quality visual-grammar cell:

1. **Direct baseline comparison.** Inspect the actual composite beside representative P5 v4 visual evidence at full
   resolution, ordinary viewing scale/playback and phone scale. Checklist-only approval is insufficient.
2. **Authored-frame test.** The frame must read as one deliberate SimilarStoic illustration, not independent cutouts or
   components arranged on a template.
3. **Same-illustrator coherence.** Character, props, environment, overlays and compositing must remain coherent in line
   weight, texture, rendering density, palette, perspective, polish and applicable lighting/treatment.
4. **Character-world integration.** The hamster must credibly occupy and act inside the illustrated situation. Floating
   props, detached UI modules and pasted character cutouts fail unless an intentionally abstract beat genuinely
   requires that language.
5. **Character Model Continuity.** Where a mascot recurs across materially different states, it must remain the same
   underlying canonical character model across pose, action, expression, crop and scene. Recognisability and plausible
   isolated anatomy are insufficient. Review the complete character, face, body/torso and bag relationship together on
   a cross-state comparison/contact sheet. Legitimate pose, perspective, foreshortening, squash/stretch and approved
   acting deformation remain allowed; unexplained drift in head/body balance, facial construction, silhouette, limbs or
   bag/body anchors is a Layer A failure.
6. **Physical integrity.** Anatomy, contact, occlusion, depth, connected topology and structural geometry must remain
   credible.
7. **Appropriate richness.** Do not remove useful environmental context, semantic objects, depth layers, physical
   relationships or scene specificity merely to simplify repair, reuse available stock or avoid generation. Preserve
   **REPAIR — DO NOT EMPTY**.
8. **Graphical restraint.** Labels, arrows, cards and diagrams may support an illustration, but must not replace a
   physical or illustrated relationship merely because local deterministic assembly is cheaper or easier.
   Intentionally abstract explanatory scenes remain valid where genuinely appropriate.
9. **Caption-profile identity.** Wording and timing parity do not establish visual-profile parity. When
   `similarstoic-social-mobile-v3` is required, inspect the actual bold dark text, warm off-white high-contrast box,
   short one/two-line semantic grouping, safe-zone placement and phone readability.
10. **Progression without degradation.** Every meaningful mutation or cut state must independently retain the quality
   floor. A scene cannot begin at public quality and visibly degrade as states or objects are added.
11. **Reuse with variation.** Reuse succeeds only when the integrated result intentionally advances action, expression,
     prop state, object relationship, crop, composition or visual understanding. Template repetition or pose swapping
     alone is insufficient.
12. **Quality before cost.** If zero-cost reuse or local adaptation visibly falls below the accepted baseline, stop at
     **BLOCKED — P5 V4 QUALITY FLOOR REQUIRES BESPOKE VISUAL WORK**. Do not improvise downward or force reuse to save
     provider cost.
13. **Human visual judgement outranks technical compliance.** Hashes, resolution, successful decode, timing, anatomy
     checks, semantic presence, collision checks and other deterministic QA cannot make a visibly weak frame pass.
     Final judgement operates on the actual composite frame.

For each meaningful state, record `PASS`, `FAIL` or `NOT ENOUGH EVIDENCE` for authored-frame coherence,
same-illustrator coherence, character-world integration, contact/occlusion/geometry, appropriate richness, caption
integration, phone-scale hierarchy, direct P5 v4 equivalence, semantic arrival and progression/visual memory. Where the
mascot recurs, also record one sequence-level Character Model Continuity result supported by the required contact sheet.
Any Layer A `FAIL` blocks grammar selection and founder-review-ready status; Layer B cannot rescue a continuity failure.

Deterministic local work remains valid for bounded compositing, layout, annotation, cleanup, crops, masks, prop-state
changes and other work that preserves this quality floor. It must not become a cost-driven substitute for integrated
visual authorship when the result is visibly weaker.

### Visual Grammar Cell 1 disposition

Visual Grammar Cell 1 is **INVALID FOR VISUAL-GRAMMAR SELECTION — USEFUL PROGRESSION EVIDENCE ONLY**. Both concealed
candidates demonstrated useful progression mechanics but fell below the independent P5 v4 visual-production quality
floor, so no grammar winner may be selected and neither treatment is canonized. The concealed mapping remains private.

Preserve Cell 1 as evidence about coherent composition turnover, persistent spatial memory, cumulative state mutation
and semantic pacing. Those mechanisms remain hypotheses for a future same-cell high-fidelity retest; this decision
does not authorize that retest, a rebuild, generation, provider work or spend.

The controlled comparison failed because zero-spend/local availability became stronger than visual quality; available
components were treated as sufficient final scenes; deterministic compositing exceeded its supporting role; component
provenance was mistaken for perceptual-quality equivalence; technical/checklist QA displaced direct authored-frame P5
v4 comparison; progression displaced scene richness/coherence; component-level checks missed composite-level
Frankensteining; and caption wording/timing parity was mistaken for visual-profile parity. These findings do not reject
deterministic composition generally; they bound it to work that preserves the accepted quality floor.

## Controlled comparisons and founder search

Avoid random candidate batches. Where practical, change one or two meaningful variables:

- narrator comparison: hold passage, visual treatment, timing and other factors constant;
- visual-grammar comparison: hold passage, narrator and art direction constant while varying compositions, mutations,
  annotations, reactions, density or deliberate holds;
- integrated comparison: use the same underlying idea for materially different finished treatments.

Founder judgement may preserve traits across candidates rather than select one whole winner: voice identity, pacing,
opening visual, mutation logic, captions, humour or transitions. The iterative method is:

> generate → compare → eliminate → preserve winning traits → recombine → retest

Repeated founder preferences may become provisional and revisable defaults, not immutable rules.

Test more than dramatic hooks. Representative cells may cover ordinary/sustained explanation, metaphor, reaction or
humour, comparison, diagram, mutation sequence, calmer material and transitions between intensity levels.

## Narrator calibration and generalisation

Narration is the highest immediate public-quality problem; Production #5 v4 narration is not accepted for public
launch. `SS-CR-F-001` is the primary perceptual performance benchmark, never an impersonation target. Do not assume a
new Marin instruction, the incumbent provider or one excellent short sample solves the narrator.

Future separately authorized comparisons should use identical passages where practical and examine naturalness,
clarity, rhythm, pace, emphasis, pauses, phrase variation, confidence, warmth, personality, engagement, fatigue,
robotic cadence and SimilarStoic fit.

Narrator validation has two stages:

1. **Short integrated audiovisual evidence:** immediate naturalness, fit, rhythm and voice/visual quality together.
2. **Longer audio-only generalisation for survivors:** sustained listenability, phrase variation, emotional/rhythmic
   stability, fatigue, robotic cadence and SimilarStoic identity at lower cost than long video.

One short win cannot establish narrator acceptance. Historical Stage-1 evidence remains authoritative that local
improvements can fail to generalise across passages and duration.

## Stitch test and broader generalisation

After multiple cells pass, reuse and stitch approximately four or five winning cells into roughly 30–60 seconds where
practical. Judge continuous pacing, visual coherence, narrator fatigue, repetitive rhythm, transitions, caption
consistency, attention density, recognisability, intensity balance and whether isolated wins become exhausting or
incoherent together.

Do not establish the grammar from one passage or subject. Core narrator and visual mechanics must show usefulness
across materially different SimilarStoic content through bounded high-fidelity evidence; multiple full videos are not
required during calibration.

## Cost and provider doctrine

**Do not save money by making the experiment unrepresentative. Save money by testing fewer seconds and eliminating
weak options earlier.** Use short final-quality cells, cheaper long audio-only tests, controlled comparisons, early
elimination, component reuse and stitch tests. Do not repeatedly generate complete 45–90 second videos while basic
choices remain unsettled. Historical unused budget is not spending authority.

Do not audition a provider merely because it exists. Ask whether it materially improves the quality, capability or
evidence required to clear the public-launch standard. Improve planning, turnover, scene mutation, existing-reference
use, humour, composition and coherence before replacing a preferred visual world for polish. If the narration stack
cannot plausibly meet the bar, a separately authorized small provider-neutral audition may compare identical passages
and eliminate quickly. No provider tourism, subscription, purchase, call or spend is authorized here.

## Public-launch master gate

Only a sufficiently stable formula may progress—under separate authority—to one complete public-launch-quality master.
Unchanged Production #5 v4 need not become public. The future master may rebuild an accepted content foundation with
improved narration, become Production #6 or be another explicitly selected launch item; identity is deferred.

Preserve **CHANGE VOICE WITHOUT REBUILD**: reuse valid accepted script and visual authorities, then regenerate and
revalidate narration, completeness, transcription/alignment, captions, duration-dependent timing, final render,
artifact digest and publishing package. Never reuse timing from materially different narration. Exact founder quality
acceptance of the complete artifact is required before any public publication.

## September 22 private pilot remains unchanged

Production #5 v4 remains byte-identical for the authorized private systems proof, SHA-256
`c35e8e6211ae9bf7bfeb694ec6dbec3c69d822862729d9d9f4440d50028ea2bd`. Do not alter its narration, visuals,
captions, timing or final video. Pilot Item #1 package v2, its approval and the reserved manual upload operation remain
unchanged. The founder-operated Studio window remains `2026-09-22 12:00–13:00 Europe/London`.

The private pilot proves **Conveyor → YouTube → remote verification**, not public creative quality. Successful private
verification does not authorize release. Do not reserve or dispatch a Production #5 v4 release operation; approval
revocation remains a future separately authorized governance action. If verification fails or stays ambiguous, preserve
and reconcile the publishing state instead of advancing merely because the date or attempt occurred.

At this methodology checkpoint, Production #6 was **NOT STARTED / NOT AUTHORIZED**. Creative Calibration was intended before the next ordinary full
production, but successful private verification does not itself authorize calibration execution.

## Future long-form and learning direction

The reference review strengthens a future, unproven 10–20 minute model built from excellent standalone narration,
frequent SimilarStoic illustrations, recurring characters/world, scene mutations, reusable environments, diagrams,
annotations/metaphors and occasional hero moments. This may scale better than continuous complex animation, but no
long-form production or audience-viability claim is authorized.

Founder-selected references establish a starting hypothesis, not eternal truth. Where platform policy permits, later
audience evidence may inform hypotheses about narrator treatment, hooks, beats, compositions, mutations, annotations,
humour, metaphors, captions, pacing and payoff. Conveyor may propose revisions; it may not override founder brand and
editorial governance or implement a new learning system from this specification.

## Authority boundary

This document defines methodology only. It authorizes no calibration cell, narrator test, media ingestion, provider
call, generation, spend, new narrator, production regeneration, Production #6, long-form work, runtime change, package
change, YouTube action or publication.
