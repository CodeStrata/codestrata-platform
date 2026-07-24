# Phase 4.4 — Dependency Intelligence Acceptance Review

**Date:** 2026-07-24  
**Scope:** Phases 4.4.1 through 4.4.6  
**Verdict:** **Accept Phase 4.4** as complete for the Dependency Intelligence
vertical through CTO report integration.

## Architecture boundaries

| Boundary | Disposition |
| -------- | ----------- |
| Evidence owns parsing | Held: collectors under `evidence/dependency`; intelligence consumes facts |
| Assessment owns inventory + synthesis | Held: section schema **1.2.0** |
| Report owns presentation only | Held: `DependencyReportAdapter` does not reparse/recollect/re-run rules |
| No generic IntelligencePack / report-pack abstraction | Held |
| Gates independent and default-off | Held: evidence, rules, assessment, report |

## Evidence ownership

- Maven / Gradle / Python declared manifests → `dependency-evidence.json`
- Declared ≠ resolved; Gradle interpolations are diagnostics
- No registry / network / CVE / license data

## Rule precision

- Five hygiene SharedRules under `dependency.core`
- Unresolved findings only when `version_resolution_status == proven_unresolved`
  (Phase 4.4.3A)
- `org.webjars.npm:*` does not imply npm ecosystem coverage gaps

## Production-primary inventory

- Primary `finding_ids` are production-only
- Complete inventory retained in `all_finding_*`
- Hotspots are presentation-ordered, not prioritized

## Synthesis traceability

- Themes / conclusions / recommendations inventory-derived
- Recommendation → conclusion → theme/finding/hotspot/manifest/diagnostic edges
- No scores, fabricated priorities, effort/financial claims

## Report accuracy (4.4.6)

| Check | Result |
| ----- | ------ |
| Adapter presentation-only | Pass |
| JSON additive `assessment.dependency` under schema 1.2 | Pass |
| HTML after Technical Debt; anchor `dependency-assessment` | Pass |
| Production vs test separation | Pass (CodeStrata dogfood) |
| Zero-production wording | Pass |
| Declared-only / unsupported Gradle wording | Pass |
| Adapter failure isolation | Pass (pattern + tests) |
| Report gate default disabled + independent | Pass |

## Determinism

- Assessment artifacts and report dependency sections identical across repeat
  dogfood runs for CodeStrata and Spring Petclinic

## Dogfood

| Repository | Assessment | Report | Notes |
| ---------- | ---------- | ------ | ----- |
| CodeStrata | succeeded; 0 production / 2 test findings | succeeded | Test observations separate |
| Spring Petclinic | succeeded; 0 findings; 65 declarations | succeeded | Plugins vs active separated; Gradle diagnostics non-findings |

See [PHASE_4_4_6_DEPENDENCY_REPORT_DOGFOOD_REVIEW.md](PHASE_4_4_6_DEPENDENCY_REPORT_DOGFOOD_REVIEW.md).

## Explicit limitations

1. Declared-manifest coverage only (no resolved/transitive graph)
2. No npm evidence collection beyond coordinate naming
3. No DependencyRole / framework classification
4. No latest-version, outdated, CVE, or license analysis
5. No composite scores or modernization priority ranking
6. No dependency CLI/MCP commands
7. Report section disabled by default

## Known future work

- Security Intelligence consuming the same Dependency Evidence
- Broader Gradle resolution inspection (without promoting diagnostics to findings
  until proven)
- npm / additional ecosystem evidence collectors
- Optional resolved-graph analysis as a separate capability
