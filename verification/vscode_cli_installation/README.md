# VS Code CLI Installation Guidance Verification (Slice 13.3)

Schema: `vscode-cli-installation-verification:1.0.0`  
Policy: `community-vscode-cli-installation-policy:1.0`  
Approach: **guidance_only**

## Run

```bash
PYTHONPATH=. python -m verification.vscode_cli_installation
PYTHONPATH=. python -m pytest tests/verification/vscode_cli_installation -q
```

Report: `.codestrata-artifacts/validation/suites/sv13-3/vscode-cli-installation-verification.json`

## Guarantees

- Explicit user action required
- No activation/discovery automatic installation
- No package-manager execution by the extension
- No curl-pipe-shell, sudo, PATH/profile mutation, or settings overwrite
- No telemetry/analytics from installation guidance
- Rediscovery is explicit
- `codestrata.installEngine` preserved as guidance entry
- Clean-install package validation completed in Slice 13.14
- Epic 13 completion verified via Slice 13.15
