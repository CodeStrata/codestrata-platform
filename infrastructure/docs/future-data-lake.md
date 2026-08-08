# Community Data Lake

## Slice 8.1: foundation landed, still unwired

Slice 8.1 landed the Community Data Lake **storage foundation** at:

```text
infrastructure/modules/community-data-lake/
```

Primary docs:

- `infrastructure/docs/community-data-lake.md`
- `infrastructure/modules/community-data-lake/README.md`
- `platform/docs/community-cloud-api/data-lake.md`

This module creates a single private, encrypted (SSE-S3), versioned S3
bucket with prefix isolation (`raw/` accepted, `quarantine/` quarantine).

Platform owns the domain contracts (policy, envelope, identity, partitions,
ports) under `codestrata_platform.community_cloud_api.data_lake`.

The foundation is **unwired**: `enable_ingestion_wire` is `false` and
validated to stay `false`. No Lambda, EventBridge rule, S3 event
notification, or other compute reads from or writes to the bucket. The
`community-cloud-api` module does not reference this bucket anywhere in its
IAM policies. Durable Community event ingestion through this bucket, and
any analytics/query layer on top of it, remain deferred to a future slice.

## Legacy planned path (superseded, never created)

An earlier plan referenced `infrastructure/modules/data-lake` as the future
location. That path was never created and is superseded by
`infrastructure/modules/community-data-lake/` above.

## Slice 8.2: immutable raw-JSON storage contract landed, still unwired

Slice 8.2 (Platform-side; **no OpenTofu change**) implements a
production-capable `CommunityDataLakeS3Store` adapter with canonical
byte-exact JSON serialization, conditional (`IfNoneMatch: "*"`) `PutObject`,
and fail-closed conflict classification. See
`platform/docs/community-cloud-api/immutable-raw-storage.md`. It remains
**unwired**: no endpoint, `app.py`, or Lambda calls it, and no exactly-once
delivery guarantee is claimed. `HeadObject` (used once per precondition
resolution) is already covered by the existing `s3:GetObject` writer IAM
grant — no IAM change was needed.

## Deferred after Epic 8 (still unwired / not started)

Epic 8 completed the lake foundation, stream partition policies, quarantine,
retention, encryption, access, storage abstraction, and verification. The
items below remain deferred to **post-Epic-8** slices (including Epic 15
analytics consumers). They are **not** unfinished Epic 8 work:

- Endpoint → sink → S3 wiring (production ingestion)
- Durable event identity store coordination
- Writer IAM attachment
- SSE-KMS migration
- Final (non-review-required) retention policy sign-off
- Analytics / query layer (Athena, Glue) — not started
- Dashboards / Community Insights consumers (Slice 15.2+)
- Replay and deletion workflows

## Must not reuse

- OpenTofu/Terraform state bucket
- Lambda deployment artifact bucket
- `community-cloud-api` ECR repository

as the Community Data Lake, and vice versa.

Do not wire ingestion, attach the writer policy to any role, or start the
analytics layer without a separate, explicitly-reviewed slice.
