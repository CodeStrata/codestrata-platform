"""
# Slice 12.9 — CI, release, and deployment boundaries

Schema: `ci-release-boundary-verification:1.0.0`

## Purpose

Update active CI, release-verification, and deployment boundaries for the
post-Slice-12.8 posture:

- VS Code is the only Community editor extension
- Community and Infrastructure are separate export targets
- CI verifies both exports independently
- Exported Infrastructure runs Python tests and OpenTofu fmt/init/validate
- No Cursor CI/release surfaces
- No publish, deploy, tag, push, plan, apply, destroy, or AWS credentials in
  ordinary validation CI
- Infrastructure remains privately and independently versioned
- Slice 12.10 Epic completion:
  `verification/product_cleanup_repository_split_completion/`
  (`product-cleanup-repository-split-completion-verification:1.0.0`)
- Epic 13 not started

## Authoritative CI workflow

`.github/workflows/ci.yml`

| Job | Role |
| --- | --- |
| `engine-tests` | Engine unit tests |
| `platform-tests` | Platform unit tests |
| `vscode-ci` | npm ci / compile / test / package:dry (no Marketplace publish) |
| `community-export-verification` | dry-run then temp Community export + Slice 12.8 verifier |
| `infrastructure-export-verification` | dry-run, temp export, pytest (empty PYTHONPATH), tofu fmt/init/validate |
| `ci-release-boundaries` | This package + focused unit tests |

Permissions: `contents: read` (workflow and export jobs). No `id-token: write`.

## Export commands (CI)

```bash
python scripts/export_repository.py --target community --destination <tmp> --dry-run
python scripts/export_repository.py --target community --destination <tmp>

python scripts/export_repository.py --target infrastructure --destination <tmp> --dry-run
python scripts/export_repository.py --target infrastructure --destination <tmp>
```

Jobs use separate temporary destinations. Export trees are not uploaded as
artifacts. No `git init` / commit / push / tag in export destinations.

## OpenTofu validation (exported tree only)

```bash
tofu fmt -check -recursive
# for each of: modules/community-cloud-api, modules/community-data-lake, production
tofu init -backend=false -input=false
tofu validate
```

Provider plugin download may occur during `init`. Guarantees: no AWS API, no
remote backend, no plan/apply/destroy.

## AWS / Git / publish boundaries

- AWS credential env vars scrubbed; `AWS_EC2_METADATA_DISABLED=true`
- No `aws-actions/configure-aws-credentials`
- No AWS CLI / STS
- Ordinary CI does not publish packages, VSIX, or GitHub Releases
- Deployment tooling may exist elsewhere but is not invoked by this workflow

## Release inventory

- Engine / VS Code at product version `0.2.0`
- Active editor extension: VS Code only
- Infrastructure: `private_infrastructure_only`, independently versioned, not a
  Community release artifact, not auto-tagged with Engine
- Assessment schema `1.2` unchanged

## Run verification

```bash
PYTHONPATH=. python -m verification.ci_release_boundaries
PYTHONPATH=. python -m pytest tests/verification/ci_release_boundaries -q
```

Report: `.codestrata-artifacts/validation/suites/sv12-9/ci-release-boundary-verification.json`

## Explicit non-goals (Slice 12.9 scope)

- Creating real Community or Infrastructure remotes
- Removing `infrastructure/` from the monorepo
- Commit / tag / publish / deploy
- Epic 13

Epic 12 completion is Slice 12.10:
`verification/product_cleanup_repository_split_completion/`.
