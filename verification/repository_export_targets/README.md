# Slice 12.8 — Repository export target integration

Schema: `repository-export-target-verification:1.0.0`

## Authoritative command

```bash
python scripts/export_repository.py --target community --destination <staging-root> --dry-run
python scripts/export_repository.py --target infrastructure --destination <repo-dir> --dry-run
```

## Run verification

```bash
PYTHONPATH=. .venv/bin/python -m verification.repository_export_targets
```

Report: `reports/verification/sv12-8/repository-export-target-verification.json`

## Notes

- Community destination = multi-repo staging root
- Infrastructure destination = single private repository directory
- Target policies/manifests remain independent
- Slice 12.9 CI/release boundaries: `verification/ci_release_boundaries/`
- Slice 12.10 Epic completion: `verification/product_cleanup_repository_split_completion/`
  (`product-cleanup-repository-split-completion-verification:1.0.0`)
- Epic 13 not started
