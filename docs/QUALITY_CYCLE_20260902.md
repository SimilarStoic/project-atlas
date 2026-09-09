# Production #1 quality-cycle continuity — 2 September 2026

## Authority and checkpoint

Recorded 8 September 2026 and updated after founder + ChatGPT accepted the isolated-character result, Candidate 4
environment style and first static composition grammar. This note records reviewed findings and bounded visual-reference
canonicalization; it does not accept the rejected implementation, select a successor milestone, or authorize the next
experiment. Final push remains subject to founder authorization.

The canonical base before the accepted-pose candidate was `c5dc39bd8b23d10ee5aef540b627b52835a47290` on local
`main` and `origin/main`, ahead/behind `0 / 0`, with the tracked tree clean. Founder-rejected experimental commit
`ad52ab38ad32f97b933099ef98a32dc8fd268662` remains separately preserved and is not promoted.

Conveyor remains the engine; SimilarStoic remains the brand. **CHANGE WITHOUT REBUILD** and founder + ChatGPT
review/acceptance authority are unchanged. Phase 1 is complete, Phase 2 is active/incomplete, and v0.27 is the latest
named accepted implementation milestone. There is no accepted v0.28, selected successor or authorized rig. Production
#2 later completed the existing governed lifecycle and passed founder + ChatGPT final quality review; its acceptance is
recorded below. Source and persistent-runtime migrations remain contiguous 1–23; Migration 24 is absent. Runtime
integrity and foreign-key checks passed. Historical acceptance and runtime records are retained.

## Production #1 and the rejected presentation proof

Production #1 completed the persistent lifecycle technically but failed founder production-quality acceptance.
Hazel's robotic voice, static visuals and dominant captions remain rejected. Marin v2 was an improvement but also
failed final quality acceptance. Their exact historical lineage and hashes remain in the canonical handoff.

The unnumbered Production #1-derived Presentation Treatment Proof was technically successful and **founder-rejected**,
not pending review. Its local experimental implementation is `ad52ab38ad32f97b933099ef98a32dc8fd268662`, intentionally
excluded from canonical main. The final proof artifact is
`final-media-artifact-similarstoic-control-v1-presentation-treatment-proof-v2`, 34.400 seconds, 1080×1920, 30 fps,
H.264/AAC, SHA-256 `66f237284fbb00b274a21d7e4f563851718e74ab58e4d1d9f27b06b8353dc952`.
The first proof is retained separately with SHA-256
`f0b0ca9d37d7b86701965d3a1489670a01c07b66c082329444a2c0b8ddcbc776`.

Founder judged the direction worse overall than Marin v2: the hamster remained static, backgrounds were incoherent,
subtitles were misaligned and the voice still sounded wrong/off. The proof reused the exact existing Marin narration
asset; it did not generate a different voice. Ten geometric compositions with mascot position/scale changes did not
provide illustrated acting or meaningful scene storytelling. Captions followed scene boundaries rather than speech.

Immutable provenance, bounded caption-style configuration and deterministic low-level compositing may be evaluated
individually in future bounded work. Static-cutout acting, geometric scene templates and scene-clock caption scheduling
are rejected presentation semantics. Preserve the experiment as evidence; do not merge or cherry-pick it wholesale.

## Narration completeness and actual alignment

Existing narration used OpenAI `gpt-4o-mini-tts`, voice `marin`, and was already not accepted as the final SimilarStoic
voice. Its WAV SHA-256 is `648c1be676cd6a68731844a9fc9676116b32f23f316ac7e6d0379af005e74486`.
The saved canonical Script snapshot matches the exact runtime Script. A `whisper-1` response against that WAV records
approximately 34.4 seconds, 88 recognized words and six segments. Raw response SHA-256:
`c514c493c8fd1de484ba5abcacb9f554072912da1a49f899add49bc1e52436c4`.

Actual aligned audio reaches **“Do that.”** at approximately 33.42–33.84 seconds and does not contain the canonical
closing line **“Let the rest be weather.”** The saved silence analysis reports a silent tail from about 33.869 seconds;
a read-only recheck with another threshold found about 33.859 seconds. This minor threshold-dependent difference does
not change the conclusion: the narration is incomplete. Do not fabricate the absent line or a caption timing for it.
Do not rewrite historical runtime rows to conceal the defect.

