# VS Code clean-install / update verification (Slice 13.14)

Schema: `vscode-clean-install-verification:1.0.0`

## Run

```bash
cd vscode-plugin && npm run package
cd ..
.venv/bin/python -m verification.vscode_clean_install
.venv/bin/python -m pytest tests/verification/vscode_clean_install -q
```

Report: `.codestrata-artifacts/validation/suites/sv13-14/vscode-clean-install-verification.json`

The verifier builds/uses `vscode-plugin/codestrata-vscode-0.2.0.vsix` and
inventories contents without leaking absolute paths.

## Scope

- `community-vscode-clean-install-policy:1.0`
- Real VSIX package integrity
- Activation / first-run / CLI / consent / update surface validation
- Cursor absence

## Limitations

- Full Extension Host UI automation may be unavailable
- Update uses synthetic prior package when no historical VSIX exists
- No Marketplace publish · no live AI

## Not in scope

- Epic 14 Product Experience
