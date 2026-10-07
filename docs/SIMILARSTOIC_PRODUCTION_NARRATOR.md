# SimilarStoic — Approved Production Narrator

Founder decision, 22 September 2026: **Daniel is the founder-approved SimilarStoic production narrator**,
not a provisional candidate. The narrator search is resolved. This supersedes the historical uninstructed Marin
development baseline and narrator-selection holds, not the separate production/publication execution gates.

## Exact configuration

- Provider: Inworld; persisted engine kind `inworld_tts`.
- Model: `inworld-tts-2`; provider-native SYSTEM voice `Daniel`; locale `en-US`.
- Delivery: `BALANCED`; WAV, 48 kHz mono; speaking rate `1.0`.
- Timestamps: `WORD`; text normalization: `ON`; enhancement: `false`.
- Instruction SHA-256: `4334ac0e0cb2e5c0870a8ef7f0b1d5f40bf0afc8381b108d7916e7d1e6f3b5cb`.

Exact approved instruction (no appended style brief):

> Speak like a relaxed, intelligent young adult explaining something useful to a friend. Conversational, grounded and lightly amused. Confident without selling. Let humour land through understatement, not performance. Use natural clause-level pauses and relaxed sentence endings. Never sound like an announcer, corporate presenter, finance guru, advertisement, podcast intro, or hyperactive social-media creator. Do not add, omit or paraphrase words.

## Founder evidence and decision

Daniel passed short-cell casting and the longer independent generalisation test. Private review WAV SHA-256:
`d7f7778928698b127d5bef4497b26b1043a37c7e3154779ff9c4df25e5243518`.
Existing raw/review audio and its private provenance remain unchanged.

Founder scored all twelve dimensions **7/7**: naturalness, fluidity/connected speech, rhythm/pace variation,
pause continuity, emphasis/phrase variation, warmth/personality, forward momentum, conviction/confidence,
accent authenticity, voice-depth suitability, SimilarStoic fit and sustained listenability.
Synthetic tells: **NONE**; talking rather than synthesized reading: **YES**; deterioration: **NO**;
public SimilarStoic quality: **YES**; Daniel/F performance gap: **NONE**.

> This is it. This is the perfect voice. This is the voice to use for SimilarStoic videos.

A slightly uncanny breath/pause around seconds 5–6 between “available credit you're using” and
“A high reported balance” was explicitly acceptable and non-blocking. No corrective processing is approved.
Reference F remains historical performance evidence, not a cloned voice or production asset.
The [Stage-1 disposition](NARRATOR_NATURALNESS_STAGE1_DISPOSITION.md), its failed Marin instruction
generalisation, and earlier casting findings remain historically valid; they do not describe the current selection.

## Spoken copy and portability

Write narration for natural speech: use ordinary contractions and conversational clause structure where semantically
appropriate (`that doesn't`, `you're`, `you've`, `didn't`, `hasn't`). Founder found the longer test's spoken-English
writing more natural than conspicuously formal readout. This is not mechanical contraction or permission for the
provider to paraphrase. Exact approved script text remains authoritative; preserve meaning, claims and tone.

Pronunciation control is a provider-facing rendering layer, not an editorial rewrite. The canonical Script and captions
retain `ISA`; synthesis sends the token-bound alias `eye-suh`, and provenance records the alias used. Aliases must not
alter substrings inside other words. Any new alias requires an explicit canonical addition and an offline regression
test; the provider receives no discretion to improvise pronunciation or wording.

**CHANGE VOICE WITHOUT REBUILD**: narrator configuration remains separate from scripts, visual authorities,
scene plans and publication metadata. A separately authorized voice change regenerates only the narration-dependent
chain: narration, completeness validation, alignment, captions, duration-dependent timing and final media.

## Implementation and execution boundary

`project_atlas.narration.resolve_narrator("similarstoic")` resolves offline with no credential access or provider call.
`MediaService.generate_brand_narration` reuses the immutable narration lifecycle; it requires explicit execution
authorization and Migration 26 before synthesis. Configuration has no OpenAI/Marin fallback or automatic retry.
Existing explicit local/OpenAI adapters remain available for other callers; they are not SimilarStoic defaults.
Credentials remain in `INWORLD_API_KEY`, never ordinary provenance. No live verification is performed by this task.

Every production narration take must pass independent Script-completeness verification (a prompt-free `whisper-1`
transcription of the exact persisted WAV, strictly reconciled against the approved Script) before it is admitted for
captions, snapshot or render; see `CONVEYOR_CURRENT_STATE.md`.

Source Migration 26 admits truthful Inworld execution provenance using the established constraint-rebuild pattern.
The persistent runtime was subsequently migrated to 26 under separate founder authority on 22 September 2026.
The [23 September read-only reconciliation](../CURRENT_STATUS.md#verified-pilot-and-runtime-state--23-september-2026)
verified migrations 1–26, integrity `ok`, zero FK violations and the preserved post-migration hash. No further migration
is needed or authorized here. Repository construction still auto-migrates/seeds: never use it merely to inspect runtime
state or to build private calibration media. Runtime readiness is not synthesis authorization.

This decision grants no provider call, generation, spend, Production #6, P5 regeneration, upload or release authority.
P5 v4 and Pilot #1 remain unchanged and public release remains held. Approved narrator quality is not acceptance of
any newly assembled production or automatic permission to publish one.
