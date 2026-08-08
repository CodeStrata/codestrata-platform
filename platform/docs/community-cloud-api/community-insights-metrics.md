# Community Insights Metrics & Privacy Contract (Slice 15.6)

Authoritative business and privacy meaning of every Community Insights metric.

## Key freezes

| Topic | Decision |
| --- | --- |
| Installations label | **Anonymous installations** (never "Users") |
| MAU window | **Rolling 30 UTC days** → display "30-day active installations" |
| Repeat assessments | **Repeat assessment events** (not installation count) |
| AI models | **AI model family adoption** only |
| Cohort suppression | Dimensional groups with count &lt; **3** → `other_suppressed` |
| Time | **UTC** for storage, query, and initial dashboard |
| Live data | **Not claimed** while ingestion remains unwired |

## Completeness

`complete` · `partial` · `unavailable` · `not_applicable`

Zero ≠ unavailable.

## Privacy

Aggregate metrics only. No raw events. No `installation_id` in API responses.
Authentication does not relax privacy.

**Policy:** `community-insights-metrics-policy:1.0`  
**Contract:** `community-insights-metrics-contract:1.0`