Twelve phrase cues were derived for thirteen canonical phrases, consuming all 88 recognized words. Actual spoken-audio
alignment was demonstrated; some word timestamps have zero duration, so these are not infallible word-level ground
truth. Word-count proportions, text-length estimates, equal scene timing and scene-clock scheduling are rejected as the
future caption timing method.

Existing frozen cue JSON can represent aligned captions without Migration 24 merely to persist those cues. The normal
media service still derives heuristic cues, and its HTTP ingress does not expose arbitrary aligned-cue submission.
Production integration and Script-versus-audio/transcription completeness QA before final rendering remain future
bounded work. Neither a migration nor implementation is authorized by this note.

## Blind voice audition

Five `gpt-4o-mini-tts` samples used the same short passage, speed 0.95 and common instructions:

| Blind sample | Voice |
|---|---|
| A | Cedar |
| B | Sage |
| C | Coral |
| D | Ballad |
| E | Verse |

Founder preferred A/Cedar relative to these five, but **Cedar remains rejected as the final voice**: too tinny and
insufficiently natural. It is the current comparison baseline only. The local review guides predate that decision.

Raw and normalized hashes match the technical record; founder-review copies match the normalized files. Raw audio is
24 kHz mono PCM; normalized files are 192 kHz mono PCM after FFmpeg loudness normalization (I=-16, TP=-1.5, LRA=11).
A raw-versus-normalized Cedar comparison remained outstanding at that checkpoint. Normalization had not been established
as the cause of the thin/tinny perception, and no additional audition was then authorized.

## Accepted audiovisual integration proof — 9 September 2026

Founder + ChatGPT accepted the later local proof at
`D:\ProjectAtlas\work\similarstoic-audiovisual-proof-20260909\founder-review\similarstoic-audiovisual-integration-proof-v1.mp4`,
SHA-256 `1267f9c05c3431ee2d71fe73433f318efc9bfb935616a13fd56593500f7d55ca`. It is 18.03 seconds, 1080×1920,
30 fps H.264 High with AAC-LC audio. Full decode, frame, silence, aspect-ratio and caption-placement checks passed.
The MP4 remains ignored/local evidence; this documentation records its accepted conclusion rather than tracking the
media bytes.

The proof received **VISUAL INTEGRATION PASS**, **EDITING PASS**, **CAPTION METHOD PASS**, **NARRATION COMPLETENESS
PASS** and **OVERALL AUDIOVISUAL PROOF PASS**. Approved still compositions remained coherent under restrained motion,
an idea-led reaction punch-in, drift, sparse foreground rain, a simple reveal and conceptual cuts. Six compact captions
were derived from actual `whisper-1` word timings and remained subordinate to mascot/action. All 45 intended words of
the exact selected Script v1 excerpt were recovered from the final mastered narration. Narration completeness and final-
audio alignment remain hard pre-render requirements; heuristic scene clocks, words-per-second timing and reuse of old
timestamps remain rejected.

This result is materially closer to publishable SimilarStoic quality than Hazel or Marin v2. It demonstrates that the
validated static language can become a short moving, narrated and speech-aligned piece while preserving mascot/style
identity. It does not make all future videos production-ready.

Three bounded auditions used OpenAI `gpt-4o-mini-tts-2025-12-15`; Marin was selected, lightly warmth-mastered and
founder-accepted **for now** as the **PROVISIONAL ACCEPTED PRODUCTION-DEVELOPMENT BASELINE**. Marin is not the permanent
SimilarStoic channel voice. Permanent narrator identity remains an independent future quality track and may use a
founder-consented custom voice through OpenAI or another provider. No recording collection, cloning or custom voice was
performed.

Narrator identity and TTS provider are separate concerns. Replacing either must preserve script/editorial/visual design
while regenerating and revalidating narration audio, completeness transcription, actual speech alignment, caption
timings, duration-dependent edit timing and final media. Provider/model/voice/reference provenance remains mandatory.

This proof added `$0.02` conservative exposure: three TTS auditions were estimated at `$0.01345`, and three Whisper
checks calculated from 57 provider-reported seconds were `$0.00570`; no other provider cost occurred. At proof
acceptance, the active `$10` envelope therefore had `$3.02` conservative exposure and `$6.98` remaining.

