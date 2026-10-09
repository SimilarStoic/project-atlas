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
- P7 remains private evidence only, with no founder acceptance. P10 (as `production-10-r2`) is founder-accepted,
  packaged and founder-approved for a manual 2026-W42 release, but is not uploaded or published (see below).
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
accepted artifact and SHA-256 (packaging does not itself enforce the founder-accepted render). v2 differs from its
immutable predecessor `publishing-package-similarstoic-youtube-pilot-1-slot-3-v1` (digest
`acfd4be7f0a84d77214d5f1c9d23bb8c6da8f5a4d4b52daedb3d3bfe5ee654f9`) only in the description's Sources line. Manual
transfer and manual release, publication window 2026-10-12T00:00 to 2026-10-19T00:00 Europe/London (2026-W42,
clear). **v2 is founder-approved** for that manual W42 release: gate decision
`publication-gate-similarstoic-youtube-pilot-1-slot-3-v2-founder-approval` (7 October 2026, after a verified backup;
routes manual/manual, timing = the package window). v1 has no decision. P10 is **not uploaded and not published**;
there are no publication operations. The publish-day runbook and SHA-manifested copy-paste metadata are kept outside
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

**Implemented, awaiting first production validation on P11** (each is code and offline tests only; no production
has yet exercised it):

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
- The same environment plus the same viewpoint locks room geometry, furniture scale and persistent fixture identity:
  new runs freeze their exact environment authority and viewpoint per AssetSpec, generation sends only that
  viewpoint's approved plate, and a v2 pass must name the frozen same-family, same-viewpoint comparison set.
- Anchor fixtures are structured authority data rendered into one deterministic prompt clause, and a v2 pass must
  attest every pinned fixture as `unchanged` or `not_in_frame` (the HOME post box reused as an energy meter would be
  a failed review).
- Acquisition review of new runs requires zoomed inspection of props, and of limbs and strap for character beats,
  bound to the inspected asset's SHA-256 (see Pinned environment identity and the v2 acquisition review).

Completed: the runtime now records the P8 and P9 manual public releases (founder-attested receipts above), so
that lesson is closed.

Before P11:

- The controlled pilot series `similarstoic-youtube-controlled-pilot-v1` is full (slots 1-3 are used), so an ongoing
  publishing series is needed before the next package.
- The manual publishing steps (reserve upload, complete manual private upload, observe, reserve release, reconcile
  receipt) have no CLI yet; the P10 runbook drives them from a Python session.

## Production 11 (in progress)

Topic "Why Investing Feels Pointless at First". Every record below was written through the existing repository
methods and gates; no production run, narration, beat AssetSpec or visual authority exists yet.

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
- Next: Batch 2 (nine beat AssetSpecs pinned to these room authorities and the `production-11` request).

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
**1 through 30**, and the protected production runtime is at **30**: migration 30 was applied on 9 October 2026
under founder authorization, after a verified backup and with the maintenance task paused, changing no existing row
(the publishing series migration becomes 31). Migration 29 was applied to the protected
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
- ceiling counting of generation calls that raise before acquisition evidence is persisted. This covers both a paid
  provider call that raises before evidence is recorded, and a provider call that returns an asset but whose
  post-provider technical inspection or probe raises before evidence is recorded;
- image size on reference-conditioned calls: a configured image size may be recorded in provenance but is not sent
  on reference-conditioned image-edit calls, so those calls use the provider's default size;
- runs frozen without `scene_timing` (every run up to and including `production-10-r2`) keep narration-weighted
  first candidates and may require a post-narration retime;
- provider word timestamps are requested but not persisted; captions use pause-aligned estimates between pauses;
- packaging does not yet require the current, founder-accepted render.

Each requires separate authorization.

Update this file deliberately whenever accepted current operational truth changes. Do not turn it into a chronological
diary; move superseded detail to historical/provenance records and keep this document usable as a fresh-agent entry
point.
