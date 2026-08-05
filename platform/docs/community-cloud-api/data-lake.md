# Community Data Lake (Platform domain)

Slice 8.1 establishes the **Platform-owned Community Data Lake domain**: policy,
envelopes, storage identity, partitions, quarantine vocabulary, and a minimal
storage port. It does **not** enable durable Community event ingestion.

Slice 8.2 adds the **immutable raw-JSON storage contract** on top of this
foundation: canonical byte-exact JSON serialization, a resolved storage
object model, fail-closed conflict classification, privacy-safe receipts,
and a production-capable but unwired S3 adapter under `data_lake/infrastructure/`.
See [immutable-raw-storage.md](./immutable-raw-storage.md) for the full
contract. It still does **not** enable durable Community event ingestion —
no endpoint is wired to storage.

Slice 8.3 evolves the envelope's canonical serialized shape from Slice 8.1's
flat fields to a nested `acceptance` / `client` / `identity` /
`source_contract` contract — still envelope schema **1.0**, a
pre-persistence foundation refinement made before the first durable write,
not a runtime migration — and adds a typed per-stream registry and
high-level builders for constructing an envelope from an already-validated
endpoint request model. See
[data-lake-event-envelope.md](./data-lake-event-envelope.md) for the full
contract, version-impact rationale, and privacy model. It still does
**not** wire any endpoint to storage.

Slice 8.4 gives the `assessment_metadata` stream its own versioned
**partition policy** (`StreamPartitionPolicy`) and a stream-specific
storage-object projector (`project_assessment_metadata_storage_object`),
plus the generic (stream-agnostic) machinery a future slice will reuse for
the remaining four streams. The accepted path stays the **generic Hive path
only** — no extra partition dimension was added. See
[assessment-metadata-data-lake.md](./assessment-metadata-data-lake.md) for
the full dimension-decision rationale and contract. It still does **not**
wire any endpoint to storage.

Slice 8.5 reuses that exact same generic machinery for a second stream,
`telemetry`: its own `StreamPartitionPolicy` (`community-telemetry-
partition-policy:1.0`) and `project_telemetry_storage_object()`. The
accepted path again stays the generic Hive path only; the only new S3
metadata key is `codestrata-client-type` (never `event_type`, which stays
private-payload-only). See
[telemetry-data-lake.md](./telemetry-data-lake.md) for the full
dimension-decision rationale, the property-cardinality review, and the
contract. It still does **not** wire any endpoint to storage.

Slice 8.6 reuses that same generic machinery for a third stream,
`cli_event`: its own `StreamPartitionPolicy` (`community-cli-event-
partition-policy:1.0`) and `project_cli_event_storage_object()`. The
accepted path again stays the generic Hive path only, and this time **no**
new S3 metadata key is added at all — the allowlist stays exactly the five
base keys, since the CLI client is always `codestrata_cli` (redundant
metadata) and `operation`/`lifecycle`/`result` stay private-payload-only.
This slice also adds one new optional field to both
`StreamPartitionPolicy` (`supported_operation_catalog_versions`) and
`PartitionProjectionDiagnostics` (`operation_catalog_version`). See
[cli-event-data-lake.md](./cli-event-data-lake.md) for the full
dimension-decision rationale and contract. It still does **not** wire any
endpoint to storage.

Slice 8.7 reuses that same generic machinery for a fourth stream,
`extension_event`: its own `StreamPartitionPolicy`
(`community-extension-event-partition-policy:1.0`) and
`project_extension_event_storage_object()`. The accepted path again stays
the generic Hive path only; Option B reuses telemetry's
`codestrata-client-type` metadata key for
`vscode_extension`/`cursor_extension` (never `editor` or `operation` in
path or metadata). Diagnostics set both `client_type` and
`operation_catalog_version`. See
[extension-event-data-lake.md](./extension-event-data-lake.md) for the
full dimension-decision rationale and contract. It still does **not** wire
any endpoint to storage, and does not claim extension collection is
operational.

Slice 8.8 reuses that same generic machinery for a fifth stream,
`ai_usage`: its own `StreamPartitionPolicy`
(`community-ai-usage-partition-policy:1.0`) and
`project_ai_usage_storage_object()`. The accepted path again stays the
generic Hive path only; Option B reuses `codestrata-client-type` for
`codestrata_cli` / `vscode_extension` / `cursor_extension` (never
`capability`, `provider_family`, or `model_family` in path or metadata).
This slice is the first to set the three AI catalog version fields on
policy and diagnostics (`capability` / `provider` / `model`; not
`operation_catalog`). See
[ai-usage-data-lake.md](./ai-usage-data-lake.md) for the full
dimension-decision rationale and contract. It still does **not** wire any
endpoint to storage, and does not claim AI usage collection is
operational.

