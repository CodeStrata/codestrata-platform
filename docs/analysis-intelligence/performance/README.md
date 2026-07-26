# Performance Intelligence

Phase 4.9 of CodeStrata Analysis Intelligence.

| Sub-milestone | Status |
| ------------- | ------ |
| 4.9.1 Domain Foundation | Complete (`performance-assessment` **1.0.0**; analytically empty) |
| 4.9.2 Repository Performance Evidence | Complete (`repository-performance-evidence` **1.0.0**; platform evidence; disabled by default) |
| 4.9.3 Performance Intelligence Rules | Complete (`performance.core` **1.0.0**; 20 hygiene rules; disabled by default) |
| 4.9.4 Assessment Inventory | Complete (`performance-assessment` **1.1.0**; inventories; disabled by default) |
| 4.9.5 Deterministic Synthesis | Complete (`performance-assessment` **1.2.0**; themes/conclusions/recommendations; disabled by default) |
| 4.9.6 Report Integration | Complete (`report.performance` **1.0.0**; presentation only; disabled by default) |

Design authority:
[intelligence-platform.md](../../architecture/intelligence-platform.md).

## Purpose

Performance Intelligence analyzes repository-observable signals related to
data access, blocking operations, caching, concurrency, and related categories.
Phase **4.9.1** registers the assessment capability as analytically empty —
lifecycle states, deterministic serialization, and independent feature gates
only. Phase **4.9.2** adds platform evidence collection for performance
signals without Findings or scoring. Phase **4.9.3** evaluates observation-only
hygiene SharedRules against that evidence and emits shared Findings.
Phase **4.9.4** projects deterministic inventories over those Findings and
rule-execution facts into `performance-assessment.json`. Phase **4.9.5** adds
deterministic synthesis (themes, conclusions, recommendations, posture)
over those inventories (**1.2.0**). Phase **4.9.6** projects the in-memory
assessment section into `assessment.performance` / HTML
**Performance Intelligence** (`#performance-assessment`).

## Capability identity

| Constant | Value |
| -------- | ----- |
| Capability | `performance` |
| Section ID | `assessment.performance` |
| Schema | `performance-assessment` **1.2.0** |
| Artifact | `performance-assessment.json` |
| Schema ID | `codestrata.performance_assessment` |
| Pack | `performance.core` @ `1.0.0` (20 hygiene rules) |
| Synthesis | **1.0.0** |
| Evidence | `repository-performance-evidence` **1.0.0** (platform; default off) |

Package: `aimf.domain.performance` / `aimf.application.performance` /
`aimf.application.rules.performance` / `aimf.reporting.performance`.
Evidence: `aimf.domain.evidence.repository_performance` /
`aimf.application.evidence.repository_performance`.

## Shared Finding integration

`FindingCategory.PERFORMANCE` and `RuleCategory.PERFORMANCE` map together. No
`PerformanceFinding` type exists. Rules emit shared Findings with
Informational/Low severity and observation-only remediation notes. When
`[analysis.performance]` is enabled with the pack on, Phase **4.9.5**
assembles inventories and deterministic synthesis over pack Findings.

## Gates

```toml
[analysis.performance]
enabled = true
# include_synthesis = true

[evidence.repository_performance]
enabled = true

[rules]
enabled = true

[rules.performance]
enabled = true

[report.sections.performance]
enabled = true
```

Defaults are **false**. Enabling `[rules.performance]` does **not** enable
`[analysis.performance]`. Enabling analysis writes
`performance-assessment.json` with inventories and synthesis when the pack ran.
Enabling evidence writes `repository-performance-evidence.json` independently.
Enabling `[report.sections.performance]` projects the in-memory assessment into
`assessment.performance` / HTML when analysis produced a section.

Hygiene rules: [hygiene-rules.md](hygiene-rules.md).
Inventory: [inventory.md](inventory.md).
Synthesis: [synthesis.md](synthesis.md).
Report: [report.md](report.md).

See [domain-foundation.md](domain-foundation.md),
[configuration.md](configuration.md), [taxonomy.md](taxonomy.md), and
[repository-performance-evidence.md](../repository-performance-evidence.md).

## Explicit non-claims

Succeeded assessments (including zero findings) do **not** mean the repository
is performant, scalable, free of latency risk, or production-ready under load.
