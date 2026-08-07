# CodeStrata Infrastructure (private)

Private OpenTofu-compatible infrastructure for CodeStrata Community Cloud.

This folder is designed for later extraction into a separate private repository
(`codestrata-infrastructure`). Application runtime code remains under
`platform/`.

**Slice 12.5** defines the authoritative extraction contract:
[`docs/repository-contract.md`](docs/repository-contract.md).

**Slice 12.6** implements the deterministic exporter (no Git/AWS/OpenTofu exec).
Authoritative target router (Slice 12.8+):

```bash
python scripts/export_repository.py \
  --target infrastructure \
  --destination ../codestrata-infrastructure \
  --dry-run
```

Compatibility wrapper:

```bash
python scripts/export_infrastructure_repository.py \
  --destination ../codestrata-infrastructure \
  --dry-run
```

Verification: Slices 12.5–12.10 under `verification/` (Epic 12 complete).
The main monorepo remains authoritative pre-cutover. Epic 13 is not started.

## Purpose

Slice 7.14 creates a **production infrastructure foundation** that packages and
serves the Community Cloud API through AWS serverless infrastructure.

The Slice 7.14 deployment proves that the Community Cloud API can be packaged
and served through serverless infrastructure. It does not enable durable
Community event ingestion because production credential verification, shared
event identity, and event sinks are not yet configured.

Slice 8.1 adds the Community Data Lake **storage foundation** at
`infrastructure/modules/community-data-lake/` (composed from
`production/community-data-lake.tf`). The bucket is private, encrypted, and
lifecycle-managed, but **unwired**: `enable_ingestion_wire = false`, and the
writer policy is not attached to Lambda. Durable ingestion and analytics remain
deferred. See `docs/community-data-lake.md` and `docs/future-data-lake.md`.

Slice 8.10 formalizes retention / lifecycle product policy (Platform
`community-data-lake-retention-policy:1.0` + aligned OpenTofu lifecycle,
including expired-delete-marker cleanup). Still unwired; does not claim
production data is stored or deleted. See
`platform/docs/community-cloud-api/data-lake-retention.md`.

Slice 8.11 formalizes encryption at rest (Platform
`community-data-lake-encryption-policy:1.0`, SSE-S3 / AES256,
`bucket_key_enabled=false`, KMS deferred). Still unwired; does not claim
production data is stored. See
`platform/docs/community-cloud-api/data-lake-encryption.md`.

Slice 8.12 formalizes restricted IAM access control (Platform
`community-data-lake-access-policy:1.0`, writer policy document with stable
SIDs, prefix-scoped Put/Get, delete Deny, `DenyInsecureTransport`, no
ListBucket, analytics/quarantine separation). Writer policy unattached;
Slice 8.13 not started. See
`platform/docs/community-cloud-api/data-lake-access-control.md`.

## Ownership

| Layer | Owns |
| --- | --- |
| `platform/` | Application runtime (FastAPI/ASGI, policies, adapters) |
| `infrastructure/` | Cloud resources, IAM, packaging scripts, deployment config |
| `engine/` | Community Edition CLI/MCP (unaware of this folder) |

The entire `infrastructure/` tree is **private** and excluded from public
Community repository exports.

## Tooling

Operational command path:

```bash
tofu init
tofu fmt
tofu validate
tofu plan
tofu apply   # never auto-approved; run only with explicit human approval
```

Do not mix Terraform and OpenTofu against the same state casually.

## Layout

```text
infrastructure/
  modules/community-cloud-api/    # API Gateway + Lambda foundation
  modules/community-data-lake/    # Slice 8.1 storage foundation (unwired)
  production/                     # sole environment root (for now)
  docs/
  policies/
  scripts/
  tests/
```

Future (documented, not created):

```text
infrastructure/dev/
infrastructure/staging/
```

## Deployment architecture

```text
Internet
  → API Gateway HTTP API
  → one Lambda function (container image from ECR)
  → Community Cloud FastAPI/ASGI application
```

One Lambda serves all six application routes via proxy integration. Route
ownership remains in `RouteRegistry` — infrastructure does not duplicate
business routes.

## Production posture

| Surface | Behavior |
| --- | --- |
| `GET /api/v1/health` | Operational, unauthenticated, rate limited |
| Five ingestion endpoints | Auth required; fail-closed 503 without production verifier/sinks/identity store |
| Rate limiting | API Gateway stage throttling + process-local app limiter (not durable distributed quotas) |
| Authentication | Enabled; production verifier remains unavailable in this foundation |
| Event sinks / identity | Unavailable — no false durable acceptance |

## Packaging

Lambda **container image** stored in private ECR.

- Dockerfile: `platform/deployment/community-cloud-api/Dockerfile`
- Runtime adapter: `codestrata_platform.community_cloud_api.deployment`
- Build: `infrastructure/scripts/build-community-cloud-api.sh`

## Secrets

Never commit credentials, tokens, AWS keys, or live account IDs.
`terraform.tfvars.example` uses unmistakable placeholders only.
No Secrets Manager resources in this slice.

## State

Remote state is documented; no live `backend.tf` with account values is
committed. See `docs/state-management.md`.

## Scripts

| Script | Role |
| --- | --- |
| `scripts/validate.sh` | fmt/validate/tests — no cloud credentials required |
| `scripts/plan-production.sh` | plan only — never apply |
| `scripts/build-community-cloud-api.sh` | build image locally — no push |
| `scripts/smoke-health.sh` | health-only smoke against an explicit base URL |

## Repository extraction readiness

- No relative imports into application source
- Module I/O explicit
- Scripts resolve repository root safely
- No parent-repo secrets
- README standalone prerequisites documented

Do not split the repository in this slice.

## System Verification SV.9

Deployment-foundation verification lives under:

`infrastructure/verification/`

```bash
PYTHONPATH=platform:platform/src:engine:engine/src:. \
  python -m infrastructure.verification
```

Report:
`infrastructure/reports/verification/platform-deployment-foundation-verification.json`
(`platform-deployment-foundation-verification` / `1.0.0`).

SV.9 does **not** run `tofu apply`, `terraform apply`, Docker push, or remote AWS
calls. When OpenTofu is unavailable, CLI validate is reported as
`not_executed_tool_unavailable` while static and runtime-adapter checks still
run. Terraform 0.11 is not used as a substitute. SV.10 is not started.
