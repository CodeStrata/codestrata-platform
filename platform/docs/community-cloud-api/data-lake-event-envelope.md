# Schema-Versioned Event Envelopes (Slice 8.3)

Slice 8.3 evolves the Community Data Lake's canonical serialized envelope
shape from Slice 8.1's flat fields to a nested `acceptance` / `client` /
`identity` / `source_contract` contract, and adds the typed, per-stream
registry and builders needed to construct a `DataLakeEnvelope` from an
already-validated Community Cloud API endpoint request model.

It does **not** wire any endpoint to storage, does not add a durable
event-identity/deduplication store, does not add stream-specific partition
policy ownership (deferred to a later slice), and does not change production
HTTP acceptance in any way. See
[data-lake.md](./data-lake.md) and
[immutable-raw-storage.md](./immutable-raw-storage.md) for the Slice
8.1/8.2 foundation this slice builds on.

## Version-impact decision

**The canonical serialized envelope shape changes; the envelope schema
version does not.**

`COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION` stays `"1.0"`, and every
source endpoint schema stays `"1.0"`. This is deliberate: Slice 8.1's flat
envelope was a **pre-persistence foundation** — no endpoint was ever wired to
storage in Slices 8.1 or 8.2, so nothing was ever durably written to S3 in
production under the flat shape. Reshaping the envelope now, before the
first durable write, is a foundation refinement, not a runtime schema
migration. A schema migration (with a version bump, dual-read/dual-write, or
backfill) would only be required if the flat shape had ever been durably
written and needed to be read back. It never was.

