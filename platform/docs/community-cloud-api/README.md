# Community Cloud API (Platform)

Platform-owned versioned HTTP API surface for Community Cloud integrations.

| Slice | Delivered |
| --- | --- |
| **7.1** | Foundation: `/api/v1`, registry, errors, deterministic JSON |
| **7.2** | `GET /api/v1/health` process availability |
| **7.3** | Request schema validation foundation |
| **7.4** | Transport payload-size limits (`payload-limit-policy:1.0`) |
| **7.5** | Structured logging foundation (`community-logging-policy:1.0`) |
| **7.6** | Retry-safe event identity contracts (`community-event-identity-policy:1.0`) |
| **7.7** | Privacy-first `POST /api/v1/telemetry` |
| **7.8** | Privacy-first `POST /api/v1/assessment-metadata` |
| **7.9** | Privacy-first `POST /api/v1/cli-events` |
| **7.10** | Privacy-first `POST /api/v1/extension-events` |
| **7.11** | Privacy-first `POST /api/v1/ai-usage` |
| **7.12** | Deterministic rate limiting (`community-rate-limit-policy:1.0` → **1.1** with auth scopes) |
| **7.13** | Community client authentication (`community-authentication-policy:1.0`) |
| **7.14** | Serverless deployment foundation (`infrastructure/` + Lambda adapter) |
| **7.15** | End-to-end pipeline verification (auth → RL → validation → payload → identity → sink) |

Epic 7 ends at Slice 7.15. Verification proves the combined request pipeline for
all six production routes with in-memory adapters. No durable store, data lake,
or client emitters were added.

No durable Community event store or data lake yet. Slice 7.14 packages and
serves the API through serverless infrastructure as a **production
infrastructure foundation** — health is operational; ingestion remains
fail-closed.

The Slice 7.14 deployment proves that the Community Cloud API can be packaged
and served through serverless infrastructure. It does not enable durable
Community event ingestion because production credential verification, shared
event identity, and event sinks are not yet configured.

Community Data Lake resources are intentionally deferred. Future S3 buckets,
lifecycle, partitioning, encryption, access, and ingestion notifications will be
added through a separate `infrastructure/modules/data-lake` module.

## Why Platform owns the API

| Layer | Role |
| --- | --- |
| **Engine / Community Edition** | Local single-repository assessment CLI and MCP |
| **Platform** | Hosts Community Cloud API and all commercial cloud services |
| **Infrastructure** (private) | OpenTofu AWS resources; extractable to `codestrata-infrastructure` |

Engine must remain unaware of this package. Community clients will call the HTTP API
later; they must not import `codestrata_platform`.

Public export excludes `platform/` (see `public-export-manifest.yaml`).

## Versioning strategy

- Current version: **`v1`**
- URL root: **`/api/v1`**

| Constant | Value | Role |
| --- | --- | --- |
| `COMMUNITY_CLOUD_API_SCHEMA_VERSION` | `1.0` | API contract |
| Request-validation / payload / logging / event-identity | `1.0` | Foundation policies |
| Telemetry / assessment metadata / CLI / extension | `1.0` | Slices 7.7–7.10 |
| AI usage schema / `community-ai-usage-policy:1.0` / catalogs | `1.0` | Slice 7.11 |
| `community-rate-limit-policy:1.1` | `1.1` | Slice 7.12 + authenticated scopes in 7.13 |
| `community-authentication-policy:1.0` / credential format `1` | `1.0` / `1` | Slice 7.13 |

Independent of assessment schema 1.2 and EIR schema 1.0.

## Architecture

```text
codestrata_platform.community_cloud_api
  health/                 # GET /api/v1/health
  validation/             # Slice 7.3
  payload_limits/         # Slice 7.4
  logging/                # Slice 7.5
  event_identity/         # Slice 7.6
  telemetry/              # Slice 7.7
  assessment_metadata/    # Slice 7.8
  cli_events/             # Slice 7.9
  extension_events/       # Slice 7.10
  ai_usage/               # Slice 7.11
  rate_limiting/          # Slice 7.12 / 7.13 scope update
  authentication/         # Slice 7.13
  deployment/             # Slice 7.14 Lambda/ASGI adapter (production foundation)
```

Packaging Dockerfile: `platform/deployment/community-cloud-api/Dockerfile`  
Cloud resources: [`infrastructure/`](../../../infrastructure/README.md)

```python
from codestrata_platform.community_cloud_api import create_community_cloud_app
# Production foundation (Lambda):
from codestrata_platform.community_cloud_api.deployment import (
    create_production_foundation_app,
)

app = create_community_cloud_app(
    telemetry_sink=...,
    assessment_metadata_sink=...,
    cli_event_sink=...,
    extension_event_sink=...,
    ai_usage_sink=...,
    event_identity_lookup=...,
    event_identity_recorder=...,
    # Optional: rate_limit_policy=, rate_limit_store=, rate_limit_clock_ms=
)
```

All event sinks are independent. Identity lookup/recorder may be shared.
Defaults fail closed for sinks (503). Rate limiting defaults to a process-local
in-memory store (see [rate-limiting.md](./rate-limiting.md)).

## Endpoints

### `GET /api/v1/health`

Process/API availability only. Independent of sinks and identity stores.

### `POST /api/v1/telemetry`

See [telemetry-ingestion.md](./telemetry-ingestion.md).

### `POST /api/v1/assessment-metadata`

See [assessment-metadata.md](./assessment-metadata.md). AI field: `ai_used` boolean only.

### `POST /api/v1/cli-events`

See [cli-events.md](./cli-events.md). AI field: `ai_requested` boolean only.

### `POST /api/v1/extension-events`

See [extension-events.md](./extension-events.md). AI field: `ai_requested` boolean only.

### `POST /api/v1/ai-usage`

See [ai-usage.md](./ai-usage.md).

Bounded AI operational classifications only — no prompts, responses, source,
credentials, exact tokens, or cost. Client emission is not wired.

### Rate limiting

See [rate-limiting.md](./rate-limiting.md). Fixed-window; authenticated scope for
ingestion after Slice 7.13; process-local by default.

### Authentication

See [authentication.md](./authentication.md). Bearer Community client tokens.
Health remains public. Default verifier is unavailable (fail-closed).

### End-to-end verification

See [verification-e2e.md](./verification-e2e.md). Slice 7.15 (final Epic 7 slice)
verifies the combined pipeline; it does not add product capabilities.

## Non-goals (Epic 7 complete through 7.15)

- Client emission / consent / privacy settings wiring
- User accounts / OAuth / SAML / sessions / credential issuance APIs
- Distributed rate-limit store / production credential store / workers / data lake
- Engine AI provider, prompt, RAG, or KG changes
- Exactly-once delivery guarantees
- Epic 8 functionality
