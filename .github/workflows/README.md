# GitHub Actions workflows

## Active

| Workflow | Role |
| -------- | ---- |
| [`ci.yml`](ci.yml) | Validation only — Engine/Platform/VS Code/export/tofu offline validate. **Never deploys.** |
| [`aws-identity-check.yml`](aws-identity-check.yml) | Slice 17.3 OIDC identity check (production env). **No apply.** Live run requires owner push. |
| [`infrastructure-plan.yml`](infrastructure-plan.yml) | Slice 17.4 production plan (offline validate + optional authenticated plan). **Plan only. No apply.** Live authenticated plan awaits commit/push. |
| [`infrastructure-apply.yml`](infrastructure-apply.yml) | Slice 17.5 production foundation apply. **`workflow_dispatch` only** (never `pull_request`). Applies a reviewed saved plan; fails closed on destroy/replace; post-apply zero-drift check. Live run awaits push + attached apply IAM. Ingestion stays OFF. |

## Designed (not activated)

Documented in `platform/policies/codestrata_cicd_architecture.json` and  
`platform/docs/deployment/community-cloud-cicd-architecture.md`:

- `platform-deploy.yml`
- `insights-deploy.yml`
- `docs-deploy.yml`
- `release.yml` (Epic 19)

Do not add Secrets/Insights/Docs deploy workflows until their owning slices activate
them under OIDC + protected environments. Slice 17.6 is not started.
