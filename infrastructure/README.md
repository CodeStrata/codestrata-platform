# CodeStrata Infrastructure (private)

Private OpenTofu-compatible infrastructure for CodeStrata Community Cloud.

This folder is designed for later extraction into a separate private repository
(`codestrata-infrastructure`). Application runtime code remains under
`platform/`.

## Purpose

Slice 7.14 creates a **production infrastructure foundation** that packages and
serves the Community Cloud API through AWS serverless infrastructure.

The Slice 7.14 deployment proves that the Community Cloud API can be packaged
and served through serverless infrastructure. It does not enable durable
Community event ingestion because production credential verification, shared
event identity, and event sinks are not yet configured.

Community Data Lake resources are intentionally deferred. Future S3 buckets,
lifecycle, partitioning, encryption, access, and ingestion notifications will be
added through a separate `infrastructure/modules/data-lake` module.

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
  modules/community-cloud-api/   # reusable module
  production/                    # sole environment root (for now)
  docs/
  policies/
  scripts/
  tests/
```

Future (documented, not created):

```text
infrastructure/modules/data-lake/
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
