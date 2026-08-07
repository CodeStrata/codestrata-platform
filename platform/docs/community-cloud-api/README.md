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
all six production routes with in-memory adapters. No durable store or client
emitters were added in Epic 7.

Slice 7.14 packages and serves the API through serverless infrastructure as a
**production infrastructure foundation** — health is operational; ingestion
remains fail-closed without production credential verification, shared event
identity, and event sinks.

**Slice 8.1** adds the Community Data Lake **foundation only** (domain contracts
under `community_cloud_api/data_lake/` and private OpenTofu module
`infrastructure/modules/community-data-lake/`). Endpoints are not wired to S3;
production ingestion remains fail-closed. See [data-lake.md](./data-lake.md).

**Slice 8.2** adds the **immutable raw-JSON storage contract**: canonical
byte-exact JSON serialization, fail-closed conflict classification, privacy-safe
write receipts, and a production-capable (but still unwired) S3 adapter under
`community_cloud_api/data_lake/infrastructure/` — the only module allowed to
import `boto3`. No endpoint, `app.py`, or `deployment/wiring.py` is touched,
and no exactly-once delivery guarantee is claimed. See
[immutable-raw-storage.md](./immutable-raw-storage.md).

**Slice 8.3** evolves the envelope's canonical serialized shape to a nested
`acceptance` / `client` / `identity` / `source_contract` contract — still
envelope schema **1.0**, a pre-persistence foundation refinement, not a
runtime migration — and adds a typed per-stream registry and high-level
builders (`build_data_lake_envelope`, `build_storage_object_from_request`)
for constructing an envelope from an already-validated endpoint request
model. Still no endpoint → storage wiring, no durable event-identity store,
and no version bump anywhere. See
[data-lake-event-envelope.md](./data-lake-event-envelope.md).

**Slice 8.4** gives the `assessment_metadata` stream its own versioned
partition policy (`StreamPartitionPolicy`, `1.0`) and a stream-specific
storage-object projector, plus generic (stream-agnostic) machinery a future
slice will reuse for the other four streams. The accepted path stays the
**generic Hive path only** — no extra partition dimension was added. Still
no endpoint → storage wiring, and the assessment report schema stays
**1.2**. See
[assessment-metadata-data-lake.md](./assessment-metadata-data-lake.md).

**Slice 8.5** reuses that same generic machinery for the `telemetry`
stream: its own versioned partition policy
(`community-telemetry-partition-policy:1.0`) and
`project_telemetry_storage_object()`. The accepted path again stays the
**generic Hive path only**; the only new S3 metadata key is
`codestrata-client-type` (`event_type` stays private-payload-only). Still
no endpoint → storage wiring. See
[telemetry-data-lake.md](./telemetry-data-lake.md).

**Slice 8.6** reuses that same generic machinery for the `cli_event`
stream: its own versioned partition policy
(`community-cli-event-partition-policy:1.0`) and
`project_cli_event_storage_object()`. The accepted path again stays the
**generic Hive path only**, and this time **no** new S3 metadata key is
added at all (`operation`/`lifecycle`/`result` stay private-payload-only;
`client_type` is redundant since the CLI client is always
`codestrata_cli`). Still no endpoint → storage wiring. See
[cli-event-data-lake.md](./cli-event-data-lake.md).

**Slice 8.7** reuses that same generic machinery for the `extension_event`
stream: its own versioned partition policy
(`community-extension-event-partition-policy:1.0`) and
`project_extension_event_storage_object()`. The accepted path again stays
the **generic Hive path only**; Option B reuses `codestrata-client-type`
for `vscode_extension` (active); historical `cursor_extension` read-only (never `editor` or `operation`
in path or metadata). Still no endpoint → storage wiring, and extension
collection is not claimed operational via the data lake. See
[extension-event-data-lake.md](./extension-event-data-lake.md).

**Slice 8.8** reuses that same generic machinery for the `ai_usage`
stream: its own versioned partition policy
(`community-ai-usage-partition-policy:1.0`) and
`project_ai_usage_storage_object()`. The accepted path again stays the
**generic Hive path only**; Option B reuses `codestrata-client-type` for
`codestrata_cli` / `vscode_extension` (active); historical `cursor_extension` read-only (never
`capability` / `provider_family` / `model_family` in path or metadata).
Adds the three AI catalog version fields on policy and diagnostics. Still
no endpoint → storage wiring, and AI usage collection is not claimed
operational via the data lake. Does not start endpoint → storage wiring.
See [ai-usage-data-lake.md](./ai-usage-data-lake.md).

**Slice 8.9** implements malformed-event quarantine (versioned records,
`quarantine-object:` identity, S3/in-memory persistence under
`quarantine/`) without wiring endpoints or claiming production quarantine.
See [data-lake-quarantine.md](./data-lake-quarantine.md).