## Accepted Production #2 — 9 September 2026

Founder + ChatGPT accepted **Why a paid-off credit card can still affect your score** as Production #2. Execution used
the exact pushed design checkpoint `9fbf807e0148a177ba86902922d17c4851a5e200` and completed the existing governed
research, editorial and production lineage. The mutable `credit-utilisation` Opportunity records the accepted state and
artifact identity; immutable render and artifact rows retain their truthful at-render review state.

The governed lineage includes research pack `research-pack-similarstoic-credit-utilisation-v1`, Script
`script-similarstoic-credit-utilisation-v1`, VisualPlan `visual-plan-similarstoic-credit-utilisation-v1`, narration
`narration-asset-similarstoic-production-2-marin-v1`, input snapshot
`final-media-input-snapshot-similarstoic-production-2-v1`, render execution
`render-execution-similarstoic-production-2-founder-review-v1` and final artifact
`final-media-artifact-similarstoic-production-2-founder-review-v1`.

The runtime-managed artifact is
`D:\ConveyorRuntime\media\production-2\similarstoic-production-2-credit-utilisation-founder-review-v1.mp4`, SHA-256
`ea7f490c046eb424624fb5147d84e792dff561af76f345ecc1ca068c5f7a5493`. It is 48.120 seconds, 1080×1920,
30 fps H.264/AAC. Full decode, frame, audio, aspect-ratio and caption checks passed. All 126 intended Script words are
present in the mastered narration, and all 32 compact caption cues derive from final-master speech alignment. The
six-scene visual continuity check passed. The UK-first editorial guardrail is preserved: consequential claims remain
tied to approved UK sources, and geography and credit-scoring-model distinctions remain explicit where material.

OpenAI `gpt-4o-mini-tts-2025-12-15` / Marin remains the **PROVISIONAL ACCEPTED PRODUCTION BASELINE**; permanent
narrator identity remains replaceable through future consented founder-voice or other provider work. The MP4 stays in
managed runtime and ignored founder-review evidence; canonical Git
records its identity and acceptance without tracking the binary.

Production #2 added `$0.781255` conservative exposure, rounded to `$0.79`: `$0.75` for three successful image calls,
`$0.022255` for one successful and one failed-transfer TTS call, and `$0.009` calculated for two Whisper calls covering
90 provider-reported seconds. No exact provider-reported dollar charge was returned. The active `$10` envelope now has
`$3.81` conservative maximum exposure and `$6.19` remaining. Acceptance and canonicalization added no provider call or
spend. Production #3 has not started.

## GPT Image 2 findings and design hypothesis

Five GPT Image 2 high-quality reference-conditioned edit experiments were performed. Saved PNG hashes match the
records and raw-response image bytes. The tested reference-board method failed the production consistency bar through
scene-adherence failures, unwanted text, bag/style drift and identity inconsistency. No candidate was retained as a
production asset. The all-candidate contact sheet includes the later corrected attempt; the earlier three-beat sheet
does not. Some review-image explanatory text is clipped; use the underlying records as well.

An important causal qualification: some prompts themselves incorrectly requested a golden/tan hamster, confounding
part of the apparent identity drift. The corrected white/light-identity attempt still failed scene adherence, copying
an explaining/whiteboard situation. The supported finding is that **the tested GPT Image 2 reference-board method is
not justified for scale-up**. It does not establish that all OpenAI image generation is inherently unsuitable. Do not
brute-force more attempts using the same failed method.

The later isolated-character experiment tested a different control method: exact canonical tracked references were
passed directly to GPT Image 2, the hamster was isolated from environment generation, and only one defect-targeted
refinement followed the first serious attempt. Candidate 1 was technically useful but retained shading and a faint
vignette. Candidate 2 corrected that defect while preserving the canonical face, colouring, bag, two-paw umbrella grip,
body weight and expressive resistance pose. Founder + ChatGPT accepted Candidate 2, SHA-256
`a6ebaec876b40a7a89b22bca26e18ffa56d0709078498d3126946990c55e581e`, as the first approved secondary acting-pose
reference / pose-pack seed. The isolated-character method therefore **PASSED**. This does not reverse the failure of
the earlier full-scene reference-board method or establish GPT Image 2 as the permanent character provider.

