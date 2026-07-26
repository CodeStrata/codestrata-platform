# MVP Acceptance Harness

Phase 5.13 provides a repeatable live acceptance harness for the CodeStrata MVP
workflow. It does not add assessment rules or AI capabilities.

## Commands

```bash
codestrata acceptance run
codestrata acceptance run --repository synthetic-multilang --json
codestrata acceptance status
codestrata acceptance status --output reports/mvp-acceptance --json
```

For monorepo release gates (security, lint, tests, export), use
`python scripts/verify_release.py`. Optionally add live acceptance:

```bash
python scripts/verify_release.py --with-acceptance
```

## Workflow (per repository)

1. Live `codestrata onboard` (real assessment + knowledge indexing)
2. `codestrata report validate` on generated `report.json`
3. Confirm `report.html` exists
4. Verify findings, recommendations, evidence, roadmap counts, and indexed chunks
5. Ask predefined grounded repository questions against the onboarded corpus
6. Compose MCP and run `repository_health`
7. Re-run onboard and compare reports with volatile fields stripped
   (`manifest.scan_id` is treated as volatile for live runs)

## Dogfood targets

| Id | Path |
|----|------|
| codestrata | repository root |
| spring-petclinic | `.codestrata/workspace/spring-petclinic` |
| synthetic-multilang | `test-fixtures/sample-js-app` |

## Outputs

- `reports/mvp-acceptance/summary.json`
- `reports/mvp-acceptance/summary.md`
- per-repo artifacts under `reports/mvp-acceptance/<id>/`

## Notes

- Acceptance enables knowledge retrieval/answering and MCP in isolated settings
  without requiring codestrata.toml changes.
- Live determinism comparisons treat `manifest.scan_id` as volatile.
- Local scanner excludes `reports/` and `.codestrata/` so self-assessment of CodeStrata
  does not ingest prior acceptance artifacts.
- Report JSON aligns roadmap supporting IDs to customer finding/recommendation
  IDs at the reporting boundary (no assessment rule changes).
