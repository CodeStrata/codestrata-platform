# VS Code CLI Discovery Verification (Slice 13.2)

Schema: `vscode-cli-discovery-verification:1.0.0`  
Policy: `community-vscode-cli-discovery-policy:1.0`

## Run

```bash
PYTHONPATH=. python -m verification.vscode_cli_discovery
PYTHONPATH=. python -m pytest tests/verification/vscode_cli_discovery -q
```

Report: `reports/verification/sv13-2/vscode-cli-discovery-verification.json`

## Guarantees

- Local-only, network-free discovery
- Explicit configuration fails closed (no silent PATH fallback)
- PATH discovery via direct spawn (`shell: false`), not shell `which`/`where`
- Side-effect-free `codestrata version` probe with timeout and output limits
- Strict CodeStrata product identity + semver parsing
- Provisional compatibility: CLI major 0 and ≥ 0.1.0 (matrix → 13.11)
- Activation performs no CLI probe
- Discovery failure prevents product CLI and telemetry consent
- No install/download/upgrade (guidance-only install completed in Slice 13.3)
- Epic 13 completion verified via Slice 13.15
