# Cloud Intelligence

Phase 4.7 of CodeStrata Analysis Intelligence.

| Sub-milestone | Status |
| ------------- | ------ |
| 4.7.1 Domain Foundation | Complete (`cloud-assessment` **1.0.0**; analytically empty) |
| 4.7.2 Repository Cloud Evidence | Complete (platform `repository-cloud-evidence` **1.0.0**; disabled by default) |
| 4.7.3 Cloud Hygiene Rules | Complete (`cloud.core` **1.0.0**; 11 rules; disabled by default) |
| 4.7.4 Cloud Assessment Inventory | Complete (`cloud-assessment` **1.1.0**; disabled by default) |
| 4.7.5 Deterministic Cloud Synthesis | Complete (`cloud-assessment` **1.2.0**; disabled by default) |
| 4.7.6 Cloud Report Integration | Complete (`report.cloud` **1.0.0**; disabled by default) |

Design authority:
[intelligence-platform.md](../../architecture/intelligence-platform.md).

## Purpose

Cloud Intelligence analyzes repository-observable cloud technology and
deployment signals. Phase **4.7.5** synthesizes themes, conclusions, and
observation-oriented recommendations from inventory + Findings + rule facts.

## Capability identity

| Constant | Value |
| -------- | ----- |
| Capability | `cloud` |
| Section ID | `assessment.cloud` |
| Schema | `cloud-assessment` **1.2.0** |
| Artifact | `cloud-assessment.json` |
| Schema ID | `codestrata.cloud_assessment` |
| Pack | `cloud.core` @ `1.0.0` (11 hygiene rules) |
| Report section | `report.cloud` **1.0.0** (`assessment.cloud` / `#cloud-assessment`) |

Package: `codestrata.domain.cloud` / `codestrata.application.cloud` /
`codestrata.application.rules.cloud`.

## Shared Finding integration

`FindingCategory.CLOUD` and `RuleCategory.CLOUD` map together. No `CloudFinding`
type exists. Hygiene Findings use the shared Finding model.

## Gates

```toml
[evidence.repository_cloud]
enabled = true

[rules]
enabled = true

[rules.cloud]
enabled = true

[analysis.cloud]
enabled = true

[report.sections.cloud]
enabled = true
```

All default to **false**. Rules require `rules` + `rules.cloud`. Evidence is
independent. When `analysis.cloud` is on with the pack enabled, assessment
writes inventories and synthesis (`include_synthesis` defaults true). Enable
`[report.sections.cloud]` to project the assessment into `report.json` and HTML.

See [hygiene-rules.md](hygiene-rules.md), [inventory.md](inventory.md),
[synthesis.md](synthesis.md), [report.md](report.md), and
[../repository-cloud-evidence.md](../repository-cloud-evidence.md).

## Explicit non-claims

A succeeded-empty assessment or zero Findings does **not** mean the repository
is cloud ready, portable, containerized, or compliant with any cloud provider
checklist.

## Docs

- [report.md](report.md)
- [synthesis.md](synthesis.md)
- [inventory.md](inventory.md)
- [hygiene-rules.md](hygiene-rules.md)
- [domain-foundation.md](domain-foundation.md)
- [taxonomy.md](taxonomy.md)
- [configuration.md](configuration.md)
- Platform evidence: [../repository-cloud-evidence.md](../repository-cloud-evidence.md)
