# Slice 17.6 — Insights secret rotation (basic)

Production secrets live only in AWS Secrets Manager. Values are never stored in
Git, OpenTofu state, Lambda environment variables, or verification reports.

## Identifiers

| Secret | Purpose | Format |
|--------|---------|--------|
| `codestrata/insights/dashboard-password` | Login password verification | scrypt verifier JSON (preferred) |
| `codestrata/insights/session-secret` | HttpOnly cookie HMAC signing | high-entropy random string |

## Dashboard password rotation

1. Generate a new password (or prompt the owner).
2. Build a scrypt verifier with the Slice 15.9 contract (`hash_password`).
3. `PutSecretValue` on `codestrata/insights/dashboard-password`.
4. Existing login credentials stop working immediately.
5. Communicate the new password out-of-band (owner one-time display).

Operational helper:

```bash
AWS_PROFILE=codestrata_infra AWS_REGION=us-west-2 \
  ./infrastructure/scripts/configure-production-secrets.sh generate
# or: ... configure-production-secrets.sh prompt-password
```

No dual-secret / gradual password rotation machinery is required for v0.2.0.

## Session secret rotation

1. Generate new cryptographically random signing material (do not reuse the dashboard password).
2. `PutSecretValue` on `codestrata/insights/session-secret`.
3. Existing signed sessions become invalid (fail closed → re-login).
4. Warm Lambda cache for the session secret (if any) expires with the next cold start or cache miss after process recycle; prefer a function update/redeploy if immediate invalidation of in-memory cache is required.

Do not display the session secret in logs or terminals retained as reports.

## Failure behavior

- Secrets Manager unavailable → Insights auth fail-closed (login/overview deny).
- Community assessment/ingestion authentication remains separate and unchanged.
- Production ingestion remains OFF in Slice 17.6 regardless of secret rotation.

## Out of scope

- Automated dual-key rotation
- Provider API-key secrets (deferred)
- Frontend secret storage (forbidden)