Slice 8.9 implements **malformed-event quarantine**: versioned quarantine
records, `quarantine-object:` identity (date-independent), canonical JSON
persistence under `quarantine/`, and S3/in-memory adapters — still **not**
wired to endpoints / `app.py` / `deployment/wiring.py`, and does **not**
claim production events are quarantined. See
[data-lake-quarantine.md](./data-lake-quarantine.md).

Slice 8.10 formalizes **data retention and lifecycle policies**: Platform
`community-data-lake-retention-policy:1.0` aligned with OpenTofu lifecycle
defaults (accepted 365 / quarantine 90 / multipart 7 / noncurrent 30),
expired-delete-marker cleanup, `force_destroy=false`, and no Object Lock or
storage-class transitions. Still unwired; does **not** claim production data
is stored or deleted. See [data-lake-retention.md](./data-lake-retention.md).

Slice 8.11 formalizes **encryption at rest**: Platform
`community-data-lake-encryption-policy:1.0` (SSE-S3 / AES256 only), bucket
default encryption + explicit Put headers, accepted/quarantine parity, KMS
deferred. Still unwired; does **not** claim production data is stored or that
customer-managed KMS is enabled. See
[data-lake-encryption.md](./data-lake-encryption.md).

Slice 8.12 formalizes **restricted IAM access control**: Platform
`community-data-lake-access-policy:1.0` (Put/Get prefix-scoped writer intent,
delete Deny, no ListBucket, no KMS IAM, analytics/quarantine separation),
OpenTofu writer policy document with stable SIDs + `DenyInsecureTransport`
bucket policy, writer policy **unattached**. See
[data-lake-access-control.md](./data-lake-access-control.md).

Slice 8.13 formalizes **storage abstraction**: Platform
`community-data-lake-storage-policy:1.0` (typed projected-object port,
adapter capability sets, explicit factory with production-default unavailable
adapter, in-memory test-only, S3 capable but unwired). Stream
`store_projected_*` helpers require `put_immutable_storage_object` — no
envelope rebuild fallback. Still unwired. **Slice 8.14** adds integration
verification (five streams + quarantine, adapter parity, privacy, static
infrastructure contract, production fail-closed) under
`platform/verification/community_data_lake/` — report
`platform/reports/verification/community-data-lake-verification.json`.
**Slice 8.15** completes Epic 8 with boundary/completion verification under
`platform/verification/community_data_lake_completion/` — report
`platform/reports/verification/community-data-lake-completion-verification.json`.
**Epic 8 is complete.** Production ingestion is **not operational**; Epic 9
is **not started**. See
[data-lake-storage-abstraction.md](./data-lake-storage-abstraction.md).

Package:

```text
platform/src/codestrata_platform/community_cloud_api/data_lake/
```

Infrastructure companion (private OpenTofu):

```text
infrastructure/modules/community-data-lake/
```

## Purpose and ownership

| Layer | Owns |
| --- | --- |
| Platform `data_lake/` | Contracts: policy, streams, envelope, identity, partitions, ports |
| `infrastructure/modules/community-data-lake/` | Private S3 foundation, lifecycle, encryption, writer IAM document |
| Community Cloud API endpoints | Unchanged; remain fail-closed / in-memory sinks |
| Engine / CLI / extensions | Must not import or know about this package |

Durable ingestion wiring (endpoint → sink → S3) is deferred to later Epic 8
slices. Creating the bucket alone does not enable acceptance.

## Architecture (target)

```text
Community Cloud API
  → validated endpoint request
  → retry-safe event identity classification
  → endpoint-specific sink
  → immutable raw event envelope
  → S3 accepted prefix (raw/)

Malformed / storage-invalid (Slice 8.9 library; unwired):
  → quarantine prefix (quarantine/)

Future consumers:
  → analytics processing
  → privacy-safe aggregates
  → Community Insights Dashboard
```

Slice 8.1 implements only the contracts and storage foundation. Endpoints are
not wired to the lake.

## Event-stream vocabulary

Canonical storage streams (not merged into one permissive schema):

| Stream | Endpoint (source) |
| --- | --- |
| `telemetry` | `POST /api/v1/telemetry` |
| `assessment_metadata` | `POST /api/v1/assessment-metadata` |
| `cli_event` | `POST /api/v1/cli-events` |
| `extension_event` | `POST /api/v1/extension-events` |
| `ai_usage` | `POST /api/v1/ai-usage` |

