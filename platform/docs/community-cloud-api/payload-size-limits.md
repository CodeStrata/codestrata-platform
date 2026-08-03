# Community Cloud API — Payload Size Limits

Transport-only protection for Community Cloud API request bodies.

Payload size limits protect the Community Cloud API process from oversized or
pathologically nested JSON. They do not authorize clients, rate-limit traffic,
persist events, or replace typed request-schema validation (Slice 7.3).

**Policy:** `payload-limit-policy:1.0`  
Independent of Community Cloud API contract 1.0, request validation policy 1.0,
assessment schema 1.2, and EIR 1.0.

## Pipeline

```text
Route resolution
  → request validation (Slice 7.3)
  → payload size validation (Slice 7.4)
  → handler
```

Unknown routes remain **404 before** payload evaluation.

Empty bodies (for example successful `GET /api/v1/health`) skip limit checks.
Forbidden-body rejections from Slice 7.3 still win when a body is present on
health.

## Default limits (`payload-limit-policy:1.0`)

| Limit | Default |
| --- | ---: |
| Maximum request bytes | 65,536 |
| Maximum JSON nesting depth | 8 |
| Maximum array length | 100 |
| Maximum object properties | 100 |
| Maximum string length | 4,096 |
| Maximum traversal count | 10,000 |

No endpoint-specific overrides in this slice.

## Error codes

All use HTTP **413 Payload Too Large** and the canonical Community Cloud error
envelope:

| Code | Meaning |
| --- | --- |
| `payload_too_large` | Body byte length exceeded |
| `payload_too_deep` | JSON nesting depth exceeded |
| `payload_array_limit` | Array length exceeded |
| `payload_object_limit` | Object property count exceeded |
| `payload_string_limit` | String length exceeded |
| `payload_complexity_limit` | Traversal complexity exceeded |

Responses may include safe metadata:

- `error.details.limit` — limit name (for example `max_request_bytes`)
- `meta.payload_limit_policy` — `payload-limit-policy:1.0`

Never included: submitted values, payload snippets, byte offsets, paths,
secrets, stack traces, or parser exception text.

## Determinism

Identical body + policy ⇒ identical status, error code, details, and body bytes.
Structural walks use sorted object keys so first-failure selection is stable.

## Ownership

Platform-only: `codestrata_platform.community_cloud_api.payload_limits`.

Engine and Community Edition remain unaware.
