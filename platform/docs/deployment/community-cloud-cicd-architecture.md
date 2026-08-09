# Community Cloud CI/CD Architecture (Authoritative)

**Policy:** `community-cloud-cicd-policy:1.0`  
**Registers:** `codestrata-cicd-architecture:1.0`, `codestrata-deployment-component-register:1.0`  
**Slice:** 17.1 — architecture / pipeline design only  
**Status:** Frozen for v0.2.0. **No AWS resources created. No OpenTofu apply. No deploy.**

Companion pointer: [`infrastructure/docs/cicd-architecture.md`](../../../infrastructure/docs/cicd-architecture.md).

---

## 1. Principle

Separate **infrastructure changes** from **application-code changes**.

| Change type | Path |
| ----------- | ---- |
| Infrastructure | OpenTofu → plan → owner review → apply |
| Application | build/test → package → update existing runtime |

Ordinary CI (`ci.yml`) **never** deploys.

---

## 2. Repository model

| Future repository | Role | Pre-cutover path |
| ----------------- | ---- | ---------------- |
| `codestrata-engine` | public Community Engine / CLI | `engine/` |
| `codestrata-platform` | private backend/runtime | `platform/` |
| `codestrata-infrastructure` | private IaC | `infrastructure/` |
| `codestrata-insights` | private Insights SPA | `insights/` |
| `codestrata-docs` | private GitHub / public site | `docs/` |
| `codestrata-vscode` | VS Code extension | `vscode-plugin/` |

Remotes are **not** created in Slice 17.1. Export contracts from Epics 12/15/16 remain authoritative.

---

## 3. Environment strategy

**Decision: production only** for v0.2.0.

Rationale: product-discovery stage; avoid standing cost of a second AWS environment. Offline CI validation covers fmt/validate without AWS. A future validation environment requires explicit evidence — not assumed.

---

## 4. First-time bootstrap (Slice 17.2 owns creation)

One-time, owner-reviewed. Slice **17.2 creates only** the dedicated OpenTofu
remote-state foundation:

1. Dedicated OpenTofu **state S3 bucket** (not the Community Data Lake)
2. Bucket **versioning**, **SSE encryption**, and **Block Public Access**
3. Native **S3 lockfile** backend configuration (`use_lockfile = true`)
4. Backend initialization + idempotency/recovery verification
5. Bootstrap identity / process documentation

**Slice 17.2 does not create:** DynamoDB, Lambda, ECR, API Gateway, Community
Data Lake, application Secrets Manager secrets, OIDC deployment role, or
production application infrastructure.

GitHub OIDC provider trust + production deploy role remain **Slice 17.3**.

Recovery: restore prior state object version via S3 Versioning; re-init; plan
before apply. Stale lock handling must use supported OpenTofu operational
procedures — do **not** casually delete lock objects.

Do **not** store application secrets in state when avoidable. State may still contain resource ARNs and non-secret config — treat as sensitive; restrict read/write.

---

## 5. Remote state

| Field | Decision |
| ----- | -------- |
| Backend type | S3 |
| Locking | **Native S3 lockfile** (`use_lockfile = true`) |
| DynamoDB locking | **Not required** (not used) |
| Bucket naming | `codestrata-opentofu-state-<account-or-alias>-production` (exact name at bootstrap) |
| State key | `codestrata/community-cloud/production/terraform.tfstate` |
| Encryption | `encrypt = true` (SSE) |
| Versioning | required on state bucket |
| Public access | Block Public Access required; private; no website hosting |
| CI role | plan/apply workflows only; least privilege on state objects + lockfile |
| Human emergency | owner break-glass IAM; audited |
| Live `backend.tf` | gitignored / not committed with account IDs |
| Data Lake reuse | **Forbidden** — state bucket ≠ Community Data Lake |

### Conceptual layout

```text
Dedicated OpenTofu State S3 Bucket
    ├── production state object
    ├── native lock file
    ├── versioning enabled
    ├── server-side encryption enabled
    └── Block Public Access enabled
```

**No DynamoDB table** for OpenTofu locking.

Reference example: `infrastructure/production/backend.tf.example`.

---

## 6. GitHub → AWS identity (OIDC)

