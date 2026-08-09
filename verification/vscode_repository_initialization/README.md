# Slice 13.4 — VS Code repository initialization verification

Schema: `vscode-repository-initialization-verification:1.0.0`  
Policy under test: `community-vscode-repository-initialization-policy:1.0`

## Run

```bash
PYTHONPATH=. python -m verification.vscode_repository_initialization
PYTHONPATH=. python -m pytest tests/verification/vscode_repository_initialization -q
```

Report: `.codestrata-artifacts/validation/suites/sv13-4/vscode-repository-initialization-verification.json`

## Scope

Verifies the Community VS Code extension coordinates **user-triggered**
repository initialization while **Engine CLI** remains the sole writer of
`codestrata.toml`.

Boundaries checked:

- Explicit `codestrata.init` only (no activation init)
- Eligible workspace + compatible CLI discovery first
- Approach A: already initialized skips CLI
- Invalid/partial config preserved (no force/overwrite/delete)
- One product `init` invocation when needed; post-init verification
- No assessment / AI / telemetry / analytics / report open
- Source / Git / network local-only guarantees
- Privacy-safe diagnostics

## Not in scope

- Slice 13.5 assessment redesign
- Epic 14 Product Experience
- Marketplace branding
- Commit / tag / publish / deploy
