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
| `advisor.json` | Optional Modernization Advisor narrative |
| `advisor-execution.json` | Internal Advisor provider/model/status/errors |

## Sections (HTML v3 — Design System aligned)

Brand and layout follow the CodeStrata Design System (tokens mirrored in the
public docs portal).

1. Cover (brand, edition, repository, KPIs)
2. Contents (TOC)
3. Executive Summary
4. Repository Overview
5. Assessment Summary (verdict, takeaways, risks)
6. Domain Intelligence (optional capability packs)
7. Findings (cross-domain insights)
8. Recommendations (Priority Actions + opportunities)
9. Engineering Assessment Conclusion
10. Implementation Sequence (Engine assess roadmap section — not Platform Strategic Roadmap)
11. Optional AI Enhancements (when AI enrichment present)
12. Technical Appendix (evidence, graphs, artifacts, rule IDs)

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
