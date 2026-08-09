# Slice 12.7 — Infrastructure repository export verification

Schema: `infrastructure-repository-export-verification:1.0.0`

## Run

```bash
PYTHONPATH=. .venv/bin/python -m verification.infrastructure_repository_export
```

Report: `.codestrata-artifacts/validation/suites/sv12-7/infrastructure-repository-export-verification.json`

## What is verified

- Dual export to isolated temporary destinations (byte-identical)
- Manifest / inventory / SHA256SUMS independently recalculated
- Approach A layout and required content
- Prohibited files, product/dependency boundaries, secrets, tfvars, local paths
- Documentation links (offline relative resolution)
- Exported Python tests without monorepo PYTHONPATH / Engine / Platform
- `tofu fmt -check -recursive`
- `tofu init -backend=false` + `tofu validate` for:
  - `modules/community-cloud-api`
  - `modules/community-data-lake`
  - `production`
- No plan/apply/destroy, no Git, no AWS credentials/API usage

## Limitations

- No real remote `codestrata-infrastructure` repository
- Provider plugins may download or use local cache during init
- Validation-generated `.terraform/` and lock updates stay in the validation copy
- External HTTP documentation links are not fetched
- CI integration: Slice 12.9 (`.github/workflows/ci.yml` job
  `infrastructure-export-verification`; verifier
  `verification/ci_release_boundaries/`)
- Epic 12 completion: Slice 12.10
  (`verification/product_cleanup_repository_split_completion/`)
- Source cutover / owner migration deferred
- Epic 13 not started
