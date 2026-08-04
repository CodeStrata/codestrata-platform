# Community Cloud API Verification (SV.7)

Platform-only end-to-end verification for the Community Cloud API as one coherent
pipeline.

This package is **not** part of the Platform runtime wheel / `codestrata_platform`
distribution.

## Purpose

Verify the six production routes and Epic 7 foundations:

Route resolution → Community client authentication → rate-limit scope → rate
limit → strict request schema → client-type matching → payload limits → endpoint
service → retry-safe event identity → endpoint sink → identity recording →
structured logging → deterministic HTTP response

Also verify production-foundation fail-closed ingestion via
`create_production_foundation_app()`.

## Production route inventory

| Route ID | Method | Path |
| --- | --- | --- |
| `health.get` | GET | `/api/v1/health` |
| `telemetry.ingest` | POST | `/api/v1/telemetry` |
| `assessment_metadata.ingest` | POST | `/api/v1/assessment-metadata` |
| `cli_events.ingest` | POST | `/api/v1/cli-events` |
| `extension_events.ingest` | POST | `/api/v1/extension-events` |
| `ai_usage.ingest` | POST | `/api/v1/ai-usage` |

No docs/OpenAPI routes. No commercial Platform API routes. No batch endpoints.

## Verification applications

1. **Fully wired in-memory app** — authentication enabled, fake `cscc_v1_TEST_ONLY_*`
   credentials, in-memory verifier / rate-limit store / identity store / sinks /
   `MemoryLogSink`, deterministic clock.
2. **Production-foundation app** — `create_production_foundation_app()`; health
   works; ingestion fail-closed (`authentication_unavailable`).

Fake credentials are never written to the verification report, logs assertions,
or diagnostics.

## Commands

```bash
# From monorepo root
PYTHONPATH=platform:platform/src:engine:engine/src \
  python -m verification.community_cloud_api

PYTHONPATH=platform:platform/src:engine:engine/src \
  python -m verification.community_cloud_api \
  --output-dir platform/reports/verification
```

Report: `platform/reports/verification/community-cloud-api-verification.json`

Schema: `community-cloud-api-verification` / `1.0.0`

## Policy versions under verification

Community Cloud API contract **1.0**, authentication **1.0**, credential format
**1**, rate-limit **1.1**, validation / payload / logging / event-identity
**1.0**, telemetry / assessment-metadata / CLI / extension / AI schemas and
policies **1.0**. Assessment report schema remains **1.2**.

## Separation

| Slice | Focus |
| --- | --- |
| SV.6 | Engineering Intelligence pipeline |
| **SV.7** | Community Cloud API E2E (this package) |
| SV.8 | Website-safe export (not started here) |
| SV.9 | Infrastructure deployment verification (not started) |
| Future | Community Data Lake / durable sinks |

## Limitations

- In-memory adapters only; no AWS, OpenTofu, Docker, durable stores, queues, or
  analytics.
- Does not add endpoints, schemas, emitters, or credential issuance.
- Does not modify Engine, Community CLI, or IDE extensions.
- Atomicity between sink acceptance and identity recording remains a documented
  limitation on recorder failure.
