# Slice 15.8 — Community Insights Application

| Field | Value |
| --- | --- |
| Policy | `codestrata-insights-application-policy:1.0` |
| Repo contract | `codestrata-insights-repository-contract:1.0` |
| Schema | `community-insights-application-verification:1.0.0` |
| App | `insights/` → future `codestrata-insights` |
| Host | `insights.codestrata.ai` (not deployed) |

```bash
cd insights && npm ci && npm test && npm run build
PYTHONPATH=engine/src:platform/src:scripts:. .venv/bin/python -m verification.community_insights_application
```