**Slice 8.10** formalizes data retention and lifecycle policies
(`community-data-lake-retention-policy:1.0`) aligned with OpenTofu
lifecycle defaults — still unwired; does not claim production data is
stored or deleted. See [data-lake-retention.md](./data-lake-retention.md).

**Slice 8.11** formalizes encryption at rest
(`community-data-lake-encryption-policy:1.0`, SSE-S3 / AES256 only; KMS
deferred) — still unwired; does not claim production data is stored. See
[data-lake-encryption.md](./data-lake-encryption.md).

**Slice 8.12** formalizes restricted IAM access control
(`community-data-lake-access-policy:1.0`, least-privilege writer policy
document, delete Deny, no ListBucket, analytics/quarantine separation) —
writer policy unattached. See
[data-lake-access-control.md](./data-lake-access-control.md).

**Slice 8.13** formalizes storage abstraction
(`community-data-lake-storage-policy:1.0`, typed projected-object port,
factory with production-default unavailable adapter, in-memory test-only) —
still unwired. **Slice 8.14** adds integration verification (in-memory +
fake-S3 end-to-end checks; does not wire ingestion). **Slice 8.15** completes
Epic 8 with boundary/completion verification (reuses SV.9; production ingestion
**not operational**; Epic 9 not started). See
[data-lake-storage-abstraction.md](./data-lake-storage-abstraction.md),
`platform/verification/community_data_lake/`, and
`platform/verification/community_data_lake_completion/`.

## Why Platform owns the API

| Layer | Role |
| --- | --- |
| **Engine / Community Edition** | Local single-repository assessment CLI and MCP |
| **Platform** | Hosts Community Cloud API and all commercial cloud services |
| **Infrastructure** (private) | OpenTofu AWS resources; extractable to `codestrata-infrastructure` (Slice 12.5 contract defined; export in 12.6) |

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

Endpoint request schemas (telemetry, CLI, extension, AI usage, assessment
metadata) remain **separate** contracts even when each is versioned `1.0`.
Policy versions (rate limit, authentication) and credential format versions are
not payload schema versions. Cross-schema compatibility with assessment/EIR is
verified by SV.14 without merging endpoint schemas. Deterministic event
identity, fingerprints, safe references, and injected-clock rate-limit behavior
are verified by SV.15 (`platform/verification/deterministic_outputs/`).

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

### System Verification SV.7

End-to-end Community Cloud API verification lives outside the runtime package:

`platform/verification/community_cloud_api/`

```bash
PYTHONPATH=platform:platform/src:engine:engine/src \
  python -m verification.community_cloud_api
```

Report: `platform/reports/verification/community-cloud-api-verification.json`
(`community-cloud-api-verification` / `1.0.0`).

SV.7 uses in-memory adapters only. It does not deploy to AWS, run OpenTofu,
build Docker images, start website-export verification (SV.8), or wire endpoints
to the Data Lake (Slice 8.1 foundation is separate and unwired).


### System Verification SV.9

Infrastructure deployment-foundation verification lives under:

`infrastructure/verification/`

```bash
PYTHONPATH=platform:platform/src:engine:engine/src:. \
  python -m infrastructure.verification
```

Report:
`infrastructure/reports/verification/platform-deployment-foundation-verification.json`.

SV.9 verifies production-only OpenTofu structure, packaging, and in-process
fail-closed foundation behavior. It does not apply infrastructure, push images,
or start SV.10.

### Community Data Lake integration verification (Slice 8.14)

End-to-end Data Lake foundation verification (streams, quarantine, adapters,
privacy, infrastructure contract):

`platform/verification/community_data_lake/`

```bash
PYTHONPATH=platform:platform/src:platform/tests:. \
  python -m verification.community_data_lake \
  --output-dir platform/reports/verification
```

Report:
`platform/reports/verification/community-data-lake-verification.json`
(`community-data-lake-verification` / `1.0.0`).

Does not wire ingestion, attach writer IAM, or start Slice 8.15.

## Non-goals (Epic 7 complete through 7.15)

- Client emission / consent / privacy settings wiring
- User accounts / OAuth / SAML / sessions / credential issuance APIs
- Distributed rate-limit store / production credential store / workers
- Engine AI provider, prompt, RAG, or KG changes
- Exactly-once delivery guarantees
- Endpoint → Data Lake / quarantine wiring (storage contract, adapter,
  typed registry, builders, five stream partition policies, and quarantine
  persistence exist but are not connected to any endpoint)
- Durable event-identity/deduplication store
- Endpoint → Data Lake wiring and durable identity remain deferred; Slices
  8.9–8.11 added unwired quarantine, retention policy, and encryption
  policy only
