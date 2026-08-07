# Community Data Lake Verification (SV.9)

Platform-only end-to-end verification for the Community Data Lake foundation:
five accepted streams, quarantine, storage adapters, privacy, retention /
encryption / access reconciliation, infrastructure contract, and production
fail-closed posture.

This package is **not** part of the Platform runtime wheel /
`codestrata_platform` distribution.

## Purpose

Verify Slice 8.14 integration contracts without enabling production ingestion:

- Typed request → envelope → stream projection → immutable storage object
- In-memory and strict fake-S3 adapter parity (STORED / ALREADY_EXISTS / CONFLICT)
- Quarantine path isolation and type rejection
- Storage factory modes (unavailable default, gated in-memory, configured S3)
- Privacy-safe receipts, metadata, and verification report output
- Static OpenTofu module contract + optional CLI validate
- Production foundation remains unwired (`enable_ingestion_wire = false`)

## Commands

```bash
# From monorepo root (full run including OpenTofu — may be slow)
PYTHONPATH=platform:platform/src:platform/tests:. \
  python -m verification.community_data_lake \
  --output-dir platform/reports/verification

# Fast pytest / CI (skip OpenTofu CLI)
PYTHONPATH=platform:platform/src:platform/tests:. \
  python -m verification.community_data_lake \
  --output-dir /tmp/sv9 --skip-opentofu
```

Report: `platform/reports/verification/community-data-lake-verification.json`

Schema: `community-data-lake-verification` / `1.0.0`

## Policy versions under verification

Data Lake policy **1.0**, envelope **1.0**, quarantine schema/policy **1.0**,
retention / encryption / access / storage **1.0**, all five partition policies
**1.0**, assessment report schema **1.2**, verification **1.0.0**.

## Separation

| Slice | Focus |
| --- | --- |
| SV.7 | Community Cloud API E2E |
| **SV.9** | Community Data Lake integration (this package) |
| **Slice 8.15** | Epic 8 completion verification (`community_data_lake_completion/`) |
| **Slice 12.4** | Active vs historical Community client boundary (`verification/community_client_boundary_cleanup/`) |

## Limitations

- In-memory and fake-S3 adapters only; no real AWS integration
- Production ingestion wiring deliberately disabled
- No atomic identity/storage coordination or exactly-once claim
- Lifecycle time not simulated in adapter tests
- Slice 12.4 retires active `cursor_extension` emission/ingestion; historical
  schema 1.0 deserialize and stored metadata inspection remain (Approach A;
  no object rewrite / S3 migration)