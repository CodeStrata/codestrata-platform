# CLI event ingestion (Slice 7.9)

Platform-owned privacy-first endpoint for bounded operational classifications of
Community CLI usage.

## Endpoint

`POST /api/v1/cli-events`

Route identity: `cli_events.ingest`

Production Community Cloud routes after this slice:

- `GET /api/v1/health`
- `POST /api/v1/telemetry`
- `POST /api/v1/assessment-metadata`
- `POST /api/v1/cli-events`

Single-event ingestion only. No `/cli`, `/commands`, `/usage`, `/events/cli`, or
`/cli-events/batch` aliases.

## Privacy statements

The CLI event endpoint accepts only bounded operational classifications. It does
not accept command lines, command arguments, working directories, repository
identity, paths, source data, configuration contents, exception text, or shell
output.

The endpoint contract does not enable CLI telemetry by itself. Client-side
emission remains separate and must follow the product’s privacy and opt-in
policies.

Do not send CLI event payloads through `POST /telemetry`. Assessment counts,
repository shape, and report artifacts belong on `POST /assessment-metadata`
(Slice 7.8). Extension UI events belong on Slice 7.10. AI provider/model/token
details belong on Slice 7.11 — only `context.ai_requested` (boolean) is allowed
here.

## Schema, policy, and operation catalog

| Constant | Value |
| --- | --- |
| Community Cloud API contract | `1.0` (unchanged) |
| Telemetry schema/policy | `1.0` (unchanged) |
| Assessment metadata schema/policy | `1.0` (unchanged) |
| **CLI event schema** | `1.0` |
| **CLI event policy** | `community-cli-event-policy:1.0` |
| **CLI operation catalog** | `cli-operation-catalog:1.0` |

Only schema version `1.0` is accepted. Unsupported versions fail closed.

## Request envelope

Required: `schema_version`, `event_id`, `client`, `event`, `context`.

Optional: `installation_id` (anonymous).

Unknown fields rejected. Top-level JSON must be an object. No timestamps in
schema 1.0.

### Client

- `name` must be `codestrata_cli` (extension clients rejected)
- bounded `version` and `platform`
- no hostname, username, machine ID, user-agent dump, or repository/workspace identity

### Event

- `operation` — canonical only (see catalog below)
- `lifecycle`: `started` | `completed` | `failed` | `cancelled`
- `result`: `succeeded` | `partially_succeeded` | `failed` | `cancelled` | `unavailable`
- `duration_bucket`: `under_1s` | `1s_to_5s` | `5s_to_30s` | `30s_to_2m` | `2m_to_10m` | `over_10m` | `unavailable`
- `failure_category` — allowlisted broad category; required when `lifecycle=failed`; forbidden on successful completed/started+succeeded

Failure categories: `invalid_configuration`, `unsupported_repository`,
`assessment_failed`, `report_generation_failed`, `ai_provider_unavailable`,
`network_unavailable`, `permission_denied`, `internal_error`, `cancelled`,
`unavailable`.

No exception class/message, stack traces, paths, command args, or provider bodies.

### Context

- `execution_mode`: `deterministic` | `deterministic_with_ai` | `unavailable`
- `output_format`: `json` | `html` | `console` | `multiple` | `none` | `unavailable`
- `offline_mode` / `ai_requested` booleans
- `selected_assessment_heads` — Community Cloud canonical heads only; sorted/deduped
- `invocation_source`: `terminal` | `script` | `ci` | `unknown`
- `terminal_environment`: `interactive` | `non_interactive` | `unknown`

No shell name, CI provider, workflow name, cwd, paths, env vars, or command strings.

## Operation catalog (`cli-operation-catalog:1.0`)

Canonical operations derived from the public Community Typer CLI:

`about`, `agent`, `ai`, `architecture`, `assess`, `config`, `doctor`, `evidence`,
`examples`, `extensions`, `help`, `incremental`, `init`, `mcp`, `onboard`,
`open`, `report`, `roadmap`, `rules`, `scan`, `telemetry`, `validate`, `version`,
`welcome`.

Reviewed aliases (payload stores canonical only):

| Alias | Canonical |
| --- | --- |
| `report.open` / `report_open` | `open` |
| `report.validate` / `report_validate` | `validate` |
| `--version` | `version` |
| `codestrata` | `help` |

Unknown operations are rejected. Semantic mapping changes require a catalog
version bump. Raw command text is never accepted.

## Event identity

Fixed source event type: `cli_event_submitted`.

Scope: `(api_version, client_type=codestrata_cli, installation_id?, event_type, event_id)`.

Operation/lifecycle/result/context affect the **fingerprint**, not the identity
scope `event_type`.

Retry behavior (Slice 7.6):

- first accept → sink once → record identity → **202** `accepted`
- exact retry → **200** `already_accepted` (no second sink/recorder call)
- conflict → **409** `event_identity_conflict` (sink not called)
- unavailable sink/store/recorder → **503** (no false success)

Shared `EventIdentityLookup` / `EventIdentityRecorder`. Separate `CliEventSink`.

No exactly-once guarantee. Record-after-accept atomicity limitation preserved.

## Responses

`CliEventResponse`: `status`, `safe_event_reference`, `retry_status`, `schema_version`.

Does not return command, operation/context echo, raw `event_id`, fingerprint,
event key, installation ID, or server timestamps.

## Defaults

`UnavailableCliEventSink` + missing identity store → **503**.
Never “accepted while discarded.”

Independent injectables on `create_community_cloud_app()`:

- `telemetry_sink`
- `assessment_metadata_sink`
- `cli_event_sink`
- shared `event_identity_lookup` / `event_identity_recorder`

Health remains independent of the CLI sink.

## Auth / rate limiting / persistence

Unauthenticated in this slice. Not production-complete until later Epic 7 slices.

No database, Redis, queue, stream, object storage, data lake, worker, or analytics
warehouse. Ports and in-memory tests only.

## Client emission

This slice creates only the server endpoint and contract. The Community CLI is
**not** wired to emit events. Do not add background HTTP calls to CLI commands.

## Logging

Bounded safe events: `cli_event_received`, `cli_event_accepted`, `cli_event_retry`,
`cli_event_conflict`, `cli_event_rejected`.

Allowed additive fields under logging policy **1.0**: `safe_event_reference`,
`source_event_type`, `retry_status`, `cli_schema_version`, `cli_policy_version`,
`canonical_operation`, `lifecycle`, `result`, status code.

Never log: `event_id`, `installation_id`, command/args, paths, context,
fingerprint, event key, assessment heads, or payload contents.