The canonical tracked copy is
`assets/visual-references/core-mascot/poses/core-v3-umbrella-resistance-acting-pose-v1.png`. It supplements the primary
Core v3 identity authority; it does not replace it or establish a complete pose pack or rig.

## Leonardo environment finding

The first Leonardo Phoenix full-scene Character + Style Reference trial was insufficient. In the later environment-only
test, one character-free stormy-street plate was requested. The output contained a different hamster holding an umbrella
despite explicit exclusions and was rejected. Its provider-reported cost was `$0.0374`; it remains local evidence and
must not be promoted. This single failure does not prove that all environment generation is impossible.

## Environment style calibration and selection

The first independently generated GPT Image 2 storm street was character-free but founder-rejected because it was dark,
cinematic, painterly, realistic, textured and too visually dominant. A subsequent style calibration used deterministic
character-free crops from approved SimilarStoic scene exemplars to ground only linework, palette, prop treatment and
negative space. Candidates 1 and 2 established a materially closer sparse direction but retained subtle tonal treatment.

Two further controlled alternatives tested the approved direction. Candidate 3 demonstrated the viable lower-detail /
maximum-simplicity pole. Founder + ChatGPT selected Candidate 4, SHA-256
`989e0da7b273a42f0bf8c229c1510b904902b1eef3336e626705966e6048ccb2`, as the approved environment style /
default-scene-language reference. Its canonical tracked copy is
`assets/visual-references/environments/style/similarstoic-default-scene-language-v1.png`. Candidate 4 represents
approximately the upper normal detail boundary for an ordinary scene. It defines visual language rather than mandatory
reusable street scenery, a universal background, an environment pack or a permanent provider selection. Candidates
1–3 and all earlier rejected environments remain untracked experimental evidence.

The ordinary-scene contract is predominantly warm white/off-white negative space, sparse composition, simple imperfect
hand-drawn outlines, restrained block colours, few useful props and only enough detail to establish place, concept or
action. Character, props and environment must appear drawn by the same illustrator; environment line weight,
complexity, colour treatment, shape language and rendering density must remain compatible with Core v3 and subordinate
to the hamster. Predominantly flat colour permits very subtle unobtrusive tonal variation, but not obvious gradients,
realistic or volumetric lighting, glossy rendering, photorealistic shading, detailed materials or painterly texture.
White/off-white is the ordinary default rather than a universal rule; purposeful later exceptions may include night,
hero/break frames, intense moments, special diagrams or deliberate jokes.

Visual simplicity is a brand choice first and production-efficiency advantage second. It may reduce inconsistency,
generation complexity and corrective attempts while improving reuse, but “simple on purpose” must never become
“cheap-looking”; quality remains authoritative over marginal savings.

## Static integration and composition grammar

The zero-provider-spend static integration test using the exact approved umbrella acting pose, verified transparent
derivative and approved environment-style reference received **INTEGRATION PASS**. Composition C provided the strongest
shared-plane integration. A single bounded refinement increased mascot emphasis while retaining C's full environment,
simple contact ellipse, sparse foreground rain and deliberate off-white negative space; it received **REFINEMENT PASS**.

Founder + ChatGPT approved the refined frame, SHA-256
`c6f933eddf7394ff3d00708650f7c1fa1df2f29ff8011e7ae4858653dd1f45d8`, as the first static composition / composition-
grammar reference. Its canonical tracked copy is
`assets/visual-references/compositions/grammar/similarstoic-static-composition-grammar-v1.png`. The experiment made no
provider call and added no provider-generated material.

The approved grammar is character-first with subordinate environmental context, deliberate warm-white/off-white
negative space, mobile-readable character scale, action-aware off-centre placement, minimal illustrative grounding and
sparse shared-plane environmental marks where useful. Character, props, environment and compositing must appear to come
from the same illustrator and avoid mismatched line weight, rendering density, shading, texture, perspective, colour or
polish. The target is simple on purpose, not cheap-looking.

