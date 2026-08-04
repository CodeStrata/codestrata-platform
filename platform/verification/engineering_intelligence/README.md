# Engineering Intelligence Pipeline Verification (SV.6)

Platform-only verification for the commercial Engineering Intelligence pipeline.

This package is **not** part of the Platform runtime wheel/`codestrata_platform`
distribution.

## Purpose

Verify:

pinned public catalog repositories
→ canonical Engine `assess --no-ai`
→ `report.json` schema 1.2
→ Platform ingestion
→ IntelligenceDataset
→ CrossRepositoryAggregation
→ Technology / Capability / Patterns / Modernization / Quality / Drill-downs
→ EngineeringIntelligenceReport schema 1.0

Focus: structure, provenance, determinism, safety, aggregation correctness, and
section population.

Editorial / commercial-quality review remains **SV.12**.  
Website-safe export belongs to **SV.8**.  
Community Cloud API verification belongs to **SV.7**.

## Permanent catalog

Only source of repository identity:

`validation/repository-catalog/catalog.json`

Preferred five-language qualified subset (catalog IDs):

- `cleanarchitecture` (C#/.NET)
- `express` (JS/TS)
- `flask` (Python)
- `slim` (PHP)
- `spring-petclinic` (Java)

All must resolve to full pinned commit SHAs. No second repository list. No
floating tags/branches.

## Assessment inputs

Generated through the existing SV.4 workflow helpers:

`codestrata assess --repo . --output reports --no-ai`

Assessments are cached under the verification output cache directory as
`assessments/<repository_id>/<sha12>/report.json`. Unit tests never clone.

## Commands

```bash
# From monorepo root
PYTHONPATH=platform:platform/src:engine:engine/src \
  python -m verification.engineering_intelligence --offline-scenarios-only

# Reuse cached assessments (no network)
PYTHONPATH=platform:platform/src:engine:engine/src \
  python -m verification.engineering_intelligence \
  --cache-dir platform/reports/verification/engineering-intelligence-assessments

# Clone pinned SHAs + assess missing caches, then verify EIR pipeline
PYTHONPATH=platform:platform/src:engine:engine/src \
  python -m verification.engineering_intelligence --with-catalog-network
```

Report: `platform/reports/verification/engineering-intelligence-verification.json`

Schema: `engineering-intelligence-verification` / `1.0.0`

## Separation

| Slice | Focus |
| --- | --- |
| SV.4 | Engine assessment workflow |
| SV.5 | Single-repo report artifact quality |
| **SV.6** | Platform EI pipeline |
| SV.7 | Community Cloud API |
| SV.8 | Website-safe export |
| SV.10 / SV.12 | Broader validation / editorial review |

## Limitations

- Does not redesign intelligence sections or aggregation policies
- Does not start the 30-repository validation run
- Does not generate website HTML/export in this slice
- Does not call Community Cloud
- Does not tune Findings/Recommendations
