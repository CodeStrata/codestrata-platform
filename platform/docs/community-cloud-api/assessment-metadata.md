# Assessment metadata ingestion (Slice 7.8)

Platform-owned privacy-first endpoint for bounded aggregate facts about a
completed local assessment.

## Endpoint

`POST /api/v1/assessment-metadata`

Route identity: `assessment_metadata.ingest`

Production Community Cloud routes after Slice 7.8 (extended by later slices):

- `GET /api/v1/health`
- `POST /api/v1/telemetry`
- `POST /api/v1/assessment-metadata`

(Slice 7.9 adds `POST /api/v1/cli-events`.)

Single-event ingestion only. Not routed through `POST /telemetry`.

## Privacy statements

The assessment metadata endpoint accepts only bounded aggregate facts about an
assessment execution. It does not accept the assessment report, Findings,
Recommendations, Evidence, repository identity, source paths, or source code.

Assessment metadata is not an assessment artifact and must not be used to
reconstruct repository-level technical findings.

## Schema and policy versions

| Constant | Value |
| --- | --- |
| Community Cloud API contract | `1.0` (unchanged) |
| Telemetry schema/policy | `1.0` (unchanged) |
| **Assessment metadata schema** | `1.0` |
| **Assessment metadata policy** | `community-assessment-metadata-policy:1.0` |

`assessment.assessment_schema_version` is informational and currently allowlisted
to Engine report schema **`1.2` only**. Syntax must be `N.N`. Future Engine
schema versions require an explicit policy update — they are not silently accepted.

## Request envelope

Required blocks: `schema_version`, `event_id`, `client`, `assessment`,
`repository`, `execution`, `artifacts`.

Optional: `installation_id` (anonymous).

No timestamps in this schema.

### Assessment block

- `assessment_status`: `completed` | `partially_completed` | `failed` | `cancelled`
- `assessment_mode`: `deterministic` | `deterministic_with_ai` | `unavailable`
- `executed_heads`: sorted/deduplicated allowlist
  (`technology_inventory`, `architecture`, `technical_debt`, `dependency`,
  `security`, `testing`, `cloud_readiness`, `ai_readiness`, `performance`,
  `modernization`)
- Aggregate counts only (no IDs, titles, severities, rule IDs)

### Repository block

Broad anonymous characteristics only: primary language vocabulary
(`python|java|javascript|typescript|go|csharp|rust|unknown|unavailable`),
count buckets, repository shape, presence booleans.

No repository name/URL/path/commit/branch/package/module/technology lists.

### Execution block

Duration buckets, result vocabulary, `ai_used` boolean, `offline_mode`,
client version/platform.

No exact durations, command args, exceptions, providers, models, tokens, or costs.

### Artifact block

Booleans for report/findings/recommendations/html generation + bounded
`artifact_count`. No paths, digests, or contents.

## Event identity

Fixed identity event type: `assessment_metadata_submitted`.

Scope: `(api_version, client_type, installation_id?, event_type, event_id)`.

Fingerprint follows the Slice 7.7 decision (`event_id` included; no timestamps;
transport `request_id` absent).

Retry: 202 first accept / 200 exact retry / 409 conflict / 503 unavailable.

Shared `EventIdentityLookup` / `EventIdentityRecorder` injectables with
telemetry; **separate** assessment-metadata sink.

## Defaults

`UnavailableAssessmentMetadataSink` + missing identity store → **503**.
Never “accepted while discarded.”

## Auth / rate limiting

Unauthenticated in 7.8. Incomplete for production exposure until Slices 7.12 and
7.13. No IP-derived identity.

## Non-goals

CLI/extension emission (7.9/7.10), AI usage details (7.11), persistence, queues,
data lake, batching, report upload.
