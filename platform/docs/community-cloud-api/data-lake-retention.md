# Community Data Lake Retention and Lifecycle (Slice 8.10)

Slice 8.10 formalizes **product-policy retention / lifecycle defaults** for the
Community Data Lake: a Platform-side
`CommunityDataLakeRetentionPolicy` (`community-data-lake-retention-policy:1.0`)
aligned with OpenTofu lifecycle variables under
`infrastructure/modules/community-data-lake/`.

This slice does **not** claim that production Community events are stored or
deleted. Endpoints, `app.py`, and `deployment/wiring.py` remain unwired from
the data lake. `enable_ingestion_wire` stays `false`.

## Retention vs immutability

| Concern | Meaning in this slice |
| --- | --- |
| **Immutability (write path)** | Conditional `PutObject` / no application overwrite of accepted objects (Slice 8.2). Writer IAM **Deny** on `s3:DeleteObject*` for `raw/*`. |
| **Retention (lifecycle)** | S3 lifecycle *expiration* after N days. Lifecycle expiry is **not** privacy erasure, legal hold release, or an opt-out API. |

Retention does not weaken immutability during the retention window: writers still
cannot delete accepted objects via the product writer policy.

## Defaults (provisional, review-required)

| Setting | Default | Notes |
| --- | --- | --- |
| Accepted (`raw/`) retention | **365** days | Provisional product-policy starting point |
| Quarantine retention | **90** days | Must be ≤ accepted |
| Incomplete multipart abort | **7** days | Bucket-wide |
| Noncurrent version expiration | **30** days | Both prefixes |
| Expired delete-marker cleanup | **enabled** | Separate lifecycle rule |
| Versioning | **Enabled** | Required for noncurrent + delete-marker rules |
| `force_destroy` | **false** | Validated to remain false |
| Storage class transitions | **disabled** | No Glacier / Deep Archive |
| S3 Object Lock | **disabled** | Not approved for v0.2.0 |

Defaults require **release-owner review** before treating them as a validated
production policy. They are not a legal or multi-jurisdiction compliance claim.

## Bounds

| Variable | Min | Max |
| --- | --- | --- |
| Accepted retention | 30 | 2555 |
| Quarantine retention | 7 | 365 |
| Incomplete multipart | 1 | 90 |
| Noncurrent version | 1 | 2555 |

Platform validation (`retention_validation.py`) and OpenTofu
`variables.tf` / `validation.tf` must stay aligned (static reconciliation tests).

## Accepted vs quarantine

- Accepted objects live under `raw/` and expire after `accepted_retention_days`.
- Quarantine objects live under `quarantine/` and expire after
  `quarantine_retention_days`.
- Product policy requires **quarantine ≤ accepted** unless an explicit,
  documented override exists (none in v0.2.0).

## Multipart, noncurrent versions, delete markers

- **Multipart abort** is a separate empty-filter rule
  (`abort-incomplete-multipart-uploads`) so incomplete uploads under either
  prefix are cleaned up without duplicating the rule.
- **Noncurrent version expiration** is attached to both prefix-scoped retention
  rules (versioning is Enabled).
- **Expired delete markers** are cleaned by a separate empty-filter rule
  (`expire-delete-markers`). AWS does not allow combining
  `expired_object_delete_marker` with `expiration.days` in the same block.

## `force_destroy = false`

Bucket `force_destroy` defaults to false and is fail-closed in module
validation. Accidental `tofu destroy` must not silently wipe retained objects.

## No Object Lock, no transitions

Slice 8.10 explicitly rejects S3 Object Lock and storage-class transitions
(Glacier, Deep Archive, etc.) in both Platform policy and HCL tests. Those
remain future, separately reviewed decisions.

## No application delete API / opt-out limitations

There is **no** Community Cloud API endpoint to delete lake objects or to
opt out of retention. Lifecycle expiry is not equivalent to GDPR-style
erasure. Durable identity / privacy coordination across stores is deferred.

## Durable identity retention limitation

Event-identity stores (when later wired) are **not** governed by these S3
lifecycle rules. Coordinating identity retention with lake expiry is an
explicit limitation of this slice.

## Platform references infrastructure; does not override HCL

`CommunityDataLakeRetentionPolicy` documents the same defaults and bounds as
the OpenTofu module. Platform code does **not** import or mutate HCL at
runtime. Alignment is enforced by static reconciliation tests.

## Unwired posture

- No `app.py` / `wiring.py` / endpoint imports of retention or data lake.
- Writer IAM policy remains unattached; `enable_ingestion_wire = false`.
- Engine remains unaware of the data lake.

## Relationship to Slice 8.11

Slice 8.10 stops at retention / lifecycle product policy and HCL alignment.
**Slice 8.11** formalizes encryption at rest (`community-data-lake-encryption-policy:1.0`,
SSE-S3 only). See [data-lake-encryption.md](./data-lake-encryption.md).
Durable ingestion wiring remains later.

## Relationship to Slice 8.12

Lifecycle expiration is **S3 service** behavior — not writer `DeleteObject`.
**Slice 8.12** adds explicit identity-policy Deny on delete for both prefixes
while keeping the writer policy unattached. See
[data-lake-access-control.md](./data-lake-access-control.md).

## Relationship to Slice 8.13

**Slice 8.13** formalizes the storage-abstraction port and factory; retention
rules remain enforced by S3 lifecycle (Slice 8.10 HCL), not by adapter delete
APIs (forbidden on the port). See
[data-lake-storage-abstraction.md](./data-lake-storage-abstraction.md).

## Package symbols

```text
community-data-lake-retention-policy:1.0
CommunityDataLakeRetentionPolicy / default_retention_policy()
RetentionValidationError / validate_retention_values()
RetentionPolicyDiagnostics / diagnostics_from_retention_policy()
```

See also: [data-lake.md](./data-lake.md),
[data-lake-quarantine.md](./data-lake-quarantine.md),
[data-lake-encryption.md](./data-lake-encryption.md),
[data-lake-access-control.md](./data-lake-access-control.md),
[immutable-raw-storage.md](./immutable-raw-storage.md),
`infrastructure/docs/community-data-lake.md`.
