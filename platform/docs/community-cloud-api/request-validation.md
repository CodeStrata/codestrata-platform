# Community Cloud API — Request Validation

Request validation protects the Community Cloud API contract. It does not
authorize clients, enforce request-byte limits, persist events, or determine
whether an event should be accepted by downstream systems.

**Policy version:** `COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION = "1.0"`  
(independent of Community Cloud API contract 1.0, assessment 1.2, and EIR 1.0)

## Pipeline

```text
HTTP request
  → route resolution
  → content-type validation (when a body is present for a schema route)
  → JSON parsing
  → typed schema validation (strict, unknown fields forbidden)
  → optional semantic validator
  → validated immutable request model on RequestContext
  → endpoint handler
```

Handlers must not parse raw bodies independently. Handlers never receive
unvalidated dictionaries when a request schema is registered.

## Body policies

| Policy | Behavior |
| --- | --- |
| `forbidden` | Non-empty body → `request_body_forbidden` (400) |
| `required` | Empty/missing body → `request_body_required` (400) |
| `optional` | Absent OK; present body validated |

Body policy is explicit on `RequestSchemaDescriptor` — not inferred from HTTP method.

`GET /api/v1/health` uses `forbidden`.

## Error codes

| Code | HTTP | Meaning |
| --- | --- | --- |
| `malformed_json` | 400 | Syntactically invalid JSON / non-UTF-8 |
| `request_body_required` | 400 | Body required but missing |
| `request_body_forbidden` | 400 | Body present but not allowed |
| `unsupported_json_shape` | 400 | Top-level non-object (array/string/number/null) |
| `unsupported_media_type` | 415 | Non-JSON Content-Type when body present |
| `invalid_request_schema` | 422 | Valid JSON object failed schema/semantic rules |

Malformed JSON and schema-invalid JSON are distinct.

Validation details are a deterministic list (max 20 by default). Field errors never
include submitted values, exception text, Pydantic class names, or stack traces.

## Strict typing and unknown fields

- Pydantic `strict=True`, `extra="forbid"`, `frozen=True`
- String `"1"` does not coerce to integer; `"true"` does not coerce to boolean
- Unknown fields are rejected (not silently discarded)

Unavoidable note: Pydantic may still normalize some container presentations
internally; Community Cloud request models use `Strict*` scalars and fail closed
on string/number/bool mismatches.

## Reusable primitives

Defined in `validation/schema.py` for future event schemas:

- `ApiEventName`, `ApiClientName`, `ApiClientVersion`, `ApiSchemaVersion`
- `ApiIdentifier`, `ApiTimestampString`, `ApiSafeLabel`
- `ApiSafeMetadataKey`, `ApiSafeMetadataValue`
- `ApiRepositoryLanguage`, `ApiPlatformName`
- `ApiRepositoryRelativePath` (path safety helper; unused by production routes yet)
- `ApiStrictInt`, `ApiStrictBool`

**Identifiers / protocol names:** ASCII set `[A-Za-z0-9._:-]`, no control characters.  
**Safe labels:** Unicode allowed; still reject controls and secret-like values.

## Secret and path safety

Reusable detectors reject likely secrets and sensitive paths (`unsafe_value`)
without echoing the submitted value:

- private-key PEM headers, bearer tokens, AWS-style access keys
- signed URL query markers, `file://`
- absolute POSIX/Windows/home/temp paths
- source-shaped multiline blobs

Repository-relative paths reject absolutes, `file://`, and `..` traversal.

## Semantic validation

`RequestSchemaDescriptor.semantic_validator` runs after typed validation and
returns the same safe field-error model. No business semantic rules ship in 7.3.

## Explicit non-goals (Slice 7.3)

- Production telemetry / metadata / CLI / extension / AI event schemas
- HTTP payload-byte-size enforcement (owned by Slice 7.4)
- Structured logging system (owned by Slice 7.5)
- Retry-safe event IDs (Slice 7.6)
- Authentication, rate limiting, persistence, queues, workers, deployment
- FastAPI default 422 leakage (overridden for Community Cloud app only)

## Ownership

Platform-only (`codestrata_platform.community_cloud_api.validation`).  
Engine and Community Edition remain unaware.
