# Slice 12.10 — Epic 12 completion verification

Schema: `product-cleanup-repository-split-completion-verification:1.0.0`

## Purpose

Authoritative Epic 12 completion gate. Verifies Slices 12.1–12.10 are complete,
internally consistent, and safe — without adding product capabilities, creating
repositories, or performing commit/tag/publish/deploy/AWS/plan/apply/destroy.

## Run

```bash
PYTHONPATH=. python -m verification.product_cleanup_repository_split_completion
PYTHONPATH=. python -m pytest tests/verification/product_cleanup_repository_split_completion -q
```

Options:

```bash
# Faster local iteration (consume existing 12.7 report; skip npm)
PYTHONPATH=. python -m verification.product_cleanup_repository_split_completion \
  --skip-expensive --skip-vscode-npm
```

Report: `reports/verification/sv12-10/product-cleanup-repository-split-completion-verification.json`

## Slice matrix

| Slice | Verification package |
| --- | --- |
| 12.1 | `cursor_extension_removal` |
| 12.2 | `cursor_release_surface_removal` |
| 12.3 | `cursor_documentation_removal` |
| 12.4 | `community_client_boundary_cleanup` |
| 12.5 | `infrastructure_repository_contract` |
| 12.6 | `infrastructure_repository_exporter` |
| 12.7 | `infrastructure_repository_export` |
| 12.8 | `repository_export_targets` |
| 12.9 | `ci_release_boundaries` |
| 12.10 | this package |

## Posture

- Active Community editor extension: **VS Code only**
- Retired historical client: `cursor_extension` (Approach A compatibility)
- Export targets: `community` (public) and `infrastructure` (private)
- Authoritative router: `python scripts/export_repository.py --target …`
- CI: `.github/workflows/ci.yml` — no Cursor, no plan/apply/destroy, no AWS creds
- `infrastructure/` remains in the monorepo until owner cutover
- No real Community/Infrastructure remotes created by Epic 12
- `start_epic_13 = false`

## Release posture

Epic 12 is complete for v0.2.0 readiness of this epic. Tagging, Marketplace
publication, owner cutover, and Epic 13 remain future gated work.
