# Community Cloud API — Structured Logging

Fail-safe structured logging for the Community Cloud API.

Structured logging records safe request metadata for operators. It does not
authorize clients, ship logs to cloud backends, persist telemetry events, or
affect request outcomes.

**Policy:** `community-logging-policy:1.0`  
Independent of Community Cloud API contract 1.0, request validation policy 1.0,
payload-limit policy 1.0, assessment schema 1.2, and EIR 1.0.

## Pipeline

```text
Incoming request
  → logging context creation
  → request_received
  → handler path (validation / payload limits / business handler)
  → optional validation_failed | payload_rejected | health_checked
  → request_completed | request_failed
  → response
```

Logging never alters response bodies. Logging failures are swallowed.

## Event types

| Event | When |
| --- | --- |
| `request_received` | Every request entering dispatch |
| `health_checked` | Successful `GET /api/v1/health` |
| `validation_failed` | Slice 7.3 request validation failure |
| `payload_rejected` | Slice 7.4 payload-limit rejection |
| `request_completed` | Terminal 2xx/3xx |
| `request_failed` | Terminal 4xx/5xx |

No telemetry business events in this slice.

## Safe fields

Allowlisted fields only (sorted keys in JSON):

- `event_type`, `level`, `policy_version`
- `api_version`, `method`, `route`, `route_name`
- `request_id`, `status_code`, `duration_ms`, `error_code`
- `client_host` (ASGI client host only — never `X-Forwarded-For`)
- `event_seq`
- `timestamp` only when policy `include_timestamps=True` (injectable clock)

## Request IDs

- Client `X-Request-Id` / `X-Correlation-Id` may be reused in logs (sanitized)
- If absent, a deterministic factory generates a logging-only id
- Auto-generated ids are **not** written into response bodies
- Existing header echo of client-supplied ids is unchanged

## Redaction

Never logged:

- request bodies / payloads
- Authorization / Cookie / API key headers
- tokens, passwords, JWTs, secrets
- local filesystem paths

Helpers live in `logging/sanitization.py`.

## Levels

`DEBUG`, `INFO`, `WARNING`, `ERROR` only.

## Failures

Sink/formatter exceptions never fail API requests. Recursive emit is suppressed.
Structured payloads never include stack traces.

## Ownership

Platform-only: `codestrata_platform.community_cloud_api.logging`.

Default sink is a no-op (`NullLogSink`). Tests inject `MemoryLogSink`.
No OpenTelemetry, cloud shipping, or backend configuration in this slice.
