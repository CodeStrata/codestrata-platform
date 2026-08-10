# GitHub Actions workflows (Slice 17.25 authority hygiene)

## Active (codestrata-platform root)

| Workflow | Classification | Role |
| -------- | -------------- | ---- |
| [`ci.yml`](ci.yml) | `ACTIVE_REQUIRED` | Validation only — Engine/Platform/VS Code/export/tofu offline validate. **Never deploys.** Repository guard: `CodeStrata/codestrata-platform`. |
| [`aws-identity-check.yml`](aws-identity-check.yml) | `ACTIVE_REQUIRED` | OIDC identity check (`workflow_dispatch` only). **No apply.** |
| [`infrastructure-plan.yml`](infrastructure-plan.yml) | `ACTIVE_REQUIRED` (monorepo pre-cutover) | Plan only — PR paths `infrastructure/**` + dispatch. **No apply.** Future authority: `codestrata-infrastructure`. |
| [`infrastructure-apply.yml`](infrastructure-apply.yml) | `ACTIVE_REQUIRED` (monorepo pre-cutover) | `workflow_dispatch` only + confirm gate. Future authority: `codestrata-infrastructure`. |

Normal push to `release/**` runs **only** `ci.yml` validation jobs (not deploy).

## Export-source workflows (do not execute in monorepo)

GitHub Actions only loads root `.github/workflows/`. Nested trees are copied into
exported repositories by the export router:

| Path | Target repo | Classification |
| ---- | ----------- | -------------- |
| `insights/.github/workflows/ci.yml` | `codestrata-insights` | `SOURCE_EXPORT_ONLY` |
| `insights/.github/workflows/deploy.yml` | `codestrata-insights` | `SOURCE_EXPORT_ONLY` |
| `infrastructure/.github/workflows/validate.yml` | `codestrata-infrastructure` | `SOURCE_EXPORT_ONLY` |
| `infrastructure/.github/workflows/aws-identity-check.yml` | `codestrata-infrastructure` | `SOURCE_EXPORT_ONLY` |

Each export-source job includes `if: github.repository == '<target>'` so a
mis-scoped run cannot execute under the wrong repository name.

## Designed (not activated)

Documented in `platform/policies/codestrata_cicd_architecture.json`:

- `platform-deploy.yml`
- `insights-deploy.yml`
- `docs-deploy.yml`
- `release.yml` (Epic 19)

Do not add Secrets/Insights/Docs deploy workflows at the monorepo root — those
authorities live in exported repos (`codestrata-insights`, `codestrata-docs`).

## Authority map

| Repository | CI / deploy authority |
| ---------- | --------------------- |
| `codestrata-platform` | Monorepo source validation (`ci.yml`); monorepo pre-cutover infra plan/apply |
| `codestrata-infrastructure` | Infrastructure CI/CD |
| `codestrata-insights` | Insights CI/deploy |
| `codestrata-docs` | Docs CI/deploy |

`platform_repo_deployment_authority=false` for Insights/Docs/product deploys.
