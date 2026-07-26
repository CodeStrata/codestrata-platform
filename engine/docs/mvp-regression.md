# MVP Regression Suite

Phase 5.15 stabilizes the full CodeStrata quality gates before declaring the
MVP engine complete. No new product capabilities were added.

## Gates

```bash
pytest
ruff check .
mypy src
```

Artifacts: `reports/mvp-regression/summary.json` (plus local gate logs).

## Intentional schema decision

`testing-assessment` schema version is **1.2.0** (inventory 1.1 + synthesis
1.2). Foundation docs that still said `1.0.0` were updated. Scoring /
release-readiness claim fields remain forbidden; synthesis / themes /
conclusions / recommendations / inventories are intentional on 1.2.0.

## Report contract decision

Recommendation `related_finding_ids` must reference runtime finding **ids**,
not rule ids. At the reporting boundary they are remapped to stable report
UUIDs via `remap_related_finding_ids`. Unknown references are dropped (JSON
and HTML share this helper).

## Intentional skips

| Skip | Reason |
| ---- | ------ |
| OpenAI live provider test | `OPENAI_API_KEY` not set |
| Bedrock/AWS live provider test | AWS credentials not set |
| pgvector Docker persistence (×5) | Docker daemon unavailable |

These are environment-gated live/integration tests, not suppressed failures.

## Non-goals (unchanged)

No assessment rules, AI capabilities, retrieval changes, report sections, UI,
API, authentication, or packaging features were added in this phase.
