# Community Cloud API — Retry-Safe Event Identifiers

Retry-safe event identity allows a client to reuse the same event identifier when
retrying the same logical event. It does not authenticate the client, authorize
submission, persist the event, or guarantee deduplication without an authoritative
identity store.

**Policy:** `community-event-identity-policy:1.0`  
Independent of Community Cloud API contract 1.0, request-validation policy 1.0,
payload-limit policy 1.0, logging policy 1.0, assessment schema 1.2, and EIR 1.0.

Slice 7.7 (`POST /api/v1/telemetry`) is the first production consumer of these
contracts. See [telemetry-ingestion.md](./telemetry-ingestion.md).

## Identity concepts

| Concept | Role |
| --- | --- |
| `request_id` | Transport/request correlation (logging). May change every retry. |
| `event_id` | Client-generated logical event identity. Stable across retries. |
| `event_key` | Server-derived scoped digest (`event:{sha256[:24]}`). |
| `payload_fingerprint` | Server-derived content digest (`fp:{sha256}`). |
| `safe_event_reference` | Bounded log reference (`evt-{12 hex}`). Not an API identity. |

Do not use `request_id` as `event_id`. Do not reuse logging-generated IDs as event IDs.

## Event ID contract

Client-supplied `event_id` (`ApiEventId`):

- 8–128 characters
- `[A-Za-z0-9._:-]`
- no whitespace/control characters/slashes
- no URLs, paths, or secret-like values
- UUIDs, ULIDs, hashes, and client-prefixed opaque ids are accepted when they meet the contract
- server does **not** auto-generate event IDs for retry-safe endpoints

## Identity scope

Preferred uniqueness scope:

`(api_version, client_type, installation_id?, event_type, event_id)`

`installation_id` is an optional future anonymous scope component
(`ApiInstallationId`). This slice does **not** generate, persist, rotate, or
require installation tracking.

Not used for identity: source IP, repository path, email, hostname, device
fingerprint, auth token, or request ID.

## Event key

Stable inputs: identity policy token, API version, client type, installation id
(or empty), event type, event id.

Excluded: timestamps, request ID, payload content, IP, response status, logging fields.

## Payload fingerprint

Canonical sorted JSON over the event payload after excluding transport-only fields
(`request_id`, `retry_count`, `received_at`, `transport_metadata`, `server_metadata`).

List order is semantic and preserved. Secret-like values are rejected before hashing.

Hashes provide deterministic identity/fingerprinting only. They are **not**
encryption and do not anonymize unsafe payloads by themselves. Fingerprints must
not be publicly exposed.

## Retry decisions

| Status | Meaning |
| --- | --- |
| `first_seen` | Lookup present and identity absent |
| `exact_retry` | Same event key + same fingerprint |
| `conflicting_retry` | Same event key + different fingerprint |
| `unavailable` | No authoritative lookup capability |

Without a lookup store, status is `unavailable` — never claim `first_seen` in
production without an authoritative store.

Future endpoint outcomes (not wired yet):

- first_seen → `accepted`
- exact_retry → `already_accepted`
- conflicting_retry → `conflict` / HTTP 409 `event_identity_conflict`

## Conflict error

Canonical code: `event_identity_conflict`  
Message: “Event identifier was previously used with different event content.”

No payload values, full fingerprints, previous bodies, storage details, or raw
event IDs.

## Lookup ports

`EventIdentityLookup` / `EventIdentityRecorder` are persistence-neutral.

Slice 7.6 provides an in-memory test store only. No database, Redis, file ledger,
queues, or production adapters.

Stored fields are minimal: event key, fingerprint, event type, client type, policy version.
No raw payloads, secrets, paths, headers, or IPs.

## Logging

Future handlers may log only:

- `safe_event_reference`
- `retry_status`
- `source_event_type`
- `identity_policy_version`

Raw `event_id`, `event_key`, `payload_fingerprint`, and `installation_id` are
rejected from free-form log fields. Health logging is unchanged.

## Non-goals (Slice 7.6 foundation)

- Deduplication persistence / production identity ledger
- Installation registration/tracking
- Authentication / rate limiting
- Queues / workers / deployment
- Acceptance windows / clock-skew rules

Production telemetry ingestion arrives in Slice 7.7 and consumes these contracts
without claiming exactly-once delivery.
