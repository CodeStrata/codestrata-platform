# Engine verification

Repository-local verification suites for CodeStrata Engine (Community Edition).

These packages are **not** part of the installed `codestrata` wheel. They live
beside `src/` so maintainers and the public Engine mirror can reproduce
first-time Community journeys.

| Suite | Purpose |
| --- | --- |
| [`cli_installation/`](./cli_installation/) | **SV.2** — clean CLI installation verification |
| [`cli_initialization/`](./cli_initialization/) | **SV.3** — CLI initialization workflow verification |
| [`repository_assessment/`](./repository_assessment/) | **SV.4** — repository assessment end-to-end verification |
| [`assessment_report/`](./assessment_report/) | **SV.5** — assessment report quality/integrity verification |
| [`curated_repository_validation/`](./curated_repository_validation/) | **SV.10** — validate 22 curated OSS repositories |
| [`assessment_consistency/`](./assessment_consistency/) | **SV.11** — assessment consistency across the 22 SV.10 outputs |

Platform-owned SV packages (EI, website export, Community Cloud, SV.13 defect
fixes, SV.14 cross-schema compatibility, **SV.15 deterministic outputs**) live
under `platform/verification/` and are documented in those package READMEs.

Permanent catalog (SV.4A / SV.10A):

`validation/repository-catalog/catalog.json`

- Single source of truth for smoke, regression, engineering intelligence, and
  release-validation repository identity.
- Release-validation target for **v0.2.0** is exactly **22** curated
  repositories (`release_validation_target`). Later releases may expand the
  catalog to 30 or more.
- Unsupported-language repositories (for example Groovy-only HiveMind) must not
  be relabeled as supported; HiveMind was retired from the v0.2.0 set and
  replaced by owner-approved BookStack.
- SV.10A readiness gate must PASS before the full SV.10 multi-repository
  assessment run. SV.11 consumes completed SV.10 records/artifacts and does not
  reassess by default.
- Dataset limitation: this catalog is a curated CodeStrata verification
  dataset. Its results describe only the included pinned repositories and are
  not a product-wide accuracy or industry benchmark claim.

```bash
python validation/repository-catalog/validate_catalog.py
python validation/repository-catalog/validate_catalog.py --write-readiness-report --write-import-template
```

See [`validation/repository-catalog/README.md`](../../validation/repository-catalog/README.md)
for qualification, roles/tiers, execution batches, and how to add or retire
repositories.

Run:

```bash
cd engine
python -m verification.cli_installation
python -m verification.cli_initialization
python -m verification.repository_assessment --local-only
python -m verification.assessment_report --local-only
python -m verification.curated_repository_validation --tier tier1
python -m verification.assessment_consistency
```
