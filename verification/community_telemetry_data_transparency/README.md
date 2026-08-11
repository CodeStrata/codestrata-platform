# Community Telemetry + Data Collection Transparency (Slice 18.2)

Verification package for Epic 18 Slice 18.2.

## Run

```bash
PYTHONPATH=platform/src:engine/src:. python -m verification.community_telemetry_data_transparency
```

## Output

`.codestrata-artifacts/validation/suites/sv18-2/community-telemetry-data-transparency-verification.json`

## Boundary

- `start_slice_18_2=true`
- `start_slice_18_3=false`
- No telemetry runtime redesign
- No new event producers
- No CLI / VS Code Marketplace publish
- No release tag
- No 22-repository Release corpus
