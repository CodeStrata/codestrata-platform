# Slice 18.7 — Validate Public Claims Against Runtime

Adversarial audit of material public claims against runtime / schema / IaC
evidence from Slices 18.1–18.6.

## Run

```bash
PYTHONPATH=platform/src:engine/src:. python -m verification.community_public_claim_runtime_validation
```

## Report

`.codestrata-artifacts/validation/suites/sv18-7/community-public-claim-runtime-validation-verification.json`

## Boundary

- `start_slice_18_7=true`
- `start_slice_18_8=false`
- No runtime redesign, CLI publish, VS Code Marketplace publish, release tag,
  or full 22-repository Release corpus.
