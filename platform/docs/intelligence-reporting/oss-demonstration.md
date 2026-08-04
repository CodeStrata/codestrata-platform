# Public OSS demonstration report (Slice 6.11)

End-to-end demonstration of the commercial Engineering Intelligence pipeline
using the five validated public OSS assessment fixtures.

## What this is

- One deterministic `EngineeringIntelligenceReport`
- Website-safe JSON + self-contained HTML + export manifest under `platform/demo/`
- Proof that slices 6.2–6.10 compose correctly on real Engine `report.json` inputs

## What this is not

- Not a SaaS feature, web app, persistence layer, or customer reporting product
- Not hosting, CDN, CMS, authentication, or HTTP APIs
- Not a 24-repository ingest of local controlled fixtures
- Not industry benchmarking
- Not SV.12 release-verification: the 22 curated catalog EIR + editorial review
  lives under `platform/verification/engineering_intelligence_quality/` and
  writes to `platform/reports/verification/sv12/` (never overwrites this demo)

## Pipeline

```text
catalog.json + fixtures/*/report.json
  → ingest_assessment_dataset (6.2)
  → aggregate_intelligence_dataset (6.3)
  → technology / capability / patterns / modernization (6.4–6.7)
  → report quality (6.8)
  → repository drill-downs (6.9)
  → build_website_safe_export (6.10)
  → platform/demo/*.json|html
```

API:

```python
from codestrata_platform.intelligence_reporting.application.oss_demonstration import (
    generate_oss_demonstration_artifacts,
)

result = generate_oss_demonstration_artifacts(overwrite=True)
```

## Defect fixes required for real Engine reports

Slice 6.11 discovered two ingestion/normalization defects when consuming
qualification `report.json` files:

1. IR ingestion no longer requires Platform `ReportJsonParser` finding projection;
   it validates via Engine canonical traceability APIs.
2. When `assessment_coverage` is absent, commercial heads are derived from Engine
   `activation.packs` with honest `partial` coverage (not invented completeness).
3. Ingestion customer-field safety allows intentional `password=[REDACTED]` markers.

These changes do not alter Engine analyzers, rules, Findings, scoring, or schemas.

## Schemas

| Schema | Version |
| --- | --- |
| Engine assessment report | 1.2 |
| Validation record / summary | 1.0 |
| Engineering Intelligence Report | 1.0 |
| Website-safe export | 1.0 |

## Boundary

Platform-only. Community CLI and Engine packages do not expose the demonstration
generator.