The later second-scene experiment used the same separated method for a calm indoor explanatory beat. Founder + ChatGPT
accepted the focused sorting pose, sparse indoor environment and deterministic 1024×1536 vertical composition. Canonical
copies are `assets/visual-references/core-mascot/poses/core-v3-sorting-decisions-acting-pose-v1.png`,
`assets/visual-references/environments/examples/similarstoic-calm-indoor-sorting-scene-v1.png`, and
`assets/visual-references/compositions/examples/similarstoic-static-composition-example-2-indoor-sorting-v1.png`.

**Static visual-production method demonstrated successfully across two materially different scene types:** an
outdoor/high-action storm scene and a calm indoor/explanatory sorting scene. This does not claim universal repeatability,
create a complete scene pack or add an architecture layer. No new full production video should be attempted before
visual quality, narration direction/completeness and actual caption alignment are established. Production #2 remained
blocked at that checkpoint.

The second-scene experiment used a separate `$10` quality-development envelope. Conservative maximum exposure is
`$1.00`, remaining authorization is `$9.00`, and top-up is not required. Vertical refinement and canonicalization added
`$0` provider spend. Account funding is not treated as experiment spend.

The later abstract/explanation experiment tested the approved “The things in your hands” concept. Founder + ChatGPT
accepted the first isolated character attempt, first separate abstract environment attempt and deterministic balanced
Composition Variant 1. Canonical copies are
`assets/visual-references/core-mascot/poses/core-v3-things-in-hand-acting-pose-v1.png`,
`assets/visual-references/environments/examples/similarstoic-abstract-reach-boundary-scene-v1.png`, and
`assets/visual-references/compositions/examples/similarstoic-static-composition-example-3-things-in-hand-v1.png`.

This is the first approved sparse abstract/explanation example. The hamster actively handles matching tokens within its
working space while matching tokens beyond a broken boundary remain unattended, so the explanatory metaphor does not
depend on text. It establishes a third bounded static capability without changing the identity, Default Scene Language
or composition-grammar authorities, claiming universal repeatability, or adding runtime architecture.

The two GPT Image 2 requests added `$0.50` conservative exposure because the generation CLI exposed no raw usage or
dollar charge. The active `$10` envelope therefore has `$1.50` conservative maximum exposure and `$8.50` remaining;
top-up is not required. Deterministic composition and canonicalization added `$0` provider spend.

The subsequent exaggerated break-frame experiment tested “One Notification, End of Days.” A colourful machinery /
cinematic direction failed because environment complexity and polish carried the frame instead of the reaction. A
rough-cartoon direction improved reaction readability but remained an enlarged ordinary cartoon. A photoreal gross-up
was rejected because realistic fur, flesh, gloss, lighting and giant-eye horror broke Same-illustrator identity. Those
candidate bytes remain rejected local evidence.

Founder + ChatGPT accepted the hand-drawn gross-up candidate as the first approved special break-frame example. Its
exact tracked copy is
`assets/visual-references/break-frames/examples/similarstoic-hand-drawn-gross-up-notification-v1.png`, SHA-256
`c38e0af357b0beb35ded28e78739115a630ca68ea9f6249f37f5ff8dcbae185e`. The narrow lesson is that a successful
break-frame creates a deliberately disproportionate comedic rupture through detail, expression, crop and reaction,
while remaining recognizable as original SimilarStoic hand-drawn work. It does not alter any ordinary identity,
acting-pose, environment or composition authority.

At the break-frame checkpoint, the active `$10` quality-development envelope had `$3.00` conservative maximum exposure
and `$7.00` remaining; top-up was not required. This canonicalization added `$0` provider spend. Account funding
remained separate from spend. The later audiovisual-proof section records the current totals.

## Spend: conservative working estimate, not verified billing

| Ledger item | USD estimate |
|---|---:|
| Whisper alignment | 0.003440 |
| Five voice samples | 0.023235 |
| Five image attempts, conservatively $2 each | 10.000000 |
| Leonardo full-scene trial, provider reported | 0.043400 |
| Two isolated GPT Image 2 edits, conservatively $2 each | 4.000000 |
| Leonardo environment-only attempt, provider reported | 0.037400 |
| Rejected independent GPT Image 2 environment, conservatively | 2.000000 |
| Four GPT Image 2 environment calibration/selection edits, conservatively $2 each | 8.000000 |
| Cumulative working estimate | **24.107475** |
| Existing cumulative authorization | **25.000000** |
| Working estimated remainder | **0.892525** |

