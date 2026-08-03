# Commercial Engineering Intelligence Reporting

Platform-only domain for multi-repository Engineering Intelligence Reports.

## Boundary

| Layer | Responsibility |
| --- | --- |
| **Engine (Community)** | One repository → evidence → findings → recommendations → Priority Actions → assessment roadmap → canonical `report.json` |
| **Platform (Commercial)** | Many canonical assessments → intelligence dataset → cross-repository intelligence → commercial Engineering Intelligence Report |

Community Edition must not construct or expose this model. Engine packages must not import `codestrata_platform.intelligence_reporting`.

## Report purpose

Answer portfolio questions deterministically:

- Which conditions recur across repositories?
- Which technologies dominate the assessed dataset?
- How do repositories compare by assessment head?
- Which capabilities are complete, partial, unavailable, or disabled?
- Which modernization actions recur?
- Which observations are strongly supported, and which dataset limitations restrict interpretation?

## Dataset model

`IntelligenceDataset` references repository assessments (IDs, schema versions, pinned revisions, visibility). It does **not** embed full assessment documents.

Dataset identity: `dataset:{sha256[:24]}` from sorted assessment references + selection policy. Timestamps and filesystem paths are excluded.

## Cross-repository comparison

`CapabilityComparison` and `AssessmentHeadDistribution` describe coverage/confidence counts per assessment head. There is **no** maturity score and no “best/worst” ranking in this model.

## Recurring patterns

`RecurringIntelligencePattern` is evidence-backed and identity-stable (`pattern:{sha256[:24]}`). Narrative text alone does not form identity. Detection is implemented in Slice 6.6 (`build_recurring_patterns`).

## Modernization observations

`ModernizationObservation` synthesizes deterministic Recommendations / Priority Actions / assessment roadmaps. These are **observations**, not new authoritative Recommendations. ROI, cost, staffing, and delivery commitments are forbidden. Synthesis is implemented in Slice 6.7 (`build_modernization_observations`).

## Distribution versus temporal trend

`AssessmentHeadDistribution` is a single-snapshot cross-repository distribution. It is **not** a temporal trend. A future `AssessmentHeadTrend` would require repeated comparable assessments over time and is deferred.

## Confidence and limitations

`IntelligenceReportConfidence` is not an average of repository confidence. `DatasetLimitation` uses interpretation severity (`material` / `moderate` / `minor` / `informational`), not Finding Severity.

Slice 6.8 derives report confidence and structured dataset limitations via
`populate_report_quality`. See [report-quality.md](./report-quality.md).

## Repository drill-down

`RepositoryIntelligenceDrilldown` holds safe references only — no source bodies, snippets, absolute paths, or secrets.

Slice 6.9 builds one bounded drill-down per included repository via
`populate_report_repository_drilldowns`. See [repository-drilldowns.md](./repository-drilldowns.md).

## Website-safe export (Slice 6.10)

Domain `WebsiteExportPolicy` / `WebsiteSafeIntelligenceReport` remain the sparse
visibility DTO from Slice 6.1. Slice 6.10 adds the application projection
`WebsiteSafeExportDocument`, static JSON/HTML export, and export manifest.

See [website-export.md](./website-export.md).

## OSS demonstration limitations

The public OSS dataset is used to validate the commercial intelligence-reporting model. It is **not** representative of all software repositories and must not be presented as a product-wide industry benchmark.

## Dataset ingestion (Slice 6.2)

Canonical Engine assessment reports are ingested into `IntelligenceDataset` via
`codestrata_platform.intelligence_reporting.application.ingest_assessment_dataset`.

See [dataset-ingestion.md](./dataset-ingestion.md).

## Aggregation foundation (Slice 6.3)

`aggregate_intelligence_dataset` builds factual `CrossRepositoryAggregation`
inputs (indexes, facts, denominators). It does not create recurring-pattern
conclusions, portfolio recommendations, or industry benchmarks.

See [aggregation-foundation.md](./aggregation-foundation.md).

## Technology Distribution (Slice 6.4)

`build_technology_distribution` converts technology facts into descriptive
`TechnologyDistribution` observations (presence vs occurrence, explicit
denominators, version states). No modern/outdated/supported claims.

See [technology-distribution.md](./technology-distribution.md).

## Capability Comparison (Slice 6.5)

`build_capability_comparisons` builds per-head `CapabilityComparison` and
`AssessmentHeadDistribution` from assessment-head / coverage / confidence facts.
No maturity, health, readiness, ranking, or composite portfolio scores.

See [capability-comparison.md](./capability-comparison.md).

## Recurring Patterns (Slice 6.6)

`build_recurring_patterns` detects deterministic cross-repository conditions
from structured rule / recommendation / technology-conflict identities.
No AI, title similarity, portfolio Recommendations, or industry prevalence.

See [recurring-patterns.md](./recurring-patterns.md).

## Modernization Observations (Slice 6.7)

`build_modernization_observations` synthesizes evidence-backed portfolio
observations from repository Recommendations/PAs/roadmaps and reviewed pattern
mappings. They are not portfolio Recommendations or delivery commitments.

See [modernization-observations.md](./modernization-observations.md).

## Report quality (Slice 6.8)

`build_report_quality` / `populate_report_quality` derive
`IntelligenceReportConfidence`, report-level `DatasetLimitation`s, methodology
references, and an `IntelligenceInterpretationPolicyBundle` that participates in
report identity. The bundle includes the repository-drilldown policy token.

See [report-quality.md](./report-quality.md).

## Repository drill-downs (Slice 6.9)

`build_repository_drilldowns` / `populate_report_repository_drilldowns` create
one bounded `RepositoryIntelligenceDrilldown` per included repository.

See [repository-drilldowns.md](./repository-drilldowns.md).

## Website-safe static export (Slice 6.10)

`build_website_safe_export` projects an EIR into website-safe JSON + self-contained
HTML + manifest.

See [website-export.md](./website-export.md).

## Public OSS demonstration (Slice 6.11)

`generate_oss_demonstration_artifacts` runs slices 6.2–6.10 against the five
validated public OSS assessment fixtures and writes artifacts under
`platform/demo/`.

See [oss-demonstration.md](./oss-demonstration.md) and `platform/demo/README.md`.

## Commercial boundary verification (Slice 6.12)

Epic 6 closes with architectural verification: Engine/Community remain
single-repository only; Platform owns all commercial Engineering Intelligence;
public export excludes `platform/`. See [commercial-boundary.md](./commercial-boundary.md).

## Schema version

Commercial report schema: **1.0** (`ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION`).

Website-safe export schema: **1.0** (`WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION`) —
separate projection contract.

Independent of:

- Engine assessment schema 1.2
- Validation record schema 1.0
- Validation summary schema 1.0