Quarantine is a separate prefix/zone, not a sixth accepted stream schema.

## Envelope contract

Independent of endpoint schemas:

- `COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION = "1.0"`
- `COMMUNITY_DATA_LAKE_POLICY_VERSION = "1.0"`

Envelope carries validated payload plus bounded system metadata (stream,
source schema/policy versions, safe event reference, storage event key,
acceptance date components, client type). As of Slice 8.3 this metadata is
nested under `acceptance` / `client` / `identity` / `source_contract` in the
canonical serialized JSON — see
[data-lake-event-envelope.md](./data-lake-event-envelope.md) for the exact
shape. Forbidden substrings (Authorization, cookies, IPs, request IDs,
credential markers, etc.) are rejected by blob scan, and forbidden field
**names** (Slice 8.3) are additionally rejected by structural key-path scan.

Raw credentials, request ID, IP, and auth principal must not be stored
unless an existing approved contract already allows a specific safe form
(for example opaque `evt-…` references derived by event identity).
`event_id` and the optional `installation_id` ARE allowed inside `payload`
as part of each endpoint's own approved request contract (Slice 8.3
decision) — never in the object key, partition, S3 metadata, logs, or any
public receipt.

## Storage identity

Deterministic opaque id:

```text
lake-object:{sha256[:24]}
```

Material: policy token + event stream + source schema version + retry-safe
event key. Excludes request ID, IP, timestamp, random UUID, Authorization.

S3 object keys end with the opaque hex filename only — never raw event IDs or
`event:` keys in the path.

## Partition contract (Hive-style)

Accepted:

```text
raw/stream=<stream>/schema_version=<ver>/year=<YYYY>/month=<MM>/day=<DD>/<opaque>.json
```

Quarantine:

```text
quarantine/reason=<safe_reason>/year=<YYYY>/month=<MM>/day=<DD>/<opaque>.json
```

Acceptance time may partition; it must not participate in logical event
identity.

**Slice 8.4** adds a versioned, per-stream `StreamPartitionPolicy` that
declares which schema versions and Hive dimensions a stream's projector may
accept — currently only for `assessment_metadata`, which keeps to exactly
this generic five-dimension path (no extra dimension). See
[assessment-metadata-data-lake.md](./assessment-metadata-data-lake.md).

**Slice 8.5** adds a second `StreamPartitionPolicy` for `telemetry`, keeping
the same generic five-dimension path. See
[telemetry-data-lake.md](./telemetry-data-lake.md).

**Slice 8.6** adds a third `StreamPartitionPolicy` for `cli_event`, again
keeping the same generic five-dimension path. See
[cli-event-data-lake.md](./cli-event-data-lake.md).

**Slice 8.7** adds a fourth `StreamPartitionPolicy` for `extension_event`,
again keeping the same generic five-dimension path (with Option B
`codestrata-client-type` metadata). See
[extension-event-data-lake.md](./extension-event-data-lake.md).

**Slice 8.8** adds a fifth `StreamPartitionPolicy` for `ai_usage`, again
keeping the same generic five-dimension path (with Option B
`codestrata-client-type` metadata and three AI catalog version fields). See
[ai-usage-data-lake.md](./ai-usage-data-lake.md).

## Immutability

First write → stored. Exact retry → already_exists. Conflicting payload at same
key → conflict (never overwrite). Storage unavailable → unavailable (callers
must not return false durable acceptance). `InMemoryCommunityDataLakeStore`
proves the contract in tests.

**Slice 8.2** implements the production-capable `CommunityDataLakeS3Store`
adapter (`data_lake/infrastructure/s3_store.py`) with the same semantics,
enforced by S3 conditional writes (`IfNoneMatch: "*"`) rather than
client-side locking. The adapter exists, is unit-tested, and is **not**
wired into `app.py`, `deployment/wiring.py`, or any endpoint. See
[immutable-raw-storage.md](./immutable-raw-storage.md) — no exactly-once
delivery guarantee is claimed.

## Retention / encryption / IAM

Policy defaults (product-policy defaults requiring review):

| Field | Default |
| --- | --- |
| Accepted retention | 365 days |
| Quarantine retention | 90 days |
| Incomplete multipart abort | 7 days |
| Noncurrent version expiration | 30 days |
| Encryption | SSE-S3 / AES256 (Slice 8.11; KMS deferred) |
| Bucket strategy | Single private bucket, prefix isolation |

Writer IAM lives in OpenTofu as an **unattached** policy document (Slice 8.12:
stable SIDs, prefix-scoped Put/Get, explicit delete Deny on both prefixes,
`DenyInsecureTransport` on the bucket). Quarantine access remains more
restricted than future analytics readers (analytics roles are not created in
this slice). See [data-lake-access-control.md](./data-lake-access-control.md).

