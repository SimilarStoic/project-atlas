---
name: zero-spend-verify
description: Run the P12 regression tests with every provider key removed and report the results. Tests only; changes nothing.
disable-model-invocation: true
---

# Zero-spend verify

Run the regression tests that prove the production path is unaffected, with all provider keys removed, and report
the results. This skill only runs tests. It holds no rules: the rules live in `docs/CONVEYOR_CURRENT_STATE.md` and in
the tests themselves. Do not edit files, fix failures, commit or push while running it; report and stop.

Run from the repository root with the Bash tool. Each command removes every provider key from its own environment
and uses the repository's bundled FFmpeg.

1. Focused set (a few minutes):

```bash
B=.tools/ffmpeg-9.0.1-essentials_build/bin; env -u OPENAI_API_KEY -u INWORLD_API_KEY -u LEONARDO_API_KEY ATLAS_FFMPEG_PATH="$B/ffmpeg.exe" ATLAS_FFPROBE_PATH="$B/ffprobe.exe" .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_provider_isolation.py tests/test_production_recipe.py tests/test_production_workflow.py tests/test_spend_control.py tests/test_review_controls.py tests/test_progression.py
```

   These cover: provider isolation, the P11 equivalence test, the zero-spend end-to-end workflow, the spend gate,
   the review controls, and progressions including retime keeping the hook.

2. Full suite (about 30 minutes; run in the background and wait for it):

```bash
B=.tools/ffmpeg-9.0.1-essentials_build/bin; env -u OPENAI_API_KEY -u INWORLD_API_KEY -u LEONARDO_API_KEY ATLAS_FFMPEG_PATH="$B/ffmpeg.exe" ATLAS_FFPROBE_PATH="$B/ffprobe.exe" .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
```

3. Report: the commit tested (`git rev-parse HEAD`), whether the working tree was clean, and for each run the
   passed/failed/skipped counts and every failing test name. A skip of FFmpeg-dependent tests means the bundled
   FFmpeg was not found; say so rather than counting the run as complete.
