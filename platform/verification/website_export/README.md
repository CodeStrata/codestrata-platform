# Website-Safe Engineering Intelligence Export Verification (SV.8)

Platform-only verification that a canonical `EngineeringIntelligenceReport` can
be projected and rendered into deterministic, website-safe static artifacts.

This package is **not** part of the Platform runtime wheel /
`codestrata_platform` distribution.

## Purpose

Verify:

Verified EngineeringIntelligenceReport (SV.6 five-language public OSS)
→ WebsiteSafeExportDocument (allowlisted projection)
→ engineering-intelligence-report.json
→ engineering-intelligence-report.html
→ export-manifest.json
→ StaticIntelligenceExportWriter

Focus: projection allowlisting, identity, JSON/HTML parity, CSP, accessibility,
repository identity safety, manifest digests, writer path safety, determinism,
and privacy.

## Source input

Reuses the SV.6 preferred five-language subset from the permanent catalog:

`validation/repository-catalog/catalog.json`

Catalog IDs: `cleanarchitecture`, `express`, `flask`, `slim`, `spring-petclinic`

Expected verified EIR IDs (offline rebuild from cached assessments):

- report: `eir:394b8574e3bc83b0878dc031`
- dataset: `dataset:51f8613688c2fdffdd876121`
- interpretation bundle: `interp-bundle:c719915c68cf94601a0e8f0b`

Does not create a second multi-repository pipeline.

## Artifacts under verification

| File | Role |
| --- | --- |
| `engineering-intelligence-report.json` | Deterministic allowlisted JSON |
| `engineering-intelligence-report.html` | Self-contained static HTML |
| `export-manifest.json` | SHA-256 digests for JSON + HTML |

## Commands

```bash
# From monorepo root (offline when SV.6 assessment cache is present)
PYTHONPATH=platform:platform/src:engine:engine/src \
  python -m verification.website_export

PYTHONPATH=platform:platform/src:engine:engine/src \
  python -m verification.website_export \
  --output-dir platform/reports/verification \
  --cache-dir platform/reports/verification/engineering-intelligence-assessments
```

Report: `platform/reports/verification/website-export-verification.json`

Schema: `website-export-verification` / `1.0.0`

## Separation

| Slice | Focus |
| --- | --- |
| SV.6 | Engineering Intelligence pipeline → EIR |
| SV.7 | Community Cloud API |
| **SV.8** | Website-safe export (this package) |
| SV.9 | Infrastructure deployment verification (not started) |
| SV.12 | Editorial / commercial-quality review (not started) |

## Limitations

- Verification only; does not publish or host artifacts.
- Does not regenerate committed `platform/demo/` artifacts for formatting.
- Does not start the 30-repository run.
- Does not redesign branding, charts, JavaScript, or PDF generation.
- Source dataset ID is verified on the EIR input; the allowlisted website export
  projection tracks dataset summary counts rather than embedding the dataset ID.
