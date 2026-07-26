# MVP Acceptance Harness

Phase 5.13 provides a repeatable live acceptance harness for the CodeStrata MVP
workflow. It does not add assessment rules or AI capabilities.

## Commands

```bash
aimf acceptance run
aimf acceptance run --repository synthetic-multilang --json
aimf acceptance status
aimf acceptance status --output reports/mvp-acceptance --json
```

Or:

```bash
python scripts/mvp_acceptance.py
```

## Workflow (per repository)

1. Live `aimf onboard` (real assessment + knowledge indexing)
2. `aimf report validate` on generated `report.json`
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
| spring-petclinic | `.aimf/workspace/spring-petclinic` |
| synthetic-multilang | `examples/sample-js-app` |

## Outputs

- `reports/mvp-acceptance/summary.json`
- `reports/mvp-acceptance/summary.md`
- per-repo artifacts under `reports/mvp-acceptance/<id>/`

## Notes

- Acceptance enables knowledge retrieval/answering and MCP in isolated settings
  without requiring aimf.toml changes.
- Live determinism comparisons treat `manifest.scan_id` as volatile.
- Local scanner excludes `reports/` and `.aimf/` so self-assessment of CodeStrata
  does not ingest prior acceptance artifacts.
- Report JSON aligns roadmap supporting IDs to customer finding/recommendation
  IDs at the reporting boundary (no assessment rule changes).
