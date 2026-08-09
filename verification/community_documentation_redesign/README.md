# Community documentation redesign verification (Slice 14.2)

Schema: `community-documentation-redesign-verification:1.0.0`

## Run

```bash
.venv/bin/python -m verification.community_documentation_redesign
```

Also run docs package tests:

```bash
cd docs && npm test
```

Report: `.codestrata-artifacts/validation/suites/sv14-2/community-documentation-redesign-verification.json`

## Verifies

- Design System tokens consumed (no duplication)
- Community-only active navigation
- Platform / commercial docs excluded from publish
- Shell components, typography, a11y, responsive, dark mode
- Slice 14.3 not started

## Non-goals

No Assessment HTML / EIR / VS Code / Marketplace redesign. No commit/tag/publish/deploy.
