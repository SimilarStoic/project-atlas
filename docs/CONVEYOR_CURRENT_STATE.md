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
- After the SimilarStoic new-run defaults, the narration-aligned first candidate, Editorial Readiness evaluator v2,
  the pinned environment identity with the v2 acquisition review and the visual reference approval gate
  (migration 30), the verified local full suite is **604 passed, 0 skipped, 0 failed**. Post-acquisition founder
  narration authorization is a recorded action; the frozen request is unchanged and each narration take is a
  separately authorized single provider call.
- After the P11 consolidation (provider isolation for every test, founder spend control with dispatch records, retime
  overlay fix, review controls, the `similarstoic-flow-v1` recipe with its P11 equivalence test and the operator CLI),
  the verified local full suite is **680 passed, 0 skipped, 0 failed**, with every provider key removed.
- After Phase 3 (PRs #1-#3, last merge `be48afd`, 19 October 2026), the verified `/zero-spend-verify` full suite is
  **761 passed, 0 skipped, 0 failed** (exit 0, on `d99b5a0`, the merged head of PR #3).
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

Conveyor models research provenance through `ResearchPack`, `Claim`, `Source`, `ClaimEvidence`, and
`ScriptClaimSet`. **Implemented for on-demand publishing (Phase 3, 16 October 2026):** `publishing_credits.py`
projects the sources supporting a production's closed script claim set into the package description's "Sources:"
block. Packaging fails closed on missing attribution, and the credits are frozen with the approval (first used for
P11). Legacy pilot packages are not projected: their source lines were written by hand.

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

- **P8 and P9 are reconciled in the protected runtime** (7 October 2026, founder-authorized, after verified backup
  `D:\ConveyorBackups\pre-migration-29-retrospective-publications-20261007-215103\conveyor.db`, SHA-256 `00a5e9d833a5a607fedf7e365a699b6951c2982b738a934afcd4b3877b2b769c`). Founder-attested receipts:
  P8 `publication-receipt-similarstoic-youtube-external-reconciliation-v1-slot-1` (2026-W40, `MbVZPnX_b_s`, second
  precision) and P9 `publication-receipt-similarstoic-youtube-external-reconciliation-v1-slot-2` (2026-W41,
  `Dd76ERbxg_w`, day precision). Runtime release-week accounting now sees W40 and W41 as occupied for the channel;
  W42 is clear. No YouTube or provider call was made, and every pre-existing publishing row is unchanged.
- They were recorded by the one-time recorder `python -m project_atlas.publishing_retrospective record` (rehearsed
  with `--dry-run` on a temporary copy, then run live with `--backup-root`), which writes the retrospective series
  `similarstoic-youtube-external-reconciliation-v1` (P8 slot 1, P9 slot 2). Per release it records one
  `retrospective_external` package (the actual historical title and description: P9 from its SHA-verified
  `production-9/publish` files, P8 from the founder-pasted YouTube Studio text with its provenance noted), one
  `attest_external` decision, one upload and one release operation (each a single founder `succeeded` event, never
  reserved or dispatched by Conveyor), a `founder_manual` platform identity and a founder-attested receipt (P8 second
  precision, P9 day precision). It refuses unless the production is founder-accepted, its latest whole-video QA passed
  on the exact artifact, that artifact is the current render and its stored and on-disk SHA-256 equal the frozen value.
  It makes no network or provider call, is idempotent on an exact rerun, fails closed on partial or conflicting state,
  never touches the P9 never-release audit package, and takes a verified SQLite backup before any live write. Release
  conflicts stay per channel and ISO week, across all pilot keys.
- P9's separate never-release private API audit-evidence copy `JuouBEMCNzg` is not its public release.
- **P11 is the first video published through Conveyor itself** (not in the manual table above):
  `production-11-flow:founder-review:1`, artifact `production-11-flow-artifact-1`
  (`6018887a53da9d9a62061353e5acab87ecbe4674102fce9434e7b2d7f36bbc85`, 36.400 s),
  https://youtube.com/shorts/62mEQWPWVpE, public 2026-10-16T17:45:28Z (18:45:28 Europe/London). It was a
  founder-confirmed scheduled API upload, YouTube made it public, and Conveyor's receipt is
  `publication-receipt-similarstoic-youtube-on-demand-v1-slot-1` (Phase 3 below).
- P7 remains private evidence only, with no founder acceptance. P10 (as `production-10-r2`) is founder-accepted,
  packaged and founder-approved for a manual 2026-W42 release, but is not uploaded or published; that window
  expired unused on 19 October 2026, as decided (see below).
- Rule: any external publication made outside Conveyor (for example a manual YouTube Studio release) must be recorded
  here the same day with URL, artifact ID and SHA-256, and then recorded in runtime as founder-attested provenance
  under its own explicit authorization.

## Open lessons from Production 10

Production 10 (`production-10`, Ofgem energy price cap) has all eight images accepted. Both narration takes failed
completeness verification with repeated material in the same passage: `production-10:narration_verification:1`
(take 1) and `production-10:narration_verification:2` (the authorized retake). `production-10` remains failed at
stage `narration_verification`. In isolated non-production calibration
(`D:\ConveyorOS\channels\SimilarStoic\narration-tests\2026-10-07-loop\`), the full Script with only the figure
sentence rewritten as spoken copy ("Take a typical household paying by Direct Debit. Ofgem puts it at £1,723 a
year. That's £60 more.") passed in both takes B1 and B2 (121/121/121); the founder heard both as good and preferred
B1 as more realistic and fluid. The supported learning is only that this rewrite materially outperformed the
existing wording for Daniel; it belongs to the OPEN speakability lesson below.

The successor run `production-10-r2` exists. It froze founder-approved Script v2 (`production-10-script-v2`, only
the figure sentence rewritten as above) with `adopt_acquisitions_from: production-10`, adopted exactly the eight
currently accepted P10 images (each SHA-matched to its accepted source, zero image calls) and passed a fresh human
acquisition review. Its single narration take `production-10-r2-narration-1` (legacy request, so the v1 narrator)
passed completeness verification (121/121/121); the weighted render `production-10-r2-artifact-1` is intermediate.
The narration-aligned retimed render `production-10-r2-artifact-2` (SHA-256
`66b0b2ed6fa5d3fedce41a98895600288e47f732af8172b6a8eff0e4adde2276`, 37.633 s) passed human whole-video QA
(`production-10-r2:qa:whole-video:1`) and was accepted by the founder (`production-10-r2:founder-review:1`); the run
is `founder_accepted` and that artifact is the accepted artifact. Its **current publishing package is
`publishing-package-similarstoic-youtube-pilot-1-slot-3-v2`** (pilot key `similarstoic-youtube-controlled-pilot-v1`,
slot 3, version 2; package digest `0ab9aaec3da51739c8892c2696aa76921ca0562d5d7279c1c1b046cae5b01f2c`), created
7 October 2026 through the normal `prepare_package` path after a verified backup and read-only confirmation of that
accepted artifact and SHA-256 (legacy pilot packaging does not itself enforce the founder-accepted render; on-demand
packaging does, Phase 3). v2 differs from its
immutable predecessor `publishing-package-similarstoic-youtube-pilot-1-slot-3-v1` (digest
`acfd4be7f0a84d77214d5f1c9d23bb8c6da8f5a4d4b52daedb3d3bfe5ee654f9`) only in the description's Sources line. Manual
transfer and manual release, publication window 2026-10-12T00:00 to 2026-10-19T00:00 Europe/London (2026-W42,
clear). **v2 is founder-approved** for that manual W42 release: gate decision
`publication-gate-similarstoic-youtube-pilot-1-slot-3-v2-founder-approval` (7 October 2026, after a verified backup;
routes manual/manual, timing = the package window). v1 has no decision. P10 is **not uploaded and not published**;
there are no publication operations. The founder does not intend to use this window (2026-10-12T00:00 to
2026-10-19T00:00 Europe/London, end exclusive) and will let it expire (15 October 2026); **it expired unused on
19 October 2026**. The video, package and approval remain; P10 is unpublished. Its content states the Ofgem cap
figure of £1,723 a year for a typical Direct Debit dual-fuel household, which applies to the cap period 1 October to
31 December 2026, so its relevance ends with that period. **Founder publication decision checkpoint: by early
December 2026** (publish, or let it lapse). Any future P10 publication needs fresh verification of its packaging,
approval and publishing-series requirements. The legacy pilot series is full and windowed, so publication would
need a new on-demand package, and that needs a closed claim set with complete source attribution. Do not assume
re-approval is trivial. The publish-day runbook and SHA-manifested copy-paste metadata are kept outside
the repository in `D:\ConveyorOS\channels\SimilarStoic\production-10\publish\`; the manual route needs only the
`youtube.readonly` authorization.

The following lessons are **OPEN: they are not current implemented behaviour**. Each must land as an enforced
extension of an existing Conveyor mechanism, not as an operator habit or a parallel subsystem. Any prompt for P10
completion, P11 or later work must check this list and must not silently treat an OPEN lesson as completed.

- The script-side preflight below flags lines and figures before synthesis, but whether a flagged line is spoken
  cleanly by Daniel remains founder/editorial judgement; it has one Script of calibration evidence (the founder A/B
  in `D:\ConveyorOS\channels\SimilarStoic\narration-tests\2026-10-07-ear\`, the P10 loop calibration in
  `...\2026-10-07-loop\`, `...\2026-10-07-delivery-mode\` and `...\2026-10-07-sentence-delivery\`, manifest SHA-256
  `fb4137108b09bba7c31bc0d9851c8e3ffb55408ae0f0d3f40b3215effd6d2478`, founder verdict "I2 preferred", now narrator
  profile `similarstoic-daniel-v2`). How a punctuated fixed term such as "Buy now, pay later" should be voiced is
  still undecided; no speech-form change exists.

**Implemented and first exercised by P11** (`production-11-flow`, founder-accepted 14 October 2026; see Production
11). Same-room consistency below remains guided and checked, not enforced:

- Narration-aligned retiming now happens by default before founder whole-video review: new SimilarStoic runs
  freeze `scene_timing: narration-aligned-v1`, so the first candidate's scene boundaries are aligned to the selected
  verified take (see Canonical v2 fidelity and safeguards). This closes the P10 v1 lesson in code only.
- The script-side preflight exists: the deterministic Editorial Readiness evaluator v2 records advisory findings for
  a sourced figure whose stated category does not match its frozen source quote (the P10 case: "default tariffs:
  around 20 million", while Ofgem gives about 22 million households on default tariffs and about 20 million on
  standard variable tariffs including prepayment), nearby phrase repetition, and Daniel speakability rules. An
  Approve over such findings requires a comment.
- New SimilarStoic runs default to the v2 narrator, the prefer-mode sentence-delivery policy and N = 3 (see
  Canonical v2 fidelity and safeguards).
- Same-room consistency is **guided and checked, not enforced**: new runs freeze their exact environment authority
  and viewpoint per AssetSpec, generation sends only that viewpoint's approved plate (guided), and a v2 pass must name
  the frozen same-family, same-viewpoint comparison set (checked). Neither prevents drift: P11 Batch 2 and
  production-11b both drifted in room geometry, furniture scale and hamster scale (see Production 11). The approved
  creative standard (consistent worlds and character) is unchanged; no mechanism yet enforces it.
- Anchor fixtures are structured authority data rendered into one deterministic prompt clause, and a v2 pass must
  attest every pinned fixture as `unchanged` or `not_in_frame` (the HOME post box reused as an energy meter would be
  a failed review).
- Acquisition review of new runs requires zoomed inspection of props, and of limbs and strap for character beats,
  bound to the inspected asset's SHA-256 (see Pinned environment identity and the v2 acquisition review).

Completed: the runtime now records the P8 and P9 manual public releases (founder-attested receipts above), so
that lesson is closed.

Publishing series (updated 19 October 2026):

- The controlled pilot series `similarstoic-youtube-controlled-pilot-v1` is full (slots 1-3 are used). The ongoing
  series is `similarstoic-youtube-on-demand-v1` (Phase 3), driven by `publishing_cli` and the loopback upload screen.
- The legacy manual publishing steps (reserve upload, complete manual private upload, observe, reserve release,
  reconcile receipt) still have no CLI; the P10 runbook drives them from a Python session.

## Production 11 (founder-accepted)

Topic "Why Investing Feels Pointless at First". **`production-11-flow` is founder-accepted** (14 October 2026) and is
the first production made with the narration-led flow method, now codified as the recipe `similarstoic-flow-v1` (see
"Running a SimilarStoic production"). It was packaged, uploaded and published through Conveyor's on-demand API path
(public 16 October 2026 as `62mEQWPWVpE`, Conveyor receipt recorded 19 October; see Phase 3).

- Run `production-11-flow` (request digest `138a193984f4c702563337ce22f8bd43d5ea6dd19f06a2615a473fa09cd68ec8`),
  VisualPlan `production-11-flow-visual-plan`: 15 states over 9 frozen worlds (new scenes, character-free states and
  frozen-scene progressions adding 6 extracted objects), hook text "WHY INVESTING FEELS POINTLESS AT FIRST" on state
  1, citations S1-S3 bound to states 4-11, `render_policy` `scene-rgba-premultiplied-over-v1`.
- Images: **19 of the frozen 20 provider calls used** (18 recorded plus one SSL failure that raised before evidence
  was written, recorded in `production-11-flow:call_ledger_note:1`; that gap is now closed by dispatch records). One
  call stays unused. Two never-accepted prompts were revised before regeneration
  (`production-11-flow:spec_revision_note:1` shoot, `:2` two-thirds pile, each with the old prompt SHA-256).
- Founder acquisition review: round 1 (`production-11-flow:qa:acquisition:round-1:1` to `:15`, 14 passes with
  placements, the gold two-thirds pile failed) and round 2 (`:round-2:1`, the grey replacement). Accepted defects are
  recorded in the review notes. State 5 clarification `production-11-flow:fixture_review_clarification:1`: the pencil
  cup, green book and lamp are intentionally absent although the desk is visible; the `not_in_frame` labels of
  `round-1:5` are not literally accurate (the `intentionally_absent` review state now exists for such cases).
- Narration: founder authorization `production-11-flow:narration-authorization:1`; Daniel v2 take 1 passed
  completeness (103/103, `whisper-1`) and delivery (471 ms against the 358 ms target) and was selected (`target_met`);
  1 of 3 narration and 1 of 3 verification calls used.
- Accepted render `production-11-flow-artifact-1` (SHA-256
  `6018887a53da9d9a62061353e5acab87ecbe4674102fce9434e7b2d7f36bbc85`, 36.400 s, narration-aligned, not retimed):
  whole-video QA `production-11-flow:qa:whole-video:1` passed and founder review
  `production-11-flow:founder-review:1` accepted. The founder accepted state 1 (and the hook) at 1.40 s and state 11
  at 1.46 s as rendered.
- Backups before each P11 flow write: `D:\ConveyorBackups\pre-p11-flow-*` (each `conveyor.db`, integrity ok).

History of the earlier P11 attempts (records unchanged):

- Editorial chain (8 October 2026): `production-11-opportunity`, Idea Gate snapshot
  `production-11-idea-gate-review-snapshot` and founder Proceed `production-11-idea-gate-decision`;
  `production-11-research-pack` with sources `production-11-source-s1` (Benartzi and Thaler, QJE 1995),
  `-s2` (Tversky and Kahneman, JRU 1992) and `-s3` (Gneezy and Potters, QJE 1997), claims
  `production-11-claim-c1` to `-c4` (verbatim quotes in claim evidence), `production-11-research-readiness`
  (Ready), `production-11-angle`, `production-11-content-piece`, `production-11-title`, `production-11-hook`,
  `production-11-script` (version 1, "Script v3"), `production-11-claim-set`, `production-11-editorial-package`,
  `production-11-editorial-readiness` (Ready, evaluator v2, two advisory `SCRIPT_PHRASE_REPETITION` findings) and
  the founder Editorial Gate Approve `production-11-editorial-gate-decision`.
- Visual plan (batch 1): `production-11-visual-plan` (nine Scenes `production-11-scene-1` to `-9`: desk 1-5, lab
  6-7, garden 8-9; word-count timeline weights 3, 8, 4, 9, 14, 20, 13, 17, 14) and the round-1 anchor AssetSpecs
  `production-11-desk-anchor-spec`, `production-11-lab-anchor-spec`, `production-11-garden-anchor-spec`.
- Round-1 plates (3 `gpt-image-2` calls), **withdrawn for production use pending continuity review**: desk
  `09dcc88d5ea78a52591048a533fdd5acbd95438977fc8c37dddeec6cf58aa941`, lab
  `7f1f9eea1dcab807b53563ecd49a9d6a2edff34b4fa686ac94f9ec9be6d0c5f9`, garden
  `bafd7631bfee048509de47648b7b3135133441f23d0068f50ead79f5b91a73c1` (review copies in
  `D:\ConveyorOS\channels\SimilarStoic\production-11\anchors\round-1\`). The round-1 descriptions requested a
  frontal camera and an emptied room; the authoring rule and plate review gate in
  [`SIMILARSTOIC_CREATIVE_CALIBRATION.md`](SIMILARSTOIC_CREATIVE_CALIBRATION.md#environment-plates) now govern
  new plates. The round-1 records and assets stay unchanged.
- Round-2 plates (`production-11-{desk,lab,garden}-anchor-spec-r2`, 3 calls), **rejected for production use**: the
  plate review gate failed shadow on all three and palette/texture on desk and garden. Hashes: desk
  `445a4e24fc607dcd2e7d75eccd1b59e76053f617cff048c69ad9a866767dfb5f`, lab
  `b85bb0cd07f03450521361ed9137b5fd52b552a1cb9f7787cc5b2a5c1686a806`, garden
  `0c2ed40ac5a00d0a3bc964a431356fea09685e587e7b704aee98fabef1847eb0` (`...\anchors\round-2\`). Records unchanged.
- Experimental treatment reference: `visual-reference-authority-similarstoic-p11-experimental-treatment-v1`
  (role `composition_depth`, parent the global illustration authority, created 9 October 2026), members the P9 home
  and shop anchors (`treatment_exemplar`), guidance "Treatment only: thick dark hand-drawn outlines, mostly white
  unfilled walls and floor, flat warm fills on objects only, sparse floor dash marks, faint soft shadow. Copy no
  object, fixture, room layout or composition." It is explicitly not canonical and not a generation default; it is
  used only through explicit `visual_authority_ids` on the round-3 anchor specs. Finding: the desk run copied P9
  home's calendar and window despite that guidance.
- Round-3 plates (`production-11-{desk,lab,garden}-anchor-spec-r3`, global style plus the experimental reference,
  one call each), **founder-approved** (founder-attested): desk
  `2031eb51909c321690059a35c96ef0d7a28d3ce46a4aff3bd76a341dff6f32e7` approved 9 October 2026 13:00, with the
  recorded exception that its calendar and window resemble P9 home's but are accepted as P11 study elements of the
  same kind (calendar stays blank, window stays a window), locked within P11 only, linking no P11 and P9 rooms,
  geometry or fixtures; lab `9a8ceee8b88f03201937f6f6d64600df4c157274d27d80f8c5bdfb7542a29231` and garden
  `8f5e5f929aedadf493e81fdb560e073c4003b7daf77d597ad023f90d7534bc89` approved 9 October 2026 13:11 ("Yep this is
  fine, happy to proceed"). Review copies and contact sheets in `...\anchors\round-3\` (desk sheet
  `review-gate-contact-sheet.png`, lab/garden sheet `review-gate-contact-sheet-lab-garden.png`).
- Runtime approval records (migration 30 applied 9 October 2026, see the gate section below): founder-attested
  decisions `production-11-desk-r3-plate-approval`, `production-11-lab-r3-plate-approval` and
  `production-11-garden-r3-plate-approval` (each `approved`, sequence 1, citing the founder's chat message). The
  review sheets are imported as `asset-production-11-desk-r3-review-sheet` (`6b54e5a8…c7a5`) and
  `asset-production-11-lab-garden-r3-review-sheet` (`a836a825…4d07`, shared by lab and garden) under the
  founder-accepted holder AssetSpec `production-11-plate-review-sheets` (scene 1, review evidence, never generated).
- Room authorities (`environment_family`, parent the global illustration authority, each with its approved round-3
  plate as the only member, role `viewpoint:front`):
  - `visual-reference-authority-similarstoic-production11-desk-v1` (family `production-11-desk`), fixtures `desk`,
    `stool`, `window`, `calendar` (stays blank), `bookshelf` (books, box, potted plant on top), `desk_lamp` (on the
    bookshelf), `pencil_cup` and `book` (both on the desk).
  - `visual-reference-authority-similarstoic-production11-lab-v1` (family `production-11-lab`), fixtures
    `lab_table`, `stool` (in front of the bench), `pendant_lamp`, `filing_cabinet`, `pinboard`, `coat_peg` (with the
    lab coat), `test_tube_rack`, `flask` and `lidded_box` (all three on the bench).
  - `visual-reference-authority-similarstoic-production11-garden-v1` (family `production-11-garden`), fixtures
    `raised_bed` (left foreground), `fence`, `garden_shed`, `watering_can` and `stepping_stones`.
- Backups before each write: `D:\ConveyorBackups\pre-p11-editorial-chain-20261008-171739\`,
  `pre-p11-editorial-gate-20261008-172325\`, `pre-p11-batch1-plates-20261008-175017\`,
  `pre-p11-round2-plates-20261009-123329\`, `pre-p11-round3-desk-20261009-125655\`,
  `pre-p11-round3-lab-garden-20261009-130801\` and `pre-migration-30-p11-approvals-20261009-185703\` (each
  `conveyor.db`, integrity_check ok).
- Superseded runs (verified read-only from the runtime, 9 October 2026; still at `acquisition_review_pending`, never reviewed and not to be resumed; superseded by `production-11-flow`):
  - `production-11` (Batch 2): request digest `ae32cc61f7e93ac6c9fc08fed4add88df27862de825f0527e53c2cbfc9b32c35`,
    frozen image-call ceiling 15, 9 calls used, beat AssetSpecs `production-11-beat-1` to `-9` pinned to the three
    room authorities, status `acquisition_review_pending`. Founder look (not recorded): beats 4 and 6 fine, beat 8
    mostly fine (enlarged head), the rest drifted (room, desk and wall depth, mascot scale and face, a physically
    wrong balance, coins drawn as a roll).
  - `production-11b` (Route B follow-on on the same approved VisualPlan, revised texts): request digest
    `8a3895907f57f9a4de1ccc659e969442a6eeaa45d571956731a40fe61152d792`, frozen ceiling 18, 10 calls used (one
    `credit_balance_exhausted` failure, then nine successes on resume), AssetSpecs `production-11b-beat-1` to `-9`,
    status `acquisition_review_pending`. `production-11b-beat-5` was corrected in place before any generation of it
    (two-versus-one coins replaced by one identical coin per pan with a tilted beam); its metadata records the
    previous prompt's SHA-256 `fae9594b38f2d3d897bc21b7a0b818065470efe6fb91c14350fd4042a2125c08` and the reason.
  - Read-only review material: `D:\ConveyorOS\channels\SimilarStoic\production-11b\review\`
    (`p11-candidates-by-beat.png`, phone-size version, and `p11-candidates.md` with blank founder columns).
- Plate-anchor trial (`84084b8`, calibration specs `production-11-anchor-trial-beat-1` and `-3`, 2 calls):
  FAILED; see "P11 result" in
  [`SIMILARSTOIC_CREATIVE_CALIBRATION.md`](SIMILARSTOIC_CREATIVE_CALIBRATION.md). Experimental and opt-in; not to be
  used without a new founder decision.
- Lifecycle facts for finishing P11: adoption takes one source run whose every variant passed review, so a
  successor cannot mix production-11 and production-11b assets without a code change; reacquisition regenerates from
  the same AssetSpecs and never reads review reasons.
- Backups before the P11 runtime writes after migration 30: `pre-p11-batch2-20261009-194204\`,
  `pre-p11-anchor-trial-20261009-203343\`, `pre-p11b-batch-20261009-210538\` and
  `pre-p11b-resume-20261009-211302\` (each `conveyor.db`, integrity_check ok).

## Running a SimilarStoic production

The approved method is the recipe `similarstoic-flow-v1` (`src/project_atlas/production_recipe.py`) driven by the
operator CLI `python -m project_atlas.production_cli` (`src/project_atlas/production_cli.py`). How to draft the story
file is creative method in
[`SIMILARSTOIC_CREATIVE_CALIBRATION.md`](SIMILARSTOIC_CREATIVE_CALIBRATION.md#drafting-a-story-file). Story files for
real productions live outside the repository under `D:\ConveyorOS\channels\SimilarStoic\<production>\`.

Every live command needs `--expect-db-sha256 <current>` and `--backup-root D:\ConveyorBackups`, rehearses on a
temporary copy first (provider-free: preconditions, authorization and wiring only), then takes a verified backup
(`project_atlas.production_backup`) and runs with only that step's provider keys; `--dry-run` stops after the
rehearsal. `status`, `check-story`, `review-template` and `preview` never write the runtime.

| Step | Command | Founder gate (unchanged) |
| --- | --- | --- |
| 1 | Editorial chain and Editorial Gate (existing records) | Idea Gate, research, Script and the Editorial Gate decision; the founder approves the story file here |
| 2 | `check-story <story.json>` | Reads the drafting findings (short states, hook state, outline wording) |
| 3 | Room plates for any new room (existing migration-30 gate) | Plate approval |
| 4 | `plan <story.json>` | None beyond step 1 (writes the plan, scenes and specs under the Editorial Gate) |
| 5 | `start <story.json> --max-image-calls N --stop-on-technical-rejection yes` | Image spend for the first step |
| 6 | `preview <run> --placements <file> --out <dir>`, `review-template <run>` | Proposals only, nothing recorded |
| 7 | `review <run> <reviews.json>` | Acquisition review of every variant, including each object's centre and scale |
| 8 | `revise-spec`, `authorize-spend`, `resume --step image --expect-targets ...` | Prompt revision and spend for any reacquisition |
| 9 | `authorize-narration`, `resume --step narration` | Narration authorization (up to the frozen N takes and checks) |
| 10 | `qa <run> --outcome ...`, `founder-review <run> --outcome ...` | Whole-video QA and founder acceptance of the exact artifact |

Publication stays separate from this runbook and separately authorized: on-demand scheduled API publishing (Phase
3 below: `publishing_cli` prepare/approve, the founder-confirmed loopback upload screen, `reconcile-scheduled`).
Retiming (`POST /api/v2/productions/{run}/retime`) stays a founder decision.

### Current founder boundaries

- **P12 is underway** as a hands-off production trial (started 21 October 2026; position in Phase 5 below). It runs
  from the recipe `similarstoic-flow-v1` and the runbook above, unchanged, under the existing founder and spend
  controls. The Idea Gate, the Editorial Gate and both room plates are approved. The founder's acquisition review
  of `production-12-flow` is recorded (9 pass, 4 fail). R2 was superseded by the founder's choice of option B. The
  run `production-12-flow-r3` (16 states, 32-call ceiling) has its founder acquisition review recorded (9 pass,
  7 fail), its first recovery reviewed (2 pass, 5 fail), and its second, five-call recovery acquired: it is at
  acquisition review for those 5, at 28 of 32 calls. The review of the 5, further spend, narration, final
  rendering and publication are not authorized.
  Any other new story still needs its own founder authorization.
- **Publishing:** Phase 3 is complete and the on-demand API path is proven. Every new package, approval, upload,
  reconciliation or other YouTube action still needs its own founder authorization. YouTube changes (new scopes,
  Analytics) are Phase 4 and are gated (below).
- **Human acquisition review is retained**: tools propose (previews, templates, placements), the founder decides.
- **Every provider step needs its own explicit founder authorization** (image spend per acquisition step, narration),
  and live runtime writes need authorization and a verified backup first.
- **Tests, rehearsals and dry runs run with all provider keys removed** (enforced for tests by `tests/conftest.py`,
  for rehearsals by the CLI). Only the live step that needs a provider sees that provider's key.
- **A cross-production pose library is deferred to after P12.**
- **Pre-P12 sequence** below (founder, 15 October 2026), as amended on 20 October 2026: P12 and Analytics are
  independent (see "Founder sequencing decision"). No phase is authorized automatically; each build, migration,
  runtime change and publication still needs its own authorization.
- **Publication windows and the channel-week rule are not wanted** (founder, 15 October 2026). Since migration 31
  (applied 16 October 2026) they apply only to the legacy pilot series; the successor series
  `similarstoic-youtube-on-demand-v1` has neither. P11 was uploaded through the API with a YouTube-accepted schedule
  (16 October 2026). YouTube made it public at `publishAt` and Conveyor's independent reconciliation recorded the
  receipt (19 October 2026): real public publishing through the API is proven.

### Recording decisions (permanent working rule)

Consequential founder decisions, completed milestones, changes to operating boundaries and material verified
findings must be recorded in the appropriate repository authority document before moving to unrelated work. Use a
short documentation commit in the same working session. Exploratory discussion is not approval. Avoid unnecessary
duplication and report the verified live main SHA after pushing.

Clarifications (founder, 22 October 2026):

- **Provenance.** A consequential founder decision relayed explicitly from another conversation is recorded with
  where it came from, its date and exactly what it authorizes (and what it does not).
- **Stale references.** When an item is completed, cancelled or superseded, search the relevant authority documents
  for its identifiers (production, finding, PR, branch, commit) and correct materially stale references.
- **Evidence.** Work is complete only with verified evidence. A local fix, a draft PR or a successful rehearsal is
  not a deployed production capability.
- **Drift.** Before consequential work, compare this documentation with verified live repository state. Correct
  material drift when authorized, without a commit for every task.

### Claude Code permissions (founder, 22 October 2026, revised the same day)

Founder authorization governs consequential decisions. Claude Code normally executes the authorized work in Auto
mode without repeated technical approvals. Conveyor enforces operational, spending and safety boundaries. Permission
prompts are exceptional; denied or unsafe operations must stop and be reported, never circumvented.

- This replaces the earlier same-day model of routine scoped `ask` approvals, and before it the P12 practice of
  switching the session to a manual permission mode for a live write. The founder gates, the verification rules and
  every schema, hash, maintenance, backup, provenance, provider-isolation and spending safeguard are unchanged.
- The local configuration lives outside Git (`.claude/settings.local.json` in the Windows checkout and the
  user-level `autoMode` guidance). It keeps the deny rules (force-push and destructive Git pushes, direct edits of
  the runtime and backups), the read-only helper allow rule and one exceptional `ask` rule, for `--allow-restore`.
  It is not a complete security boundary and authorizes nothing by itself.
- If Auto mode refuses an authorized operation, stop and report the exact refusal. Do not switch modes, reintroduce
  blanket `ask` rules or try another execution route.

### Standing operating rules (founder, 22 October 2026)

1. **Recording commits are pre-authorized.** A documentation commit that records already-approved founder decisions
   or verified outcomes needs no fresh approval. It must be docs-only, with the diff checked, pushed, CI verified and
   the Windows checkout synchronized. Do not ask first.
2. **No mid-run questions within an authorized stage.** Finish the current safe operation, then stop with one
   consolidated report, only at the next founder gate or a genuine blocker. If something is unsafe or refused, stop
   and report; never work around it.

### Durable production learning (founder, 23 October 2026)

A standing requirement for every production, recorded in that production's trial log and summarized here:

- **For every verified material finding**, record:
  - the observed defect and its evidence;
  - the root cause, marking confirmed causes separately from hypotheses;
  - the existing protections, and what they failed to prevent or detect;
  - the smallest reusable improvement;
  - its status (**documented**, **guided**, **checked** or **enforced**);
  - the verification evidence needed.
- **No overstatement.** A documented lesson or a revised one-off image prompt is not a completed Conveyor
  improvement.
- **Agent recommendation against founder decision.** At each acquisition review, record the agent's original
  per-asset recommendation, exactly as made before the founder's decision, next to that decision. Track:
  - total reviewed assets and the agreement rate;
  - founder failures the agent recommended as passes;
  - founder passes the agent recommended as failures;
  - recurring defect categories the agent missed.
  Evaluate improvement over later productions on the same measures, acknowledging small samples.
- **After P12**, propose one bounded, prioritized task that converts the highest-value findings into reusable
  checks or guidance with regression tests. Do not implement it without separate founder authorization.
- Use the existing trial log and this document; no separate tracking system.

### Verification working rules (founder, 16 October 2026)

- Any test run used to justify a commit must preserve and check pytest's real exit code (`set -o pipefail` or an
  explicit check of the exit status). A filter such as `| tail` must never decide whether a commit proceeds. The
  commit is a separate step, taken after a real exit 0.
- Long verification (the full suite, CI) is waited on to completion before ending a turn: write the output to a
  file, then wait in consecutive foreground calls until an exit code is reported. Never end a turn with "I'll
  report when it finishes".

### Pre-P12 sequence (founder, 15 October 2026)

**Permanent working rule:** complete the phases below in order. After each phase, record its verified outcome,
decisions, remaining obligations and evidence here before moving to the next phase. Every new session must consult
this section. No subsequent phase is authorized automatically.

**Founder sequencing decision (20 October 2026), amending the order above for Phases 4 and 5:**

- P12 and Analytics are independent. P12 does not require Phase 4 completion or Google's decision. P12 stays
  separately authorized, with the unchanged `similarstoic-flow-v1` and the existing founder and spend controls. This
  decision neither authorizes nor prioritizes P12.
- Analytics remains the next development priority. Its next step is a read-only implementation plan for the approved
  Option B design; implementation needs separate authorization.
- Analytics activation stays gated by Google's written approval (or confirmation that none is required), the
  privacy-policy update, renewed acceptance and separate Analytics consent. No new scopes or live Analytics access.
- P12 checkpoint (historical: the founder started P12 on 21 October 2026, Phase 5): reconsider authorizing P12 when
  the switched-off Analytics implementation is verified, when the plan is not approved, or when implementation stalls
  awaiting an external decision. The founder may revisit P12 earlier. Do not automatically substitute another
  engineering project.
- Reason: the 19 October audit introduced an external approval wait that should constrain Analytics activation, not
  P12.

**Phase 1 — Skills and external capabilities: assessment COMPLETE.**

- Adopted: the user-invoked `/zero-spend-verify` skill (`.claude/skills/zero-spend-verify/`), which runs the
  regression tests with every provider key removed.
- Adopted: the repeatable P9 retention-alignment procedure (below).
- Adopted: the Task Observer principle: a correction is closed only when a mechanism (a test or a check) prevents it,
  through the existing decision records, lessons and tests.
- The other research decisions and optional evaluations stay as recorded in `ROADMAP.md` ("External capabilities —
  research decisions"). The image-provider blind bake-off is deferred until after P12, so it cannot confound P12's
  repeatability test. The optional security-reviewer subagent is to be evaluated when Phase 3 is planned.

**P9 retention-alignment experiment (method validation, done; adopted as a repeatable step):**

- Data source: the founder's manual YouTube Studio export of P9's audience retention (`Dd76ERbxg_w`; organic
  absolute retention and "Compared to other videos" by video position, 1% steps). It is not API data.
- Timing source: the frozen snapshot of the accepted artifact `production-9-attempt-2-artifact-3` (34.400 s): exact
  scene cuts (250 ms crossfades) and phrase-level caption cues whose timing is a pause-anchored estimate. No
  word-level timing exists for P9. Each retention position is one 0.344 s bucket (about ±0.35 s).
- Result: the observed drops (about 0.7-1.4 s in the hook line, about 8.3-8.6 s late in the long, dense scene 2,
  about 28.6-29.6 s as the "aren't covered" sentence completes before the final scene) and the stable 75% stretch
  (about 20-28.5 s, scenes 5-7) align cleanly with P9's own records. These are hypotheses only, not causal findings.
  "Compared to other videos" is YouTube's own measure, reported as returned.
- Studio summary (founder's screenshot, 15 October 2026): 46 total views, 39% stayed to watch, 0:28 average view
  duration. The retention curve's denominator and rounding method are not documented; do not infer them from the
  6.25-point increments.
- **Founder decision: repeatable, founder-supplied, offline step (no code yet).** Procedure:
  1. The founder exports the video's audience-retention CSV from YouTube Studio.
  2. Store the export as founder evidence under the channel folder
     (`D:\ConveyorOS\channels\SimilarStoic\<production>\retention\`), never in the repository.
  3. Read-only, offline, zero spend: verify the published video against the accepted artifact (ID, SHA-256,
     duration); take the cuts and caption phrases from that artifact's frozen snapshot (for P11 onwards also the
     frozen `scene_timing` evidence and the story file); convert positions to seconds and align them.
  4. Write one page: the aligned table, each timing source and its precision, and hypotheses only. No derived numbers
     (no differences, ratios, rankings or scores); YouTube's values are quoted as exported.

**Phase 2 — Google compliance: REVIEWED; formal Analytics audit SUBMITTED 19 October 2026; Google's response
PENDING.**

- Google acknowledged the YouTube API Services submission on 6 October 2026, sent a review update on 7 October and
  closed it on 8 October (founder's email thread).
- The exact original submission wording has not been located in the available email thread or the evidence folder.
  The recorded commitment stands: before any new YouTube API use (such as Analytics), update the privacy policy and
  notify YouTube in writing.
- Historical: on 16 October 2026 the founder emailed an inquiry about the planned Analytics use as a reply on the
  closed 6-8 October thread. Delivery to a human on a closed case is unconfirmed, and no reply is recorded.
- **Formal notification route.** Developer Policies III.D ("Usage and Quotas") says: "If your API Client's use case
  changes ... you must notify YouTube of the change by resubmitting an API Compliance Audit and receive approval".
  The route is therefore Google's YouTube API Services Audit and Quota Extension Form
  (https://support.google.com/youtube/contact/yt_api_form?hl=en-GB), not a reply on the old thread.
- **New audit submitted by the founder on 19 October 2026** for the proposed read-only YouTube Analytics use. The
  submitted facts:
  - project `1031021502761`, channel SimilarStoic `UC1cX-OTF9-LZeNo5TaFgrgQ`;
  - existing use unchanged: video uploading and account management, with `channels.list`, `videos.list` and
    `videos.insert`;
  - proposed: YouTube Analytics API `reports.query`, under a separate authorization (`yt-analytics.readonly` +
    `youtube.readonly`), for non-monetary video metrics and audience retention, for the operator's own editorial
    learning;
  - collection about 24 h, 72 h, 7 d and 28 d after publication;
  - no monetary or revenue data, and no derived numeric metrics, scores or rankings;
  - "No change/Default quota (10K quota points)" selected; no derived-metrics or extended-storage allowance
    requested;
  - Analytics disclosed as not implemented and not active.

  The form has no exact-fit request type for a voluntary use-case change without extra quota. The founder chose the
  general audit option ("…request additional quota") and explained the discrepancy in the narrative. The narrative
  also discloses the 16 October email as a possible duplicate.
- Evidence (outside the repository; it contains account details and stays out of GitHub), in
  `D:\ConveyorOS\evidence\youtube-audit\2026-10-19\submission\`:
  - `01-analytics-audit-submission-confirmation.png` (SHA-256
    `3cdc2e9e1689dd8cf99c0abf9815647d93480e30fb67b22d1bc913a1f4fccc94`): Google's page "Your email has been sent —
    Thank you for submitting the YouTube API Services form". **The website submission is confirmed.**
  - `02-submitted-audit-narrative.txt` (SHA-256
    `671115b1331f4fa3b8ca042621017209c837cd972c049b73bedfa7c559085baf`): the founder's saved copy of the submitted
    narrative. Google's form shows no echo, so exact identity with what Google received cannot be independently
    verified.
  - `03-google-acknowledgement-email.png` (SHA-256
    `47208588d61532550beb552c057ddbad5e05b07d67b888dc94e338c329a57d07`; a copy of the founder's screenshot
    `Screenshot 2026-10-19 155522.png`). It shows Google's email "YouTube API Services: Thank you for your
    submission" from YouTube API Quota, received 15:24 on 19 October 2026: "We will follow up with a response once
    the application has been reviewed." **Google's receipt of the submission is acknowledged.**
  - The 6 October evidence is untouched.
- The evidence shows an acknowledgement email, not an email-verification step. No verification link or its completion
  is evidenced, and none is recorded as needed.
- No case or reference number is stated in the acknowledgement. **Google's review, approval or determination of the
  Analytics use is pending.** The submission is the formal written notification. Whether it satisfies the
  notification obligation is established only by Google's response.
- **Google review update (founder's screenshot of the official YouTube API Services email thread):**
  - 19 October 2026: Google acknowledged receipt of the submission.
  - 20 October 2026: the YouTube API Services Team confirmed that its compliance review was already in progress and
    that it had received the Project Key and Attachment. It will contact the submitter through the existing email
    thread if further information is needed.
  - This confirms an **active review only**. It is not approval, not authorization to activate Analytics, and not
    confirmation that approval is unnecessary. **Google's written decision remains pending.**
- Material difference from the approved Phase 4 design: the narrative commits that no Analytics request is made until
  YouTube **approves the change, or confirms in writing that approval is not required**. That is in addition to
  implementing and testing, the privacy-policy update, renewed acceptance and separate Analytics consent. The Phase
  4 activation order (YouTube block below) did not include this approval wait, so it is now a binding activation
  requirement. Scopes, method, metrics, retention and re-verification, deletion periods, the no-derived-metrics rule
  and quota match the approved design.
- The OAuth app and both authorizations remain as recorded (YouTube block below). The durability check is due on or
  after 23 October 2026 and still needs explicit founder authorization.
- Future analytics compliance obligations stay open (Phase 4;
  [`drafts/YOUTUBE_ANALYTICS_COMPLIANCE_DRAFTS.md`](drafts/YOUTUBE_ANALYTICS_COMPLIANCE_DRAFTS.md)).

**Phase 3 — On-demand publishing: COMPLETE (19 October 2026).** Conveyor published P11 through its own API path and
independently verified the public outcome.

- Conveyor's API upload (16 October 2026): one founder-confirmed private `videos.insert` with `status.publishAt`
  (video `62mEQWPWVpE`).
- YouTube's scheduled public transition: YouTube made the video public at `2026-10-16T17:45:28Z`, 28 seconds after the
  scheduled `2026-10-16T17:45:00Z`. Conveyor did not dispatch it.
- Conveyor's independent reconciliation (19 October 2026): a read-only observation of the exact video, then the
  publication receipt (P11 reconciliation record below).

Applied and merged (founder-authorized, one sitting, 16 October 2026; every check passed):

- Maintenance task "Conveyor YouTube maintenance" disabled first (no sidecars, no other process on the runtime) and
  re-enabled only after `main` contained migration 31.
- Before: runtime `conveyor.db` SHA-256 `75829bfa0740bc35c31505ee85ff70c9c29971b0d6afeead8f0a39da960a37ec`, schema 30.
- Verified backup: `D:\ConveyorBackups\pre-migration-31-on-demand-publishing-20261016-150347\conveyor.db`, SHA-256
  `1f33831f5f89e2199713c67a44392ea9ebbcdec2866576828b06faa49f52b5a1` (integrity ok, 0 FK violations, content
  identical, schema 30).
- Migration 31 applied once with the branch code at `2921ed9`. After: SHA-256
  `5f1c982e877f606ea9e3521089210a8182ab9b8c6ae223f42493d9c322150a81`, schema 31.
- Verified read-only against the backup:
  - `integrity_check` ok and `foreign_key_check` empty;
  - all 68 tables' fingerprints identical except `schema_migrations` (30 → 31 rows);
  - schema changes exactly: the rebuilt `publishing_packages` and `publication_receipts`, the scoped
    `publication_receipt_weekly_limit` trigger and the new `idx_publication_receipts_channel_week` index; nothing
    removed, no `_v30` leftovers.
- PR #1 merged with merge commit `c5a97292039d9b1084242afd677fb891b424c17c` (parents `3222150`, `2921ed9`); CI on
  `main` run 38912834217 passed. The main checkout was pulled to `c5a9729`.

P11 on-demand package prepared and approved (founder-authorized, 16 October 2026; no YouTube call, no upload, no
`publishAt` chosen):

- Package `publishing-package-similarstoic-youtube-on-demand-v1-slot-1-v1` (series
  `similarstoic-youtube-on-demand-v1`, slot 1, week `on-demand`). Artifact `production-11-flow-artifact-1`, SHA-256
  `6018887a53da9d9a62061353e5acab87ecbe4674102fce9434e7b2d7f36bbc85`.
- Package digest `7d0249f7715174f93b3f66c0bb6c5fdd9484319b84a16e3e22842b5f1d707fff`, identical to the reviewed dry
  run. Source-credits digest `301f5de9f1328e30b09454aa3862a2c92ed049617b396e9ac1d00e507809cb42` (claim set
  `production-11-claim-set`; three peer-reviewed sources).
- Metadata: `D:\ConveyorOS\channels\SimilarStoic\production-11\publish\p11-on-demand-metadata.json`. Title "Your
  investments barely moved in a year. Should you sell?". Founder decisions:
  - the original source URLs are kept (the founder confirmed the Tversky & Kahneman EHESS PDF);
  - Sources follow `#Shorts`;
  - `altered_or_synthetic_media.declare_to_youtube` is false (non-realistic animation; AI narration voice disclosed
    in the description).
- Founder approval `publication-gate-similarstoic-youtube-on-demand-v1-slot-1-v1-founder-approval`.
- Backups:
  - before prepare:
    `D:\ConveyorBackups\pre-publishing-prepare-publishing-package-similarstoic-youtube-on-demand-v1-slot-1-v1-20261016-153426\conveyor.db`
    (SHA-256 `57963d33904fd8e508a7ea05480a6e758887dec8cdd8f20c0bbdae1234f3879b`);
  - before approve:
    `D:\ConveyorBackups\pre-publishing-approve-publishing-package-similarstoic-youtube-on-demand-v1-slot-1-v1-20261016-153440\conveyor.db`
    (SHA-256 `c69baac0140f09c1e55ce59cf6cdecc3984808b4a6632e1ee82ab82ea794119e`).
- Runtime database SHA-256: `5f1c982e…0a81` → `4e821bde…5981` (prepare) → `3e2148eb71f4f02deaee41fc0576f089a63aa6bbac38da8df4ebc2554c041040` (approve).
- **Founder decision (16 October 2026): publish P11 as soon as practical, not after 23 October.** The P11 proof no
  longer depends on the 23 October OAuth durability check, which stays a separate obligation. Before the upload: a
  verified backup and `youtube_consent reconfirm` with both authorizations `reconfirmed`. Then the founder personally
  reviews and confirms the scheduled upload (title, description, private, `publishAt`) on the loopback upload screen;
  after `publishAt`, `reconcile-scheduled`. Each step is separately authorized.

P11 scheduled upload — Conveyor's first successful real scheduled YouTube API upload (16 October 2026):

- Preconditions:
  - verified backup `D:\ConveyorBackups\pre-oauth-reconfirm-p11-publication-20261016-155740\conveyor.db` (SHA-256
    `b2dfc715dbaa75470d9a2e87a9fae43c845a09dc3f046a9d2263780eb5afb7cf`);
  - `youtube_consent reconfirm` returned `readonly: reconfirmed` and `upload: reconfirmed` (14:57 UTC); no
    credential was deleted and no data was purged.
- First attempt: refused before anything reached YouTube ("The confirmed description must keep the source credits
  exactly"). Browsers submit a textarea's line breaks as CRLF, while the frozen source credits use LF.
  - Fix: PR #2 (branch `fix-upload-form-newlines`, `df6d151`), merge commit
    `83ba00cfd3cdb2992a4dec857fec598974b3dd52`. The upload screen now normalizes CRLF/CR to LF in the submitted
    description before validation and before the confirmed intent is recorded.
  - Tests: CI passed, and the full `/zero-spend-verify` suite passed (750, exit 0).
  - Source-credit tampering still fails closed: edited, removed, reordered or dropped sources are refused before
    dispatch, through the real form path. The service-layer exact-credit check is unchanged.
- Retry on the corrected main: the founder reviewed and confirmed the scheduled upload on the loopback screen. One
  `videos.insert` (private, with `status.publishAt`).
- Stored journal, read-only and reconciled with the founder's result-page report (consistent):
  - **YouTube video ID `62mEQWPWVpE`** on channel `UC1cX-OTF9-LZeNo5TaFgrgQ`.
  - Upload operation `publication-operation-2a975ee56f0b5558f46fc781a302211db54d21f57b667f37cd303a81e212124a`
    (schema `scheduled-upload-v1`, attempt 1).
    - Events: reserved 16:25:06Z → dispatch_started 16:25:07Z → remote_identity_observed 16:25:16Z → succeeded
      16:25:16Z.
    - Requested at 16:25:08Z, completed at 16:25:15Z. Requested and returned privacy `private`, upload status
      `uploaded`.
    - Requested and returned `publishAt` `2026-10-16T17:45:00Z` (18:45 BST).
  - Founder confirmation: actor `founder`, confirmed 16:25:06Z, expiry 16:40:06Z, used once. The confirmed title and
    description are byte-identical to the frozen package (no CR); source-credits digest `301f5de9…cb42` matches.
  - Publication `platform-publication-2a975ee56f0b5558f46fc781a302211db54d21f57b667f37cd303a81e212124a`
    (identified 16:25:16Z, identity source `api`).
  - Scheduled transition (release) operation
    `publication-operation-c9e6e085df76725a506a7767472af5aa122e2613f7c13cb201c7dabb6717e3bf` (schema
    `scheduled-public-transition-v1`): reserved, then `progress` by actor YouTube, `scheduled-commitment-accepted`,
    `conveyor_dispatch: false`. Outcome pending at upload time (succeeded on 19 October, below).
  - At upload time, no status snapshot and no receipt.
- The unaudited project's private-only lock no longer applied: YouTube made the video public at `publishAt` (record
  below).

P11 publication reconciliation — Phase 3 completion (19 October 2026, founder-authorized, one live attempt):

- First attempt (19 October, before PR #3): refused before any backup, runtime write or YouTube call. The backup label
  `pre-publishing-reconcile-<publication id>` was 110 characters, but `verified_backup` accepts at most 100.
  - Fix: PR #3 (branch `fix-publishing-backup-label`, `d99b5a0`), independently reviewed and merged with merge commit
    `be48afdfe1dd4dc01ff21e5fbe22fd61230509d6`; CI on main run 39252433607 passed.
  - Valid labels are unchanged. Oversized or invalid labels become a readable prefix plus a 12-character SHA-256
    fingerprint (at most 100 characters). `verified_backup`'s validation is unchanged.
  - Tests: the real CLI backup path for prepare, approve and reconcile-scheduled, with full-length IDs. The full
    `/zero-spend-verify` suite: 761 passed, exit 0.
- Pre-checks:
  - no process held the database and there were no sidecars;
  - package, approval, upload journal, publication `62mEQWPWVpE` on `UC1cX-OTF9-LZeNo5TaFgrgQ`, pending scheduled
    transition and schema 31 all as recorded; no receipt;
  - consent current.
- Dry run: stopped at its designed boundary (YouTube observation blocked); database unchanged.
- Database hashes:
  - fresh before: `4593143c3174e83bda28fddd9bd9c9d6bf8fbc81be0f2f3a6896e68962fed445` (moved by the 19 October
    maintenance catch-up run, a no-op);
  - after: `92329e8c335b6b2c37ab20c846c2cabb512a99eacaaa9c9b9ef0ced8168f7351`.
- Verified backup:
  `D:\ConveyorBackups\pre-publishing-reconcile-platform-publication-2a975ee56f0b5558f46fc781a302211db54d21f57-128e4393a261-20261019-133139\conveyor.db`
  (SHA-256 `7426ad9dc0e3e888bd4ea769c635157c1e9a7d00d313a1dd96a14f4956226872`; integrity ok, 0 FK violations,
  content identical, schema 31).
- Independent observation (read-only `videos.list`, 2026-10-19T12:31:42Z) of the exact video `62mEQWPWVpE`:
  - video ID and channel matched;
  - privacy `public`, processing succeeded, upload status `processed`, not API-locked;
  - all metadata checks passed: title, description (including the source credits), tags, category, language,
    audience, synthetic-media declaration;
  - YouTube public time `2026-10-16T17:45:28Z`, at or after `publishAt`.
- Persisted records:
  - status `publication-status-similarstoic-youtube-on-demand-v1-slot-1-public-1` (verification passed; its
    `adapter_version` column reads `offline-adapter-v1`, the service's fixed label, while the provider payload schema
    is `youtube-readonly-observation-v1`);
  - scheduled transition `publication-operation-c9e6e085df76725a506a7767472af5aa122e2613f7c13cb201c7dabb6717e3bf`:
    reserved → progress (YouTube, scheduled commitment) → succeeded (Conveyor, independent public observation);
  - **receipt `publication-receipt-similarstoic-youtube-on-demand-v1-slot-1`**: public at `2026-10-16T17:45:28Z`,
    source `provider-public-state`, second precision, first observed public 2026-10-19T12:31:42Z, week `on-demand`,
    mode `api`, receipt digest `c3a431a8e536e8e5addf338e2820848f2c152aa60fb67d95d52a8877eb74d3eb`;
  - artifact `production-11-flow-artifact-1`, SHA-256
    `6018887a53da9d9a62061353e5acab87ecbe4674102fce9434e7b2d7f36bbc85`.
- Testing lesson: both real-workflow failures (browser textarea CRLF line breaks; a 110-character backup label from a
  real publication ID) passed every synthetic test, and both failed closed before any external effect. Realistic
  browser submissions and full-length operational identifiers must be exercised through the actual workflow (real
  HTTP form path, real CLI backup path) before a live step relies on them.
- **P11 provider-data purge horizon (existing 30-day refresh-or-delete rule, unchanged).** Without a fresh verified
  observation, the daily maintenance (or the web app's start-up) deletes P11's YouTube-origin fields:
  - from about **16 November 2026**: the provider evidence on the upload and transition events (recorded 16 October);
  - from about **19 November 2026**: the status snapshot's observed values (observed 19 October), then the
    publication identity (`remote_id`, binding digest) and the receipt's `public_at`, `first_public_observed_at` and
    receipt digest.
  - Retained: Conveyor-authored records, meaning the package and frozen manifest (title, description, credits),
    approval, operation intents and journals, and the publication, status and receipt rows with their links and
    `provider_purged_at`.
  - After the purge, `collect_performance` and any analytics for P11 are refused ("purged provider binding"). P8 and
    P9 are unaffected: their founder-attested identities are not API data.
  - Refresh: a new verified status observation (the existing read-only `observe_status`, `videos.list`) within 30
    days keeps the identity for another 30 days. Only `verification = passed` counts. It is a read-only YouTube
    call, now available as the manual `publishing_cli observe` command (PR #4, below), and running it for P11 is an
    **unresolved founder decision**. Existing deletion behaviour is preserved until the founder decides otherwise.
  - P11's historical `public_at`: the transition's `succeeded` event evidence (Conveyor-authored, immutable) also
    records YouTube's `public_at`, which the purge does not clear. **Unresolved.** PR #4 fixes only future writes, and
    `observe` neither corrects nor re-verifies this stored value.
  - Earlier purge than the horizon: a definitive authorization failure (`handle_definitive`) deletes that credential
    and purges all stored YouTube API data. An unsuccessful OAuth durability check (on or after 23 October 2026,
    separately authorized) or a future maintenance reconfirmation could therefore purge P11's identity before the
    ordinary 30-day horizon.

P11 retention fixes — PR #4 merged 21 October 2026 (merge commit `a74f2df3d3a79927f6de4b6dc5294168abb78f02`,
parents `1ebcbdc`, `7cedcbb`; independently reviewed; CI on `main` run 39595240101 passed):

- Future scheduled reconciliations store YouTube's `public_at` in the success event's purgeable provider evidence,
  not the immutable Conveyor evidence, so the 30-day rule clears it.
- Interrupted-reconciliation recovery completes only from current-format, unpurged evidence. It refuses once that
  evidence is purged, and refuses an earlier-format event rather than reusing its immutable `public_at`.
- `python -m project_atlas.publishing_cli observe <publication-id> --status-id <id>` is implemented: one manual
  read-only status observation through the unchanged `observe_status`, with database SHA-256 verification, a
  rehearsal on a copy (YouTube blocked) and a verified backup. There is no scheduling, automatic refresh or
  maintenance hook. It refuses retrospective packages and purged identities.
  - Exit codes: `0` = observation recorded, verification passed, counts as an identity refresh; `2` = refused;
    `3` = observation recorded, but verification did not pass, so it does not count as an identity refresh.
  - Live refusals are reported, not raised. Observation and authorization refusals carry a warning that governed
    access may have deleted stored YouTube API data. A `reconcile-scheduled` refusal that leaves a status without a
    receipt names the recovery path (rerun, subject to unpurged current-format evidence).
- **No observation has been authorized or executed against production.**
- Tests: local `/zero-spend-verify` full suite **781 passed, 0 skipped** (exit 0, on `7cedcbb`). GitHub CI (PR run
  39587910686 and `main` run 39595240101): **630 passed, 151 skipped**. The skips are the FFmpeg-dependent tests,
  which all ran locally with the bundled FFmpeg.

Phase 3 plan as approved on 16 October 2026 (historical; completed, outcome recorded above):

- Intended outcome: controlled YouTube publication of accepted videos on founder command, without publication
  windows or the channel-week restriction. **Phase 3 must prove that Conveyor itself publishes through the API.**
- Successor series `similarstoic-youtube-on-demand-v1` with timing mode `on_demand` and an unbounded slot number.
  Packaging requires the run's founder-accepted current render (ID and SHA-256).
- Source credits: on-demand packages populate the publication description's source credits from the production's
  existing approved script claims and source evidence (`ScriptClaimSet`, `Claim`, `Source`, `ClaimEvidence`); the
  attribution is shown on the founder confirmation and frozen with the approval, and packaging fails closed where a
  sourced claim's required attribution is missing. No parallel credit system. Implemented and first used for P11:
  this closed the "source-credit projection" gap for on-demand packages.
- Per-publication founder authorization: a single-use, expiring founder confirmation bound to the package digest,
  the artifact SHA-256, the exact metadata (title, description including source credits), the privacy and the
  scheduled `publishAt`. That confirmation, given before dispatch, **is** the publication authorization; any preview
  of the private YouTube copy is optional, not a second gate.
- Proof route = **scheduled publish**: one founder-authorized private `videos.insert` carrying `status.publishAt`
  under the existing `youtube.upload` scope; YouTube performs the public transition at `publishAt`. The publishing
  journal distinguishes the scheduled commitment from the actual public outcome; success (and the receipt) only
  after independent observation that the exact video became public. Conveyor cannot cancel a scheduled release with
  `youtube.upload`; stopping it requires manual YouTube Studio intervention, and the confirmation screen says so.
  Proof video: P11, as soon as practical (founder decision, 16 October 2026; see the P11 package record above).
- Route A (a direct public `videos.insert`) is a separately authorized fallback and is not built now. `videos.update`
  and any new scope are not proposed.
- Migration 31 (applied 16 October 2026, above): rebuilds `publishing_packages` (slot CHECK ≥ 1; the pilot series keep their 1-3 limit in
  code) and `publication_receipts`, copying every legacy row verbatim. It lifts the channel-week rule **only for
  on-demand receipts** (pilot week `on-demand`): legacy series keep it in the database through the
  `publication_receipt_weekly_limit` trigger, now scoped to `pilot_week <> 'on-demand'`, and a partial UNIQUE index
  `idx_publication_receipts_channel_week` with the same scope, plus their windows and week rule in code. Every
  other trigger, index and constraint is recreated unchanged; tested fresh and as an upgrade from 30 (every table's
  fingerprint, integrity and foreign keys unchanged), and rolls back atomically on failure.
- Packaging or publishing P11 and any YouTube API call remain separately authorized.

Build result (branch `phase3-on-demand-publishing` at `2921ed9`, PR #1, 16 October 2026):

- Verification on `2921ed9`: CI run 38906794669 passed; `/zero-spend-verify` full suite 745 passed, 0 failed,
  0 skipped, pytest exit 0; focused set 41 passed.
- Built: the successor series and on-demand packaging; source credits projected from the closed claim set (fail
  closed, including an empty set); the single-use 15-minute founder confirmation; the scheduled private
  `videos.insert`; the scheduled-transition journal; `reconcile_scheduled_publication`; migration 31; and
  `python -m project_atlas.publishing_cli` (`status` read-only; `prepare`, `approve` and `reconcile-scheduled` with
  hash check, rehearsal on a copy and verified backup).
- `publishAt` must carry an explicit offset and fall between 30 minutes and **14 days** ahead (re-checked at
  dispatch). 14 days, not 30: the daily 30-day stale-data purge deletes an unobserved publication's YouTube
  identity, so reconciliation must stay well inside that window.
- Security review (read-only reviewer under `.claude/agents/security-reviewer.md`), seven findings, all fixed with
  regression tests:
  1. High: live CLI commands would have applied migration 31 implicitly → every live command refuses unless the
     database is already at the code's schema head.
  2. Medium: an uncertain upload did not block the same artifact in another slot → any non-failed on-demand upload
     of the same bytes blocks another.
  3. Medium: a schedule YouTube did not echo was closed as failed → it stays pending (unknown); the result page
     directs the founder to YouTube Studio; a receipt still needs an observed public state.
  4. Low: a stop between upload and commitment left no recovery → reconciliation records the missing commitment
     idempotently.
  5. Low: the transition was marked succeeded before the receipt's times were checked → times validated before any
     write.
  6. Low: migration 31 dropped the database week guard for legacy series too → restored, scoped to non-on-demand
     weeks.
  7. Low: the repository accepted scheduled intents on any package → only on on-demand packages, and only scheduled
     intents there.
  Also: foreign-key rebuild migrations from 31 on may not add a violation (checked before commit).
- Reconciliation recovery (independent review): if the receipt fails after the transition is recorded succeeded, a
  retry rebuilds the receipt from the public observation recorded on the success event (status ID and `public_at`):
  no new YouTube observation, status or event. A publication that already has its receipt is refused, so receipts
  are never duplicated.
- Compliance fit: scheduled publishing is the existing `videos.insert` / `youtube.upload` use (`status.publishAt` is
  a field of the declared endpoint; use case Video Uploading & Account Management). Policy 2026-10-06 covers "the
  selected video file and publishing metadata" when expressly authorised, and "authorised publishing features". It
  is not a new API use, so no policy update or YouTube notice is needed for it. Caveat (resolved 16 October 2026):
  the unaudited project's private-only lock did not apply; P11 became public at its `publishAt`.

Migration 31 apply procedure (completed 16 October 2026, record above; kept as the template for future
migrations; PowerShell in `D:\ConveyorOS\source\Conveyor`
after `. .\scripts\set_conveyor_environment.ps1`):

- **Rule:** applying migration 31, verifying, marking PR #1 ready, merging, pulling main and re-enabling
  maintenance happen in one sitting. Nothing runs from the main checkout between applying and merging.
- **Failure before merge:** restore the backup with maintenance still disabled.
- **Failure after merge:** leave maintenance disabled and report. Do not restore a version-30 backup under
  version-31 code.

1. `Disable-ScheduledTask -TaskName "Conveyor YouTube maintenance"`; confirm it is Disabled and not running, and
   that `conveyor.db` has no `-wal` or `-journal` sidecar files.
2. Record `(Get-FileHash $env:ATLAS_DB_PATH -Algorithm SHA256).Hash` and confirm the schema version is 30 (read with
   `mode=ro`).
3. Verified backup with the branch code:
   `$env:PYTHONPATH="D:\ConveyorOS\source\Conveyor-phase3\src"; .venv\Scripts\python.exe -c "import os; from pathlib import Path; from project_atlas.production_backup import verified_backup; print(verified_backup(Path(os.environ['ATLAS_DB_PATH']), Path(r'D:\ConveyorBackups'), 'pre-migration-31-on-demand-publishing'))"`
4. Apply (one repository open with the branch code):
   `$env:PYTHONPATH="D:\ConveyorOS\source\Conveyor-phase3\src"; .venv\Scripts\python.exe -c "import os; from project_atlas.persistence import AtlasRepository; AtlasRepository(os.environ['ATLAS_DB_PATH']).close()"`
5. Verify with `mode=ro` against the backup:
   - schema version 31;
   - `integrity_check` ok and `foreign_key_check` empty;
   - `table_fingerprint` identical for every table except `schema_migrations`;
   - the only schema changes are the two rebuilt tables, the scoped `publication_receipt_weekly_limit` trigger and
     the new `idx_publication_receipts_channel_week` index.
6. Mark PR #1 ready, merge it, then `git pull` in the main checkout and confirm the HEAD SHA.
7. `Enable-ScheduledTask -TaskName "Conveyor YouTube maintenance"`.
8. Record the new database SHA-256, the backup path and the date here.

**Phase 4 — YouTube Analytics: implemented offline in draft PR #5 (not merged, deployed or activated); Google's
written decision pending.**

- The approved Option B design (YouTube block below) and its activation sequence stand. The formal written
  notification was submitted on 19 October 2026 through Google's audit form. Google acknowledged receipt and on 20
  October confirmed its compliance review is in progress (Phase 2); that is not approval. Remaining sequence:
  switched-off implementation (done offline, PR #5, unmerged) → YouTube's approval, or its written confirmation that
  none is required (pending) → privacy-policy update with the matching `POLICY_VERSION` → renewed acceptance and
  analytics consent → first authorized collection.
- **Implementation status:** Analytics Option B is implemented offline, disabled by default
  (`ANALYTICS_ENABLED = False`), in draft PR #5 (branch `analytics-option-b`). It includes the additive migration 32
  (`analytics_video_checks`, durable and independently purgeable video-existence evidence), which the founder
  authorized on 21 October 2026 for isolated offline implementation and testing only. It is not merged, not applied
  to production, and not activated.
- **Founder-approved amendment (21 October 2026), cross-authorization behaviour.** It replaces the earlier
  immediate-re-check requirement outside maintenance; no extra credential plumbing is needed.
  - A definitive authorization failure immediately invokes the existing purge of stored YouTube API data, and the
    other authorizations' reconfirmation status is invalidated.
  - Within maintenance, the affected authorizations are re-verified in the same pass (the bounded logic in PR #5).
  - Outside maintenance, they are re-verified before their next use and at the next permitted maintenance run, not
    immediately from the failing command.
  - Access stays fail-closed until an authorization is successfully verified.
  - This decision does not resolve P11's historical immutable `public_at` retention defect.
- **Deployment boundary:** opening `AtlasRepository` applies pending migrations. That happens in `production_cli`
  live commands and in `youtube_consent`, including the daily 03:00 maintenance task from the Windows checkout.
  - **PR #5 must remain unmerged** until a migration-32 production rollout procedure has been independently
    reviewed and separately authorized.
  - Until then, the Windows checkout may be synchronized only to `main` commits whose highest database migration
    is 31.
- No analytics activation or additional scopes are authorized now.
- Completion criteria: authorized Analytics collection, storage, refresh and revocation verified working, **and** at
  least one compliant production-linked learning review that interprets YouTube's reported values without creating
  prohibited derived metrics. Prefer P11, the first Conveyor-published video with a provider-verified receipt; P8
  or P9 (the design's original first candidates, with founder-attested receipts whose identities are never purged)
  are allowed if P11 data is not available. P11 stays usable only while its identity is refreshed within the 30-day
  rule (purge horizon about 16-19 November 2026, Phase 3).
- Applying the Studio-export alignment procedure to API data needs its own compliance check; the Studio-export
  procedure stays independently available.
- Revocation and deletion are verified on isolated fixtures and rehearsals first. Live Google credentials and
  production data are never revoked or deleted without separate founder authorization.

**Phase 5 — P12: STARTED as a hands-off production trial (founder authorization, 21 October 2026); independent of
Phase 4.**

- P12 tests whether the P11-approved production method is repeatable on new content, using the unchanged recipe
  `similarstoic-flow-v1` and the existing production runbook.
- **Hands-off trial:** Claude Code independently generates, researches and selects the idea, then develops the
  editorial package and story file; the founder approves, rejects or redirects one recommendation at each genuine
  gate. The trial also audits Claude Code orchestration against native Conveyor automation.
  - Working materials and the single running trial log live outside the repository under
    `D:\ConveyorOS\channels\SimilarStoic\production-12\`.
  - Initially authorized (21 October): only the zero-spend editorial start (free, read-only public-web research,
    idea evaluation and the Idea Gate recommendation).
  - **Unchanged gates:** the Editorial Gate, room-plate approval, acquisition reviews, QA and founder acceptance.
    Every live database write, provider call, `spend_authorization` and narration authorization still needs its own
    founder authorization.
  - No live database writes between 02:45 and 03:30 local time or while maintenance runs. YouTube upload and
    publication are not authorized.
  - The P11 room plates are locked to P11; any P12 room needs its own plate approval.
- This sequencing decision authorizes no change to the production recipe, the production CLI, providers or spend
  gates.

**P12 position (verified 22 October 2026; founder decisions given in chat on 22 October, the latest relayed as the
founder instruction "P12 continuity, F08 review and editorial recording"):**

- Topic "The Minimum-Payment Anchor". **Idea Gate: approved** by the founder (Proceed on idea A), with authorization
  of the editorial chain up to but excluding the Editorial Gate decision. FCA Occasional Papers 42, 43 and 45 entered
  as reviewer research input at that gate (introduced during the founder's review, not found by the initial
  research; P12-F01/F02).
- **Editorial records:** the founder authorized one bounded P12 editorial-record write (operator scripts
  `story\p12_editorial_write.py` and `story\p12_editorial_chain.py`). **Written and verified on 22 October 2026 at
  14:40 local time**, run from the Windows checkout (`dc28b26`, no F08 code) with provider keys removed and without
  `--allow-restore`:
  - 22 records (41 rows in 18 tables), all `production-12-*`; nothing removed; schema unchanged at 31;
    `integrity_check` ok and `foreign_key_check` empty, checked independently in read-only mode against the backup;
  - research readiness `production-12-research-readiness` Ready; editorial readiness
    `production-12-editorial-readiness` Ready (evaluator v2, 0 findings);
  - Idea Gate decision `production-12-idea-gate-decision` (Proceed, actor `founder`, noted as recorded by Claude
    Code); sources S1-S3 (FCA OPs 42, 43, 45) carry their PDF SHA-256 and reviewer-input provenance; 7 claim-evidence
    quotes; the stored Script equals the story file's excerpts;
  - verified backup `D:\ConveyorBackups\pre-p12-editorial-chain-20261022-144047\conveyor.db` (SHA-256
    `e233115c4a4be340490ec665e99bd2eb1c489215dceccce0bc6244546341ef90`, content identical to the pre-write database);
  - report `rehearsals\live-editorial-write-3.json` in the P12 folder.

  **Editorial Gate: APPROVED by the founder** (in chat, 22 October 2026: "Editorial Gate: APPROVE the exact P12
  Script v1 and story file SHA-256 515fb3f1…534c. … Plates and spend still need separate approval."). Recorded at
  16:34 local time as `production-12-editorial-gate-decision` (Approve, actor `founder`, over
  `production-12-editorial-package` and `production-12-editorial-readiness`, comment quoting the founder) by the
  guarded operator script `story\p12_editorial_gate_write.py` (isolated tests in `rehearsals\editorial-gate-tests\`):
  - verified backup `D:\ConveyorBackups\pre-p12-editorial-gate-20261022-163424\conveyor.db` (content identical);
  - read-only verification against it: only `editorial_gate_decisions` changed (+1, -0); schema 31/31,
    `integrity_check` ok, `foreign_key_check` empty; no P12 VisualPlan or production run exists.

  Not approved by this decision: room plates and their spend, the P12-only use of the experimental treatment
  reference, `plan`, `start`, narration and publication.
- **Room plates (founder decisions, 22 October 2026):** the experimental P11 treatment reference is approved for
  P12's two room plates only (not canonical, not a default), and exactly two `gpt-image-2` calls were authorized,
  one per plate, with no retries. Run at 17:04 local time by the guarded operator script
  `story\p12_plate_stage_write.py` (isolated tests in `rehearsals\plate-stage-tests\`; hard two-call cap; live scope
  must equal the rehearsal's):
  - verified backup `D:\ConveyorBackups\pre-p12-room-plates-20261022-170436\conveyor.db` (content identical);
  - staging plan `production-12-plate-staging-plan`, scenes `production-12-plate-staging-scene-1`/`-2`, specs
    `production-12-sitting-room-plate-spec` and `production-12-harbour-plate-spec`;
  - 2 calls, both succeeded (17:04:38 and 17:04:55 local): sitting room `asset-267465b52e3141a9b7d0866a3bcd8f78`
    (`d7fcb879…40f3`) and harbour `asset-674cc95390f94163b287c3346eb8344f` (`775f7671…73a0`), each sent the global
    style reference plus the P9 home and shop anchors;
  - read-only verification: 14 rows added in 7 tables, nothing removed, schema 31/31, integrity ok, no FK
    violations; no plate approval, room authority or production run.

  Agent plate review (`review\plates\P12-PLATE-REVIEW.md`, evidence only): harbour all PASS; sitting room round 1 FAIL
  on the zoomed defect check (malformed side-table legs).
- **Plate decisions and the first acquisition step (founder, 22 October 2026):** "Harbour plate: APPROVED as is.
  Sitting room: not approved." The founder authorized exactly one more call with the side table "with three
  straight legs, about the height of the armchair's armrest" and the bookcase top clear. The founder approved it
  conditionally on passing the full plate review, then authorized: record both approvals, register both
  authorities, `plan`, and `start` with up to 13 calls, stopping on the first technical rejection.
  - Round 2 (`p12_plate_regen_write.py`, 1-call cap, spec `production-12-sitting-room-plate-spec-r2`): 1 call,
    17:23:30 local, succeeded, `asset-05ed78a90f324743bc2535b230b3e93c` (`0d3a9e2d…80ab`); full plate review PASS.
    Backup `pre-p12-sitting-room-plate-r2-20261022-172329`.
  - Approvals and authorities (`p12_plate_approve_write.py`, provider-free; backup
    `pre-p12-plate-approvals-20261022-172643`): `production-12-sitting-room-plate-approval` and
    `production-12-harbour-plate-approval` (founder-attested, bound to contact sheet
    `asset-production-12-plate-review-sheet`); authorities
    `visual-reference-authority-similarstoic-production12-sitting-room-v1` and `-harbour-v1` (`environment_family`,
    `viewpoint:front`, structured fixtures); both plates eligible.
  - `production_cli plan` (backup `pre-plan-20261022-172711`): `production-12-flow-visual-plan`, 13 scenes, 13 specs.
    This was the first live use of the F08 gate.
  - `production_cli start` (backup `pre-start-production-12-flow-20261022-172749`; `spend_authorization` max 13, stop
    on technical rejection): w1 and w2 admitted; w3 (`production-12-flow-w3-base`) came back 1254×1254 and was
    technically rejected by the aspect admission check. The step stopped with no retry. **Run `production-12-flow`:
    `failed` at stage `acquisition`, 3 of 18 image calls counted.** No acquisition review is recorded. Findings:
    - P12-F17 (corrected wording): Conveyor supports an optional `ATLAS_OPENAI_IMAGE_SIZE` but does not set it by
      default, so with no explicit size configured the provider may return a non-portrait image. The close-view
      prompt is not proven to be the sole cause.
    - P12-F18: w3's unspecified coin colour came back gold.
  - **Resume (founder, 22 October 2026):** w1 and w2 kept unchanged. Exactly four prompts were revised through
    `production_cli revise-spec`, each with a verified backup (`production-12-flow:spec-revision:1`–`:4`): w3–w6 gained
    "tall vertical 9:16 composition, full portrait frame", and w3 and w6 "plain grey coins, the same grey as ordinary
    coins". `ATLAS_OPENAI_IMAGE_SIZE` was left unchanged. Spend authorization `production-12-flow:spend-authorization:2`:
    11 calls, stop on technical rejection.
  - `resume --step image` (dry run clean; live with `--expect-targets` set to the 11 rehearsed targets; backup
    `pre-resume-production-12-flow-20261022-212344`): the first dispatch (w3) **failed with a transient network error**
    ("EOF occurred in violation of protocol", no provider request ID), and the run stopped. **Run
    `production-12-flow`: `failed` at stage `acquisition`, 4 of 18 calls counted (2 admitted: w1, w2).** The step
    consumed authorization 2, so a new founder spend authorization is needed to resume (P12-F19).
  - **Resume 2 (founder, 22 October 2026):** a new spend authorization (`production-12-flow:spend-authorization:3`,
    11 calls, stop on technical rejection), plus exactly one pre-authorized recovery for a network failure with no
    provider request ID (not used). `resume --step image` (dry run clean; backup
    `pre-resume-production-12-flow-20261022-213346`): w3 base admitted (`asset-b952f8bd8daa4aebaa50be8e26c597a3`,
    grey coins, portrait), then the `w3/tall_stack` object came back 1024×1536 and was technically rejected, and the
    step stopped with no retry. **Run `production-12-flow`: `failed` at stage `acquisition`, 6 of 18 calls counted
    (3 admitted: w1, w2, w3 base); 10 images still missing; 12 calls remain under the ceiling.** Findings P12-F20
    (object sources are judged by the full-frame aspect rule and their prompts carry no portrait wording) and
    P12-F21 (w1's bag strap is not continuous; founder review pending).
  - **Continuation (founder, 22 October 2026):** "tall vertical 9:16 composition, full portrait frame" was added to
    the four object specs and to w7, w8 and w9 (seven `revise-spec` calls, each with a verified backup; read-only
    check: exactly those seven prompts changed). Spend authorization `production-12-flow:spend-authorization:4`: 10
    calls, stop on technical rejection, no network recovery. `resume --step image` (backup
    `pre-resume-production-12-flow-20261022-215237`): **all 10 admitted**.
  - **Run `production-12-flow`: `acquisition_review_pending`, all 13 assets active, 16 of 18 calls counted, 2
    remaining.** Agent review notes: `review\acquisition-review\P12-ACQUISITION-REVIEW-NOTES.md` (recommend failing w1
    for the strap and w7 for blue-filled water; w8's black purse against the brown state-9 purse is for founder
    judgement). Findings P12-F22 (cross-world visual consistency is guided, not enforced) and P12-F23 (the ceiling
    leaves too little for review reacquisitions).
  - **Founder acquisition review (22 October 2026), recorded natively** with `production_cli review` (backup
    `pre-review-production-12-flow-20261022-221619`): `production-12-flow:qa:acquisition:round-1:1`–`:13`.
    - **Pass (9):** w1 (strap accepted as drawn), w3, `tall_stack`, w4, `one_coin`, `empty_purse`, w8 (purse accepted
      as drawn), w9, `falling_stacks`.
    - **Fail (4):**
      - w2: face and mouth distorted; the oar collides with the jetty; malformed head linework.
      - w5: torso missing between the arms; arms wrong at the dial.
      - w6: the chute is malformed at the wall; the jar coins merge.
      - w7: blue-filled water.
    - v2 evidence is bound to each asset SHA-256, with no object placements. The run is `failed` at
      `acquisition_review`; nothing was assembled or narrated; the 2 remaining calls were not used.
  - **R2 prepared offline (founder authorization; nothing written to the runtime).**
    - Story `story\production-12-flow-r2.story.json`, SHA-256
      `cd17153391f9214280b26336cbdfc06866f2acb6f5cd214c7b18e725db199fd7`: run `production-12-flow-r2`, VisualPlan
      `production-12-flow-r2-visual-plan`, proposed frozen ceiling 26 (13 initial plus 13 founder-controlled
      recovery).
    - The Script, excerpts, states, hook, claims, citations, rooms and Editorial Gate decision ID are unchanged; the
      visual text adds only the authorized corrections.
    - `check-story` 0 findings. On a temporary copy, `plan` ran under the existing Editorial Gate with the
      approved P12 room authorities pinned, and `start --dry-run` made 13 dispatches. No new Editorial Gate is
      needed.
    - Findings P12-F24 and F25.
  - **R2 live (founder, 23 October 2026):** the R2 specification (story SHA-256 `cd171533…99fd7`) and the frozen
    26-call ceiling were approved. Authorized: `plan`, `start` with up to 13 calls stopping on the first technical
    rejection, and one conditional network recovery (not needed).
    - `plan` and `start` each ran a dry run, then live with a verified backup (`pre-plan-20261023-083946`,
      `pre-start-production-12-flow-r2-20261023-084008`).
    - **All 13 were admitted first time** (07:40:26Z–07:43:15Z). **Run `production-12-flow-r2`:
      `acquisition_review_pending`, 13 of 26 calls counted, 13 remaining.**
    - Agent notes: `review\r2-acquisition-review\R2-ACQUISITION-REVIEW-NOTES.md`. The w2 face, w5 torso, w6 chute
      and w7 water are fixed. Still open: w2's left oar overlaps the jetty corner (founder judgement), and w6's
      jar coins still merge (recommend fail). Placements were proposed from the real R2 images by a zero-spend
      preview. Finding P12-F26. No acquisition review is recorded.
  - **R2 creative and pacing review (founder findings, 23 October 2026; not recorded natively; no acquisition
    pass):**
    - **Fail:**
      - w1: smile and O-shaped mouth conflict;
      - w2: incomplete mouth; expression marks merge into the waves;
      - w6: unclear mechanism, questionable relevance, merged jar coins;
      - w9: the chain merges with the paws, oar and bag; malformed chain end; stray marks.
    - w5's arms stay under review.
    - Zero-spend stand-in video on a temporary copy (`review\r2-pacing-review\preview\standin-preview.mp4`; local
      voice, approximate pacing only).
    - P11 reference: 102 words, 36.38 s, 15 states, mean 2.43 s per state. R2: 135 words, about 48 s at P11's pace,
      13 states, mean about 3.7 s, with holds of 5.0–6.4 s on states 1, 3 and 5.
    - **Option B draft** (proposal only, no live run): `story\production-12-flow-r3.PROPOSED.story.json` (SHA-256
      `3189447b…b601`), the unchanged Script over 16 states, 8 worlds and 16 images.
      - The chute and jar are replaced by the dial box's tray (automatic payments) and a purse holding one coin
        (payments by hand).
      - `check-story` 0 findings. On a temporary copy, `plan` ran under the existing Editorial Gate and
        `start --dry-run` made 16 dispatches.
    - Findings P12-F27 (the identity reference's default open smile and emphasis marks, a hypothesis) and P12-F28
      (long static holds against the P11 density). The R2 run and its frozen plan are unchanged.
  - **R3 live (founder, 23 October 2026: option B).** Approved `production-12-flow-r3` (story SHA-256
    `3189447bb4082f7625f9fd70ea0f268eb33d7a1e7d94f4091d17ff7ad274b601`, 16 states, 8 worlds, 16 images) and the frozen
    32-call ceiling; authorized `plan`, `start` with up to 16 calls, and one network recovery (not needed).
    - Backups: `pre-plan-20261023-100632`, `pre-start-production-12-flow-r3-20261023-100642`.
    - **All 16 admitted first time** (09:07:10Z–09:10:36Z). **Run `production-12-flow-r3`:
      `acquisition_review_pending`, 16 of 32 calls counted, 16 remaining.** R2 stays at acquisition review, unreviewed
      and superseded (13 of 26 calls).
    - Agent notes: `review\r3-acquisition-review\R3-ACQUISITION-REVIEW-NOTES.md`.
      - fail: w2 (oar on the jetty; default smile mouth);
      - weak: the bank card (reads as a phone) and the state-2 coin on the held bill;
      - founder judgement: w8 (closed, upright purse) and w9 (chain-coil tangle; slight "w" mouth);
      - the other 11 pass.
    - Further F27 evidence: smile mouths recurred in w2 and w9; no expression marks recurred.
    - Zero-spend placement previews and a stand-in video were made. Finding P12-F29. No acquisition review is
      recorded.
  - **R3 review safety (founder, 23 October 2026; zero-spend, nothing recorded).**
    - `preview` on a temporary copy proposes `minimum_coin` at centre [416, 935], scale 0.50
      (`placements\preview-3\`). There is also a w5 arm close-up for the founder (`zoom\w5-arms.png`).
    - Finding P12-F30: an object's placement is not bound to its base image. `falling_stacks` must therefore be
      rejected and reacquired with w9. `auto_pile` and `hand_purse` would follow w5 if w5 fails.
    - Baseline agent-versus-founder agreement: 8 of 15 decided assets (53%). Founder failures recommended as
      passes: 5, mostly mouths, marks and prop contacts. In the trial log.
  - **R3 founder corrections (23 October 2026; zero-spend, nothing recorded).**
    - The founder failed w5: the left body–arm join is unnatural and the dial is malformed (P12-F31; the agent had
      recommended a pass).
    - The founder rejected the state-2 composition: the coin reads as a puck stuck to the held bill.
    - A side-table test (`preview-4`, centre [640, 1012], scale 0.34) is physically plausible, but it neither
      carries the narration nor advances the story, so the concept is stopped (P12-F32).
    - A conceptual mock-up, not generated, proposes a thought bubble holding one small coin, through `revise-spec`
      of `minimum_coin` within R3.
    - Proposed reacquisition targets, 9 (founder decision pending): w2, w5, w8, w9, `bank_card`, `minimum_coin`,
      `auto_pile`, `hand_purse` (placement dependents of w5) and `falling_stacks` (of w9). That would make 25 of 32
      calls.
    - P12-F33: in state 1 the hook box covers the citation label. This needs a founder decision before render.
  - **R3 founder review and seven-call recovery (founder, 23 October 2026).** This replaces the nine-call proposal.
    - Preflight: the nine-call recovery had not run; the 16 active hashes matched the inspected images. The
      `falling_stacks` placement preview against the accepted w9 was clearly satisfactory.
    - `review` (backup `pre-review-production-12-flow-r3-20261023-134858`):
      - **pass:** w1, w3, w4, w7, w9 (as drawn), `low_pile` [413, 861] 0.42, `tall_stack` [826, 870] 0.36,
        `one_coin` [300, 1180] 0.38, `falling_stacks` [230, 1217] 0.40;
      - **fail:** w2, w5, w8, `bank_card`, `minimum_coin` (the authorized deviation to a thought bubble is
        recorded; the frozen Scene is unchanged), plus `auto_pile` and `hand_purse` (w5 dependency).
    - Five `revise-spec` (w2, w5, w8, `bank_card`, `minimum_coin`; exactly those prompts changed),
      `production-12-flow-r3:spend-authorization:2` (7 calls, stop on technical rejection), then `resume --step
      image` (backup `pre-resume-production-12-flow-r3-20261023-135157`).
    - **All 7 admitted first time** (12:52:09Z–12:53:27Z); no recovery used. **Run `production-12-flow-r3`:
      `acquisition_review_pending`, 23 of 32 calls counted, 9 remaining.**
    - Agent notes, before any founder decision (`review\r3b-acquisition-review\R3B-ACQUISITION-REVIEW-NOTES.md`):
      - pass: `minimum_coin` (thought bubble) and `bank_card`;
      - object pass, dependent on w5: `auto_pile` and `hand_purse`;
      - founder judgement: w2 (staging fixed; toothy grimace mouth);
      - fail: w5 (dial fixed; no arms to the dial paws, extra paws on the table rim) and w8 (purse under the
        chin).
    - Proposed placements: `minimum_coin` [680, 490] 0.55, `bank_card` [575, 1000] 0.45, `auto_pile` [545, 1120]
      0.37, `hand_purse` [905, 1222] 0.60 (`placements\preview-4\`, with a stand-in video). Not recorded.
    - Finding P12-F34 (plate–action incompatibility). Agent-versus-founder agreement through R3: 18 of 27 firm
      recommendations (67%).
  - **R3 second recovery: recomposition and five calls (founder, 23 October 2026).**
    - Review recorded (backup `pre-review-production-12-flow-r3-20261023-145414`):
      - **pass:** `minimum_coin` [680, 490] 0.55, `bank_card` [575, 1000] 0.45;
      - **fail:** w2 (fang mouth), w5 (no arms, extra paws), w8 (purse at the mouth), `auto_pile` and
        `hand_purse` (w5 dependency; the state-12 purse placement also rejected).
    - w2, w5 and w8 were recomposed by complete prompt replacement (`revise-spec`; exactly those three changed):
      w2 as rear three-quarter rowing, w5 as a medium shot with the whole body, w8 with the purse in the lap.
    - `production-12-flow-r3:spend-authorization:3` (5 calls); `resume --step image` (backup
      `pre-resume-production-12-flow-r3-20261023-145603`). **All 5 admitted first time. Run
      `production-12-flow-r3`: `acquisition_review_pending`, 28 of 32 calls counted, 4 remaining.**
    - Agent notes, before any founder decision (`review\r3c-acquisition-review\R3C-ACQUISITION-REVIEW-NOTES.md`):
      - w5: pass, with the uncertainties stated;
      - w2: founder judgement, not a pass recommendation (weak effort; the bag drawn on its back; the boat is now
        far from the mooring post, unlike w7 and w9);
      - w8: fail (two mouth lines; the purse upright, reading as a bowl);
      - objects: pass, dependent on w5;
      - `auto_pile` proposed at [590, 972] 0.28;
      - state-12 purse placement unresolved: on the table [705, 1002] 0.42 it is small; on the rug [600, 1330]
        0.70 it is off the table.
    - Contact sheet and stand-in video: `placements\preview-2\`. Findings P12-F35 and F36.
- **Story file:** `story\production-12-flow.story.json`, SHA-256
  `515fb3f14dbd6e9b2b8d00f907d74d9db1753f96dc78f6da5e74a6347875534c` (13 states, 9 worlds, 4 objects, 2 new rooms;
  `check-story` 0 findings). State 13 now shows three coin stacks stepping down from left to right instead of an
  hourglass. Approved at the Editorial Gate (above).
- **Production database observations (read-only, 22 October 2026):** before the editorial write, schema 31 (code
  head 31), no P12 rows, SHA-256 `6e61b351a05fd08d67907bda81aae76ea3c0f8049097ccb9dba148c9eb0826e8` (unchanged by
  both earlier refused attempts); after it, `6fbeaaa9a65d8bb63488953d15b41d753db5909d32d16bfe0ee8488225798134`;
  after the Editorial Gate decision, `7c2f8405144eead535d9f4bbab7c10ff4ee71de6de0d8cc1e8904d2fc595555d`; after the
  room plates, `86dfb3633e993c1bb0ad4bfe12fabb9a48d0c808945675aa8540e0f8488b282d`; after the stopped `start`,
  `1e13cbf09222caa2f8c50183d043f843cfa5a99986a5e1441da2b5fbb9c2e726`; after the first stopped resume,
  `997d244e5fe74011e28be886141e0b4ee6d30e23febeb9bf618b2b62ddcf2c5f`; after resume 2,
  `4a956c8efbe30c8433daa2cd8970e076a5c105b9a6f6b4561e62eb9388c3b8b3`; at acquisition review,
  `264e7dd8295da8e9f9a928a88e54aeb6be9a7a7d30eda47427b352874713e1e7`; after the founder's acquisition review,
  `33373791137ea34d6da5595d3bc4baaa2902f985b5fd53b98f55cba90892e8c0`; after R2's `plan` and `start` (23 October
  2026), `2d4cbf6c9691b2754f3bf5bbc8520d4cf203a8dc7d1894aa972707136d2c12b9`; **after R3's `plan` and `start`,
  SHA-256 `8b825df0ece6659992b493ec242a183ccf091c0eafe5373383de28204f528cc3`; after the R3 review,
  `9971af223f1022dcc0fcbbb634707d304761f47f2ebd9e8ac295b9b456147c9e`; after the R3 recovery (revisions, spend
  authorization and resume), `75fe42bb1a14bced5456c23605054634336acba441e559364a9d85c95ed91761`; **after the second
  recovery (review, three revisions, spend authorization and resume), SHA-256
  `71cade554660de28bd1125bcb93dcc20b4b3f5123e04d143fab3ca9fd72eaa16`**, schema 31. These are dated
  observations, not the current value; re-verify before any write.
- Working materials, the trial log (`P12-TRIAL-LOG.md`, findings P12-F01 to F36), the operator scripts, the
  editorial package and the staging procedure live under `D:\ConveyorOS\channels\SimilarStoic\production-12\`.
- **Plate-before-plan staging route** (`STAGING-PLATES-PROCEDURE.md` there): `plan` needs the new rooms'
  `environment_family` authorities, so a staging VisualPlan under the same Editorial Gate decision carries the plate
  AssetSpecs (the P11 precedent). Rehearsed end to end on an isolated copy with simulated approvals; it is an operator
  procedure, **not native Conveyor automation** (P12-F07).
- Historical provider-cost observations (founder-reported account figures, not independently verified per-image
  costs and not P12 cost limits): about $5.30 of OpenAI expenditure from 23 September to 22 October 2026, including
  P11; about $15 of OpenAI expenditure in total since August 2026.

### Open lessons from Production 12

These are **OPEN** under the Task Observer principle (Phase 1): recording a finding, or handling it in an operator
script, does not close it. Closure needs a verified mechanism (a test or check) and, where stated, a demonstration in
a later production. The full register with evidence is `P12-TRIAL-LOG.md`.

- **P12-F08 (Conveyor defect, correct during P12):** a `production_cli` live command proceeded to the backup and
  the live write after its rehearsal reported an error, so `plan` could leave a partial VisualPlan. **Corrected and
  deployed (22 October 2026):** PR #6 (branch `fix-f08-rehearsal-gate`, head
  `60180e8edbc335f0a3cb1889dde93b549e13d2bf`, 3 files: `production_cli.py` and two test files), independently
  reviewed and merged with merge commit `fa4566cf2def6994327f435244f1492aaec29c9e` (parents `8604641`, `60180e8`);
  CI on `main` run 39804720470 passed; the Windows checkout was fast-forwarded to it (Open items).
  - The shared `_live` boundary refuses before the backup, the live database or any provider unless the rehearsal
    was clean. The one accepted stop is the step's own provider, recognised by the exception object (the rehearsal's
    own `ProviderBlocked`, bare or as the direct cause of the lifecycle's `ProductionLifecycleError`), never by
    message text; a swallowed or second block is refused. This follows the review of the first head `57a8ffc`.
  - Regression tests cover all nine live commands and the narration boundary (29 tests; 8 of the 9 review tests
    fail on `57a8ffc`). Local full suite 810 passed (exit 0, provider keys removed); PR CI run 39801213204 passed;
    focused tests in the Windows checkout after the sync: 47 passed (exit 0).
  - Behaviour change: an undersized `start`/`resume` authorization is refused before any spend.
  - Closure condition (regression test on `main`) is met. Its first live use will be the P12 `plan`.
- **P12-F11 (operator script):** the editorial write's "no other Conveyor process" guard matched its own venv
  launcher parent. Corrected in the operator script; its first authorized live use (22 October 2026) passed the
  guard and its report was read and verified. Corrected for P12 only; the native capability remains F04.
- **P12-F14 (operator script):** the editorial write restored the production database automatically on a partial
  failure. Now opt-in (`--allow-restore`, a separate founder authorization); rehearsed both ways.
- **P12-F09 (missing native capability, improve after P12):** provider usage and cost are not recorded
  (`generation_executions` keeps no token usage), so image cost is only estimable.
- Also open, improve after P12: F01 primary-source research procedure, F03 PDF access, F04 no native editorial-chain
  command, F05 a second quote from the same source silently replaces the first in `link_claim_evidence`, F07 no native
  plate step, F13 dating and group-level wording. Retained controls: F02 independent review, F06 the permission
  control. No change: F15 (the opportunity's idea-stage description still mentions the superseded hourglass).
- Creative and review findings F22 and F25–F33 carry a durable-learning status table in the trial log (all
  **documented** or **guided**; none checked or enforced yet).
  - F30: placements are not bound to their base image (confirmed in code).
  - F31: a one-sided limb join and stray prop marks were missed by the agent.
  - F32: a visual progression must make physical and narrative sense, not just add a clean object or improve
    pacing figures. Planning and review should ask, for each added object:
    - is it physically coherent?
    - is it tied to the exact narration?
    - does it advance the story?
    - does it improve pacing through meaningful development?
  - F33: the hook box covers the citation label; nothing checks overlay overlap. **Open; resolve before final
    rendering.**
  - F34: plate–action incompatibility. The plate's moored-boat arrangement left no room for the near oar. Restaging
    the boat in open water fixed it first time (confirmed geometry). The separate hypothesis that references
    dominate corrective wording stays with F27, which is preserved as a hypothesis; the character references are
    unchanged.
  - F35: recomposing a base changes the space its progression objects need. The medium-shot w5 left no room on
    the table for a phone-legible state-12 purse.
  - F36: correction outcomes are recorded separately:
    - an individual defect fixed;
    - a different defect emerging on regeneration;
    - improvement through recomposition rather than rewording (w5, w2, w8);
    - agent recommendations that classified visibly defective results as acceptable.
  - **Before P13**, the separate production-quality work must test whether Conveyor detects these actual P12
    defects (fang and double mouths, missing arms, extra paws, collisions, a stuck-on coin, undersized placements).
    It should prioritize fewer false passes over overall agreement. Not authorized yet; no new QA architecture in
    P12.

### Open items (as of 22 October 2026)

- Phase 3 (on-demand publishing): COMPLETE (19 October 2026). P11 is public as `62mEQWPWVpE` with receipt
  `publication-receipt-similarstoic-youtube-on-demand-v1-slot-1` (merges `c5a9729`, `83ba00c`, `be48afd`).
- OAuth durability check on or after 23 October 2026: pending, needs founder authorization. It is a separate
  obligation and no longer gates the P11 proof.
- Analytics audit (Phase 2): formal audit submitted 19 October 2026; Google acknowledged receipt (19 October) and
  confirmed an active compliance review (20 October). No case reference stated. **Google's written decision is
  pending; nothing is approved.** Checkpoint on or after 23 October 2026: check for Google's decision and, only if
  needed, decide a proportionate follow-up. Do not resubmit or contact Google automatically.
- Phase 4 (analytics): implemented offline and disabled in draft PR #5 (includes migration 32); not merged, not
  deployed, NOT authorized for activation. PR #5 stays unmerged until a migration-32 rollout procedure is
  independently reviewed and separately authorized. Activation also requires YouTube's approval of the 19 October
  submission (or written confirmation that none is needed). The published privacy policy stays at version
  `2026-10-06` until an authorized Phase 4 activation step.
- Phase 5 (P12): underway. Idea Gate approved; editorial records written and verified; Editorial Gate approved and
  recorded; both room plates approved (3 plate calls) and registered; `plan` done; `start` stopped at a technical
  rejection; four prompts revised; `resume` stopped at a transient network failure; resume 2 stopped at the
  `tall_stack` object's aspect rejection; seven more prompts revised; resume 3 admitted the remaining 10 (all 22
  October 2026). Founder acquisition review recorded: 9 pass, 4 fail (run `failed` at `acquisition_review`, 16 of 18
  calls). R2 (`production-12-flow-r2`) approved, planned and acquired on 23 October 2026: all 13 admitted first time,
  13 of 26 calls counted. The founder's R2 creative review failed w1, w2, w6 and w9, and a P11-density option (R3
  draft) was prepared. The founder chose option B: R3 (`production-12-flow-r3`) was planned and acquired on 23
  October 2026, with all 16 admitted first time and 16 of 32 calls counted. The founder's R3 review was recorded
  (9 pass, 7 fail) and the seven-call recovery acquired, all admitted (23 of 32). Recovery 1 was reviewed (2 pass,
  5 fail), and the five-call recovery acquired, all admitted (28 of 32). Next: the founder's review of the 5
  replacements. No further paid step is authorized. F08 is merged and deployed (Open lessons from Production 12).
  Independent of Google's decision.
- P11 provider-data purge horizon about 16-19 November 2026 (earlier on a definitive authorization failure): any
  live `publishing_cli observe` of P11 needs separate founder authorization (PR #4, merged `a74f2df`, Phase 3).
- P11's historical immutable `public_at`: unresolved retention decision; not corrected or re-verified by PR #4.
- P10 publication decision by early December 2026 (cap period ends 31 December 2026).
- Next: the founder's review of the 5 R3 second-recovery replacements. Also: check for Google's decision; on or after 23 October, the
  OAuth durability check, when the founder authorizes it.
- The Windows checkout `D:\ConveyorOS\source\Conveyor` was synchronized on 22 October 2026, by fast-forward
  (`git merge --ff-only`), from `dc28b26` to `fa4566c` (the F08 merge; 4 files: `production_cli.py`, two test files
  and this document; persistence and migrations unchanged, schema-31 code), then to the documentation commit that
  records it. Before and after: clean tree, maintenance task Ready and unchanged, production database SHA-256
  `6fbeaaa9…8134`, schema 31/31, integrity ok. (Previous sync: 21 October 2026, `1ebcbdc` to `dc28b26`.) Further
  syncs only to `main` commits whose highest migration is 31 until the migration-32 rollout is authorized.
- Analytics PR #5 (with migration 32) remains parked and unmerged.
- P10 (`production-10-r2`) is founder-accepted, not uploaded and not published; its manual 2026-W42 window expired
  unused on 19 October 2026, as the founder decided (decision checkpoint above). P11 (`production-11-flow`) is public on YouTube
  (`62mEQWPWVpE`, public 2026-10-16T17:45:28Z) with a Conveyor publication receipt.

## Approved visual evidence

The human quality benchmark for the SimilarStoic treatment; use these for same-illustrator comparison.

- Global style reference `asset-visual-authority-default-scene-language-v1`
  (`989e0da7b273a42f0bf8c229c1510b904902b1eef3336e626705966e6048ccb2`), the only member of
  `visual-reference-authority-similarstoic-global-illustration-v1`.
- P9 room anchors (founder-approved 4 October 2026): home `asset-4b30cc2631964e3ea9ea87985ba434fc`
  (`3d854b2f8f97b47882833f580caab27dd9ac6068ab3da9ed668eeb2f972a40d2`) and shop
  `asset-3888589e5e684985949ff716f6fbe5c6` (`6ee6def1bee66265e65615ebd759117807f11be985e104c3def3b0dc02f67453`).
- P8 room anchors, imported crops of finished P8 Attempt-1 scene art: office `asset-production-8-office-anchor-v1`
  (`19d1ac7a7a0400b592f2666d400d4a11f9ac9b081317019b934a92929998391a`) and store-room
  `asset-production-8-storeroom-anchor-v1` (`296dfd01de89dd4bb105be3321cd27e64262992f6ca62a8a6c6ef765fb3489f2`).
- Approved baseline beats `beat-1.png` to `beat-8.png` in
  `D:\ConveyorOS\evidence\similarstoic\approved-production-baseline\2026-10-03-v1\next-private-production\`
  (hashes in that directory's `SHA256-MANIFEST.txt`).
- P10 accepted scene art (adopted by `production-10-r2`), beats 1-8:
  `asset-fb7994766a1148d1988e817de92348b2`, `asset-0bd3f8a05e3047fdbb603c925bb3b16c`,
  `asset-b344b448bc6f479bad81edd03ef633a4`, `asset-9f47eb6b70294f63850f836e49a90b21`,
  `asset-8b73651001c341819be87c5c422320a1`, `asset-ea15a2e1b98c465e967119a4f1e1935c`,
  `asset-60f391af8da346018c4ae50aff0cbf73`, `asset-52965b5441be473ea99d9e3c30079744`.

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
persistence does not guarantee a compelling, semantically active, publication-ready product. The Persistent Scene
Model applies after acquisition: it holds an admitted image exactly, so it preserves defects already in that image
and does not prevent drift or defects inside a generated full-frame beat. Generated-image properties are guided by
prompts and references and checked by review; none is guaranteed unless a code invariant enforces it.

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
  failed calls (`forecast.narration_calls` must be 1 for legacy requests; a request with a `delivery_policy` freezes
  `narration_calls = verification_calls = N`, N = 1-3, see the bounded-attempts section below);
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

SimilarStoic new-run defaults (`NEW_RUN_DEFAULTS["similarstoic"]` in `production.py`; the v2 lifecycle is
SimilarStoic-bound, so there is no global default):

- `start()` first checks whether the run id exists. An existing run never consults today's defaults: any omitted
  defaultable field (`narrator`, `delivery_policy`, `scene_timing`, `forecast.narration_calls`,
  `forecast.verification_calls`) is reconstructed from that run's own frozen request, then validated and
  digest-compared, so the raw and the frozen forms both stay idempotent whatever the defaults later become, and an
  explicit conflicting value still fails. Runs frozen without these fields keep their historical request exactly.
- A new run that omits all four narration fields freezes narrator `CURRENT_NARRATOR_PROFILE_ID`
  (`similarstoic-daniel-v2`, its settings digest computed at freeze), delivery policy
  `similarstoic-sentence-delivery-v1` in `prefer` mode and N = 3. The legacy copy-paste shape (a narration budget
  without a narrator) is refused with a message naming the default. Explicit choices (for example N = 2, or an
  explicit v1 single take) are kept; an explicit spend ceiling is never raised.
- `scene_timing` carries no spend, so a new run without it freezes `narration-aligned-v1` even when the narration
  fields were explicit. `narration-aligned-v1` is the only accepted value; there is no weighted opt-out for new runs.

Narration-aligned first candidate (`scene_timing: narration-aligned-v1`):

- At `start()`, before any provider call, the Scene narration excerpts must concatenate to the Script under
  `speech_timing.script_words`; otherwise the request is refused.
- After the existing completeness gate, the first snapshot's durations come from the selected verified take through
  the same computation as the retime recommendation; a narration retake re-aligns to its new take. Each such render
  has versioned `{run}:scene_timing:{version}` evidence (policy, source, durations, weights and weighted durations,
  boundaries, timing and silence settings, narration asset and WAV SHA-256), shown in `status().current_render`.
- Sources are `narration_aligned`, `weighted_fallback` (alignment raised; weighted timing is recorded as a recovery
  state only) and `manual_retime` (a founder `retime` of such a run, referencing its retime evidence, actor, reason
  and durations). For a `narration-aligned-v1` run, whole-video QA `passed` fails closed when the current render
  has no scene-timing record or its source is `weighted_fallback`; `failed` is always allowed, and a founder retime
  then produces a reviewable `manual_retime` render.
- Only runs frozen before scene timing existed (every run up to and including `production-10-r2`) have no
  `scene_timing`; they are timed from the narration weights exactly as before, including on resume and retake,
  record no scene-timing evidence and are not subject to the timing QA rule.

Script preflight (Editorial Readiness evaluator `deterministic-editorial-readiness` v2,
`src/project_atlas/script_preflight.py` and `narration.speakability_findings`):

- Before the Editorial Gate, the exact Script and its frozen ScriptClaimSet evidence are checked. Findings are
  `blocking: false`, `requires_editorial_judgement: true`; the outcome stays `Ready` and the Script is never
  mutated. Figures are recognised only through the completeness normalization (`narration-completeness-v1`).
- `SCRIPT_NUMBER_QUALIFIER_MISMATCH` (a qualifier beside a Script figure appears in the frozen quotes only beside a
  different figure, or shares no word with the quote for that figure), `SOURCED_NUMBER_WITHOUT_QUOTE` and
  `SCRIPT_NUMBER_NOT_IN_FROZEN_EVIDENCE` are channel-neutral, as is `SCRIPT_PHRASE_REPETITION` (a canonical run of
  three or more words repeated in the same or the next sentence).
- `SPEAKABILITY_*` rules (two or more figures in a sentence, a dash or colon joining a figure, the narrator's
  punctuated fixed-term list, sentences over 28 words) belong to the narrator brand in `narration.py` and are found
  through the new-run default narrator. They are provisional calibration from one Script.
- Automated findings are evidence; whether a figure or line is wrong is editorial judgement. An Approve decision
  over an assessment with such findings requires a non-empty comment. Stored v1 assessments and their decisions
  resolve unchanged.

Pinned environment identity and the v2 acquisition review (new runs; no migration):

- An `environment_family` authority may declare `metadata.fixtures` (`[{key, identity[, placement]}]`, unique
  lowercase keys) and approved viewpoint plates as members with role `viewpoint:<key>`; both are validated when the
  authority is created. An AssetSpec may name `environment_viewpoint` beside its `environment_family` (or an
  explicit environment authority in `visual_authority_ids`). AssetSpecs are never mutated.
- New runs freeze `acquisition_review_profile: similarstoic-raw-world-acquisition-v2` (a `NEW_RUN_DEFAULTS` field)
  and `environment_pins`: per AssetSpec that names an environment, the exact `{authority_id, environment_family,
  viewpoint}` resolved once at `start()` (the latest family version at that moment, or an explicit pin supplied in
  the request). A missing, extra, ambiguous or contradictory pin, an unknown family, authority or viewpoint, or
  invalid fixture metadata is refused before any provider call. Existing runs reconstruct an omitted profile and
  pins from their frozen request, so resubmission stays idempotent whatever the defaults or authorities become.
- Generation and every reacquisition of a pinned run consume the frozen pin directly and never resolve the latest
  family version. The recipe freezes the pinned authority's `fixtures` and `viewpoint` (checked against the
  authority when the execution is recorded), the prompt gains one deterministic fixture clause rendered from the
  structured fixtures (no new free-text rules and no style-profile change), and only the pinned viewpoint's plate is
  sent among that authority's viewpoint plates; a pinned spec that names no viewpoint sends none of them, so plates
  of different geometries are never sent together. The recipe records every member of the pinned authority with a
  `sent` flag, so provenance never overstates the references used (historical recipes carry no flags). Each
  execution's recorded environment authority and viewpoint must equal the pin, or the attempt is never admitted.
- A v2 `passed` acquisition review must carry `zoom_inspection` with the inspected asset's `asset_sha256` and exactly
  `props` (plus `limbs` and `strap` when the AssetSpec has a character), all `passed`; `fixtures` for exactly the
  recorded authority's fixture keys, each `unchanged` or `not_in_frame`; and `geometry_compared_with` equal to the
  other variants with the same pinned family and viewpoint. Requirements come from the frozen request and the
  asset's recorded generation authority (the source generation for an adopted asset), never from the latest
  authority, so they do not change with later reviews, rounds or authority versions. A pass carrying any violation
  is refused before any review is recorded; a failed review may record the violation. Adoption still requires the
  exact recorded authorities, now including the successor's pin.
- For v2 runs, the existing read-only status (`GET /api/v2/productions/{run}`) adds
  `acquisition_review_requirements`: at `acquisition_review_pending`, one entry per variant awaiting review (variant,
  asset ID and SHA-256, zoom checks, fixture keys, comparison set), otherwise an empty list. Runs frozen without the
  profile have no such field; their status is unchanged.
- Runs frozen without the profile (production-8 through `production-10-r2`, and any historical run awaiting
  acquisition review) keep the v1 review contract and today's family resolution exactly.

Canonical post-narration retiming (`retime`, also `POST /api/v2/productions/{run}/retime`):

- It is available only from `qa_review_pending`, or after a failed whole-video QA (`failed` at stage `qa`).
- Caller-supplied per-beat durations must sum exactly to the persisted narration duration.
- The approved images, scene states and narration are reused, with zero provider calls.
- Outputs are versioned, and all prior snapshots, renders and reviews are preserved.
- The newest successful render is the current render; later human whole-video QA binds to it.
- Retime is refused after a founder decision, or once any render of the run has been packaged.
- Retime (and the read-only retime recommendation) is refused unless the current narration take passed its
  completeness verification, so timing is always computed from the current verified take.
- A retime keeps every overlay of the first candidate (hook text and citations); only durations and overlay timing
  change (regression-tested since the P11 consolidation, when `retime()` had dropped the hook).
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
  failing take stops at `narration_verification`. A `narration-aligned-v1` run's new candidate is aligned to the
  new take instead. Earlier takes, snapshots, renders and reviews remain history.
- Runs frozen without the verification forecast can authorize one check of a specific take with
  `POST .../narration-verification-authorization`; a check is never repeated for the same take.

Successor-run adoption of accepted acquisitions (optional frozen request field `adopt_acquisitions_from`):

- A successor production with its own revised Script, VisualPlan, Scenes and AssetSpecs may adopt every accepted
  image of a predecessor run instead of generating. The first version is all-or-nothing: the source run must exist
  and differ from the successor, the semantic variant keys (world, entity, variant) must match exactly, every
  source variant's current active asset must have a passing acquisition review (earlier rejected or superseded
  assets are never adopted), and the successor freezes `forecast.image_calls: 0` and `verification_calls` equal to
  its `narration_calls`. There is no fallback to image generation; the generation service is never reached.
- Before the run is created, each adoption is verified: source bytes against their SHA-256, intrinsic size and
  full-frame aspect, and the source generation's recorded authority (style, character profile and reference set,
  global visual authority, and every recorded visual authority such as the environment anchor) against the
  successor's request and AssetSpec. Any failure refuses the request with zero provider calls.
- Adopted bytes are imported under the successor's AssetSpecs. Successor acquisition evidence records `adopted`
  provenance (source run, asset and SHA-256, generation execution, acquisition evidence and passing review,
  successor AssetSpec) and no generation execution. The successor stops at `acquisition_review_pending` and needs a
  fresh normal human acquisition review; a rejected adopted image is never replaced. The source run is not
  mutated; it gains one appended `successor_run` lineage record. Packaging of the source is not a refusal reason.

Versioned narrator profiles (`project_atlas.narration.NARRATOR_PROFILES`, the single narrator authority):

- `similarstoic-daniel-v1` is the historical Daniel configuration (instruction SHA-256 `4334ac0e…b5cb`);
  `similarstoic-daniel-v2` is identical except the exact founder-preferred calibration instruction (SHA-256
  `abd56573e2c068f147b84403c3322f42b16733a7e9d2a5f97643298256bff4cb`). Each profile pins the SHA-256 of its canonical
  settings JSON; profiles are append-only.
- A new request may freeze `narrator: {profile_id, profile_sha256}`; an unknown profile or digest mismatch is refused.
  A request that froze no narrator (every request up to and including `production-10-r2`) resolves to v1 at runtime;
  nothing is written into its frozen request, so its digest and `start()` idempotence are unchanged.
- Before every narration provider call the frozen `profile_sha256` is re-checked against the registered profile;
  any drift fails closed with no provider call and is never replaced by another profile. Narration evidence records
  the profile id and settings digest; the execution keeps the exact settings used.

Bounded automatic narration attempts and prefer-mode delivery selection (new requests only):

- A request that freezes `delivery_policy: {policy_id: similarstoic-sentence-delivery-v1, mode}` must also freeze a
  narrator and `forecast.narration_calls = verification_calls = N` (1-3). Modes are `record_only` and `prefer`;
  `enforce` is defined but refused. Requests without a delivery policy behave exactly as before (one take, one check,
  latest verified take).
- Each automatic take gets one completeness check and, if complete, one delivery score computed from that check's
  own `whisper-1` word timestamps, the existing silence detection (−35 dB / 0.12 s) and the canonical Script
  punctuation: no extra transcription. Classifier `sentence-pause-classifier-v1`; score = mean of the lowest
  max(3, ceil(n/4)) sentence-boundary pauses; provisional target 358 ms from one Script's calibration, not a settled
  quality law. Evidence `{run}:narration_delivery:N` is bound to the narration asset, WAV SHA-256 and completeness
  evidence; outcomes are `passed`, `below_target`, `unreliable` (alignment cannot support classification,
  including any sentence boundary without timestamps on both sides, which is never scored as a 0 ms pause) or
  `not_applicable` (fewer than three sentence boundaries).
- Prefer loop: an incomplete take, or a complete take below target or unreliable, leads to the next take while the
  frozen budget remains; a complete take at or above target (or not applicable) is selected at once. When the budget is
  used, the best reliably scored complete take is selected, else the earliest complete take (`target_met: false`,
  `pacing_unusable` recorded); pacing never fails a run. No complete take fails closed before snapshot/render with
  `narration_budget_exhausted`. `record_only` selects the first complete take and only records its score.
  Provider or transcription failures stop the run rather than spending another take.
- Each selection is versioned `{run}:narration_selection:N` evidence (selected asset and WAV SHA-256, reason,
  candidates and scores, policy). Snapshot, retime, recommendation and render use the newest selection; a resume
  reuses a persisted selection with no provider call. Calls are counted before every take and never exceed N.
- A founder-authorized retake on a policy run is still one take plus one check, never consumes or refills the
  automatic budget and never starts the loop; if complete it is scored (never blocked by pacing) and appended as a new
  selection with reason `founder_authorized_retake`, otherwise the current selection is unchanged. A run whose budget
  was exhausted remains eligible for that explicit retake.

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
  While the OAuth app's publishing status was Testing, Google issued refresh tokens that expired after 7 days (a
  property of the Testing publishing status, not of verification); that caused those purges. The app has been In
  production since 15 October 2026 (below).
- YouTube API Services audit: submitted 2026-10-06 15:40 Europe/London; Google's confirmation received. Purpose:
  lift the private-only upload restriction on unaudited project 1031021502761; no quota increase requested.
  Declared endpoints `channels.list`, `videos.list`, `videos.insert`; scopes `youtube.readonly` and
  `youtube.upload`; use case Video Uploading & Account Management; policy version `2026-10-06`. Evidence is kept
  outside the repository at `D:\ConveyorOS\evidence\youtube-audit\2026-10-06\submission\` and must not be
  committed. Google acknowledged it on 6 October, sent a review update on 7 October and **closed it on 8 October
  2026** (the founder's email thread is the evidence). The live `videos.insert`
  documentation now says uploads from unverified API projects are not restricted to private viewing, but the
  YouTube Data API revision history still shows only the 2020 restriction; treat unrestricted API publishing as
  unconfirmed until a real API publish shows it. The closure is not an approval of the OAuth app or of any analytics
  use. Attestation made: any new YouTube API use (e.g. YouTube Analytics) first requires a privacy policy update and
  written notification to YouTube.
- OAuth app status: on 15 October 2026 the founder moved the OAuth app (project 1031021502761) from Testing to In
  production under the personal-use exemption (no verification submitted, no scope changes) and re-authorized both
  the upload and the read-only authorizations with fresh consent, each with an exact PASS. Full verification is not
  planned. A durability check (`youtube_consent reconfirm`, expected to show both authorizations `reconfirmed` beyond
  the former 7-day Testing limit) is scheduled for on or after 23 October 2026; it is pending and needs founder
  authorization (it makes API calls).
- **YouTube Analytics design: approved (Option B as revised, 15 October 2026; amended 21 October 2026, Phase 4).**
  Not in `main`: implemented offline and disabled only in draft PR #5 (unmerged). On `main` and the runtime, the
  existing 30-day purge of all stored YouTube API data still applies.
  - Data: YouTube Analytics `reports.query` for the channel's own videos, non-monetary metrics and audience retention,
    under a separate analytics authorization (`yt-analytics.readonly` + `youtube.readonly`) in the same Cloud
    project; collected at the existing 24h/72h/7d/28d checkpoints into the existing `performance_snapshots` (YouTube
    computes the totals for each date range). No migration. First candidates (original design): P8 and P9
    (founder-attested receipts); Phase 4 now prefers P11 while its identity is retained (Phase 4 above).
  - Retention (Developer Policies III.E.4(b)): analytics data is kept while needed for editorial learning, provided
    the analytics authorization is re-verified within every 30 days. Proactive re-checks start about day 23;
    transient failures are retried until day 30; if not confirmed by day 30, the data is no longer used and is
    deleted. All other stored YouTube API data keeps the 30-day refresh-or-delete rule.
  - Three local credentials (read-only, upload, analytics), but a Google-level revocation may affect all of them:
    any definitive loss triggers an immediate re-check of every stored authorization, and each that also fails is
    deleted with its data. Conveyor's revoke covers all three. Videos are checked for existence at least every 30
    days; a deleted video's analytics are deleted. Transient failures fail closed without deleting.
  - Activation gate: default off, explicit, requiring current privacy-policy acceptance; while off, upload,
    observation, maintenance, revocation and deletion behave exactly as today.
  - Learning records (III.E.4(h), conservative): a note may reference snapshot IDs, quote YouTube's values exactly as
    returned, describe the returned data qualitatively and use Conveyor's own production facts; it must not contain
    any number, comparison, ranking or score derived from API data. Labelling alone does not make derived data
    acceptable.
  - Activation order: build switched off with `POLICY_VERSION` unchanged; the formal written notification was
    submitted on 19 October 2026 (Phase 2), and YouTube's approval, or its written confirmation that none is needed,
    is required before any Analytics request; on a day with no planned upload, publish the new policy and ship the
    matching `POLICY_VERSION`, re-accept at once, then authorize analytics and collect. Drafts of the policy addition and the notice:
    [`drafts/YOUTUBE_ANALYTICS_COMPLIANCE_DRAFTS.md`](drafts/YOUTUBE_ANALYTICS_COMPLIANCE_DRAFTS.md) (not
    authority).
- Consent state (accepted version, reconfirmation times; no secrets) is a JSON file outside the repository, required
  as `--consent-state` or `ATLAS_YOUTUBE_CONSENT_STATE`; losing it forces re-acceptance and reconfirmation.
- Daily maintenance (Windows Task Scheduler, under the same Windows account that owns Conveyor's Credential Locker
  entries) always purges stale data locally and reconfirms due authorizations only with current acceptance:
  `D:\ConveyorOS\source\Conveyor\.venv\Scripts\python.exe -m project_atlas.youtube_consent --consent-state
  <consent-state.json> --db D:\ConveyorOS\runtime\ConveyorRuntime\conveyor.db maintain --client-config
  <client-config.json>` (both JSON paths outside the repository).

Founder spend control (P11 consolidation; append-only production evidence and run events, no migration):

- **Enforced.** Every billable image dispatch is recorded as `acquisition_dispatch` evidence *before* its provider
  call and counted against the frozen `forecast.image_calls` ceiling, so a call that raises at any point afterwards
  still counts. Runs acquired before dispatch records count their recorded executions exactly as before.
- **Enforced.** Every dispatch needs an unused founder `spend_authorization` (`authorized_by`, `max_image_calls`,
  `stop_on_technical_rejection`, `reason`) for that acquisition step, given with `start` (`spend_authorization`
  beside the request, never frozen in its digest) or `POST /api/v2/productions/{run}/spend-authorization`. One step
  (start or resume) consumes one authorization; without one nothing is dispatched; with
  `stop_on_technical_rejection` the step stops at the first technical rejection instead of retrying automatically.
  The state lives in the database, so every per-request HTTP service instance enforces it.
- Status shows `spend`: calls counted, the ceiling and the next step's authorization.

Progressions, character-free states, extracted objects and the hook (opt-in request fields, first used by P11):

- `render_policy: scene-rgba-premultiplied-over-v1` (alpha compositing, required for extracted objects); entity
  `initial_visible` and `depth`; transitions with `set_visible` add objects to a frozen base state by state.
- AssetSpec metadata `character_free: true` lets a full-frame image omit the character (it may not name a character
  profile); base images are pinned to their room like any other.
- Object variants (`object_center`: a frame point, or `at_review`): the generated object is cut out with the
  object-mode soft matte (every intended part kept, specks under 50 px dropped), cropped, optionally scaled once by the
  founder's `object_scale` (0-1, premultiplied area average) and placed 1:1 at the founder-approved centre recorded
  with its passing acquisition review. World evidence records each admission and an advisory outline width.
- `on_screen_text_overlay: true` renders the VisualPlan's on-screen text (the hook on state 1) in the top zone while
  its scene is on screen.

Review and decision controls (P11 consolidation, no migration):

- A v2 pass may attest a fixture `intentionally_absent` (a visible place deliberately left without it), only with a
  `fixture_notes` entry saying why (**checked**).
- `revise_asset_spec` (`POST .../spec-revision`) changes only the prompt of a variant that is missing or whose active
  asset was rejected, never a spec another run uses, and records the previous prompt and both SHA-256 digests as
  `spec_revision` evidence (**enforced**).
- A founder review records the exact current artifact ID and SHA-256 in its event; status shows it (**enforced**).

Production recipe `similarstoic-flow-v1` (`production_recipe.py`): a story file compiles into the VisualPlan, Scenes,
AssetSpecs and start request; the request freezes `recipe: {id, story_sha256}`. The recipe holds only reusable
patterns, and the P11 equivalence test proves that compiling P11's story reproduces its frozen request exactly
(apart from the recipe provenance P11 predates). Drafting findings (states that may be under ~1.5 s, a hook state too
short to read, objects without heavy outlines) are advisory evidence for the founder's Editorial step.

## Visual reference approval gate (migration 30)

`src/project_atlas/visual_reference_approvals.py` adds the append-only table `visual_plate_approvals`: per image,
sequential founder-attested decisions (`approved`, `rejected`, `withdrawn`) bound to the exact asset ID and
SHA-256 (database triggers), each citing a traceable founder authorization (`decision_reference`), with an
`approved` decision also bound to its review contact-sheet asset and SHA-256 and a per-criterion PASS/FAIL record,
plus any recorded exceptions. Decisions are founder-attested records, not cryptographically authenticated; agent
review findings are evidence, never the decision. The latest decision governs; rows are never updated or deleted.
Read them with `AtlasRepository.list_plate_approvals()`.

- Authority creation of every role refuses any member image without an eligible approval.
- At new-production authorization, before any provider call, every visual reference authority the run will use
  (global, environment pins, `visual_authority_ids`, `use_composition_depth`, `special_break_frame`) must have only
  eligible member images, checked by exact asset ID and SHA-256; an image withdrawn after its authority was created
  is refused. Runs frozen before the gate keep their established behaviour.
- `HISTORICAL_ALLOWLIST` names the 11 reference images in use before the gate (the seven canonical repository
  references, the P8 office and store-room crops and the P9 home and shop anchors) by exact ID and SHA-256. It is a
  fallback only for images with no decision record; once any decision exists, the latest decision governs.

## Schema authority

Application schema authority is the `schema_migrations` table. The repository defines contiguous versions
**1 through 31**, and the protected production runtime is at **31**: migration 31 (on-demand publishing) was applied
on 16 October 2026 under founder authorization (Phase 3 below), changing no existing row. Migration 30 was applied on
9 October 2026 under founder authorization, after a verified backup and with the maintenance task paused, changing no
existing row. The P11 consolidation (spend authorizations, dispatch records, spec
revisions, fixture clarifications and the founder-review artifact binding) uses existing append-only production
evidence and run events and adds no migration. Migration 29 was applied to the protected
runtime on 7 October 2026 under founder authorization, after a verified backup, together with the P8/P9 recording.
Migration 28 adds only append-only production-run events, cross-stage evidence, QA-review outcomes and founder-review decisions; existing
generation, persistent-scene, narration and media tables remain authoritative for their artifacts.

Migration 29 (founder-attested retrospective publications) rebuilds two publishing tables under the existing
foreign-key rebuild mode, preserving every existing row:

- `publication_gate_decisions` gains the decision `attest_external` (no routes, sequence 1 only). Triggers allow it
  only on a `retrospective_external` package, and allow such a package nothing else, so it can never become
  `approve` authority for an upload, release, observation or receipt.
- `publication_receipts.public_status_id` may be NULL only for a founder-attested receipt
  (`timestamp_source = 'founder-attestation'`, manual, `public_at` present, second or day precision, no observed
  time); a trigger binds every status-less receipt to an `attest_external` decision and vice versa. Ordinary receipts
  still require a verified public observation. Channel-week uniqueness is unchanged.
- Operations under an attestation must be manual with intent schema `retrospective-external-v1`.
- Attested receipts are excluded from the YouTube API-data purge (they hold no API data); provenance stays
  append-only and immutable.

`PRAGMA user_version = 0` does not mean that no application migrations exist. `PRAGMA schema_version = 203` is
SQLite's internal schema-cookie counter, not the Conveyor application migration version.

Migrations 25–28 remain immutable historical provenance. Migration 28 was applied to the protected production
runtime on 1 October 2026 after a dedicated pre-migration backup; migration 29 on 7 October 2026. Subsequent
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
6. Do not open the production database through application code merely to inspect it
   (`python -m project_atlas.production_cli status <run>` reads it with `mode=ro`).
7. Before any consequential action, identify the exact authorization boundary: code, migration, provider, spend,
   production, publication, evidence movement, and Git operations are separate decisions.
8. Use `ROADMAP.md` for future direction, bounded design documents for their subjects, and historical snapshots only
   for provenance.

9. To continue a production, run `python -m project_atlas.production_cli status <run>` (read-only) and find the next
   founder gate in "Running a SimilarStoic production"; the run's frozen `recipe` names the story file version it was
   compiled from. Nothing is resumed without that gate's authorization.

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
- source-credit projection (on-demand packages: Phase 3 scope, closed once implemented);
- character continuity;
- scene density;
- the hook overlay lasts only as long as state 1 (1.40 s on P11); whether it should have a minimum on-screen time is
  a founder decision;
- a failed retime has no recovery path;
- same-room consistency is guided and checked, not enforced;
- a cross-production pose library (deferred to after P12);
- runs frozen without `scene_timing` (every run up to and including `production-10-r2`) keep narration-weighted
  first candidates and may require a post-narration retime;
- provider word timestamps are requested but not persisted; captions use pause-aligned estimates between pauses;
- packaging does not yet require the current, founder-accepted render.

Each requires separate authorization.

Update this file deliberately whenever accepted current operational truth changes. Do not turn it into a chronological
diary; move superseded detail to historical/provenance records and keep this document usable as a fresh-agent entry
point.
