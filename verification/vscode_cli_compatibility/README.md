# VS Code CLI–extension compatibility verification (Slice 13.11)

Schema: `vscode-cli-compatibility-verification:1.0.0`

## Run

```bash
PYTHONPATH=. python -m verification.vscode_cli_compatibility
PYTHONPATH=. python -m pytest tests/verification/vscode_cli_compatibility -q
```

Report: `reports/verification/sv13-11/vscode-cli-compatibility-verification.json`

## Scope

- `community-vscode-cli-compatibility-policy:1.0`
- Extension 0.2.0 ↔ CLI 0.2.x matrix
- Ordering after discovery, before consent
- Doctor reuse / install guidance / privacy

## Not in scope

- Epic 14 Product Experience
- Engine protocol changes