## Quarantine (Slice 8.9)

See [data-lake-quarantine.md](./data-lake-quarantine.md). Reason codes now
include the Slice 8.1 set plus specific unsupported-schema / partition /
storage-object / checksum codes. Records never store raw HTTP bodies,
headers, Authorization, cookies, IPs, `event_id`, `installation_id`,
prompts, or credentials. Persistence is implemented and unit-tested but
**unwired** from production ingestion.

## Fail-closed posture

Community Cloud production ingestion remains authentication-unavailable /
sinks-unavailable. This package is not imported by `app.py`, production wiring,
or endpoints.

## What this is not

- Terraform state storage
- ECR image storage
- CloudWatch logging
- Engineering Intelligence report storage
- Source-code or customer repository storage

## Schema impact

Unchanged: Assessment 1.2, EIR 1.0, website export 1.0, Community Cloud API 1.0,
endpoint schemas 1.0, authentication 1.0, rate-limit 1.1.

New independent contracts: Data Lake policy 1.0, envelope schema 1.0.

## Limitations (Slice 8.1)

- No endpoint → S3 wiring
- No durable event identity store
- No production boto3 adapter
- No queues, workers, Glue, Athena, dashboards
- No apply / deploy of AWS resources by this slice alone

## Limitations (Slice 8.2)

See [immutable-raw-storage.md](./immutable-raw-storage.md#limitations-slice-82)
for the full list. In short: a production-capable S3 adapter now exists
(`data_lake/infrastructure/`) but is still not wired to any endpoint, and
no exactly-once delivery is claimed. Quarantine persistence was completed
in Slice 8.9 (still unwired).

## Limitations (Slice 8.3)

See [data-lake-event-envelope.md](./data-lake-event-envelope.md#limitations-slice-83)
for the full list. In short: the envelope's canonical serialized shape is
now nested and a typed per-stream registry/builder exists, but no endpoint
is wired to storage, no durable event-identity store was added, and no
stream-specific partition policy ownership was introduced (resolved for
one stream in Slice 8.4 below).

## Limitations (Slice 8.4)

See [assessment-metadata-data-lake.md](./assessment-metadata-data-lake.md#limitations-slice-84)
for the full list. In short: `assessment_metadata` now has a versioned
partition policy and storage-object projector, but still no endpoint is
wired to storage, no partition policy exists yet for the other four
streams, and the accepted path gained no extra dimension.

## Limitations (Slice 8.5)

See [telemetry-data-lake.md](./telemetry-data-lake.md#limitations-slice-85)
for the full list. In short: `telemetry` now also has a versioned partition
policy and storage-object projector, but still no endpoint is wired to
storage, no partition policy exists yet for `cli_event`,
`extension_event`, or `ai_usage`, and the accepted path again gained no
extra dimension.

## Limitations (Slice 8.6)

See [cli-event-data-lake.md](./cli-event-data-lake.md#limitations-slice-86)
for the full list. In short: `cli_event` now also has a versioned partition
policy and storage-object projector, but still no endpoint is wired to
storage, and the accepted path again gained no extra dimension — this
time with no new S3 metadata key either. Partition ownership for
`extension_event` followed in Slice 8.7; `ai_usage` followed in Slice 8.8.

## Limitations (Slice 8.7)

See [extension-event-data-lake.md](./extension-event-data-lake.md#limitations-slice-87)
for the full list. In short: `extension_event` now also has a versioned
partition policy and storage-object projector (Option B client-type
metadata), but still no endpoint is wired to storage, no partition policy
exists yet for `ai_usage`, and the accepted path again gained no extra
dimension. Extension collection is not claimed operational via the data
lake.

## Limitations (Slice 8.8)

See [ai-usage-data-lake.md](./ai-usage-data-lake.md#limitations-slice-88)
for the full list. In short: `ai_usage` now also has a versioned partition
policy and storage-object projector (Option B client-type metadata, three
AI catalog version fields), but still no endpoint is wired to storage, and
the accepted path again gained no extra dimension. AI usage collection is
not claimed operational via the data lake.

## Limitations (Slice 8.9)

See [data-lake-quarantine.md](./data-lake-quarantine.md). In short:
quarantine records can be projected and stored under `quarantine/`
(in-memory + S3), but no endpoint / `app.py` / wiring path calls them,
and production events are not claimed quarantined. Slice 8.10 formalizes
retention; Slice 8.11 formalizes encryption at rest (SSE-S3) — both still
unwired.
