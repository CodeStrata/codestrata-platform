# Slice 17.26 — Community public documentation reconciliation

Verifies canonical Community privacy documentation, reports landing privacy +
favicon wiring, docs stale-path hygiene, gitignore guards for `reports/` /
`docs/reports/`, and Epic 17 boundary fencing (`start_slice_17_27=false`).
Optional live probes against docs/reports/corporate surfaces are soft.

## Run

```bash
PYTHONPATH=engine/src:platform/src:. .venv/bin/python -m verification.community_public_documentation_reconciliation
```

Report: `.codestrata-artifacts/validation/suites/sv17-26/community-public-documentation-reconciliation-verification.json`

## Tests

```bash
PYTHONPATH=engine/src:platform/src:. .venv/bin/pytest tests/verification/community_public_documentation_reconciliation/ -q
```

## Soft limitations (PASS_WITH_LIMITATIONS)

- `live_docs_privacy_unreachable`
- `live_reports_favicon_unreachable`
- `live_reports_landing_privacy_mismatch`
- `codestrata_ai_favicon_stale`

## Hard fail

- Missing privacy section markers in `docs/security/privacy.md`
- Reports landing Privacy link not pointing at `https://docs.codestrata.ai/security/privacy`
- Missing reports favicon assets / HTML link
- Stale `reports/<repo>/<timestamp>/report.html` paths in docs markdown
- Bare `reports/` or `docs/reports/` gitignore rules
- `start_slice_17_27=true` in this slice policy
