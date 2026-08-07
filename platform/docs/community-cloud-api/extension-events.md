# Extension event ingestion (Slice 7.10)

Platform-owned privacy-first endpoint for bounded operational classifications of
supported CodeStrata editor extensions.

## Endpoint

`POST /api/v1/extension-events`

Route identity: `extension_events.ingest`

Production Community Cloud routes after this slice:

- `GET /api/v1/health`
- `POST /api/v1/telemetry`
- `POST /api/v1/assessment-metadata`
- `POST /api/v1/cli-events`
- `POST /api/v1/extension-events`

Single-event ingestion only. No `/extension`, `/vscode-events`, `/editor-events`,
`/events/extension`, or `/extension-events/batch` aliases.

## Privacy statements

The Extension Event endpoint accepts only bounded operational classifications.
It does not accept document contents, selected text, file or workspace identity,
repository identity, editor URIs, source code, command arguments, settings,
terminal contents, or exception text.

The endpoint contract does not enable extension telemetry by itself.
Client-side emission, consent, privacy controls, retry behavior, and installation
identity remain separate product decisions.

Do not send Extension Event payloads through `POST /telemetry`. Assessment
summaries remain on `POST /assessment-metadata`. CLI operations remain on
`POST /cli-events`. AI provider/model/token details belong on Slice 7.11 — only
`context.ai_requested` (boolean) is allowed here.

## Schema, policy, and operation catalog

| Constant | Value |
| --- | --- |
| Community Cloud API contract | `1.0` (unchanged) |
| Telemetry / assessment metadata / CLI policies | `1.0` (unchanged) |
| **Extension event schema** | `1.0` |
| **Extension event policy** | `community-extension-event-policy:1.0` |
| **Extension operation catalog** | `extension-operation-catalog:1.0` |

Only schema version `1.0` is accepted. Unsupported versions fail closed.

Logging policy remains `community-logging-policy:1.0` with additive allowlisted
`extension_event_*` events and safe fields (same additive pattern as Slices
7.7–7.9).

## Request envelope

Required: `schema_version`, `event_id`, `client`, `event`, `context`.

Optional: `installation_id` (anonymous).

Unknown fields rejected. Top-level JSON must be an object. No timestamps in
schema 1.0.

### Client

Active clients for current ingestion (Slice 12.4):

- `vscode_extension` with `editor=vscode`

Retired historical client value (schema 1.0 deserialize only; not accepted by
current ingestion policy or active storage projection):

- `cursor_extension` with `editor=cursor`

`other_extension` is deferred until a real third-party client exists.
`codestrata_cli` is rejected on this endpoint.

Fields: bounded `version`, `editor`, `editor_version`, `platform`.
No hostname, username, account, workspace, repository, remote host, or
installation path.

### Event

- `operation` — canonical only (see catalog)
- `lifecycle`: `started` | `completed` | `failed` | `cancelled`
- `result`: `succeeded` | `partially_succeeded` | `failed` | `cancelled` | `unavailable`
- `duration_bucket`: shared Community Cloud buckets
- `failure_category` — required when `lifecycle=failed`; forbidden on successful
  completed/started+succeeded

Failure categories justified by extension behavior: `invalid_configuration`,
`unsupported_workspace`, `assessment_failed`, `report_open_failed`,
`extension_not_ready`, `engine_unavailable`, `network_unavailable`,
`permission_denied`, `internal_error`, `cancelled`, `unavailable`.

### Context

- `invocation_source`: `command_palette` | `status_bar` | `editor_action` |
  `automatic_activation` | `api` | `unknown`
- `user_initiated` / `offline_mode` / `ai_requested` booleans
- `selected_assessment_heads` — Community Cloud canonical heads; sorted/deduped
- `report_surface`: `editor_tab` | `external_browser` | `none` | `unavailable`
- `workspace_state`: `workspace_open` | `folder_open` | `no_workspace` | `unknown`

Broad UI state only — never workspace name/URI/path, open tabs, documents,
selection, search, settings, or command IDs.

## Operation catalog (`extension-operation-catalog:1.0`)

Canonical operations from the public VS Code extension command surfaces
(identity-free). Historical Cursor command aliases may remain in Platform
catalogs for read compatibility of previously accepted records; Cursor is not
an active emitter (Slice 12.4):

`activate`, `assess`, `assess_with_ai`, `ask_suggested`, `check_environment`,
`clear_results`, `copy_conversation_prompt`, `filter_findings`, `init_config`,
`install_engine`, `missing_assessment_help`, `open_documentation`, `open_output`,
`open_report`, `refresh_findings`, `refresh_recommendations`,
`set_findings_group_by`, `show_findings`, `show_recommendations`, `show_welcome`.

Reviewed aliases map VS Code command IDs (for example
`codestrata.openHtmlReport` → `open_report`). Path-bearing UX such as
`openFindingLocation` is intentionally absent from the catalog.

Unknown operations are rejected. Semantic mapping changes require a catalog
version bump.

## Event identity

Fixed source event type: `extension_event_submitted`.

Scope: `(api_version, client_type, installation_id?, event_type, event_id)`.

Operation/lifecycle/result/context affect the **fingerprint**, not the identity
scope `event_type`.

Same raw `event_id` under CLI client scope remains a distinct identity.

Retry: 202 first accept / 200 exact retry / 409 conflict / 503 unavailable.

Shared `EventIdentityLookup` / `EventIdentityRecorder`. Separate
`ExtensionEventSink`. No exactly-once guarantee.

## Defaults

`UnavailableExtensionEventSink` + missing identity store → **503**.
Never “accepted while discarded.”

Independent injectables on `create_community_cloud_app()`:

- `telemetry_sink`
- `assessment_metadata_sink`
- `cli_event_sink`
- `extension_event_sink`
- shared `event_identity_lookup` / `event_identity_recorder`

Health remains independent of the extension sink.

## Auth / rate limiting / persistence / emitter

Unauthenticated in this slice. Not production-complete until later Epic 7 slices.

No database, Redis, queue, stream, object storage, data lake, worker, or
analytics warehouse. Ports and in-memory tests only.

This slice creates only the server endpoint and contract. The VS Code
extension is **not** wired to emit events. The former Cursor extension
product is removed (Epic 12).
