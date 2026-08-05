# Community Data Lake infrastructure

Private OpenTofu module for the Community Data Lake storage foundation
(Slice 8.1).

**Slice 8.2** (Platform-side, no OpenTofu change) adds a production-capable
S3 adapter (`platform/.../data_lake/infrastructure/`) that can write to this
bucket's `raw/` prefix using conditional (`IfNoneMatch: "*"`) `PutObject`
and a `HeadObject`-based conflict check. The adapter is **not** wired to any
endpoint or Lambda in this slice. `HeadObject` is authorized by the
`s3:GetObject` action already granted by this module's writer IAM policy
document — no IAM change was needed or made. See
`platform/docs/community-cloud-api/immutable-raw-storage.md`.

**Slice 8.3** (Platform-side, no OpenTofu change) evolves the envelope this
bucket will eventually store to a nested `acceptance` / `client` /
`identity` / `source_contract` shape and adds a typed per-stream
registry/builder layer — still envelope schema `1.0`, still not wired to
any endpoint or Lambda. No infrastructure change accompanies it. See
`platform/docs/community-cloud-api/data-lake-event-envelope.md`.

**Slice 8.4** (Platform-side, no OpenTofu change) gives the
`assessment_metadata` stream its own versioned partition policy and
storage-object projector, keeping the accepted path at exactly this
module's generic Hive-style dimensions (`stream=` / `schema_version=` /
`year=` / `month=` / `day=`) — no extra path dimension was added. Still not
wired to any endpoint or Lambda; no bucket structure, prefix, or IAM change
accompanies it. See
`platform/docs/community-cloud-api/assessment-metadata-data-lake.md`.

**Slice 8.5** (Platform-side, no OpenTofu change) gives the `telemetry`
stream its own versioned partition policy and storage-object projector,
reusing the exact same generic Hive-style dimensions — again no extra path
dimension. Still not wired to any endpoint or Lambda; no bucket structure,
prefix, or IAM change accompanies it. See
`platform/docs/community-cloud-api/telemetry-data-lake.md`.

**Slice 8.6** (Platform-side, no OpenTofu change) gives the `cli_event`
stream its own versioned partition policy and storage-object projector,
again reusing the exact same generic Hive-style dimensions and adding no
new S3 metadata key at all (unlike Slices 8.4/8.5, which each added one
optional key). Still not wired to any endpoint, the CLI emitter, or Lambda;
no bucket structure, prefix, or IAM change accompanies it. See
`platform/docs/community-cloud-api/cli-event-data-lake.md`.

**Slice 8.7** (Platform-side, no OpenTofu change) gives the
`extension_event` stream its own versioned partition policy and
storage-object projector, again reusing the exact same generic Hive-style
dimensions and Option B `codestrata-client-type` metadata
(`vscode_extension` / `cursor_extension`; never `editor` or `operation` in
path or metadata). Still not wired to any endpoint, extension emitter, or
Lambda; no bucket structure, prefix, or IAM change accompanies it.
Extension collection is not claimed operational via the data lake. See
`platform/docs/community-cloud-api/extension-event-data-lake.md`.

**Slice 8.8** (Platform-side, no OpenTofu change) gives the `ai_usage`
stream its own versioned partition policy and storage-object projector,
again reusing the exact same generic Hive-style dimensions and Option B
`codestrata-client-type` metadata (`codestrata_cli` / `vscode_extension` /
`cursor_extension`; never `capability`, `provider_family`, or
`model_family` in path or metadata). Adds three AI catalog version fields
on policy and diagnostics. Still not wired to any endpoint, Engine AI
provider, client emitter, or Lambda; no bucket structure, prefix, or IAM
change accompanies it. AI usage collection is not claimed operational via
the data lake.

**Slice 8.9** (Platform-side) implements malformed-event quarantine
persistence under `quarantine/` (Put/Get + 90-day lifecycle already
present). Still not wired to endpoints; `enable_ingestion_wire` remains
false. See `platform/docs/community-cloud-api/data-lake-quarantine.md`.

**Slice 8.10** formalizes retention / lifecycle product policy and aligns
OpenTofu lifecycle (including `expire-delete-markers`, quarantine ≤
accepted validation, `force_destroy=false`). Still unwired; does not claim
production data is stored or deleted. See
`platform/docs/community-cloud-api/data-lake-retention.md`.

**Slice 8.11** formalizes encryption at rest (SSE-S3 bucket default + explicit
Put headers; no KMS resources; no bucket-policy Deny for missing encryption
headers). See `platform/docs/community-cloud-api/data-lake-encryption.md`.

**Slice 8.12** formalizes restricted IAM access: writer policy document with
stable SIDs (`WriteAcceptedRawObjects`, `WriteQuarantineRecords`,
`VerifyAcceptedRawObjects`, `VerifyQuarantineRecords`,
`DenyAcceptedObjectDeletion`, `DenyQuarantineObjectDeletion`), prefix-scoped
Put/Get, delete Deny on both prefixes, `DenyInsecureTransport` bucket policy,
no ListBucket, no KMS IAM, writer policy **unattached**. See
`platform/docs/community-cloud-api/data-lake-access-control.md`.

