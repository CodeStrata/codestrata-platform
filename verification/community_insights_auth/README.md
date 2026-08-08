# Slice 15.9 — Community Insights Auth

| Field | Value |
| --- | --- |
| Policy | `community-insights-auth-policy:1.0` |
| Contract | `community-insights-auth-contract:1.0` |
| Schema | `community-insights-auth-verification:1.0.0` |
| Platform | `platform/src/codestrata_platform/community_cloud_api/insights_auth/` |
| Frontend | `insights/src/pages/LoginPage.tsx`, `insights/src/api/authClient.ts` |
| Infra | `infrastructure/modules/community-insights-auth/` (IDs only, not deployed) |

```bash
PYTHONPATH=engine/src:platform/src:. python -m verification.community_insights_auth
PYTHONPATH=engine/src:platform/src:. python -m pytest tests/verification/community_insights_auth platform/tests/community_cloud_api/insights_auth -q
```

No AWS calls. No deploy. No secret values in reports.
