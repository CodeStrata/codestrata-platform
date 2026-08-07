# Epic 13 completion verification (Slice 13.15)

Schema: `vscode-epic13-completion-verification:1.0.0`

## Purpose

Authoritative completion verification for **Epic 13 – VS Code Extension** at
CodeStrata **v0.2.0** epic scope. This package proves slices 13.1–13.15 are
complete. It does **not** add product capability and does **not** start Epic 14.

## Run

```bash
.venv/bin/python -m verification.vscode_epic13_completion
```

Report:

`reports/verification/sv13-15/vscode-epic13-completion-verification.json`

## Contract highlights

- Extension version remains `0.2.0`
- Assessment schema remains `1.2`
- 14 Slice-specific policies remain `1.0`
- VS Code is the only active Community editor extension
- Cursor absent from active product/package/Marketplace surfaces
- Marketplace publication / release tag / deploy remain **false**
- `start_epic_14 = false`

## Limitations (expected PASS_WITH_LIMITATIONS)

- Full Extension Host UI automation unavailable
- One-OS clean-install execution
- Synthetic prior VSIX for update validation
- No live AI provider validation
- Telemetry production collection intentionally unavailable
- Marketplace not published
- `@vscode/vsce` pinned to 2.32.0
- Worktree may be uncommitted
- Epic 14 not started

## Explicit non-goals

- No commit / tag / publish / deploy
- No Epic 14 Product Experience work
- No product schema bumps
