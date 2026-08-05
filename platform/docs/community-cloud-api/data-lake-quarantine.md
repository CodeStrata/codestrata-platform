# Community Data Lake Quarantine (Slice 8.9)

Slice 8.9 implements **malformed-event quarantine**: a versioned,
privacy-safe quarantine record, deterministic `quarantine-object:` identity,
canonical JSON serialization, in-memory + S3 persistence under `quarantine/`,
and bounded error mapping — still **unwired** from any endpoint, `app.py`, or
`deployment/wiring.py` to quarantine or S3.

Production remains fail-closed (`enable_ingestion_wire=false`). This slice
does not claim that production events are quarantined.

## What is persisted

A `QuarantineRecord` (schema `1.0`) under:

```text
quarantine/reason=<code>/year=YYYY/month=MM/day=DD/<opaque-hex>.json
```

No `event_stream` path dimension. The opaque filename is derived from
`quarantine-object:{sha256[:24]}`.

### Identity vs date

Quarantine object **identity** excludes `detected_at` and partition date.
The same logical rejection produces the same quarantine object id even on
different calendar days. The **object key** still includes the date
partition for operational listing; only the hex filename is
identity-stable across dates.

Identity material (pipe-joined): quarantine policy token, schema version,
reason code, validation stage, event stream (or empty), safe event /
object references (or empty), and sorted diagnostic codes.

## Reason codes

Existing codes are preserved. Slice 8.9 adds:

- `unsupported_envelope_schema`, `unsupported_source_schema`,
  `unsupported_source_policy`, `stream_contract_mismatch`,
  `invalid_source_payload`, `envelope_too_large`, `invalid_partition`,
  `invalid_storage_object`, `checksum_mismatch`, `malformed_stored_object`

`unsupported_schema` remains as a generic backward-compatible code.

Validation stages: `request_validation`, `envelope_projection`,
`envelope_validation`, `partition_projection`, `storage_object_validation`,
`storage_write`, `storage_read_verification`.

## Privacy

Records and S3 metadata **never** store raw HTTP bodies, headers,
Authorization, cookies, IPs, `event_id`, `installation_id`, prompts,
`source`, credentials, exception text, bucket names, or object keys.

Quarantine-only S3 metadata allowlist:

- `codestrata-content-sha256`
- `codestrata-quarantine-schema`
- `codestrata-quarantine-reason`
- `codestrata-object-id`

Diagnostic codes are an allowlist (no free-text).

## Retention

Platform quarantine policy documents `retention_days_reference = 90` to
align with the lake policy / OpenTofu lifecycle default. This module does
**not** duplicate HCL; infrastructure lifecycle already scopes expiration
to `quarantine/`.

**Slice 8.10** formalizes retention product policy
(`community-data-lake-retention-policy:1.0`), including quarantine ≤ accepted,
expired-delete-marker cleanup, and static Platform ↔ HCL reconciliation. See
[data-lake-retention.md](./data-lake-retention.md). Quarantine still has no
application delete / opt-out API; lifecycle expiry is not privacy erasure.

**Slice 8.11** applies the same SSE-S3 encryption contract to quarantine
Puts as to accepted objects (`ServerSideEncryption=AES256`, no KMS). See
[data-lake-encryption.md](./data-lake-encryption.md).

**Slice 8.12** scopes writer IAM separately for `quarantine/*` (Put/Get +
delete Deny) and documents that future analytics roles must not auto-include
quarantine read access. See [data-lake-access-control.md](./data-lake-access-control.md).

**Slice 8.13** formalizes the typed quarantine storage port
(`put_immutable_quarantine_object`) and adapter parity with accepted writes.
See [data-lake-storage-abstraction.md](./data-lake-storage-abstraction.md).

## Explicitly out of scope

- Endpoint → quarantine wiring (later slice)
- Claiming that quarantine runs in production ingestion
- Claiming production events are stored or deleted
- HCL Object Lock or storage-class transitions (rejected in Slice 8.10)
- Customer-managed KMS encryption (deferred in Slice 8.11)
