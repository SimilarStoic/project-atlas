# Conveyor — instructions for Claude sessions

This file only points to the authorities; it holds no rules of its own.

1. **Read [`docs/CONVEYOR_CURRENT_STATE.md`](docs/CONVEYOR_CURRENT_STATE.md) first.** It is the single operational
   authority: current state, the founder's current boundaries ("Current founder boundaries"), how to run a production
   ("Running a SimilarStoic production") and the open gaps.
2. **Creative method:** [`docs/SIMILARSTOIC_CREATIVE_CALIBRATION.md`](docs/SIMILARSTOIC_CREATIVE_CALIBRATION.md),
   including how to draft a story file for the recipe `similarstoic-flow-v1`.
3. **Authorization is per step and comes only from the founder in chat**: provider calls and spend, live runtime
   writes, migrations, production runs, publication and Git pushes are separate decisions. Do not infer one from
   another.
4. **Tests, rehearsals and dry runs run with all provider keys removed** (`tests/conftest.py` enforces it for tests).
5. **Live production writes go through `python -m project_atlas.production_cli`**, which checks the database hash,
   rehearses on a temporary copy and takes a verified backup first. Inspect the runtime read-only
   (`production_cli status`, or SQLite `mode=ro`), never by constructing `AtlasRepository` on it.
6. Story files for real productions live under `D:\ConveyorOS\channels\SimilarStoic\`, not in this repository.
