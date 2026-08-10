# Insights secret rotation and password lifecycle (Slice 17.24)

Production secrets live only in AWS Secrets Manager. Values are never stored in
Git, OpenTofu state, Lambda environment variables, or verification reports.

## Identifiers

| Secret | Purpose | Format |
|--------|---------|--------|
| `codestrata/insights/dashboard-password` | Login password verification | scrypt verifier JSON (required) |
| `codestrata/insights/session-secret` | HttpOnly cookie HMAC signing | high-entropy random string |

## Authority

- **Single production verifier authority:** Secrets Manager secret
  `codestrata/insights/dashboard-password` at stage `AWSCURRENT`.
- The Secrets Manager value is **not** the password typed into the login form.
- Owner plaintext lives in the owner's password manager (durable) and optionally
  a local gitignored `dashboard_password.owner-once` bootstrap file (mode `0600`).
- Plaintext must **never** be stored inside the verifier JSON or in Git.

## Password normalization contract

Applied identically by Insights UI (`trim()`), API verification, and rotation
hashing:

- Unicode `str.strip()` / JS `trim()` only
- Leading/trailing whitespace and newlines removed
- Interior characters preserved (no case folding, no other transforms)

## Dashboard password rotation

1. Generate a new password (or prompt the owner).
2. Store the plaintext in the owner's password manager **before** publishing the
   verifier (do not rely permanently on a disposable local file).
3. Build a scrypt verifier with `hash_password` / configure-production-secrets.
4. `PutSecretValue` on `codestrata/insights/dashboard-password` (becomes
   `AWSCURRENT`).
5. **Effective immediately on next login** — the password verifier is **not**
   cached in Lambda; each login reads Secrets Manager `AWSCURRENT`.
6. Optionally refresh local `infrastructure/production/.local/dashboard_password.owner-once`
   (mode `0600`, gitignored) for operator bootstrap only.
7. Communicate the new password out-of-band. Never paste Secrets Manager JSON,
   `hash_b64`, or `salt_b64` into the login form.

Operational helper:

```bash
AWS_PROFILE=codestrata_infra AWS_REGION=us-west-2 \
  ./infrastructure/scripts/configure-production-secrets.sh generate
# or: ... configure-production-secrets.sh prompt-password
```

No dual-secret / gradual password rotation machinery is required for v0.2.0.

## Session secret rotation

1. Generate new cryptographically random signing material (do not reuse the
   dashboard password).
2. `PutSecretValue` on `codestrata/insights/session-secret`.
3. Existing signed sessions become invalid once the runtime loads the new
   signing secret (fail closed → re-login).
4. Warm Lambda caches the session signing secret with a **300s TTL**. After
   rotation, new signing material is effective within that window without a
   cold start; prefer a function update/redeploy only when immediate
   invalidation of all warm containers is required before TTL expiry.

Do not display the session secret in logs or terminals retained as reports.

## Recovery when login shows "Invalid password"

1. Confirm you are using owner **plaintext** from the password manager — not
   Secrets Manager JSON.
2. Confirm local owner-once (if used) matches `AWSCURRENT` via offline scrypt
   verify (never log plaintext/verifier).
3. Wrong password → HTTP 401 with public code `invalid_credentials`.
4. Auth/Secrets Manager unavailable → HTTP 503 with
   `auth_service_unavailable` (fail closed; UI must **not** label this as
   "Invalid password").
5. Rate limited → HTTP 429 with `rate_limited`.

## Failure behavior

- Secrets Manager unavailable → Insights auth fail-closed (login/overview deny).
- No default password. No authentication bypass.
- Community assessment/ingestion authentication remains separate and unchanged.

## Out of scope

- Automated dual-key rotation
- Provider API-key secrets (deferred)
- Frontend secret storage (forbidden)
