# VS Code Marketplace documentation verification (Slice 13.13)

Schema: `vscode-marketplace-documentation-verification:1.0.0`

## Run

```bash
.venv/bin/python -m verification.vscode_marketplace_docs
.venv/bin/python -m pytest tests/verification/vscode_marketplace_docs -q
```

Report: `.codestrata-artifacts/validation/suites/sv13-13/vscode-marketplace-documentation-verification.json`

## Scope

- `community-vscode-marketplace-documentation-policy:1.0`
- README as authoritative Marketplace listing
- Claim matrix · privacy/AI qualification · CLI 0.2.x · Cursor/Cloud absence

## Not in scope

- Epic 14 Product Experience
- Marketplace publish
- Branding redesign (Slice 13.12)
