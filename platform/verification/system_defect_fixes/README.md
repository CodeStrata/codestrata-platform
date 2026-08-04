# SV.13 — Resolve Engineering Intelligence Unsafe-Metadata Ingestion Defect

Verification package for System Verification slice SV.13.

## Purpose

Repair the release defect where Platform Engineering Intelligence ingestion
rejected three curated assessments (`dubbo`, `juice-shop`, `nodegoat`) with
`unsafe_metadata` while Engine treated the same reports as customer-safe and
SV.11 marked them EI-input-ready.

## Root cause (safe summary)

SEC002 Finding descriptions embedded PEM **header markers** (not full key
bodies). Engine redaction previously only replaced complete BEGIN…END blocks,
so header-only markers remained in customer fields. Platform correctly
rejected `-----BEGIN` shapes (fail-closed).

Classification:

- **A** Engine unsafe canonical serialization (all three repositories)
- **E** SV.11 readiness did not invoke Platform `validate_report_document`

## Fix boundary

1. Engine: redact PEM header / begin fences; SEC002 uses categorical evidence
2. Engine: `customer_safe_text` contract + report / finding serialization
3. SV.11: Platform ingestion safety adapter (production validator)
4. EI loaders: apply Engine customer-safe projection before ingestion

Privacy validation remains fail-closed. No repository allowlists, Known Issues
bypasses, or global keyword exemptions.

## Command

```bash
cd platform
PYTHONPATH=src:../engine/src:../engine:. python -m verification.system_defect_fixes
```

## Output

```
platform/reports/verification/sv13/
  system-defect-fixes-verification.json
  system-defect-fixes-verification.md
  sv13-defect-ledger.json
  classification.json
```

Also rebuilds `platform/reports/verification/sv12/` for the repaired 22/22 EIR.

## Relationship

| Slice | Role |
| --- | --- |
| SV.11 | EI readiness now uses Platform safety authority |
| SV.12 | Failed at 19/22; re-run must reach 22/22 |
| SV.13 | This defect fix |
| SV.14 | Not started |

## Dataset disclaimer

Results describe only the 22 curated pinned repositories in the v0.2.0
release-validation catalog and are not a product-wide accuracy claim.
