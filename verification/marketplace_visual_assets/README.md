# Marketplace visual assets verification (Slice 14.6)

Schema: `marketplace-visual-assets-verification:1.0.0`

Policy: `codestrata-marketplace-visual-assets-policy:1.0`

## Purpose

Verify VS Code Marketplace listing visuals align with Design System 1.0 and the
current Community product journey (VS Code → CLI assessment → Assessment HTML →
optional AI). Does not publish, bump versions, or change Marketplace copy semantics.

## Run

```bash
.venv/bin/python -m verification.marketplace_visual_assets
pytest tests/verification/marketplace_visual_assets -q
```

Report: `.codestrata-artifacts/validation/suites/sv14-6/marketplace-visual-assets-verification.json`

## Boundaries

- Extension remains `0.2.0`
- Marketplace documentation/copy from Slice 13.13 unchanged (image refs/alt/captions only)
- VS Code runtime unchanged (activity SVG remains theme-safe `currentColor`)
- Universal logo authority deferred to Slice 14.10
- Slice 14.7 not started
- No commit / tag / publish / deploy

## Limitations

Recorded in the report when applicable:

- Extension Host screenshot automation may be unavailable
- Pixel-perfect screenshot determinism depends on rendering host
- Marketplace not remotely previewed or published
