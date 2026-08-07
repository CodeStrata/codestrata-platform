# VS Code failure recovery verification (Slice 13.8)

Schema: `vscode-failure-recovery-verification:1.0.0`

## Run

```bash
PYTHONPATH=. python -m verification.vscode_failure_recovery
PYTHONPATH=. python -m pytest tests/verification/vscode_failure_recovery -q
```

Report: `reports/verification/sv13-8/vscode-failure-recovery-verification.json`

## Scope

- `community-vscode-recovery-policy:1.0`
- Bounded failure domains and recovery actions
- No automatic retry/install/assess/open
- Privacy-safe what/why/next messaging
- Primary vs secondary ownership
- Extension wiring for presentation

## Not in scope

- Epic 14 Product Experience
- Telemetry/analytics schema changes
- Engine/Platform/Cloud changes
