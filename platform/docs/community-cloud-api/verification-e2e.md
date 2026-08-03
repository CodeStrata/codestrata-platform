# End-to-end verification (Slice 7.15)

Verification-only suite for the complete Community Cloud API request pipeline
after Slices 7.1–7.14.

## Scope

Exercises production routes with injected in-memory adapters:

- `InMemoryCommunityCredentialVerifier`
- `InMemoryRateLimitStore`
- `InMemoryEventIdentityStore`
- Per-endpoint in-memory sinks
- Deterministic clocks / request IDs

Does **not** add product capabilities, AWS deployment, OpenTofu apply, Docker
builds, persistence, queues, analytics, or Epic 8 work.

## Pipeline under test

```text
Route resolution
→ Authentication
→ Rate limiting
→ Schema validation
→ Client↔payload match
→ Payload limits
→ Handler (identity lookup → sink → identity recorder)
→ Logging
→ Response
```

## Test modules

| Module | Role |
| --- | --- |
| `platform/tests/community_cloud_api/e2e_helpers.py` | Shared verification harness |
| `platform/tests/community_cloud_api/test_verification_e2e.py` | Full-lifecycle pipeline assertions |
| `platform/tests/community_cloud_api/test_verification_boundary.py` | Engine/CLI/extensions/infra/export/version guards |

## Production foundation

`create_production_foundation_app()` remains fail-closed for ingestion (unavailable
verifier). Health remains deployable without sinks.
