# Conveyor Current State

## Authority and purpose

This document is the single current operational authority for Conveyor. It records the state from which a fresh
agent should resume and the boundaries that prevent historical material from being mistaken for current instruction.

When current documentation conflicts, resolve current truth through this file. `README.md` is an onboarding map,
`ROADMAP.md` is strategy and future sequencing, and `CURRENT_STATUS.md` plus `docs/CANONICAL_HANDOFF.md` are historical
provenance. Design notes and evidence records remain authoritative for their bounded subjects only when they do not
conflict with this operational snapshot.

This checkpoint describes state; it does not authorize application execution, provider calls, spend, publication,
migration, or new production work.

## Product identity

**Conveyor** is the long-term production operating system/platform. It is continuously developed to support multiple
channels and products.

**SimilarStoic** is Conveyor's first autonomous pilot channel and flagship proving ground. SimilarStoic owns its
channel-specific editorial, visual, audience, and creative decisions. It does not define or own Conveyor itself.

**Project Atlas** is the historical development name for the system that evolved into Conveyor. Preserve that name in
historical records and in technical compatibility identifiers that have not yet undergone their bounded migration.
The Python package/import name `project_atlas`, the class name `AtlasRepository`, and `ATLAS_*` environment variables
remain valid technical identifiers for now; they are not current product branding. Do not rename them opportunistically.

## Current repository and runtime layout

The intended active Windows layout is:

```text
D:\ConveyorOS\
  source\
    Conveyor\
  runtime\
    ConveyorRuntime\
  channels\
    SimilarStoic\
  evidence\
  archives\
  docs\
  temp\

D:\ConveyorBackups\
```

Active source is `D:\ConveyorOS\source\Conveyor`. Active runtime is
`D:\ConveyorOS\runtime\ConveyorRuntime`. The SimilarStoic channel root is
`D:\ConveyorOS\channels\SimilarStoic`. `D:\ConveyorBackups` stays outside `ConveyorOS` as the independent recovery
boundary.

The former active roots `D:\ProjectAtlas` and `D:\ConveyorRuntime` no longer exist. Those strings may remain in
historical provenance, but they are not startup instructions. Do not recreate them or add compatibility junctions.
The post-relocation `.venv` was rebuilt fresh.

At the repository level:

- `src/project_atlas/` contains the current compatibility-named Python application packages.
- `tests/` contains automated tests and support.
- `scripts/` contains bounded operational and development automation.
- `database/` documents persistence and migration history.
- `docs/` contains this authority plus bounded architecture, policy, creative, and historical records.
- `assets/` contains tracked project assets; production runtime assets and media belong under the runtime root.

## Runtime environment contract

In each new PowerShell process intended for production operation, establish the runtime contract by dot-sourcing:

```powershell
. .\scripts\set_conveyor_environment.ps1
```

The script derives the approved layout from its own repository location, validates every required path, resolves the
repository-bundled FFmpeg/FFprobe pair, fails closed on missing or ambiguous paths, and sets these process-level values:

- `ATLAS_DB_PATH`
- `ATLAS_ASSET_STORAGE_ROOT`
- `ATLAS_MEDIA_STORAGE_ROOT`
- `ATLAS_FFMPEG_PATH`
- `ATLAS_FFPROBE_PATH`

The `ATLAS_*` prefix is temporary technical compatibility, not active product identity. Do not fall back to
working-directory-relative `data/atlas-local.db`, `data/assets`, or `data/media` for production. Do not use a system
`PATH` FFmpeg as an implicit production substitute.

The protected production database SHA-256 recorded below is a verification checkpoint, not a permanent runtime
contract. Legitimate future production operations may change it; never embed it in startup code or use it as a reason
to reject an authorized future database change.

## Current Git and verification checkpoint

The active repository is expected to be clean on `main`. Before consequential Git operations, fresh agents must inspect
the working tree and index and verify current `HEAD`, `origin/main`, and live remote `main` directly. Exact current
commit SHAs and GitHub Actions run IDs are volatile verification results, not permanent operational truth.

- The immutable rollback/reference checkpoint is the pre-cleanup tag `pre-conveyor-cleanup-2026-09-30` at
  `f17ab0cf89bc99a95bcfb4a9d28d31d8fc2d0fa3`.
- The relocated full offline suite originally passed **316 tests**.
- After successor-run adoption of accepted acquisitions, the verified local full suite is
  **492 passed, 0 skipped, 0 failed**. Post-acquisition founder narration authorization is a recorded action;
  the frozen request is unchanged and each narration take is a separately authorized single provider call.