**Slice 8.13** (Platform-side, no OpenTofu change) formalizes storage
abstraction: typed projected-object port, adapter capability sets, explicit
factory with production-default unavailable adapter, and stream
`store_projected_*` helpers that require `put_immutable_storage_object`. Still
not wired to any endpoint or Lambda; no IAM change. See
`platform/docs/community-cloud-api/data-lake-storage-abstraction.md`.

```text
infrastructure/modules/community-data-lake/
infrastructure/production/community-data-lake.tf
```

Platform domain contracts live under
`platform/.../community_cloud_api/data_lake/` — see
`platform/docs/community-cloud-api/data-lake.md`.

## Purpose

Provide a private, encrypted, lifecycle-managed S3 bucket with accepted and
quarantine prefixes, plus an **unattached** writer IAM policy document for
later composition.

**Bucket existence does not enable Community event ingestion.**
`enable_ingestion_wire` defaults to and is validated as `false`.

## Bucket strategy

**Decision: one private bucket with prefix isolation** (not separate accepted /
quarantine buckets).

| Factor | Rationale |
| --- | --- |
| Operational simplicity | One bucket to name, encrypt, version, and monitor |
| IAM separation | Prefix-scoped Allow/Deny on `raw/*` vs `quarantine/*` |
| Lifecycle separation | Independent expiration rules per prefix |
| Accidental read exposure | Analytics roles (future) can be denied `quarantine/*` |
| Cost / management | Avoids duplicate encryption/versioning/public-access blocks |

Do not reuse Terraform state buckets, ECR repositories, or Lambda artifact
buckets as the Data Lake.

## Resources

- Private S3 bucket (deterministic name, environment-scoped)
- Block public access (all four settings)
- `BucketOwnerEnforced` (no ACL dependency)
- Versioning enabled
- SSE-S3 bucket encryption (AES256; `bucket_key_enabled = false`; KMS
  migration documented, not implemented — Slice 8.11)
- Lifecycle: accepted / quarantine expiration, multipart abort, noncurrent
  version expiration, expired delete-marker cleanup (no storage-class
  transitions, no Object Lock)
- Writer IAM policy document + standalone policy resource (**not attached**);
  prefix-scoped Put/Get; explicit Deny delete on `raw/*` and `quarantine/*`
  (Slice 8.12 stable SIDs)
- Bucket policy: `DenyInsecureTransport` (TLS only — not at-rest encryption)

No website hosting, no CORS, no public bucket policy Allow statements.

## Relationship to Community Cloud API

The `community-cloud-api` module remains independent. Its Lambda IAM must not
gain Data Lake write access until a later slice explicitly wires ingestion and
keeps fail-closed semantics until durable identity + sinks are ready.

## Relationship to other storage

| Store | Role |
| --- | --- |
| Community Data Lake bucket | Future immutable Community event envelopes |
| OpenTofu state bucket | Infrastructure state only — never event storage |
| ECR | Container images only |
| CloudWatch Logs | Operational logs — not the Data Lake |

## Extraction

This module is extraction-ready for a future private
`codestrata-infrastructure` repository. It has no dependency on Engine,
Community CLI, or extensions.

## Commands (validate only in this slice)

```bash
cd infrastructure
tofu fmt -check -recursive
cd modules/community-data-lake && tofu init -backend=false && tofu validate
cd ../../production && tofu init -backend=false && tofu validate
```

Do not run `tofu plan` or `tofu apply` unless explicitly approved outside this
slice's automation.

## Limitations

- No ingestion wire / Lambda attach
- No queues, workers, Athena, Glue, dashboards
- Retention defaults are provisional product-policy defaults requiring
  release-owner review (Slice 8.10); not a claim that production data is
  stored or deleted
- No application delete / opt-out API; lifecycle expiry ≠ privacy erasure
- SSE-S3 only; SSE-KMS deferred (Slice 8.11 encryption policy;
  no bucket-policy Deny for missing encryption headers — defense in depth
  is bucket default + explicit Put headers)
- Least-privilege writer IAM document (Slice 8.12); `DenyInsecureTransport`;
  writer policy unattached; no ListBucket; no KMS IAM
- No S3 Object Lock; no Glacier / Deep Archive transitions
- Full quarantine pipeline completed in Platform library (Slice 8.9); still
  unwired from endpoints / ingestion (`enable_ingestion_wire=false`)
- Slice 8.2's S3 adapter exists and is unit-tested but is not wired to any
  Lambda, endpoint, or ingestion path
- **Slice 8.14** integration verification
  (`platform/verification/community_data_lake/`) statically inspects this
  module (retention defaults, AES256, IAM, `DenyInsecureTransport`,
  `enable_ingestion_wire=false`) and optionally runs OpenTofu CLI validate;
  does not apply infrastructure or attach writer IAM.
- **Slice 8.15** Epic 8 completion verification
  (`platform/verification/community_data_lake_completion/`) reuses the SV.9
  report and confirms boundary/completion posture. **Epic 8 is complete.**
  Production ingestion is **not operational**. **Epic 9 not started.**

See also: `infrastructure/docs/future-data-lake.md`,
`infrastructure/modules/community-data-lake/README.md`,
`platform/docs/community-cloud-api/data-lake-retention.md`,
`platform/docs/community-cloud-api/data-lake-encryption.md`,
`platform/docs/community-cloud-api/data-lake-access-control.md`.
