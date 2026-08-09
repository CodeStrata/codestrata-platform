# VS Code telemetry consent integration verification (Slice 13.9)

Schema: `vscode-telemetry-consent-integration-verification:1.0.0`

## Run

```bash
PYTHONPATH=. python -m verification.vscode_telemetry_consent_integration
PYTHONPATH=. python -m pytest tests/verification/vscode_telemetry_consent_integration -q
```

Report: `.codestrata-artifacts/validation/suites/sv13-9/vscode-telemetry-consent-integration-verification.json`

## Scope

- `community-vscode-telemetry-integration-policy:1.0`
- Relationship to Slice 9.13 runtime policy 1.0
- Eligibility, readiness-before-consent, command-local Deny-default
- Report/recovery/init/install/activation boundaries
- No persistence, identity, or HTTP transport

## Not in scope

- Epic 14 Product Experience
- Marketplace (13.12 / 13.13)
- Production telemetry transport
