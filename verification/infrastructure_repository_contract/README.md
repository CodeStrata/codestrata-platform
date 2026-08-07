# Slice 12.5 — Infrastructure Repository Contract Verification

Schema: `infrastructure-repository-contract-verification` @ `1.0.0`  
Report: `reports/verification/sv12-5/infrastructure-repository-contract-verification.json`

## Posture

- Contract / inventory / architecture / documentation only
- Repository name: `codestrata-infrastructure` (private)
- Destination layout: Approach A (remove `infrastructure/` prefix)
- Source authority: main monorepo until cutover; dual-authoring forbidden
- No exporter, no destination repo, no Git, no AWS, no OpenTofu plan/apply
- `infrastructure/` retained in the main repository

Authoritative human contract:

`infrastructure/docs/repository-contract.md`

Policy: `community-infrastructure-repository-policy:1.0`

## Run

```bash
PYTHONPATH=. .venv/bin/python -m verification.infrastructure_repository_contract
```

## Tests

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/verification/infrastructure_repository_contract -q
```

## Later slices

- Slice 12.6 — exporter (`scripts/export_infrastructure_repository.py` /
  `scripts/repository_export/`)
- Slice 12.7 — exported-repository OpenTofu validation and secret scanning
- Slice 12.8 / 12.9 — export-target integration / CI
- Slice 12.10 — Epic 12 completion
  (`verification/product_cleanup_repository_split_completion/`)
- Epic 13 not started
