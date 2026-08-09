# Slice 17.7 — Community Cloud production ingestion

Verification of production ingestion activation: Data Lake writer attach,
`CODESTRATA_INGESTION_ENABLED`, five-stream Data Lake sinks, client consent,
privacy, quarantine, failure isolation. Report artifacts remain out of the lake.

## Verify

```bash
PYTHONPATH=. .venv/bin/python -m verification.community_cloud_production_ingestion
```

Report: `.codestrata-artifacts/validation/suites/sv17-7/community-cloud-production-ingestion-verification.json`

## Evidence

Prefers sanitized files under `infrastructure/production/.local/` when present:

- `sv17-7-preactivation.json`
- `sv17-7-activation.json`
- `sv17-7-stream-results.json`
- `sv17-7-data-lake-before.json` / `sv17-7-data-lake-after.json`

Fails closed on critical gates; **PASS_WITH_LIMITATIONS** when operational
evidence is partial (does not invent PASS).

## Non-actions

Slice 17.8 not started · no Insights frontend · no Docs · no commit/tag/publish
by this package.
