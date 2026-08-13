# Assessment metadata ingestion

Platform-owned privacy-first endpoint for bounded aggregate facts about a
completed local assessment. Engine product emission is gated by durable **v2**
consent (`assessment_metadata` schemas **1.0** and **1.1**).

## Endpoint

`POST /api/v1/assessment-metadata`

Route identity: `assessment_metadata.ingest`

Related Community Cloud routes:

- `GET /api/v1/health`
- `POST /api/v1/telemetry`
- `POST /api/v1/assessment-metadata`
- `POST /api/v1/cli-events` (capacity; not emitted by current assess path)

Single-event ingestion only. Not routed through `POST /telemetry`.

## Privacy statements

The assessment metadata endpoint accepts only bounded, allow-listed derived
metadata about an assessment execution. It does **not** accept:

- assessment report bodies (`assessment.html` / `assessment.json`)
- finding prose, evidence, or raw vulnerability locations
- repository identity (name / URL / remote)
- source paths or source code
- graph nodes / edges / symbols
- credentials, prompts, responses, stack traces
- report ID / report URL

Assessment metadata is not an assessment artifact and must not be used to
reconstruct repository-level technical findings.

## Schema and policy versions

| Constant | Value |
| --- | --- |
| Community Cloud API contract | `1.0` |
| Telemetry schema/policy | `1.0` |
| **Assessment metadata schema** | **`1.0`** and **`1.1`** (both accepted) |
| **Assessment metadata policy** | `community-assessment-metadata-policy:1.0` (+ 1.1 additives) |

`assessment.assessment_schema_version` is informational and currently allowlisted
to Engine report schema **`1.2` only**. Syntax must be `N.N`. Future Engine
schema versions require an explicit policy update — they are not silently accepted.

### Schema 1.0

Required blocks: `schema_version`, `event_id`, `client`, `assessment`,
`repository`, `execution`, `artifacts`.

Optional: `installation_id` (pseudonymous).

No client timestamps in this schema. Server records `accepted_at` on accept.

### Schema 1.1 additives (bounded / strict)

In addition to the 1.0 envelope, **1.1** may include:

| Field | Role |
| --- | --- |
| `assessment_id` | Opaque assessment correlation id (not a report URL) |
| `finding_aggregates` | Privacy-safe aggregates: approved rule ID + severity + category + count |
| `head_confidence` | Categorical head confidence levels |
| `failure_category` | Bounded failure category when assessment failed |

Unknown fields are **rejected** for schema **1.1** where server validation is
strict (allow-list only). Do not treat amd as an open extension point.

Numeric overall “health scores” and numeric per-head scores are **not** part of
this contract. Graph telemetry is **not** part of this contract.

## Request envelope (1.0 core)

### Assessment block

- `assessment_status`: `completed` | `partially_completed` | `failed` | `cancelled`
- `assessment_mode`: `deterministic` | `deterministic_with_ai` | `unavailable`
- `executed_heads`: sorted/deduplicated allowlist
  (`technology_inventory`, `architecture`, `technical_debt`, `dependency`,
  `security`, `testing`, `cloud_readiness`, `ai_readiness`, `performance`,
  `modernization`)
- Aggregate counts (1.0); finding pattern aggregates via 1.1 `finding_aggregates`

### Repository block

Broad categorical characteristics only: primary language vocabulary
(`python|java|javascript|typescript|go|csharp|rust|unknown|unavailable`),
count buckets, repository shape, presence booleans.

No repository name/URL/path/commit/branch/package/module/technology lists.

### Execution block

Duration buckets, result vocabulary, `ai_used` boolean, `offline_mode`,
client version/platform.

No exact durations, command args, exceptions, provider identity, models, tokens,
or costs.

### Artifact block

Booleans for report/findings/recommendations/html generation + bounded
`artifact_count`. No paths, digests, or contents.

## Event identity

Fixed identity event type: `assessment_metadata_submitted`.

Scope: `(api_version, client_type, installation_id?, event_type, event_id)`.

Fingerprint follows the established decision (`event_id` included; no client
timestamps; transport `request_id` absent).

Retry: 202 first accept / 200 exact retry / 409 conflict / 503 unavailable.

Shared identity lookup/recorder injectables with telemetry; **separate**
assessment-metadata sink.

## Defaults

Unavailable sink + missing identity store → **503**.
Never “accepted while discarded.”

## Auth / rate limiting

Authenticated Community client credential + consent-gated client emission.
Anonymous writes return `401`.

## Storage honesty

Accepted events project into the Community Data Lake as **derived metadata**,
not source repositories. One assessment that also emits lifecycle telemetry is
counted once in Insights Total/Successful/Failed authorities.

## Non-goals

- Graph telemetry
- AI provider identity / prompts / responses
- Report publish packages
- Historical self-service deletion via telemetry disable