The ledger arithmetic is correct, but the OpenAI amounts remain conservative working estimates pending billing
reconciliation, not verified provider billing. The original five image raw responses contain usage: 21,361 input
tokens (20,484 image, 877 text), 27,440 output tokens and 48,801 combined tokens. The bundled CLI used for the later
GPT Image 2 edits did not expose billed dollar amounts, so the existing `$2`-per-image conservative convention was
retained.
Whisper reports 35 usage seconds, slightly different from the approximately 34.4-second duration used in the old
estimate. Leonardo amounts above are generation-response dollar costs. Do not invent a more exact billed total or
increase available authority on the strength of an unverified recalculation. The `$25` envelope is cumulative, not
renewed per task. The founder's `$5` Leonardo funding is provider credit, not automatically consumed experiment spend.

## Reference-set provenance qualification

`character-reference-set-similarstoic-hamster-core-v1` exists in separate database histories with different members:

| Database/history | Member asset | SHA-256 |
|---|---|---|
| `D:\ProjectAtlas\work\phase1-v014-review-20260817\atlas-review.db` | `asset-9a02b4cb416744a994965e2e1f2f0c33` (asset version 9) | `eaf0af82fe98120613793465f94029a72ae13a79f8e3e258d265e88fa47c450b` |
| `D:\ConveyorRuntime\conveyor.db` | `asset-similarstoic-control-v1-reference-anchor` (imported asset version 1) | `11332518cdace450f8e432fe8cb3558ea2374cf0273f94973912e914cee66956` |

Neither database is described as corrupt. Historical assertions that the original set remains unchanged apply to that
historical database, not a globally interchangeable set ID. Future reporting must qualify database/history, set ID,
member asset and digest. Do not rewrite either history. An exact-file Leonardo trial needs no database repair.

## Evidence preservation and recovery

The [evidence manifest](QUALITY_CYCLE_20260902_MANIFEST.json) records all 48 original quality-cycle files
(118,190,653 bytes), their hashes/sizes, the two rejected prototype scripts and verified archive details. Sources remain
unchanged under `D:\ProjectAtlas\work\similarstoic-quality-cycle-20260902` and the primary checkout's `scripts\`.
No binaries, raw provider responses, account details or credential values are embedded in this documentation commit.

Preservation outputs are outside canonical source at `D:\ConveyorRuntime\continuity-archives\20260908`:

- `project-atlas-ad52ab3.bundle`: complete bundled Git history; verified with `git bundle verify` and `list-heads`,
  including exact rejected commit `ad52ab38ad32f97b933099ef98a32dc8fd268662`.
- `quality-cycle-20260902.zip`: all 48 files plus an internal `PRESERVATION_MANIFEST.json`.
- `rejected-v028-prototypes.zip`: both untracked prototype scripts plus an internal manifest; preserved passively.
- External manifests and `PRESERVATION_SUMMARY.json` retain the same correlation information.

Both ZIPs passed CRC checks and every member's decompressed SHA-256/size matched its unchanged source. The tracked
manifest contains archive SHA-256 values. Recover by first verifying the archive hash, then extracting to a new scratch
directory and checking member hashes; never overwrite the originals as a recovery shortcut. Inspect or restore the Git
bundle in a separate repository, preserving its rejected/experimental classification.

GitHub can recover the findings and correlation manifest after authorized publication. Binary recovery still requires
access to these local archives or a separately verified copy; an on-disk archive is not an off-machine backup. This task
does not archive or alter the operational runtime database/assets/media. Historical prototype source files were not
executed, promoted or staged. No permanent experimental branch or primary-main realignment is performed in this task.

## Accepted-pose candidate validation

The canonical suite passed **127 tests** in 641.98 seconds on 8 September 2026 using isolated temporary fixtures.
Ruff passed for all 14 canonical tracked Python files. Black 26.3.1 passed the repository-safe in-process equivalence
check with full safety validation and no files requiring changes. `git diff --check` passed. No source, test,
configuration or migration files changed.