| Field | Decision |
| ----- | -------- |
| Mechanism | GitHub Actions OIDC → AWS IAM role |
| Long-lived access keys | **Forbidden** in GitHub secrets |
| GitHub environment | `production` (protected) |
| Trust conditions | repository + environment (+ optional ref) |
| Session duration | ≤ 1 hour |
| Permissions | narrow: state, ECR push, Lambda update, CloudWatch read as needed per workflow |
| Role name (pattern) | `codestrata-github-actions-production` |

Role is created in **Slice 17.3** (`infrastructure/docs/github-aws-oidc.md`).

---

## 7. Workflow architecture

| Workflow | Purpose | Deploy? | Status |
| -------- | ------- | ------- | ------ |
| `ci.yml` | validation only | no | **active** |
| `infrastructure-plan.yml` | fmt/init/validate/plan | no | designed |
| `infrastructure-apply.yml` | approved apply | yes (infra) | designed, inactive |
| `platform-deploy.yml` | backend image update | yes (app) | designed, inactive |
| `insights-deploy.yml` | Insights SPA | yes (frontend) | designed, inactive |
| `docs-deploy.yml` | docs.codestrata.ai | yes (docs) | designed, inactive |
| `release.yml` | CLI/VS Code publish | Epic 19 | deferred |

Machine-readable: `platform/policies/codestrata_cicd_architecture.json`.

### Infrastructure plan

- Trigger: PR touching `infrastructure/**` or `workflow_dispatch`
- Offline: `tofu fmt`, `init -backend=false`, `validate` (already partially in `ci.yml`)
- Authenticated plan: OIDC + remote backend when activated
- **No apply**

### Infrastructure apply

- Explicit `workflow_dispatch` on exact commit/SHA
- Protected `production` environment approval
- Same reviewed configuration as plan
- No auto-approve from arbitrary PR
- Failure surfaces in Actions logs; no silent continue

---

## 8. Backend application deployment

Authoritative deployable unit today (IaC):

| Unit | Detail |
| ---- | ------ |
| Runtime | Single Lambda image: `codestrata-community-cloud-production-api` |
| Includes | Community Cloud API, telemetry routes, Insights APIs/auth handlers |
| Package | `platform/deployment/community-cloud-api/` Dockerfile |
| Build | `./infrastructure/scripts/build-community-cloud-api.sh --tag <tag>` |
| Artifact | ECR `codestrata/community-cloud-api` IMMUTABLE tag/digest |
| Deploy | `aws lambda update-function-code --image-uri …` |
| Infra dependency | ECR + Lambda + API Gateway must already exist |

Do **not** require full OpenTofu apply for routine code updates.

### Lambda update strategy (frozen)

**`ecr_immutable_image_uri_update`**

- Prefer immutable ECR tags/digests
- Update existing function image URI for application releases
- Rollback: point function at previous known-good image URI
- Lambda versions/aliases are **optional** later; not required for v0.2.0 simplicity

---

## 9. Insights deployment (`insights.codestrata.ai`)

| Concern | Decision |
| ------- | -------- |
| Frontend | React + Vite static SPA |
| Hosting | Cloudflare Static Assets (Cloudflare-ready per application policy) |
| API | Same-origin `/api/v1/...` proxy → Community Cloud API |
| DNS/TLS | Cloudflare owner-operated |
| Auth | Shared internal password + HttpOnly signed session |
| Secrets | Secrets Manager IDs `codestrata/insights/dashboard-password`, `codestrata/insights/session-secret` |
| Frontend AWS creds | **never** |
| Frontend Secrets Manager read | **never** |
| CSP / noindex | required for internal dashboard |
| Rollback | redeploy previous git revision’s `dist/` |

Not deployed in 17.1.

---

## 10. Docs deployment (`docs.codestrata.ai`)

Uses Slice 14.12 contract unchanged:

| Item | Value |
| ---- | ----- |
| Package root | `docs/` |
| Output | `./.vitepress/dist` (never `docs/.vitepress/dist` inside Wrangler) |
| Wrangler | checked-in, locally pinned |
| Deploy | `npm run deploy:check` then `npm run deploy:upload` |
| No dynamic `npx wrangler` auto-setup | |

---

## 11. Community Data Lake (operational relationship)

