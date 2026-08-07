# Infrastructure repository contract (Slice 12.5)

Authoritative definition for extracting `infrastructure/` into a separate
private repository. Slice 12.5 defined this contract. **Slice 12.6** implements
the deterministic exporter (`scripts/export_infrastructure_repository.py`).
**Slice 12.7** independently verifies dual export, secret/prohibited scans, and
exported OpenTofu `fmt` / `init -backend=false` / `validate` (no plan/apply,
no Git, no AWS credentials). Slice 12.8 owns Community/Infrastructure target
integration.

## Repository purpose

The private **CodeStrata Infrastructure** repository owns OpenTofu modules,
production compositions, infrastructure validation, infrastructure-focused
tests, security controls, and deployment documentation for CodeStrata-hosted
services.

It provisions and configures hosting resources. It does **not** own:

- Engine product code
- Platform application code
- Community Cloud API implementation
- VS Code extension source
- telemetry / analytics / AI provider runtimes
- product reports
- application schemas except copied, versioned interface references where
  strictly necessary
- deployment credentials
- Terraform / OpenTofu state

## Repository name and visibility

| Field | Value |
| --- | --- |
| Repository name | `codestrata-infrastructure` |
| Visibility | **private** |
| Organization convention | Matches Community export naming (`codestrata-*`) |

Rationale: name already appears in monorepo architecture guidance and
Infrastructure README extraction notes. No alternate name is required.

## Source-of-truth transition

### Preferred decision

**A → B**

1. **Pre-cutover (A):** Main monorepo (`codestrata-platform`) remains
   authoritative. Edit `infrastructure/` only in the main repository. Export
   is one-way. Destination edits are review-only.
2. **Cutover:** Owner-operated after exporter verification, destination
   validation, manual Git init/commit/remote/push, and explicit acceptance.
3. **Post-cutover (B):** `codestrata-infrastructure` becomes authoritative.
   Dual-authoring is **forbidden**. Future main-repo changes require a
   deliberate import/sync from the Infrastructure repository.

### Emergency fixes during transition

Fix in the authoritative repository for the current stage; re-export or
re-import through the documented sync process. No silent bidirectional merge.

### Source deletion

Deleting `infrastructure/` from the main repository is **deferred** until after
successful cutover and acceptance. Not part of Slice 12.5–12.7 by default.

## Destination layout (Approach A)

Remove the `infrastructure/` prefix so the independent repository is rooted at
its own content:

```text
codestrata-infrastructure/
├── modules/
│   ├── community-cloud-api/
│   └── community-data-lake/
├── production/
├── tests/
├── verification/
├── docs/
├── policies/
├── scripts/
├── README.md
├── SECURITY.md          # generated/copied Infrastructure-specific
├── LICENSE              # approved license reference / copy
├── .gitignore           # Infrastructure-specific (track lock files)
├── export-manifest.json # produced by Slice 12.6 exporter
└── (minimal test config as required)
```

**Approach B** (nested `infrastructure/`) is rejected: an independent repo
should not retain a redundant outer folder name.

## Export allowlist (required)

Relative to monorepo root:

| Source path | Purpose |
| --- | --- |
| `infrastructure/modules/**` (source only) | OpenTofu modules |
| `infrastructure/production/**` (source only) | Production composition |
| `infrastructure/tests/**` (source only) | Infrastructure tests |
| `infrastructure/verification/**` (source only) | SV.9-style verification |
| `infrastructure/docs/**` | Infrastructure docs |
| `infrastructure/policies/**` | Deployment / policy docs & JSON |
| `infrastructure/scripts/**` | validate / packaging helper scripts |
| `infrastructure/README.md` | Repository README (path rewrite in 12.6) |
| `infrastructure/__init__.py` | Python package marker for tests |
| `infrastructure/.gitignore` | Base ignore rules (adapt lock-file rule) |
| Provider lock files `**/.terraform.lock.hcl` when present | Reproducible providers |

Every included shared/root file must have a documented purpose (see shared-file
decisions below).

## Optional source inventory

| Item | Decision |
| --- | --- |
| `infrastructure/production/backend.tf.example` | export_optional (secret-free template) |
| `infrastructure/production/terraform.tfvars.example` | export_optional (synthetic example only) |
| Local `.terraform.lock.hcl` if generated | export_optional → track in destination |
| Root `LICENSE` / `SECURITY.md` | generate Infrastructure-specific copy |

## Prohibited paths and files

Never export:

