# VS Code source locality verification (Slice 13.10)

Schema: `vscode-source-locality-verification:1.0.0`

## Run

```bash
PYTHONPATH=. python -m verification.vscode_source_locality
PYTHONPATH=. python -m pytest tests/verification/vscode_source_locality -q
```

Report: `.codestrata-artifacts/validation/suites/sv13-10/vscode-source-locality-verification.json`

## Scope

- `community-vscode-source-locality-policy:1.0`
- Extension upload/network/Cloud/Data Lake/AI-client boundaries
- Engine-owned AI-provider qualification
- Telemetry/analytics source exclusions
- Git/source mutation absence

## Not in scope

- Epic 14 Product Experience
- Marketplace 13.12 / 13.13
- Engine AI redesign
