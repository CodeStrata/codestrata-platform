# Slice 13.7 — VS Code HTML report opening verification

Schema: `vscode-html-report-opening-verification:1.0.0`  
Policy: `community-vscode-report-opening-policy:1.0`

## Run

```bash
PYTHONPATH=. python -m verification.vscode_html_report_opening
PYTHONPATH=. python -m pytest tests/verification/vscode_html_report_opening -q
```

Report: `.codestrata-artifacts/validation/suites/sv13-7/vscode-html-report-opening-verification.json`

## Scope

Engine remains sole HTML report generator. Extension locates and opens
`report.html` inside the approved repository output boundary only (Approach B:
prompt-driven open).

## Not in scope

- Epic 14 Product Experience
- Report content parsing/transmission
- Commit / tag / publish / deploy
