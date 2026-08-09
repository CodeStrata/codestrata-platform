# Slice 13.1 — VS Code Community workflow verification

Schema: `vscode-community-workflow-verification:1.0.0`

## Run

```bash
PYTHONPATH=. python -m verification.vscode_community_workflow
PYTHONPATH=. python -m pytest tests/verification/vscode_community_workflow -q
```

Also required (from `vscode-plugin/`):

```bash
npm run compile
npm test
npm run package:dry
```

Report: `.codestrata-artifacts/validation/suites/sv13-1/vscode-community-workflow-verification.json`

## Verifies

- Workflow policy `community-vscode-workflow-policy:1.0`
- Command → operation mapping
- State vocabulary and transitions
- Activation remains lightweight
- Init / assess / AI assess / open-report boundaries
- Single CLI invocation recording API
- Telemetry/analytics isolation
- Progress start/close ownership
- Report-open failure distinct from assessment failure
- Privacy-safe diagnostics
- VS Code version 0.2.0
- Epic 13 completion verified via Slice 13.15 (`sv13-15`)
- Epic 14 Product Experience not started

## Non-goals

- CLI auto-detection/install
- Marketplace publish
- Commit/tag/deploy