- `.git/`, credentials, deployment secrets
- `**/.terraform/**`, `**/.tofu/**`
- `*.tfstate`, `*.tfstate.*`, `*.tfplan`, `*.plan`, `crash.log`, `crash.*.log`
- `override.tf`, `*_override.tf`, `local.auto.tfvars`, real `*.tfvars` / secrets tfvars
- `.env`, `.env.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, AWS credential files
- `__pycache__/`, `.pytest_cache/`, coverage, `node_modules/`, build/dist artifacts
- `infrastructure/reports/**` (generated; may contain local paths)
- Engine / Platform runtime source (`engine/`, `platform/`), `vscode-plugin/`,
  `cursor-plugin/`
- Community release artifacts, VSIX, wheels/sdists
- Absolute paths, remote URLs with credentials, real account/bucket secrets under policy

## Shared root-file decisions

| File | Decision |
| --- | --- |
| Root `pyproject.toml` | **omit** broad monorepo file; generate minimal Infrastructure test config in 12.6 if required |
| `pytest.ini` | **omit** unless Infrastructure-specific generated |
| `.gitignore` | **generate** Infrastructure-specific (do **not** ignore tracked lock files) |
| `LICENSE` | **copy** approved license text / reference |
| `SECURITY.md` | **generate** Infrastructure-focused security doc |
| `CODEOWNERS` | **defer** / generate owner-operated |
| `.editorconfig` | **omit** or copy if present and neutral |
| `Makefile` | **omit** unless Infrastructure-only |
| Monorepo `public-export-manifest.yaml` | **omit** (source_repository_only) |

## Provider lock-file decision

**Intentionally track** `.terraform.lock.hcl` in the destination repository when
present after `tofu init -backend=false`.

Current `infrastructure/.gitignore` ignores lock files (local-only today).
Slice 12.6 must adapt destination `.gitignore` so lock files are **not**
excluded from the independent repository.

## State / backend boundary

- No state files exported
- No backend credentials exported
- `backend.tf.example` may be included only if secret-free
- Production backend init remains owner/CI controlled
- Validation uses `tofu init -backend=false`
- Export validation performs no backend access
- Source and remote state are separate assets

## Secrets boundary

Forbidden: AWS keys/tokens, API/GitHub/Marketplace tokens, passwords, signing
keys, private certs, webhook/OAuth secrets, real sensitive ARNs/bucket names
under policy, customer identifiers, environment-specific secrets.

Allow clearly synthetic examples only. Slice 12.7 owns destination secret
scanning.

## Dependency boundary

Ordinary OpenTofu validation must not require Engine or Platform packages.

Current posture:

- Most Infrastructure tests are path/HCL static checks (good).
- `infrastructure/tests/verification/test_boundary.py` currently imports Engine
  and Platform schema constants (**application import** — adapt in 12.6/12.7 to
  static duplicated/versioned constants or move cross-repo checks to main
  integration/release process).

Preferred: Infrastructure tests operate on Infrastructure source + static
expected contracts only.

## OpenTofu validation contract

Commands (no plan/apply/destroy; no AWS credentials; no remote backend):

```bash
tofu fmt -check -recursive
tofu init -backend=false -input=false
tofu validate
```

**Validation roots:**

1. `modules/community-cloud-api` (destination) / `infrastructure/modules/community-cloud-api` (source)
2. `modules/community-data-lake`
3. `production`

Provider plugin init for local validate is allowed. Bounded retry for known
provider-plugin flakiness may remain as documented in current verification
helpers. Slice 12.7 validates the **exported** tree.

## Versioning contract

- Infrastructure commits and tags independently
- Does not automatically share Engine `0.2.0` package version
- Deployment compatibility recorded via compatibility notes / release docs
- First extracted repository: **no release tag required**; baseline tag later
  and owner-operated
- Export script never creates tags

## Git-operation boundary

The future exporter **must not**: `git init`, `add`, `commit`, branch, remote,
push, fetch, pull, tag, open PR, or modify Git config. All Git actions remain
owner-operated.

## Synchronization contract

- One-way export (main → destination) pre-cutover
- Fail if destination contains unmanaged files
- Fail if export would overwrite unexpected files
- Replace only manifest-managed paths
- Report deletions before applying
- Dry-run shows additions, changes, removals
- No silent merge; no bidirectional sync

## Manifest contract (future operational artifact)

```text
schema_name = infrastructure-repository-export-manifest
schema_version = 1.0.0
```

Fields: `target`, layout versions, `files`, `file_count`, `checksums` (SHA-256,
sorted by relative destination path), `executable_files`, `excluded_categories`,
`validation_roots`, `limitations`.

Never include absolute paths, usernames, hostnames, timestamps, credentials,
state, or plan details.

## Inventory / checksum / permissions

- Destination relative path, classification, file mode category, SHA-256
- Optional size in bytes if deterministic and useful
- No timestamps, absolute paths, inode/owner
- Regular files non-executable; approved scripts retain `+x`
- No setuid/setgid; no world-writable
- Symlinks rejected unless explicitly approved (fail closed)

## Documentation-link policy

Monorepo-relative links to `platform/docs/...` must become conceptual external
references or copied interface notes at export time. Exported repository must
have no broken relative links to Engine, Platform, VS Code, or Cursor files.
Slice 12.7 verifies where practical.

## Public / private boundary

Infrastructure repository is private. Community public export continues to
exclude `infrastructure/` (`public-export-manifest.yaml`). Slice 12.8 owns
export-target integration refinements.

## CI expectations (Slice 12.9)

Active monorepo workflow: `.github/workflows/ci.yml`

- Job `infrastructure-export-verification` exports via
  `python scripts/export_repository.py --target infrastructure`
- Dry-run then temporary destination (Approach A layout)
- Exported `pytest tests` with empty `PYTHONPATH` (no monorepo injection)
- `tofu fmt -check -recursive`
- Per root (`modules/community-cloud-api`, `modules/community-data-lake`,
  `production`): `tofu init -backend=false` then `tofu validate`
- No plan/apply/destroy; no AWS credentials / OIDC; no git init/push/tag
- Export verification performs no push/tag/release
- Export trees are not uploaded as public CI artifacts
- Infrastructure remains independently versioned (not Engine-tag-coupled)
- Authoritative boundary verifier:
  `python -m verification.ci_release_boundaries`
  → `reports/verification/sv12-9/ci-release-boundary-verification.json`

Secret/prohibited-file scan and dual-export determinism remain covered by
Slices 12.6–12.7 packages invoked where appropriate.

## Migration stages

1. Contract accepted (this slice)
2. Exporter implemented (12.6)
3. Exporter verified (12.7)
4. Destination repository created **manually**
5. Dry-run reviewed
6. Initial export reviewed
7. OpenTofu validated on destination
8–11. Git init / commit / remote / push **manually**
12. Cutover decision recorded
13. Main-repo source removal planned separately (deferred)

## Rollback

Before cutover: main repo authoritative; failed export discarded; no source
deletion; no state/AWS change. After cutover: rollback requires explicit
ownership decision.

## Policy identity

```text
policy_id = community-infrastructure-repository-policy
policy_version = 1.0
```

Verification: `infrastructure-repository-contract-verification:1.0.0`  
Report: `reports/verification/sv12-5/infrastructure-repository-contract-verification.json`

## Exporter command (Slice 12.6)

```bash
python scripts/export_infrastructure_repository.py \
  --destination ../codestrata-infrastructure \
  --dry-run

python scripts/export_infrastructure_repository.py \
  --destination ../codestrata-infrastructure
```

Supporting package: `scripts/repository_export/`. Approach A mapping removes the
`infrastructure/` prefix. Dry-run writes nothing. Managed destinations require a
valid `export-manifest.json`. Unmanaged files fail closed and are never deleted.

Verification: `infrastructure-repository-exporter-verification:1.0.0` →
`reports/verification/sv12-6/`.

## Deferred

- Owner-operated destination repository creation, Git, and cutover
- Removing `infrastructure/` from the monorepo (post-cutover only)
- Epic 13 (VS Code Extension completion)

## Slice 12.8 / 12.9 / 12.10

- Slice 12.8: `scripts/export_repository.py --target community|infrastructure`
- Slice 12.9: CI jobs verify both targets independently; VS Code-only extension CI
- Slice 12.10: Epic 12 completion verification
  (`product-cleanup-repository-split-completion-verification:1.0.0`)

## Slice 12.7 verification outcome

Schema: `infrastructure-repository-export-verification:1.0.0`  
Report: `reports/verification/sv12-7/infrastructure-repository-export-verification.json`

Dual export is byte-identical. Manifest/inventory/checksums independently
validate. Exported Python tests pass without Engine/Platform. OpenTofu
`fmt -check -recursive`, `init -backend=false`, and `validate` pass for
`modules/community-cloud-api`, `modules/community-data-lake`, and `production`.
No plan/apply/destroy, no Git, no AWS service calls.
