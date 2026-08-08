# Community Analytics Partition Strategy (Slice 15.2)

Authoritative partition strategy for Community Insights Dashboard query
planning. **Baseline:** Slice 15.1 / `community-data-lake-policy:1.0`.

## Decision

**No additive Hive path dimensions are required.**

The existing hierarchy already supports privacy-safe, retention-bounded
analytics. Dashboard metrics are satisfied by:

1. listing one stream’s day/month prefixes, then
2. aggregating allowlisted payload fields (future aggregation slices).

Putting identity, versions, providers, heads, or languages into the path
would violate privacy/`forbidden_partition_fields` and is rejected.

## Authoritative path

```text
raw/stream=<stream>/schema_version=<ver>/year=<YYYY>/month=<MM>/day=<DD>/<opaque>.json
quarantine/reason=<safe_reason>/year=<YYYY>/month=<MM>/day=<DD>/<opaque>.json
```

Optional S3 metadata filters (not path dims):

- `codestrata-client-type`
- `codestrata-assessment-schema`

## Metric support (summary)

| Support class | Metrics |
| --- | --- |
| Supported directly | Extension event volume by day prefix; assessment-schema release surrogate via metadata |
| Requires bounded aggregation | Installations (total/DAU/MAU), first/repeat/success/fail assessments, CLI version, heads, languages, AI provider/model, VS Code usage detail, release version mix |
| Requires future enhancement | Named package-ecosystem dimensions (payload additive later; still not path dims) |
| Not applicable | Validation dataset growth; GitHub download counts |

## Compatibility

- Backward compatible with Epic 8 / Slice 15.1 objects
- No ingestion redesign
- No event schema change
- No existing-data migration

## Out of scope for 15.2

Aggregations · APIs · dashboard UI · ingestion enablement · Slice 15.7

**Policy:** `community-analytics-partition-policy:1.0`