- Repository CI is restored to green for Ruff lint, Black formatting, and pytest. Verify the current run live when its
  result matters.
- The SHA-256 `97FF9F4B37766A98BE3C94506D5E45A399648B070DEAC686CA25EF755B29EDE2` is a historical
  pre-Migration-28 verification checkpoint. Migration 28 and legitimate Production #7-era writes changed the
  protected runtime afterward; do not treat that hash as its current value.

The founder-rejected, non-canonical v028 prototype scripts were intentionally removed from active `scripts/` after
preservation. Their exact source bytes and representative visual evidence are stored outside the repository at
`D:\ConveyorOS\archives\experiments\similarstoic\rejected-v028\2026-09-01\`. The tracked
[rejected-v028 evidence index](evidence/experiments/REJECTED_V028_PROTOTYPES.md) records their disposition. Do not
restore them or treat them as production tooling merely because historical evidence exists.

## Current production status

**SimilarStoic is production-worthy now.** The founder-approved public-production-quality baseline is
`output/production-tests/next-private-production/next-private-production.mp4` (SHA-256
`FE99094664FF2F3514BC4D66485FD24BDD2A63591811F98EE6C89DF0DC566B3A`, 38.720 seconds). This local artifact is the
creative-treatment reference, not a publication authorization or a scene library. Future videos must use new topics,
scripts, and scenes through the same production method recorded in
[`SIMILARSTOIC_CREATIVE_CALIBRATION.md`](SIMILARSTOIC_CREATIVE_CALIBRATION.md#founder-approved-production-method),
not reuse this video's content.

Fundamental visual tweaking is complete. Continue to improve character continuity without sacrificing expressive
variation, generate enough meaningful narration-driven scene changes to sustain engagement, and preserve factual
sources with appropriate publication-flow attribution. These are continuing quality improvements, not blockers and
not reasons to redesign the approved visual treatment or restart architecture experimentation. The successful eight
beats over approximately 39 seconds are evidence for useful density, not a universal beat-count rule.

The approved MP4 was assembled outside Conveyor's canonical production path: its eight images came from Conveyor's
generation service against a scratch database copy, it reuses the Production #7 attempt-2 Daniel narration, and its
final assembly procedure was not preserved. Canonical v2 has since reproduced the approved method offline from the
preserved beats and narration (Phase 1 replay, reaching `private_founder_review_ready`). That replay is technical
evidence, not founder acceptance of a new production.

Preserved evidence:

- approved baseline: `D:\ConveyorOS\evidence\similarstoic\approved-production-baseline\2026-10-03-v1\`
  (backup `D:\ConveyorBackups\approved-production-baseline\2026-10-03-v1\`);
- Phase 1 replay: `D:\ConveyorOS\evidence\similarstoic\phase1-replay\`;
- production DB backup (post-Migration-28, pre-Claude-implementation):
  `D:\ConveyorBackups\post-migration-28-pre-claude-implementation-2026-10-03\`.

Conveyor already models research provenance through `ResearchPack`, `Claim`, `Source`, `ClaimEvidence`, and
`ScriptClaimSet`. The bounded remaining integration is to project the sources supporting a production's approved
script claims into publishing-package source/credit metadata; extend those existing structures rather than inventing
a second sourcing subsystem.

**Production #6 was completed as a private diagnostic production cycle. It mechanically exercised the current
Conveyor production path and produced useful evidence, but failed founder creative acceptance and was not approved
for publication. Its failures informed subsequent generalized production rules. P6 is closed as diagnostic evidence,
not accepted/publicly released.**

The status distinctions are:

| Question | P6 status |
| --- | --- |
| Mechanically executed | Yes |
| Founder creatively accepted | No |
| Published | No |
| Lessons retained and generalized | Yes |
| Closed as diagnostic evidence | Yes |

Do not reopen P6 merely to make it pass. Production #7 and its experiments supplied later private evidence; the
founder-approved baseline above is the current creative authority.

P6 evidence included halos/edge defects, long static stretches, weak background semantic support, repeated poses and
hamster blocking, a ghost circle, character drift, a pronunciation issue, and a repeated ending. Narration was the
strongest component. These findings explain learned rules. Production #5 v4 remains historical accepted evidence;
the founder-approved `next-private-production.mp4` identified above is the current creative baseline.

## Public releases

The founder published these videos manually in YouTube Studio, outside Conveyor. Each uploaded file is byte-identical
to the founder-accepted final artifact.

| Production | Accepted review | Artifact (SHA-256, duration) | Public URL | Public |
| --- | --- | --- | --- | --- |
| P8 | `production-8-attempt-2:founder-review:1` | `production-8-attempt-2-artifact-2` (`6f2b248a14002efc1a2e39ba930efb442a5b7a2eb8e293e6924334379a95c000`, 30.220 s) | https://youtube.com/shorts/MbVZPnX_b_s | 2026-10-04 13:57:41 Europe/London |
| P9 | `production-9-attempt-2:founder-review:1` | `production-9-attempt-2-artifact-3` (`4c0a8bb23cff0ba8487f0ca0aa92950d60c100e75b63f463b1f6ea26f6b2132f`, 34.400 s) | https://youtube.com/shorts/Dd76ERbxg_w | 2026-10-05 (date only) |

- Neither release has a Conveyor PublishingPackage, approval, release operation, platform publication or publication
  receipt, so runtime release-week accounting cannot see them (P8: 2026-W40; P9: 2026-W41).
- P9's separate never-release private API audit-evidence copy `JuouBEMCNzg` is not its public release.
- P7 remains private evidence only, with no founder acceptance. P10 is in progress and not published (see below).
- Rule: any external publication made outside Conveyor (for example a manual YouTube Studio release) must be recorded
  here the same day with URL, artifact ID and SHA-256, until Conveyor can record such a publication in runtime.

## Open lessons from Production 10

Production 10 (`production-10`, Ofgem energy price cap) has all eight images accepted. Both narration takes failed
completeness verification with repeated material in the same passage: `production-10:narration_verification:1`
(take 1) and `production-10:narration_verification:2` (the authorized retake). `production-10` remains failed at
stage `narration_verification`. In isolated non-production calibration
(`D:\ConveyorOS\channels\SimilarStoic\narration-tests\2026-10-07-loop\`), the full Script with only the figure
sentence rewritten as spoken copy ("Take a typical household paying by Direct Debit. Ofgem puts it at £1,723 a
year. That's £60 more.") passed in both takes B1 and B2 (121/121/121); the founder heard both as good and preferred
B1 as more realistic and fluid. The supported learning is only that this rewrite materially outperformed the
existing wording for Daniel; it belongs to the OPEN speakability lesson below. No successor run has been started.

The following lessons are **OPEN: they are not current implemented behaviour**. Each must land as an enforced
extension of an existing Conveyor mechanism, not as an operator habit or a parallel subsystem. Any prompt for P10
completion, P11 or later work must check this list and must not silently treat an OPEN lesson as completed.

- Retime must run by default before founder whole-video review (P10 v1's estimated scene timing ran visibly behind its
  narration until a manual retime).
- Daniel script-speakability preflight, based on the founder A/B evidence in
  `D:\ConveyorOS\channels\SimilarStoic\narration-tests\2026-10-07-ear\` and the P10 loop calibration in
  `...\narration-tests\2026-10-07-loop\` (both non-production calibration).
- The same environment plus the same viewpoint must lock room geometry, furniture scale and persistent fixture
  identity across beats.
- Anchor fixtures must never be repurposed as different objects (the HOME post box was reused as an energy meter).
- Acquisition review must inspect limbs, props and straps zoomed in, not only at full frame.
- The runtime must record the P8 and P9 manual public releases before P10 is published.

## Creative operating rules

The current generalized creative rules are:

- Use a sparse, light, hand-drawn visual language with deliberate imperfection.
- Preserve generous white or off-white negative space.
- Avoid generic polished corporate, vector, or cartoon appearance.
- Avoid gradients, painterly shading, glossy dimensional rendering, and unnecessary surface detail.
- Preserve the recognizable Core v3 hamster with its crossbody bag.
- **THE NARRATOR EXPLAINS. THE HAMSTER ILLUSTRATES.**
- Make movement and visual change follow meaning rather than arbitrary time intervals.
- Treat captions as part of composition, not an overlay afterthought.
- Review the complete video at normal speed, at phone scale, before acceptance.
- Persistence does not mean stillness.
- Stale states, ghost markers, repeated endings, and other residual visual state are unacceptable.

Quality must be judged at the stage that owns the defect:

- At **raw-world acquisition**, judge source-world/style quality, semantic action support, believable scale and world
  logic, and crisp intentional source edges.
- At **actor-fit/final-composite**, judge actor, object, and composite edge quality separately.
- If softness appears only during placement, scaling, compositing, or rendering, localize the defect to that stage
  instead of regenerating otherwise strong source art.

## Pipeline model

Conveyor's high-level pipeline is:

```text
brief
→ script
→ visual beats
→ canonical characters/worlds
→ controlled animation/state
→ narration
→ captions
→ render
→ QA
→ publish
→ learn
```

Core reliability has three dimensions: creative/product quality, reproducibility/control, and audience progression.

> A perfectly persistent boring video is still a bad product.

Generation may be stochastic. Accepted production state must be deterministic and reproducible.

## Current mechanical foundation

The repository has mechanically established:

- the Persistent Scene Model;
- exact inheritance and admitted lineage;
- resolved scene state flowing into render;
- caption integration;
- the Daniel narration path; and
- deterministic accepted production state.

These mechanisms are foundations, not proof of creative quality or end-to-end autonomous readiness. Mechanical
persistence does not guarantee a compelling, semantically active, publication-ready product.

## Known pipeline boundaries

The following limitations remain operationally important:

- The legacy v1 `AssetSelection` snapshot path still has HTTP ingress and is not dead.
- Persistent-scene v2 has an explicit canonical HTTP lifecycle under `/api/v2/productions`. It starts from an
  approved `VisualPlan` plus semantic world/entity/variant intent, performs managed acquisition, pauses for raw-world
  review, adapts approved images into provenance-linked scene rasters, persists world/admission/state lineage, uses
  approved narration, captions and rendering, and then pauses for whole-video review before it can become
  `private_founder_review_ready`.
- `WHOLE_VIDEO_QA_PROFILE` and related QA profile structures are largely metadata and human-review contracts; their
  existence is not proof of fully automated semantic creative QA. The v2 lifecycle records automated bounded cell
  evidence and explicit human acquisition/whole-video outcomes without treating either as founder acceptance.
- `static_character.py` is tested but currently has no production caller.

Do not delete or modify these areas merely because they are bounded or incomplete. Resolve each through a separately
authorized implementation phase.

## Canonical v2 fidelity and safeguards

Canonical v2 previously could not render full-frame beats acceptably: its compositor forward-maps source pixels, so
upscaling a 941x1672 generated image to the 1080x1920 frame left about 24% of pixels unwritten (a visible grid).
This is fixed by:

- a versioned scene adapter, `managed-image-to-rgba-v2`, that resamples full-frame variants to exactly 1080x1920
  with bit-exact FFmpeg Lanczos scaling and records the scale method in derived-asset metadata (derived raster IDs
  are versioned so pre-fix rasters are never reused);
- a production guard that rejects any layer mapping requiring upscale and requires full-frame layers at exact 1:1;
- a pre-encode compositor coverage gate: every composited frame must have zero unwritten alpha pixels.

New persistent snapshots freeze render profile `similarstoic-vertical-v3`: libx264 CRF 18, preset medium, yuv420p,
1080x1920 at 30 fps, AAC 192k mono 48 kHz, faststart. Existing `similarstoic-vertical-v2` behaviour is unchanged:
v1 AssetSelection snapshots and older persistent snapshots keep their historical encoding.

v2 production requests now:

- require an explicit boolean `narration_authorized`, frozen into the request digest; narration fails closed before
  any synthesizer call when it is not `true`;
- treat `forecast.image_calls` as a frozen per-run ceiling counted per recorded provider generation call, including
  failed calls (`forecast.narration_calls` must be 1);
- may plan the standard narration completeness check with `forecast.verification_calls: 1` (exactly 1 when present).
  Requests frozen without it stay valid and unchanged, but get no transcription spend authority: their check needs a
  recorded founder narration-verification authorization;
- check generation authority before any provider call and the persisted execution provenance after each call; a
  mismatched execution counts as a call but is never admitted as an acquisition;
- require full-frame integrated beats to carry the request's character authority, while non-full-frame
  characterless entities remain allowed.

Acquisition review and retry:

- Rejected raw images can be reacquired within the same production run.
- Acquisition reviews are round-scoped and bound to the exact asset reviewed, and previously passed variants are
  never regenerated.
- Rejected and retried generation attempts continue to count toward the frozen image-call ceiling.
- Narration does not begin until every currently active variant has a passing acquisition review.

Full-frame aspect admission:

- Full-frame generated results are checked against the approved 9:16 shape immediately after generation.
- A source more than 0.5% relative error from 9:16 is technically rejected before founder review. The rejected
  attempt still counts toward the image-call ceiling, is never presented as an active founder-review asset, and only
  the affected variant is regenerated.
- The assembly-time full-frame aspect check remains as defense in depth.

Automated cell QA claims only persistent-aggregate verification and compositor coverage
(`conveyor-automated-cell-v2`); perceptual final-frame quality remains human review.

Canonical post-narration retiming (`retime`, also `POST /api/v2/productions/{run}/retime`):

- It is available only from `qa_review_pending`, or after a failed whole-video QA (`failed` at stage `qa`).
- Caller-supplied per-beat durations must sum exactly to the persisted narration duration.
- The approved images, scene states and narration are reused, with zero provider calls.
- Outputs are versioned, and all prior snapshots, renders and reviews are preserved.
- The newest successful render is the current render; later human whole-video QA binds to it.
- Retime is refused after a founder decision, or once any render of the run has been packaged.
- Retime (and the read-only retime recommendation) is refused unless the current narration take passed its
  completeness verification, so timing is always computed from the current verified take.
- A failed retime has no recovery path yet.

Narration completeness gate (`src/project_atlas/narration_verification.py`, enforced in
`ProductionLifecycleService`):

- Every new production narration take is independently checked after synthesis and persistence, before it can feed
  captions, a snapshot or a render. The exact persisted WAV (bound to its SHA-256) is transcribed once by prompt-free
  OpenAI `whisper-1`, the Productions 1-4 method, and strictly reconciled against the canonical approved Script.
- Normalization `narration-completeness-v1` removes only differences that do not change the spoken words: case,
  punctuation, ordinary contractions, token splits/joins, approved pronunciation aliases (written or approved spoken
  form) and numbers, currency and percentages (one canonical spoken form). Any remaining insertion, omission,
  repetition or substitution fails closed; there is no verification override. The Script stays the only authority.
- Each check is recorded once as versioned `narration_verification` production evidence (no migration) with the
  narration asset and execution IDs, WAV SHA-256, method/model, transcript, expected/recovered token counts,
  normalization version, structured differences and outcome (`passed`, `failed`, or `error` when transcription
  itself failed). A take is never transcribed twice; there is no automatic provider retry.
- A failed or unverified take is preserved but never admitted: the run stops at stage `narration_verification`,
  resume never regenerates or overwrites it, and snapshot creation and retime refuse a current take without a passing
  verification.
- Narration takes are versioned monotonically (`:narration-execution:N`, `{run}-narration-N`,
  `:narration:evidence:N`, `:narration_verification:N`); snapshots, renders and automated cell QA are versioned and
  bound to the exact narration take they use.

Versioned narration retake (`retake_narration`, also `POST /api/v2/productions/{run}/narration-retake`):

- Requires a recorded founder retake authorization (`POST .../narration-retake-authorization`) naming the run's
  current defective narration asset, `authorized_by` and a reason. One authorization permits exactly one provider
  take and that take's single completeness check, and is consumed by it.
- Allowed only when every acquired variant is accepted, the run awaits or is failing whole-video review (or stopped at
  a failed narration verification), no founder decision exists and no render has been packaged.
- Reuses the approved Script unchanged and all accepted imagery, worlds and scene states; no image provider is
  reachable. A passing take produces a new snapshot/render/cell-QA candidate bound to the new take, timed from the
  request's narration weights over the new take's duration (earlier retime durations are never copied forward); a
  failing take stops at `narration_verification`. Earlier takes, snapshots, renders and reviews remain history.
- Runs frozen without the verification forecast can authorize one check of a specific take with
  `POST .../narration-verification-authorization`; a check is never repeated for the same take.

Successor-run adoption of accepted acquisitions (optional frozen request field `adopt_acquisitions_from`):

- A successor production with its own revised Script, VisualPlan, Scenes and AssetSpecs may adopt every accepted
  image of a predecessor run instead of generating. The first version is all-or-nothing: the source run must exist
  and differ from the successor, the semantic variant keys (world, entity, variant) must match exactly, every
  source variant's current active asset must have a passing acquisition review (earlier rejected or superseded
  assets are never adopted), and the successor freezes `forecast.image_calls: 0`, `narration_calls: 1` and
  `verification_calls: 1`. There is no fallback to image generation; the generation service is never reached.
- Before the run is created, each adoption is verified: source bytes against their SHA-256, intrinsic size and
  full-frame aspect, and the source generation's recorded authority (style, character profile and reference set,
  global visual authority, and every recorded visual authority such as the environment anchor) against the
  successor's request and AssetSpec. Any failure refuses the request with zero provider calls.
- Adopted bytes are imported under the successor's AssetSpecs. Successor acquisition evidence records `adopted`
  provenance (source run, asset and SHA-256, generation execution, acquisition evidence and passing review,
  successor AssetSpec) and no generation execution. The successor stops at `acquisition_review_pending` and needs a
  fresh normal human acquisition review; a rejected adopted image is never replaced. The source run is not
  mutated; it gains one appended `successor_run` lineage record. Packaging of the source is not a refusal reason.

Explicit claim-timed citation overlays are supported.

- They come only from an optional `citations` request field. Each citation has a scene, a label of 24 characters or
  fewer, and source IDs drawn from the script's frozen ScriptClaimSet. They are frozen in the request digest and are
  never inferred.
- Each citation is bound to one Scene, rendered small in the upper-right safe area only while that Scene is on screen,
  and carried through retime with its timing recomputed.
- Productions without citations render exactly as before.

Canonical persistent-scene snapshots use pause-aligned phrase captions (`caption_policy`
`pause-aligned-phrase-captions-v1`, `src/project_atlas/speech_timing.py`).

- Timing evidence is FFmpeg `silencedetect` (-35 dB, 0.12 s) on the exact persisted narration, matched to the approved
  script's punctuation phrases; unmatched boundaries are estimated by the same builder. No provider call is made.
- Cues follow natural phrases, never start before the spoken words, keep mobile readability, and end at a scene change
  that falls in a narration pause. A continuous spoken phrase is not split merely because a scene changes.
- Future persisted provider word timestamps must feed this same cue builder as a timing source, not a second caption
  path. The historical five-word cues remain only for legacy AssetSelection snapshots.
- `GET /api/v2/productions/{id}/retime-recommendation` recommends scene durations whose boundaries sit at the pause
  ending each scene's narration excerpt. It is read-only; applying it remains a founder-approved retime.

A controlled founder-confirmed YouTube upload path exists (`src/project_atlas/youtube_upload.py`), with the YouTube
Developer Policies obligations implemented in `src/project_atlas/youtube_consent.py`. **Live use requires** an
API-route PublishingPackage and founder approval for the chosen artifact, plus current upload OAuth consent. P9's
public release `Dd76ERbxg_w` was a manual Studio upload outside this path (see [Public releases](#public-releases));
its only API-route package is the never-release private audit-evidence package below (video `JuouBEMCNzg`).

- One `videos.insert` of the exact artifact bound to an API-route founder-approved PublishingPackage, with the title,
  description and privacy the founder confirms on the upload screen; no update, privacy transition or delete.
- Authorization is exactly `youtube.readonly` + `youtube.upload`, held as a separate Windows Credential Locker entry;
  the read-only observation token is never upload-capable. `python -m project_atlas.youtube_upload authorize` always
  runs fresh consent and stores the token only after exact scope and SimilarStoic channel verification.
- `/youtube/upload` is served only when configured, only on a loopback bind to a loopback peer, with Host/Origin
  checks, a single-use nonce, anti-framing headers and the YouTube API Terms section 9.1 upload notice.
- After dispatch, an uncertain outcome is shown as unknown and reconciliation-required, never as nothing sent.
- Versioned acceptance: Conveyor Privacy Policy version `2026-10-06` (constant `POLICY_VERSION`, matching the published
  page) must be accepted before any authorization or YouTube API use; a changed version requires re-acceptance.
  Acceptance, revocation and data deletion live at `/youtube/privacy` and are reachable without acceptance.
- Revoke (button and `youtube_consent revoke`) revokes each stored token with Google (only HTTP 200 counts as
  confirmed), deletes both local credentials and purges stored YouTube API data, processing each authorization
  independently; anything unconfirmed shows the Google security-settings link. Delete-data purges API data and states
  that nothing on YouTube is affected. Conveyor-authored records are retained.
- The read-only and upload authorizations each reconfirm independently every 30 days, automatically before API use and
  only after acceptance. Definitive revocation deletes the credential and purges data; transient failures fail closed.
  Stored YouTube API payloads older than 30 days that were not refreshed are deleted.
- The only publishing/YouTube mutation routes are `POST /youtube/upload`, `POST /youtube/privacy/accept`,
  `POST /youtube/revoke` and `POST /youtube/delete-data` (`YOUTUBE_MUTATION_ROUTES`, test-enforced).
- A public or unlisted upload must satisfy the existing release authority: API release route, the approved
  publication time open now, and a clear channel pilot week; otherwise it is refused before anything is sent.
- A package may declare `caption_artifact: {"kind": "burned_in"}` and/or `cover_choice: {"kind": "platform_default"}`;
  observation then skips only the caption-track or custom-thumbnail check. Asset-backed packages are verified as before.
- An evidence-only package declares `release_policy: "never_release"` with exactly `release_route: "manual"`,
  `publication_timing: {"mode": "never_release"}` and `private_first: true` (pilot week `never-release`). The manual
  route is a legacy-schema compatibility sentinel only, never release authority: only a private upload is allowed;
  public/unlisted upload, every API or manual release path and public receipts are refused before dispatch, and such
  packages never count toward release weeks.
- Audit evidence: on 2026-10-06 the founder privately uploaded a copy of P9 v3 through the API as YouTube video
  `JuouBEMCNzg` (never-release package `publishing-package-similarstoic-youtube-pilot-1-slot-2-v1`; distinct from
  P9's public manual release `Dd76ERbxg_w`); its first observation
  failed verification only on tags: YouTube stored them verbatim but returns them sorted. Tags verification is now
  order-independent but exact (same strings, case, whitespace and count). The Task Scheduler task "Conveyor YouTube
  maintenance" is enabled (daily 03:00); its first run found the expired read-only authorization revoked, deleted
  it and purged all stored YouTube API data (including this evidence's remote id and observations), as accepted.
  While the OAuth app is in Testing mode, tokens for both authorizations expire after ~7 days, so such purges are
  expected until OAuth verification.
- YouTube API Services audit: submitted 2026-10-06 15:40 Europe/London; Google's confirmation received. Purpose:
  lift the private-only upload restriction on unaudited project 1031021502761; no quota increase requested.
  Declared endpoints `channels.list`, `videos.list`, `videos.insert`; scopes `youtube.readonly` and
  `youtube.upload`; use case Video Uploading & Account Management; policy version `2026-10-06`. Evidence is kept
  outside the repository at `D:\ConveyorOS\evidence\youtube-audit\2026-10-06\submission\` and must not be
  committed. Status: awaiting Google's response; the OAuth app is still in Testing mode. Attestation made: any new
  YouTube API use (e.g. YouTube Analytics) first requires a privacy policy update and written notification to
  YouTube.
- Consent state (accepted version, reconfirmation times; no secrets) is a JSON file outside the repository, required
  as `--consent-state` or `ATLAS_YOUTUBE_CONSENT_STATE`; losing it forces re-acceptance and reconfirmation.
- Daily maintenance (Windows Task Scheduler, under the same Windows account that owns Conveyor's Credential Locker
  entries) always purges stale data locally and reconfirms due authorizations only with current acceptance:
  `D:\ConveyorOS\source\Conveyor\.venv\Scripts\python.exe -m project_atlas.youtube_consent --consent-state
  <consent-state.json> --db D:\ConveyorOS\runtime\ConveyorRuntime\conveyor.db maintain --client-config
  <client-config.json>` (both JSON paths outside the repository).

## Schema authority

Application schema authority is the `schema_migrations` table with contiguous versions **1 through 28**. The current
maximum application migration is **28**. Migration 28 adds only append-only production-run events, cross-stage
evidence, QA-review outcomes and founder-review decisions; existing generation, persistent-scene, narration and media
tables remain authoritative for their artifacts.

`PRAGMA user_version = 0` does not mean that no application migrations exist. `PRAGMA schema_version = 203` is
SQLite's internal schema-cookie counter, not the Conveyor application migration version.

Migrations 25–27 remain immutable historical provenance. Migration 28 is current application schema authority and was
applied to the protected production runtime on 1 October 2026 after a dedicated pre-migration backup. Subsequent
authorized Production #7-era activity produced legitimate runtime writes; the old pre-migration hash is historical.

For read-only database auditing, do not instantiate application repository code: repository construction can apply
migrations or seed data. Use an explicitly read-only method under a separately authorized audit procedure.

## SimilarStoic's role

SimilarStoic is where Conveyor's generalized capabilities are first exercised against a real channel. Its accepted
creative language, narrator choices, audience strategy, and editorial rules are channel-specific evidence that can
improve Conveyor. They must not hard-code SimilarStoic ownership into the platform or turn its creative preferences
into universal rules for every future channel.

The strategic direction remains a useful, evidence-led explanatory channel spanning money, work, behaviour, and life
strategy. Current detailed channel strategy lives in bounded SimilarStoic documents and `ROADMAP.md`; current
operational status always resolves here.

## Historical and evidence policy

Preserve knowledge that explains why the system exists while removing its ability to confuse current operation.
Evidence can be conceptually classified as:

- accepted;
- rejected;
- experiments;
- archives; or
- disposable.

This classification is not authorization to move or delete evidence. Historical documents retain their original
claims as provenance. Their current-looking language must be read in the context of their dated snapshot and the
historical notice at the top of the file.

The [rejected SimilarStoic v028 prototype evidence](evidence/experiments/REJECTED_V028_PROTOTYPES.md) is a bounded
historical record of non-canonical experiments, not active production tooling.

## Safe starting procedure for a fresh agent

1. Read this document before treating any other status or handoff file as current.
2. Confirm the repository is `D:\ConveyorOS\source\Conveyor`, expect a clean working tree unless the authorized task
   deliberately creates changes, and inspect `git status` without altering it.
3. Do not restore the rejected v028 prototypes into active `scripts/`; consult their
   [evidence index](evidence/experiments/REJECTED_V028_PROTOTYPES.md) only when historical context is relevant.
4. For authorized production operation in a new PowerShell process, dot-source
   `scripts/set_conveyor_environment.ps1` and inspect the five resolved values.
5. Fail closed if the structure or required runtime paths differ; do not recreate legacy roots or accept relative
   production fallbacks.
6. Do not open the production database through application code merely to inspect it.
7. Before any consequential action, identify the exact authorization boundary: code, migration, provider, spend,
   production, publication, evidence movement, and Git operations are separate decisions.
8. Use `ROADMAP.md` for future direction, bounded design documents for their subjects, and historical snapshots only
   for provenance.

Reading or dot-sourcing the environment script does not itself authorize starting Conveyor.

## Current cleanup and migration boundaries

At this checkpoint:

- source/runtime relocation is complete;
- the durable runtime environment contract and storage-path normalization are complete;
- documentation authority consolidation and final reconciliation are complete;
- CI restoration is complete;
- rejected-v028 prototype preservation and disposition are complete;
- Git working-tree cleanup is complete;
- the `project_atlas` technical rename, `AtlasRepository` rename, and `ATLAS_*` compatibility migration remain future
  bounded work;
- the legacy v1 `AssetSelection` ingress remains available and unchanged while canonical v2 production uses its
  explicit `/api/v2/productions` lifecycle;
- QA automation improvements and the `static_character.py` production-integration decision remain future bounded
  work;
- broader evidence/work-directory cleanup and multi-channel expansion remain future bounded work;
- no compatibility junction is authorized;
- no schema cleanup migration is authorized;
- Production #7-era private work occurred and informed the founder-approved production baseline; and
- provider calls, spend, application startup, publication, and runtime mutation require separate authorization.

Phase 1 (canonical v2 fidelity) and Phase 1B (acquisition retry rounds and aspect admission) are complete. Remaining
gaps are:

- recipe binding, including moving the full-frame character requirement into the channel recipe;
- source-credit projection;
- character continuity;
- scene density;
- speech-aligned initial beat timing (a post-narration retime recommendation exists);
- ceiling counting of generation calls that raise before acquisition evidence is persisted. This covers both a paid
  provider call that raises before evidence is recorded, and a provider call that returns an asset but whose
  post-provider technical inspection or probe raises before evidence is recorded;
- image size on reference-conditioned calls: a configured image size may be recorded in provenance but is not sent
  on reference-conditioned image-edit calls, so those calls use the provider's default size;
- initial beat timing is estimated before narration exists and may require a post-narration retime;
- provider word timestamps are requested but not persisted; captions use pause-aligned estimates between pauses;
- packaging does not yet require the current, founder-accepted render.

Each requires separate authorization.

Update this file deliberately whenever accepted current operational truth changes. Do not turn it into a chronological
diary; move superseded detail to historical/provenance records and keep this document usable as a fresh-agent entry
point.
