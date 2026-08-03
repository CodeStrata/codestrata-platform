# Community Cloud API client authentication (Slice 7.13)

Community client authentication verifies possession of an issued client
credential. It does not identify a human user, authorize repository access, or
establish an organization or billing relationship.

Raw client credentials are never included in API responses, request contexts,
structured logs, diagnostics, rate-limit keys, or event payloads.

## Policy

| Field | Value |
| --- | --- |
| Policy | `community-authentication-policy:1.0` |
| Credential format | `cscc_v1_<opaque>` (`COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION=1`) |
| Scheme | `Authorization: Bearer <token>` |
| Public route | `health.get` |
| Protected routes | all five ingestion endpoints |
| Default verifier | `UnavailableCommunityCredentialVerifier` (fail-closed) |

## Pipeline order

```text
Route / method resolution
  → authentication
  → authenticated rate-limit scope (ingestion) / transport scope (health)
  → pre-auth transport throttle on failed auth attempts (auth_attempt group)
  → request-schema validation
  → client-type payload match
  → payload-size limits
  → handler
```

Unknown routes remain 404 and unsupported methods remain 405 before
authentication.

## Credential verification

Persistence-neutral `CommunityCredentialVerifier.verify(credential)` port.

- Stores/lookups use one-way `cred:{sha256}` fingerprints only
- In-memory verifier for tests
- No database, Redis, Secrets Manager, Cognito, or API Gateway authorizer in this slice
- Credential issuance / registration / rotation APIs are deferred

## Authenticated principal

Opaque `AuthenticatedCommunityClient` with client type, credential version, and
`rate_limit_scope_id`. No email, username, organization, repository, IP, or raw
token.

## Rate-limit integration

`community-rate-limit-policy` deliberately bumped to **1.1**:

- Protected ingestion uses authenticated scope `auth-scope:{sha256[:24]}`
- Health remains transport-scoped
- Failed auth attempts use transport-scoped `auth_attempt` budget
- Forwarded headers remain untrusted
- Changing IP / request ID / event ID does not bypass authenticated buckets

## HTTP behavior

| Case | Status | Code |
| --- | --- | --- |
| Missing credential | 401 | `authentication_required` (+ `WWW-Authenticate: Bearer`) |
| Malformed/invalid/inactive/revoked | 401 | generic invalid credential codes |
| Route/client-type denied | 403 | `client_not_authorized` |
| Verifier unavailable | 503 | `authentication_unavailable` |

Success endpoint bodies are unchanged and do not include client identity.

## Client-type matching

Authenticated `client_type` must match payload `client.name` when present
(CLI / VS Code / Cursor). Mismatch → 403 without principal details.

## Non-goals

- User accounts, OAuth, SAML, cookies, sessions
- Credential issuance or client emitter wiring
- Production credential store / serverless authorizers (Slice 7.14)
- CORS / CSRF
