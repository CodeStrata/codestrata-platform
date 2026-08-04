# SV.15 — Deterministic Output Verification

Verification-only package for System Verification slice SV.15.

## Purpose

Prove that equivalent semantic inputs and policies produce equivalent canonical
outputs across Engine, validation, Platform Engineering Intelligence, website
export, Community Cloud, infrastructure verification, and System Verification
reports — independent of input order, temporary directories, and Python hash seed.

Approved volatile fields (timestamps, durations, transport request IDs) are
documented explicitly and excluded from canonical fingerprints. Accidental
environment-derived volatility is a defect.

## Command

```bash
# From monorepo root (use project venv; requires Python >= 3.12)
PYTHONPATH=platform:platform/src:engine:engine/src:. \
  .venv/bin/python -m verification.deterministic_outputs
```

No network. No full 22-repository reassessment by default.

## Inputs

- `validation/repository-catalog/catalog.json`
- `engine/reports/verification/sv10/` (+ `determinism-samples.json`)
- `platform/reports/verification/sv12/`
- Prior SV reports for stable serialization checks

## Output

```
platform/reports/verification/sv15/
  deterministic-output-verification.json
  deterministic-output-verification.md
```

Contract: `schema_name=deterministic-output-verification` / `1.0.0`

## Relationship

| Slice | Role |
| --- | --- |
| SV.10–SV.14 | Produced preserved release-validation artifacts |
| SV.15 | This deterministic-output verification |
| **SV.16** | Release artifact verification (`verification/release_artifacts/`) |
| SV.17 | Release tag / publish — **not started** |

## Dataset disclaimer

Results describe only the 22 curated pinned repositories in the v0.2.0
release-validation catalog and are not a product-wide accuracy claim.
