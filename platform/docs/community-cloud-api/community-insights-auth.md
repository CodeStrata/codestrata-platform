# Community Insights authentication (Slice 15.9)

## Purpose

Protect the internal Community Insights SPA (`insights.codestrata.ai`) and every
Insights metric API with a shared internal password and short-lived server
session. Product discovery only — no Cognito, OAuth, MFA, or individual accounts.

## Topology (frozen, not deployed)

Prefer **same-origin API proxy**:

```text
https://insights.codestrata.ai/          → static SPA
https://insights.codestrata.ai/api/v1/... → Platform Community Cloud API
```

Cookie auth is host-only on `insights.codestrata.ai` with
`Path=/api/v1/insights`, `HttpOnly`, `Secure`, `SameSite=Strict`.

Alternative B (`https://api.codestrata.ai/insights/...`) is deferred; it would
require careful cross-subdomain cookie scoping and is not selected for v0.2.0.

## Secrets Manager

| Secret ID | Purpose |
|-----------|---------|
| `codestrata/insights/dashboard-password` | Password verifier (scrypt JSON preferred) |
| `codestrata/insights/session-secret` | HMAC session signing key |

Source and Terraform hold **identifiers only**. Owners inject values outside Git.
No real secrets are created in this slice. No AWS calls from verification.

### Password verifier

Preferred Secrets Manager payload (JSON):

```json
{
  "algorithm": "scrypt",
  "salt_b64": "...",
  "hash_b64": "...",
  "n": 16384,
  "r": 8,
  "p": 1
}
```

If a raw password string is stored instead, comparison is constant-time and
server-side only; this is documented as a limitation and discouraged.

The dashboard password is **never** reused as the session signing secret.

## Endpoints (under `/api/v1`)

| Method | Path | Auth |
|--------|------|------|
| POST | `/insights/auth/login` | public (password body) |
| POST | `/insights/auth/logout` | session optional |
| GET | `/insights/auth/session` | cookie → `{authenticated: bool}` |
| GET | `/insights/api/overview` | session required → aggregate `MetricResult[]` |

## CSRF

`SameSite=Strict` plus Origin/Referer validation on state-changing POSTs.
Login CSRF risk is low for shared-password internal discovery; still validated
when Origin is present.

## Rate limit / brute force

API Gateway stage throttling (existing Community Cloud API module) plus
application `auth_attempt` rate-limit group on login failures. No product
analytics IP storage.

## Auth ≠ privacy

Authenticated callers still receive aggregates only. Cohort suppression,
`model_id` / `installation_id` prohibition, and raw-event bans remain enforced
by the aggregation/metrics policies.

## Production

`production_deployment_enabled: false`. No DNS, no real Secrets Manager values,
no deploy of `insights.codestrata.ai` in this slice.
