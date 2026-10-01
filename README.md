# Conveyor

Conveyor is the long-term production operating system/platform for developing and operating multiple channels and
products. SimilarStoic is its first autonomous pilot channel and flagship proving ground; its editorial and creative
choices belong to the channel, not to Conveyor as a whole.

Project Atlas is the historical development name. Compatibility identifiers such as `project_atlas`,
`AtlasRepository`, and `ATLAS_*` remain temporarily valid technical names, but Project Atlas is not the active product
identity.

## Start here

Read [Conveyor Current State](docs/CONVEYOR_CURRENT_STATE.md) first. It is the single current operational authority.
When another document appears to conflict with it, the current-state document wins.

- [Roadmap](ROADMAP.md) contains strategy and future sequencing, not live status.
- [Current Status](CURRENT_STATUS.md) is a historical status archive.
- [Canonical Handoff](docs/CANONICAL_HANDOFF.md) is a historical handoff and governance artifact.
- [Documentation index](docs/README.md) routes to bounded architecture, policy, creative, and evidence records.

## Repository orientation

| Path | Purpose |
| --- | --- |
| `src/project_atlas/` | Current compatibility-named Python application packages |
| `tests/` | Automated tests and test support |
| `scripts/` | Bounded development and operational automation |
| `database/` | Persistence and migration documentation |
| `docs/` | Current authority, architecture, policy, creative, and historical records |
| `assets/` | Tracked project assets; not the production runtime asset store |
| `config/` | Safe version-controlled configuration |

The active repository is `D:\ConveyorOS\source\Conveyor`. Production runtime data is separate under
`D:\ConveyorOS\runtime\ConveyorRuntime`. The independent recovery boundary is `D:\ConveyorBackups`.

## Runtime environment

Before an authorized production operation in a new PowerShell process, establish the fail-closed process environment:

```powershell
. .\scripts\set_conveyor_environment.ps1
```

This validates the relocated layout and sets the existing `ATLAS_*` compatibility variables for the production
database, asset/media roots, and repository FFmpeg/FFprobe binaries. It does not start Conveyor. Do not substitute
working-directory-relative data paths or recreate legacy roots.

See [Conveyor Current State](docs/CONVEYOR_CURRENT_STATE.md#runtime-environment-contract) for the full contract and safe
starting procedure.

## Development

Install the project in a fresh virtual environment, keep secrets outside Git, and use the repository's existing Black,
Ruff, and pytest configuration for authorized code changes. Application execution, migrations, providers, spend,
production, and publication are separate authorization boundaries; onboarding through this README authorizes none of
them.
