# SV.16 — Release Artifact Verification

Verification-only package for System Verification slice **SV.16**. Validates
Community Engine release artifacts (wheel, sdist), installation smoke, export
boundaries, extension packaging, prior SV report gates, and preserved EI
identities — without tagging, publishing, deploying, or running `tofu apply`.

## Run

From the monorepo root (with `.venv` active and dependencies installed):

```bash
python -m verification.release_artifacts
```

Optional flags:

```bash
python -m verification.release_artifacts \
  --monorepo-root . \
  --output-dir reports/verification/sv16 \
  --skip-build \
  --skip-install
```

## OpenTofu requirement

SV.16 reuses `infrastructure.verification.opentofu` for static `tofu fmt` /
`tofu init -backend=false` / `tofu validate` checks.

When `tofu` ≥ 1.6 is on `PATH` and validation passes, the prior
`opentofu_unavailable` blocker is closed. Terraform is never used as a
substitute. Lock files and `.terraform/` remain gitignored.

Verified locally (SV.16A): OpenTofu **v1.12.5**, fmt/init/validate passed for
`modules/community-cloud-api` and `production` (no plan/apply).

## Output

Reports are written under:

```
reports/verification/sv16/
├── release-artifact-verification.json
├── release-artifact-verification.md
├── release-notes-input.json
└── artifacts/          # copied wheel/sdist from dual builds
```

Paths inside JSON reports are **relative to the monorepo root** only.

## Intended release

- **Product version:** `0.2.0` (Engine Community package)
- **Verification schema:** `release-artifact-verification` @ `1.0.0`
- **Repository count:** 22 (release-validation catalog)

## Relationship to other slices

| Slice | Role |
| ----- | ---- |
| SV.10–SV.11 | Curated assessment + consistency (inputs) |
| SV.12–SV.13 | EI quality + defect fixes (identities) |
| SV.14 | Cross-schema compatibility |
| SV.15 | Deterministic outputs |
| **SV.16** | **This release artifact verification** |
| SV.17 | **Not started** (`start_sv17=False`) |

## Confirmations (always false / true by contract)

- `no_tag`, `no_publish`, `no_deploy`, `no_tofu_apply` — enforced
- `start_sv17` — **False**; do not begin SV.17 from this package
