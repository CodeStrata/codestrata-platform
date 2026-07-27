# Report generation

Customer-facing CodeStrata Engineering Assessment (HTML) and companion JSON.

```text
ModernizationReportInput
        │  (+ Phase 3 findings / recommendations / optional Advisor)
        ▼
build_customer_report_document()
        ▼
CustomerReportDocument  (alias: HtmlReportViewModel)
        ▼
HtmlReportRenderer.render()
        ▼
report.html (self-contained, branded, HTML report version 3.0)
```

## Artifacts

| File | Role |
| ---- | ---- |
| `report.html` | CodeStrata Engineering Assessment (customer deliverable) |
| `report.json` | Machine-readable assessment contract (schema 1.2) |
| `findings.json` | Deterministic findings (unchanged by HTML) |
| `recommendations.json` | Deterministic recommendations |
| `ai-enrichment.json` | Optional Modernization Advisor narrative |

## Sections (HTML v3)

1. Cover (brand, repository, report/engine/advisor versions, generated time, KPIs)
2. Contents (TOC with section anchors)
3. Key Takeaways (3–5 bullets from deterministic evidence + Advisor when present)
4. Engineering Modernization Assessment (posture summary + technology overview)
5. Priority Actions (Immediate / Near Term / Future recommendations)
6. Findings (severity-led overview)
7. Capability Assessments (optional Analysis Intelligence packs)
8. Phased Modernization Plan (when roadmap pack present)
9. Modernization Advisor (only when enrichment is present)
10. Technical Appendix (repository, evidence, artifacts, metadata)

## Executive dashboard cards

Factual, evidence-backed values only (no composite “health” or “readiness” scores):

| Card | Source | Display |
| ---- | ------ | ------- |
| Files | Repository file count | integer |
| Technologies | Detected technologies | integer |
| Findings | Phase 3 / Phase 1 findings count | integer |
| Recommendations | Recommendation count | integer |
| Test Files Detected | `StructureFacts.test_file_count` / `has_tests` | count, Detected, Not detected, or Unknown |
| CI/CD | `CicdFacts.has_ci` / `pipeline_count` | Detected, Not detected, or Unknown |
| Cloud Enablement Signals | Seven cloud flags | `N of 7` + Established / Partial / Not detected, or Unknown |
| Repository Size | File count | `N files` |
| Highest Finding Severity | Max finding severity | Critical…Informational, None Detected, or Unknown |

Cloud signals counted: Docker, Kubernetes, Helm, Terraform, CloudFormation, Serverless, Docker Compose.

## Boundaries

* Renderer performs HTML/CSS only — no analysis re-run
* Must not invent or rewrite findings/recommendations
* Absolute host paths are not leaked into customer HTML
* JSON artifact contracts are unchanged by presentation redesign
* `CustomerReportDocument` is renderer-neutral (HTML today; PDF/Markdown later)
* `ModernizationHTMLReportRenderer` is a thin facade over this renderer

See also [architecture/html-report-v2.md](architecture/html-report-v2.md).
