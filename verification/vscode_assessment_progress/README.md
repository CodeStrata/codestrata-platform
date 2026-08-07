# Slice 13.6 — VS Code assessment progress verification

Schema: `vscode-assessment-progress-verification:1.0.0`  
Policy under test: `community-vscode-assessment-progress-policy:1.0`

## Run

```bash
PYTHONPATH=. python -m verification.vscode_assessment_progress
PYTHONPATH=. python -m pytest tests/verification/vscode_assessment_progress -q
```

Report: `reports/verification/sv13-6/vscode-assessment-progress-verification.json`

## Scope

Verifies assessment progress is:

- one lifecycle per assessment after readiness/consent
- indeterminate (Decision A — no Engine structured progress protocol)
- cancellation-aware without retry
- isolated from primary assessment authority
- privacy-safe (no paths/providers/findings in progress text)

## Not in scope

- Slice 13.7 report-opening UX
- Epic 14 Product Experience
- Engine progress protocol changes
- Commit / tag / publish / deploy
