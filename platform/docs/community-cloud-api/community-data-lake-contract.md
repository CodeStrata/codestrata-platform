# Community Data Lake — Authoritative Contract (Slice 15.1)

This document freezes the audited Community Data Lake architecture that all
future Community Insights / analytics work must follow. It does **not**
redesign telemetry, schemas, ingestion, or storage behavior.

**Policy:** `community-data-lake-policy:1.0`  
**JSON mirror:** `platform/policies/community_data_lake_policy.json`  
**Python source of truth:** `codestrata_platform.community_cloud_api.data_lake.policy`

## Ownership

| Layer | Owns |
| --- | --- |
| Platform `community_cloud_api/data_lake/` | Envelopes, partitions, adapters, ports, policies |
| `infrastructure/modules/community-data-lake/` | Bucket, lifecycle, encryption, unattached writer IAM |
| Engine / CLI / VS Code | Emitters only; must not import the lake |
| Public Community export | Must exclude Platform + Infrastructure lake paths |

## Bucket and hierarchy

- Strategy: **single private bucket**, prefix isolation
- Default name: `codestrata-community-data-lake-production`
- Accepted prefix: `raw/`
- Quarantine prefix: `quarantine/`
- Versioning: enabled
- Encryption: SSE-S3 / AES256 (KMS deferred)
- Ingestion wire: **disabled** (`enable_ingestion_wire=false`)
- Writer IAM: document exists, **unattached**

## Event categories (streams)

`telemetry` · `assessment_metadata` · `cli_event` · `extension_event` · `ai_usage`

## Partition strategy

```text
raw/stream=<stream>/schema_version=<ver>/year=<YYYY>/month=<MM>/day=<DD>/<opaque>.json
quarantine/reason=<safe_reason>/year=<YYYY>/month=<MM>/day=<DD>/<opaque>.json
```

Forbidden in path/metadata: `installation_id`, `event_id`, source paths,
personal identifiers, prompts, credentials.

## Object naming

- Accepted id: `lake-object:{sha256[:24]}`
- Quarantine id: `quarantine-object:{sha256[:24]}`
- Filename: opaque `{hex}.json` only

## Schemas / versioning

- Envelope schema: **1.0** (nested acceptance/client/identity/payload/source_contract)
- Lake policies: **1.0**
- Source endpoint schemas: **1.0** (rate-limit policy **1.1**; Assessment report **1.2**)

## Privacy

- Community-only collection
- No customer source code
- No personal identifiers in lake keys/metadata/logs
- Anonymous installation identity may appear **only** inside approved envelope payloads
- Privacy-first telemetry contracts remain authoritative

## Retention

Accepted 365 / quarantine 90 / multipart 7 / noncurrent 30 (provisional;
release-owner review still required).

## Export / build

Data lake is **private Platform/Infrastructure** and is excluded from public
Community export (`public-export-manifest.yaml`).

## Dashboard readiness (Slice 15.1 verdict)

| Capability | Status |
| --- | --- |
| Storage contract for future dashboard consumers | Ready (Accepted) |
| Production ingestion | Not wired (Deferred) |
| Aggregations / APIs / auth / dashboards | Not started (Deferred; Slice 15.2+) |

**Slice 15.2 has not started.**

## Audit finding classes

See `audit_classifications` in `platform/policies/community_data_lake_policy.json`.
