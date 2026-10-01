# Configuration

Keep safe, version-controlled defaults and configuration templates here. Never commit credentials, API keys, private certificates, or environment-specific secrets.

Production runtime paths are established separately through the fail-closed process contract in
`scripts/set_conveyor_environment.ps1`; see `docs/CONVEYOR_CURRENT_STATE.md`. Keep other configuration explicit,
validated, versioned where appropriate, and free of secrets.