All Slice 8.1/8.2 tests that asserted the flat shape have been updated to
build and assert against the nested shape (see
`platform/tests/community_cloud_api/data_lake/_envelope_test_helpers.py`,
the shared `make_envelope()` helper used across the domain's test suite).

## Canonical serialized shape

```json
{
  "acceptance": {
    "accepted_at": "2026-08-04T12:34:56Z",
    "partition_date": "2026-08-04"
  },
  "client": {
    "client_type": "codestrata_cli"
  },
  "envelope_schema_version": "1.0",
  "event_stream": "telemetry",
  "identity": {
    "event_key": "event:abcdef1234567890abcdef12",
    "safe_event_reference": "evt-aaaaaaaaaaaa"
  },
  "payload": { "...": "allowlisted projected endpoint fields" },
  "source_contract": {
    "policy_id": "community-telemetry-policy:1.0",
    "schema_name": "community-telemetry",
    "schema_version": "1.0"
  }
}
```

Top-level keys, nested-object keys, and array order are exactly as produced
by `DataLakeEnvelope.to_stable_dict()` — sorted, deterministic, and
byte-for-byte reproducible for identical logical input (see
[Determinism](#determinism) below).

`payload_fingerprint` is intentionally **never** part of the storage
envelope. Content fingerprinting is an identity-layer concern
(`community_cloud_api.event_identity`), not a storage-envelope field — the
envelope's own idempotency signal is `identity.event_key` plus the content
digest computed at serialization time (`canonical_json.serialize_canonical_raw_json`).

## Nested envelope dataclasses

`envelopes.py` defines four small, independently-validated nested
dataclasses plus the `DataLakeEnvelope` that composes them:

| Dataclass | Fields | Structural guard |
| --- | --- | --- |
| `SourceContract` | `schema_name`, `schema_version`, `policy_id` | `policy_id` must be a full URN (`id:version`) |
| `EnvelopeIdentity` | `event_key`, `safe_event_reference` | `event_key` must start with `event:`; `safe_event_reference` must start with `evt-` |
| `EnvelopeAcceptance` | `accepted_at`, `partition_date` | `partition_date` must equal the date component derived from `accepted_at` |
| `EnvelopeClient` | `client_type` | Non-blank |

`DataLakeEnvelope` itself validates `envelope_schema_version` (non-blank),
`event_stream` (must be a registered `EventStream` value), `payload` (must
be a mapping), and that every nested field is an instance of its expected
dataclass — never a raw string or dict passed through unchecked.

### Slice 8.1/8.2 compatibility properties

Every flat-shape accessor Slice 8.1/8.2 code and tests relied on is
preserved as a read-only property on `DataLakeEnvelope`, delegating to the
nested fields:

| Property | Delegates to |
| --- | --- |
| `source_schema_version` | `source_contract.schema_version` |
| `source_policy_version` | `source_contract.policy_id` (full URN, despite the "version"-sounding name — kept for 8.1/8.2 call-site compatibility) |
| `event_key` | `identity.event_key` |
| `safe_event_reference` | `identity.safe_event_reference` |
| `client_type` | `client.client_type` |
| `accepted_year` / `accepted_month` / `accepted_day` | `acceptance.year` / `.month` / `.day` |

`identifiers.build_lake_object_id` and `partitions.build_accepted_object_key`
continue to work unmodified against these properties —
`build_lake_object_id` deliberately keys off `source_schema_version` (the
source endpoint schema version), never `source_policy_version`.

`DataLakeEventEnvelope` is a plain alias for `DataLakeEnvelope`, for Slice
8.3+ modules that prefer the more explicit name; both names refer to the
exact same class.

## Typed per-stream registry

Slice 8.3 adds a registry that binds each of the five event streams to its
endpoint request model, allowlisted payload projector, client-type
extractor, and schema/policy identity — the single lookup table every
typed envelope builder consults.

```text
data_lake/
  source_contracts.py     # SourceContractDescriptor dataclass (the binding shape)
  envelope_registry.py     # the five concrete SourceContractDescriptor instances
  source_projection.py      # project_request_payload() / extract_client_type() dispatch
  streams/
    __init__.py
    telemetry.py               # SCHEMA_NAME, project_payload(), client_type_from_request()
    assessment_metadata.py
    cli_events.py
    extension_events.py
    ai_usage.py
```

| Event stream | Schema name | Policy URN | Request model |
| --- | --- | --- | --- |
| `telemetry` | `community-telemetry` | `community-telemetry-policy:1.0` | `TelemetryIngestionRequest` |
| `assessment_metadata` | `community-assessment-metadata` | `community-assessment-metadata-policy:1.0` | `AssessmentMetadataRequest` |
| `cli_event` | `community-cli-event` | `community-cli-event-policy:1.0` | `CliEventRequest` |
| `extension_event` | `community-extension-event` | `community-extension-event-policy:1.0` | `ExtensionEventRequest` |
| `ai_usage` | `community-ai-usage` | `community-ai-usage-policy:1.0` | `AiUsageRequest` |

Each stream module's `project_payload()` is an **allowlisted passthrough**:
`request.to_stable_dict()`. It preserves every field already approved as
part of that endpoint's own request contract — including `event_id` and the
optional `installation_id` — and adds nothing beyond it. `client_type_from_request()`
reads `request.client.name`. `get_source_contract()` (in `envelope_registry.py`)
is fail-closed: an unregistered or unknown stream raises
`UnknownEventStreamError` rather than falling back to a partial match.

## Building an envelope from a typed request

`envelope_builders.build_data_lake_envelope()` is the one high-level entry
point every future call site should use:

```python
from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
    build_data_lake_envelope,
)

envelope = build_data_lake_envelope(
    event_stream="telemetry",
    request=validated_telemetry_request,   # already-validated Pydantic model
    event_key=event_key,                    # from event_identity, Slice 7.6
    safe_event_reference=safe_reference,     # from event_identity, Slice 7.6
    clock=FixedAcceptanceClock(when),         # or SystemAcceptanceClock() in a future wired slice
)
```

Steps, each fail-closed with a bounded `EnvelopeErrorCode` (never a raw
`ValueError` or pydantic error) on rejection:

1. Look up the stream's `SourceContractDescriptor` — unregistered stream →
   `invalid_envelope`.
2. Confirm `request` is an instance of the descriptor's registered request
   model — mismatch → `stream_contract_mismatch`.
3. Project the allowlisted payload and extract the client type; any
   unexpected projector/extractor failure → `invalid_source_payload`.
4. Validate the client type against the stream's allowlist — disallowed →
   `stream_contract_mismatch` (detail `client_type_not_allowed`).
5. Stamp `accepted_at` / `partition_date` from the supplied `AcceptanceClock`.
6. Construct and structurally + privacy-validate the envelope — failure →
   `unsafe_envelope`.
7. Check the serialized size against `policy.max_envelope_bytes` — over
   bound → `envelope_too_large`.

`build_storage_object_from_request()` composes this with
`immutable_write.build_immutable_raw_storage_object()` for a one-call
request → resolved storage object path. `put_request_via_store()` further
composes that with `store.put_immutable_event()` for a one-call request →
store-write path. None of these three functions is imported by `app.py`,
`deployment/wiring.py`, or any endpoint `routes.py`/`service.py`.

## Acceptance clock

`accepted_at` is server-assigned acceptance time — never a client-submitted
timestamp — so archival partitions are deterministic and reproducible from a
given clock:

- `AcceptanceClock` (protocol): `now_utc() -> datetime`.
- `FixedAcceptanceClock(when)`: always returns the same instant. The
  reference implementation for every test and any future deterministic
  replay tooling.
- `SystemAcceptanceClock()`: the only clock that reads real wall time.
- `format_accepted_at(dt)`: normalizes to UTC and formats as
  `YYYY-MM-DDTHH:MM:SSZ` — sub-second precision is truncated for
  deterministic, compact envelopes.
- `partition_date_from_accepted_at(accepted_at)`: derives `YYYY-MM-DD`.
- `partition_components(partition_date)`: splits into `(year, month, day)`.

## Serialization and deserialization

`envelope_serialization.py` does **not** invent a second serializer: it
wraps the Slice 8.2 canonical JSON primitives
(`canonical_json.serialize_canonical_raw_json` /
`canonical_json.validate_utf8_json_object_bytes`) with envelope-aware,
fail-closed structure checks.

`serialize_data_lake_envelope(envelope)` returns the same `CanonicalRawJson`
(bytes, `sha256:` digest, length) Slice 8.2 already defines — sorted keys,
compact separators, ASCII-escaped, no trailing newline.

`deserialize_data_lake_envelope(data, *, policy=None, revalidate_payload=True)`
reconstructs a validated `DataLakeEnvelope` from untrusted bytes, fail-closed
at every step:

1. `data` must be valid UTF-8 JSON with an object root.
2. Every top-level and nested-object field set must match **exactly** —
   both unknown and missing fields are rejected (`invalid_envelope`).
3. `envelope_schema_version` must exactly equal `policy`'s (default: the
   active policy's `"1.0"`) — mismatch → `unsupported_envelope_schema`.
4. The reconstructed envelope is re-validated against `policy` (privacy scan
   + `max_envelope_bytes` size bound) — failure → `unsafe_envelope` or
   `envelope_too_large`.
5. When `revalidate_payload` (the default), the payload is re-validated
   against its registered source contract: re-parsed through the same
   Pydantic request model and re-projected through the same allowlisted
   projector, then compared against the stored payload — any mismatch
   (structural or projection) → `invalid_source_payload`. This confirms the
   payload still round-trips through its original contract, not merely that
   the JSON is well-formed.

## Size policy

`CommunityDataLakePolicy.max_envelope_bytes` (default `70_000`, bounds
`[1_024, 131_072]`) is a **separate, storage-envelope-level** bound — not
the HTTP transport limit. Community Cloud API request bodies are already
bounded well below `65_536` bytes by the Slice 7.4 payload-limits policy;
this bound additionally accounts for the acceptance/identity/source-contract
wrapper material Slice 8.3 adds around the projected payload, and is
deliberately generous relative to (not equal to) the HTTP limit.

## Privacy: structural key-name scanning

Slice 8.1 shipped a coarse, case-insensitive **substring** scan over the
entire canonical JSON blob (`FORBIDDEN_ENVELOPE_KEYS`) — effective, but
prone to false positives on legitimate values (a hex digest or enum value
that happens to contain the substring `"secret"`, for example).

Slice 8.3 adds a second, independent pass targeting a distinct problem: new
forbidden field **names** (`authorization`, `cookie`, `request_id`, `ip`,
`remote_addr`, `principal`, `credential`, `rate_limit_key`,
`aws_request_id`, `lambda_request_id`, `repository_name`, `project_name`,
`file_path`, `source_code`, `prompt`, `response`) that are common enough
identifiers that a blob-substring scan would either miss them (if not
scanned) or false-positive constantly (if scanned coarsely — e.g.
`"outcome": "authentication_failed"` is a legitimate enum value, not a
credential).

`FORBIDDEN_ENVELOPE_KEY_NAMES` is scanned **structurally**: every dict key,
at any nesting depth of the canonical envelope (including inside lists of
objects), is checked against the set by exact, case-insensitive name —
never by substring. This means:

- `{"response_time_bucket": "1s_to_5s"}` passes (distinct key name).
- `{"outcome": "authentication_failed"}` passes (the forbidden name check
  only inspects keys, never values).
- `{"authorization": "Bearer ..."}` at any depth is rejected, regardless of
  the value.

`validate_envelope_privacy(envelope)` runs **both** passes (structural
key-name scan, then the original Slice 8.1 blob-substring scan) as
defense-in-depth over whatever redaction the source domain already
performed — a caller must keep payload string values free of the
Slice 8.1 substrings (e.g. never encode a hex digest containing the literal
word `"secret"`).

### `event_id` and `installation_id` are allowed inside `payload`

Both fields are part of every endpoint's own approved request contract and
are preserved verbatim by every stream's `project_payload()`:

- They are **never** part of the object key, partition path, S3 metadata,
  logs, or any public receipt — only inside the private, encrypted raw
  storage payload.
- `installation_id` is an **optional**, endpoint-policy-defined pseudonymous
  identifier. Hashing or truncating it does **not**, by itself, constitute
  anonymization — it remains client-correlatable identity material and must
  be treated with the same handling care as any other pseudonymous
  identifier, even though it is permitted inside the private payload.

## Determinism

- Two envelopes built from the same logical inputs (event stream, request
  contents, `event_key`, `safe_event_reference`, and clock) serialize to
  **byte-identical** canonical JSON, regardless of Python dict insertion
  order in the source payload (canonical JSON always sorts map keys).
- A different `accepted_at` changes the serialized bytes (different
  `acceptance.accepted_at` / `acceptance.partition_date`) but **never**
  changes the lake-object id — `identifiers.build_lake_object_id` is keyed
  off `policy_token`, `event_stream`, `source_schema_version`, and
  `event_key` only, never acceptance time.

See `platform/tests/community_cloud_api/data_lake/test_envelope_determinism.py`.

## Bounded error taxonomy

`EnvelopeErrorCode` (in `envelope_models.py`) is the single, stable set of
error identifiers every Slice 8.3 rejection path raises via
`EnvelopeBuildError` — never raw exception text, payload fragments, or file
paths:

| Code | Raised when |
| --- | --- |
| `invalid_envelope` | Unknown/unregistered event stream, or structural envelope construction/deserialization failure |
| `unsupported_envelope_schema` | `envelope_schema_version` does not match the active policy |
| `unsupported_source_schema` | Source contract `schema_name`/`schema_version` does not match the registry |
| `unsupported_source_policy` | Source contract `policy_id` does not match the registry |
| `stream_contract_mismatch` | `request` is not an instance of the stream's registered model, or its client type is not allowlisted |
| `invalid_source_payload` | Projector/extractor failure, or payload fails re-validation against its request model |
| `unsafe_envelope` | Structural or privacy validation failure |
| `envelope_too_large` | Serialized envelope exceeds `policy.max_envelope_bytes` |
| `envelope_serialization_failed` | Canonical JSON serialization failure |
| `envelope_deserialization_failed` | Input bytes are not valid UTF-8 JSON with an object root |

`envelope_diagnostics.safe_envelope_error_diagnostic(error)` returns a
bounded `{"code": ..., "detail": ...}` dict (detail capped at 64 characters)
safe to log or return — mirroring the shape of the Slice 8.1/8.2
`diagnostics.safe_storage_diagnostic()`.

## Schema compatibility matrix

`schema_compatibility.py` makes the (envelope schema, event stream, source
schema) compatibility relationship an explicit, queryable data structure:

```python
from codestrata_platform.community_cloud_api.data_lake.schema_compatibility import (
    is_compatible,
)

is_compatible("1.0", "telemetry", "1.0")  # True
is_compatible("1.0", "telemetry", "2.0")  # False — no source schema 2.0 registered yet
```

Slice 8.3 supports exactly one envelope schema version (`1.0`) and exactly
one source schema version per stream (`1.0`, for all five streams). A
future schema bump has one obvious place to extend:
`COMPATIBILITY_MATRIX`.

## What this slice does NOT do

- Does not wire any endpoint to S3 — `app.py`, `deployment/wiring.py`, and
  every endpoint `routes.py`/`service.py` are unchanged.
- Does not change production HTTP acceptance in any way.
- Does not add a durable event-identity/deduplication store.
- Does not add stream-specific partition policy ownership (deferred to a
  later slice — added for `assessment_metadata` in
  [Slice 8.4](./assessment-metadata-data-lake.md), for `telemetry` in
  [Slice 8.5](./telemetry-data-lake.md), for `cli_event` in
  [Slice 8.6](./cli-event-data-lake.md), for `extension_event` in
  [Slice 8.7](./extension-event-data-lake.md), and for `ai_usage` in
  [Slice 8.8](./ai-usage-data-lake.md)).
- Does not bump `COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION` or any
  endpoint schema version — all remain `1.0`.
- Does not commit, plan, or apply any OpenTofu change.
- Does not add a `boto3` import anywhere outside
  `data_lake/infrastructure/` (unchanged from Slice 8.2).

## Package layout (new in this slice)

```text
platform/src/codestrata_platform/community_cloud_api/data_lake/
  accepted_clock.py           # AcceptanceClock protocol + Fixed/System implementations
  envelope_models.py           # EnvelopeErrorCode + re-exports
  envelope_registry.py          # the five SourceContractDescriptor instances
  envelope_builders.py           # build_data_lake_envelope / build_storage_object_from_request / put_request_via_store
  envelope_validation.py          # EnvelopeBuildError + require_*() fail-closed guards
  envelope_serialization.py        # serialize/deserialize wrapping Slice 8.2 canonical_json
  envelope_diagnostics.py           # safe_envelope_error_diagnostic / safe_error_code_for_exception
  source_contracts.py                # SourceContractDescriptor dataclass shape
  source_projection.py                # project_request_payload() / extract_client_type() dispatch
  schema_compatibility.py               # COMPATIBILITY_MATRIX + is_compatible()
  streams/
    __init__.py
    telemetry.py
    assessment_metadata.py
    cli_events.py
    extension_events.py
    ai_usage.py
```

## Testing

```bash
.venv/bin/pytest platform/tests/community_cloud_api/data_lake -q
.venv/bin/pytest platform/tests/community_cloud_api -q
```

Slice 8.3 adds 16 new test modules covering the canonical shape contract,
registry lookups, source contract structural validation, the high-level
builder (including cross-stream rejection — a telemetry payload cannot
build as a `cli_event`, etc.), fail-closed validation guards,
serialize/deserialize round-trips and rejection paths, one dedicated module
per event stream, the structural privacy scan, the schema compatibility
matrix, end-to-end request → envelope → store integration, determinism, and
a broad structural boundary sweep. Every Slice 8.1/8.2 test that
constructed a flat-shape envelope was updated to the nested shape via the
shared `_envelope_test_helpers.make_envelope()` helper.

## Limitations (Slice 8.3)

- No endpoint → storage wiring (still Slice 8.1/8.2's posture)
- No durable event-identity/deduplication store
- No stream-specific partition policy ownership (deferred; see
  [Slice 8.4](./assessment-metadata-data-lake.md) for `assessment_metadata`,
  [Slice 8.5](./telemetry-data-lake.md) for `telemetry`,
  [Slice 8.6](./cli-event-data-lake.md) for `cli_event`,
  [Slice 8.7](./extension-event-data-lake.md) for `extension_event`, and
  [Slice 8.8](./ai-usage-data-lake.md) for `ai_usage`)
- No new HTTP contract or version bump anywhere
- No OpenTofu / IAM change
- Quarantine persistence for malformed envelopes is Slice 8.9 (see
  [data-lake-quarantine.md](./data-lake-quarantine.md)); still unwired from
  endpoints
