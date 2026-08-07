# Platform Deployment Foundation Verification (SV.9)

Private infrastructure verification for the Slice 7.14 Community Cloud
production-foundation deployment.

This package is **not** part of Engine or Platform runtime wheels. It lives with
`infrastructure/` so it can extract later with `codestrata-infrastructure`
(Slice 12.5 contract: `../docs/repository-contract.md`; Slice 12.6 exporter:
`scripts/export_infrastructure_repository.py`; Slice 12.7 export verification:
`verification/infrastructure_repository_export/`).

## Purpose

Verify that the production-only OpenTofu foundation is structurally valid,
secure, extraction-ready, and capable of serving Community Cloud health through:

```text
Internet
→ API Gateway HTTP API
→ one Lambda (ECR container)
→ Mangum
→ create_production_foundation_app()
→ Community Cloud FastAPI
```

Production-foundation posture:

| Concern | Expected |
| --- | --- |
| Health | Deployable, public, deterministic, rate-limited |
| Authentication | Enabled; verifier unavailable |
| Ingestion | Disabled / fail-closed; no false 202/200 |
| Rate limiting | API Gateway throttling + process-local app limiter |
| Data Lake | Not implemented |

## Commands

```bash
# From monorepo root
PYTHONPATH=platform:platform/src:engine:engine/src:. \
  python -m infrastructure.verification

PYTHONPATH=platform:platform/src:engine:engine/src:. \
  python -m infrastructure.verification \
  --output-dir infrastructure/reports/verification
```

Report: `infrastructure/reports/verification/platform-deployment-foundation-verification.json`

Schema: `platform-deployment-foundation-verification` / `1.0.0`

## OpenTofu validation honesty

If `tofu` is available, SV.9 runs:

- `tofu fmt -check -recursive`
- `tofu init -backend=false`
- `tofu validate`

(for both `modules/community-cloud-api` and `production`)

If `tofu` is unavailable:

- `opentofu_validation_status = not_executed_tool_unavailable`
- static/HCL structure checks still run
- Terraform 0.11 is **not** used as a substitute

SV.16A closed the release gate when OpenTofu ≥1.6 is installed: CLI validation
status becomes `pass` (no plan/apply).

SV.9 does **not** run `plan` or `apply`, does not build/push images, and does
not call AWS.

## Separation

| Slice | Focus |
| --- | --- |
| SV.7 | Community Cloud API in-process E2E |
| SV.8 | Website-safe EI export |
| **SV.9** | Infrastructure deployment foundation (this package) |
| SV.10–SV.14 | Assessment/EI/schema System Verification (platform/engine packages) |
| **SV.15** | Deterministic output verification (`platform/verification/deterministic_outputs/`) — reuses SV.9 static run twice; no plan/apply |

SV.16 (release packaging) is not started from this package.

## Limitations

- No AWS credentials required.
- No automatic OpenTofu installation.
- No Data Lake / Secrets Manager / distributed rate-limit store verification as
  implemented resources (they must remain absent).
- Runtime fail-closed checks are in-process only (no remote Lambda invoke).
