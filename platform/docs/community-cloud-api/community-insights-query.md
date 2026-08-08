# Community Insights Bounded S3 Query Strategy (Slice 15.5)

Defines the **read strategy** for future on-demand Insights aggregation.

## Decisions

| Topic | Decision |
| --- | --- |
| Direct S3 | **preferred** |
| Athena / Glue / DB / Redis | **not required** |
| Timezone | **UTC** partition dates |
| Quarantine | **never queried** |
| Caller prefixes | **forbidden** — planner owns prefixes |
| Lifetime totals | retention window **+ hard object/byte budgets** + future checkpoint (15.7) |
| Aggregation / dashboard | **not in 15.5** |

## Prefix shape

```text
raw/stream=<stream>/schema_version=<ver>/year=<YYYY>/month=<MM>/day=<DD>/
```

## Pure planner

`codestrata_platform.community_cloud_api.insights_query` — SDK-free.

**Policy:** `community-insights-query-policy:1.0`  
**Contract:** `community-insights-query-contract:1.0`