| Concern | Decision |
| ------- | -------- |
| Bucket | Created by OpenTofu (`codestrata-community-data-lake-production`) |
| Write / quarantine / retention | Existing module + policies |
| Ingestion enablement | **Deferred** (later Epic 17 slices) |
| Aggregation reader / API writer | IAM wiring after foundation apply |

Preserve `community-data-lake-policy:1.0`. No Athena/Glue.

---

## 12. Secrets Manager

| Identifier | Consumer | CI visibility | Frontend |
| ---------- | -------- | ------------- | -------- |
| `codestrata/insights/dashboard-password` | Insights auth runtime | never values | never |
| `codestrata/insights/session-secret` | Insights auth runtime | never values | never |

Rotation: manual owner update. IAM reader: insights auth runtime role (module contract). Values **not** created in 17.1.

Provider credentials (OpenAI / Bedrock / OpenRouter) are **product runtime / E2E validation** config — never frontend, never logged, never GitHub unless ephemeral OIDC-scoped retrieval is later designed. Not exercised in 17.1.

---

## 13. Deployment order (frozen)

1. Bootstrap remote state  
2. Establish GitHub OIDC  
3. Production tofu plan  
4. Infrastructure apply  
5. Secrets Manager configuration  
6. Runtime IAM  
7. Platform backend deployment  
8. Enable ingestion  
9. Insights frontend deployment  
10. Docs deployment  
11. Production smoke  
12. 22-repo validation  

---

## 14. Rollback

| Surface | Procedure |
| ------- | --------- |
| OpenTofu config | Revert config → plan → owner-approved apply (no promised auto undo) |
| OpenTofu state object | S3 Versioning restores a prior state object version; re-init; plan before apply |
| OpenTofu concurrency | Native S3 lockfile; resolve stale locks via supported OpenTofu procedures (do not casually delete lock objects) |
| Lambda/backend | `update-function-code` to previous ECR URI |
| Insights / Docs | Redeploy prior revision artifact |
| Secrets/config | Owner restores prior secret version; restart/redeploy consumers if needed |

---

## 15. Observability (minimum)

CloudWatch Lambda logs · API Gateway 4xx/5xx · ingestion success/fail counters (when enabled) · quarantine object counts · S3 presence checks · aggregation/auth failure logs · GitHub Actions deployment logs. No Datadog/New Relic.

---

## 16. Cost posture

Prefer Lambda, S3, API Gateway, CloudWatch baseline, Cloudflare static hosting.

OpenTofu remote state: **S3 only** (native lockfile; **no DynamoDB**).  
Community analytics / Insights: **S3 + Lambda** bounded reads (no DynamoDB, Athena, Glue, RDS, Redis, warehouse).

Forbid permanent EC2, ECS, RDS-for-deploy, Redis, Athena, Glue, and DynamoDB for OpenTofu state locking or Insights analytics as deployment requirements.

---

## 17. Security

- No long-lived AWS keys in GitHub  
- Least privilege OIDC roles  
- Protected production environment  
- Secrets outside source; never in build logs  
- Artifact integrity via immutable tags + commit SHA provenance  
- Explicit deployment identity per workflow  

---

## 18. Artifact / provenance

v0.2.0 rebuilds from **exact git revision** at deploy time (deterministic simplicity). Capture: commit SHA, workflow run id, image digest / dist hash, plan file hash for infra apply. No separate artifact registry required.

---

## 19. Release boundary

VS Code / CLI publication = **Epic 19**, not Epic 17 deployment.

---

## 20. Slice boundaries

| Slice | Owns |
| ----- | ---- |
| **17.1** | This architecture (no AWS create/apply/deploy) |
| 17.2 | Dedicated S3 remote-state bucket only (versioning, encryption, public-access block, native S3 lockfile, backend init). **No DynamoDB.** |
| 17.3 | GitHub OIDC role |
| 17.4+ | Plan/apply activation, app/frontend deploys, ingestion, validation |

**`start_slice_17_2 = false`** during 17.1.

### Final remote-state statement

CodeStrata v0.2.0 uses a dedicated S3 backend with native S3 lockfile support for
OpenTofu remote state. DynamoDB is **not** required for OpenTofu state locking.
DynamoDB is **not** part of the Community Insights analytics architecture.
Community Insights continues to use bounded direct S3 reads through the
Platform/Lambda aggregation service.
