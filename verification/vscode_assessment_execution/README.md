# Slice 13.5 — VS Code assessment execution verification

Schema: `vscode-assessment-execution-verification:1.0.0`  
Policy under test: `community-vscode-assessment-execution-policy:1.0`

## Run

```bash
PYTHONPATH=. python -m verification.vscode_assessment_execution
PYTHONPATH=. python -m pytest tests/verification/vscode_assessment_execution -q
```

Report: `.codestrata-artifacts/validation/suites/sv13-5/vscode-assessment-execution-verification.json`

## Scope

Verifies that Community VS Code assessment commands:

- require eligible workspace + initialized repository + compatible CLI
- prompt telemetry consent only after readiness
- invoke Engine `assess` exactly once (standard or AI)
- treat Engine exit as primary authority
- treat report availability as a postcondition
- isolate telemetry/analytics failures

## Not in scope

- Slice 13.6 progress UX redesign
- Slice 13.7 report-opening UX
- Epic 14 Product Experience
- Live AI provider calls
- Commit / tag / publish / deploy
