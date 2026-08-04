# SV.14 — Cross-Schema Compatibility Verification

Verification-only package for System Verification slice SV.14.

## Purpose

Prove that Engine, validation, Platform Engineering Intelligence, website-safe
export, Community Cloud API, and System Verification contracts are mutually
compatible for the v0.2.0 release.

This suite verifies **compatibility only**. It does not redesign schemas, bump
versions, migrate artifacts, or change assessment / EI / API product behavior
unless a release-blocking incompatibility is reproduced.

## Version namespaces

| Namespace | Example | Meaning |
| --- | --- | --- |
| Product assessment | `1.2` | Engine `report.json` |
| Product validation / EIR / export / API | `1.0` | Runtime product contracts |
| System Verification reports | `1.0.0` | Verification package outputs |

Product `1.0` and verification `1.0.0` are **not** interchangeable.

## Inputs (preserved)

- `validation/repository-catalog/catalog.json`
- `engine/reports/verification/sv10/`
- `engine/reports/verification/sv11/`
- `platform/reports/verification/sv12/`
- `platform/reports/verification/sv13/sv13-defect-ledger.json`
- Optional: `engine/validation/results/**/latest/record.json`
- Optional: `engine/validation/results/summaries/latest/validation-summary.json`

No clone or reassessment by default.

## Command

```bash
PYTHONPATH=platform:platform/src:engine:engine/src:. \
  python -m verification.cross_schema_compatibility
```

No network is required.

## Output

```
platform/reports/verification/sv14/
  cross-schema-compatibility-verification.json
  cross-schema-compatibility-verification.md
```

Contract: `schema_name=cross-schema-compatibility-verification` / `1.0.0`

## Registry

`registry.py` references live product constants (Engine assessment 1.2, validation
record/summary 1.0, EIR 1.0, website export 1.0, Community Cloud endpoint
schemas 1.0, verification reports 1.0.0). It is **not** a new product schema
authority.

## Privacy chain

Engine redaction → `customer_safe_text` → Platform `validate_report_document` →
EIR safe facts → website-safe projection. Aligned with SV.13.

## Relationship

| Slice | Role |
| --- | --- |
| SV.10–SV.13 | Produced/repaired the 22-repository release-validation artifacts |
| SV.14 | This compatibility verification |
| SV.15 | Release packaging / next slice — **not started** |
| SV.16 | Deferred |

## Dataset disclaimer

Results describe only the 22 curated pinned repositories in the v0.2.0
release-validation catalog and are not a product-wide accuracy or industry
benchmark claim.
