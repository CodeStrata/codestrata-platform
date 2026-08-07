# VS Code Marketplace branding verification (Slice 13.12)

Schema: `vscode-marketplace-branding-verification:1.0.0`

## Run

```bash
.venv/bin/python -m verification.vscode_marketplace_branding
.venv/bin/python -m pytest tests/verification/vscode_marketplace_branding -q
```

Report: `reports/verification/sv13-12/vscode-marketplace-branding-verification.json`

## Scope

- `community-vscode-marketplace-branding-policy:1.0`
- Website visual reference (codestrata.ai)
- Icon / gallery banner / screenshots / package metadata
- Cursor absence · claims review · VSIX boundary via `.vscodeignore`

## Not in scope

- Slice 13.13 Marketplace long-form listing documentation
- Epic 14 Product Experience
- Epic 14 design system
- Publish / deploy
