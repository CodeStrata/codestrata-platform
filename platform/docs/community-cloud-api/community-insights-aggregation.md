# Community Insights Aggregation (Slice 15.7)

Privacy-safe on-demand aggregation from bounded S3 Data Lake reads into `MetricResult`.

## Architecture

```text
MetricRequest → planner (15.5) → BoundedS3Reader → decode → aggregators
  → suppression → completeness → MetricResult
```

- Domain: `community_cloud_api/insights/` (no boto3)
- Storage: `community_cloud_api/insights_storage/` (injected S3 client)
- Checkpoint: **retention-only** with `first_repeat_retention_only` limitation (no derived S3 state in 15.7)
- Cache: **none** (optional TTL deferred)
- Athena/Glue/Redis/RDS: not used
- Production ingestion: still disabled
- Dashboard / auth: not started (15.8+)

## Policy

`community-insights-aggregation-policy:1.0`
