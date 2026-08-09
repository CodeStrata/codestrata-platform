# Slice 12.6 — Infrastructure repository exporter verification

Schema: `infrastructure-repository-exporter-verification:1.0.0`

## Run

```bash
PYTHONPATH=. .venv/bin/python -m verification.infrastructure_repository_exporter
```

Report: `.codestrata-artifacts/validation/suites/sv12-6/infrastructure-repository-exporter-verification.json`

## Authoritative exporter command

```bash
python scripts/export_infrastructure_repository.py \
  --destination ../codestrata-infrastructure \
  --dry-run

python scripts/export_infrastructure_repository.py \
  --destination ../codestrata-infrastructure
```

## Boundaries verified

- allowlist / Approach A mapping
- prohibited content
- destination safety
- generated root files and boundary-test transforms
- deterministic manifest / inventory / checksums
- managed-destination fail-closed sync
- dry-run writes nothing
- no Git / AWS / OpenTofu execution

Slice 12.7 owns exported-repository OpenTofu validation and secret scanning
(`verification/infrastructure_repository_export/`).

Epic 12 completion: Slice 12.10
(`verification/product_cleanup_repository_split_completion/`). Epic 13 not started.
