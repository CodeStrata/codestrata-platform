# Community Cloud API rate limiting (Slice 7.12)

Rate limiting controls request volume. It does not authenticate the client,
authorize event submission, identify a person, or guarantee distributed
enforcement when only the in-process store is configured.

Raw client network addresses are not persisted or logged. A policy-bound
one-way scope is used only for rate-limit enforcement and diagnostics.

## Policy

| Field | Value |
| --- | --- |
| Policy ID | `community-rate-limit-policy` |
| Version | `1.1` (`community-rate-limit-policy:1.1`) |
| Algorithm | **Fixed window** |
| Default health limit | 120 requests / 60 seconds |
| Default ingestion limit | 30 requests / 60 seconds per safe scope |
| Auth-attempt limit | 60 requests / 60 seconds (transport scope) |
| Client scope | Authenticated preferred for ingestion; transport for health / auth attempts |
| Default store | Process-local `InMemoryRateLimitStore` |

Policy **1.1** deliberately replaces 1.0 transport-only ingestion scoping after
Slice 7.13 authentication. Health remains transport-scoped.

These defaults are development-oriented and replaceable in Slice 7.14 deployment
configuration. They are not final production limits.

### Why fixed window

Fixed window is deterministic under an injectable monotonic clock, easy to test
at exact boundaries, and maps cleanly to persistence-neutral store adapters.
Token bucket is deferred; this slice implements one algorithm only.

Tradeoffs: bursts at window edges are possible; distributed fairness depends on
a future shared store.

## Route coverage

Every production route has an explicit policy entry (route IDs):

| Route ID | Group | Role |
| --- | --- | --- |
| `health.get` | `health` | Higher limit, unauthenticated |
| `telemetry.ingest` | `ingestion` | Shared ingestion budget |
| `assessment_metadata.ingest` | `ingestion` | Shared ingestion budget |
| `cli_events.ingest` | `ingestion` | Shared ingestion budget |
| `extension_events.ingest` | `ingestion` | Shared ingestion budget |
| `ai_usage.ingest` | `ingestion` | Shared ingestion budget |

`RouteSpec.rate_limit_group` is additive metadata (excluded from route identity).
Unknown routes remain **404** and never consume a rate-limit bucket.
Unsupported methods (for example `POST /health`) resolve to **405** before
rate limiting, so they do not consume the resolved route’s budget.

## Transport scope

Preferred scope material:

1. Rate-limit policy token / scope salt version
2. Direct ASGI `scope["client"]` host only
3. Rate-limit policy group (`health` or `ingestion`)

Derived forms:

- Safe scope: `rate-scope:{sha256[:24]}`
- Safe reference (logs/diagnostics): `rls-{sha256[:12]}`
- Store key: `rate:{sha256[:24]}` (includes window identity in key material)

**Never trusted in this slice:**

- `X-Forwarded-For`, `Forwarded`, `X-Real-IP`, `CF-Connecting-IP`, `True-Client-IP`
- Request body, event ID, request ID, user-agent, authorization, cookies

Missing ASGI client host uses `global_anonymous_scope` (documented limitation).
Random per-request scopes are forbidden.

Trusted-proxy / serverless edge identity is deferred to deployment follow-up.

## Request pipeline order

```text
Route / method resolution
  → rate-limit transport evaluation
  → request-schema validation
  → payload-size limits
  → handler
```

Change from Slices 7.3–7.4: rate limiting now runs **before** body validation and
payload traversal so abusive volume is rejected without parsing JSON.

Limited requests never reach handlers, identity lookup/recorder, or sinks.

Exact event retries still consume rate-limit capacity (identity and rate limiting
are independent). Changing `X-Request-Id` or `event_id` does not create a new
bucket.

## HTTP behavior

| Outcome | Status | Code | Notes |
| --- | --- | --- | --- |
| Allowed | unchanged endpoint status | — | Optional `RateLimit-*` headers |
| Limited | 429 | `rate_limit_exceeded` | `Retry-After` + `RateLimit-*` |
| Store unavailable (ingestion) | 503 | `rate_limit_unavailable` | Fail closed |
| Store unavailable (health) | health process-local fallback | — | Explicit policy behavior |

Headers (bounded relative seconds, no timestamps in bodies):

- `Retry-After`
- `RateLimit-Limit`
- `RateLimit-Remaining`
- `RateLimit-Reset`

Safe messages only. No scope identity, raw IP, store details, or payload values
in responses.

## Store ports

- `RateLimitStore.evaluate(...)` — persistence-neutral
- `InMemoryRateLimitStore` — tests / local explicit default (process-local)
- `UnavailableRateLimitStore` — fail-closed probe

No Redis, database, filesystem, DynamoDB, or API Gateway usage plans in this
slice. Slice 7.14 must select a distributed enforcement layer for multi-instance
deployments; an in-memory limiter alone is insufficient across serverless
instances.

## Logging

Additive events under `community-logging-policy:1.0` (no policy version bump):

- `rate_limit_allowed`
- `rate_limit_exceeded`
- `rate_limit_unavailable`

Safe fields may include route name, policy ID, limit, remaining,
`retry_after_seconds`, and `safe_scope_reference`. Rate-limit events omit raw
`client_host`. Logging failures remain fail-safe.

## Authentication boundary (Slice 7.13)

Future authenticated client IDs may replace anonymous transport scope. This
slice does not parse API keys, Authorization headers, or registration flows.
Installation IDs are not trusted as authentication.

## Explicit non-goals

- Authentication / API keys / client registration
- Distributed stores / queues / workers / analytics
- CORS changes / bypass lists / admin tokens
- CLI or extension client 429 handling
- Engine / Community Edition changes
