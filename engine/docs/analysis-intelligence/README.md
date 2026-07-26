# Analysis Intelligence

Phase 4 of CodeStrata.

| Milestone | Status |
| --------- | ------ |
| 4.1 Shared Rule Platform | Implemented (infrastructure) |
| 4.1.1 Rule Platform Integration Bridge | Complete |
| 4.1.2 CodeStrata Assessment Framework | Complete (methodology) |
| 4.2 Architecture Intelligence | Complete (4.2.1–4.2.5) |
| 4.3 Technical Debt Intelligence | Complete (4.3.1–4.3.6) |
| 4.4 Dependency Intelligence | Complete through report integration |
| 4.5 Security Intelligence | Complete through report integration |
| 4.6 Test Intelligence | Complete through report integration |
| 4.7 Cloud Intelligence | Complete (4.7.1–4.7.6) |
| 4.8 AI Readiness Intelligence | Complete (4.8.1–4.8.6) |
| 4.9 Performance Intelligence | Complete through report integration |
| 4.10 Modernization Intelligence | See Phase 5.10 modernization roadmap |

Canonical phase status: [ROADMAP.md](../../../ROADMAP.md).

## Phase 4.1

The Shared Rule Platform provides deterministic rule identity, registration,
planning, execution, evidence, suppression, finding mapping, telemetry, and
explainability. It is **disabled by default** and **not wired into**
`codestrata assess`.

Production Assessment Graph rules continue to use the existing
`services/rule_engine.RuleEngine` path.

See [shared-rule-platform.md](shared-rule-platform.md).

## Phase 4.1.1

Compatibility bridge between legacy `RuleEngine` and the Shared Rule Platform:

- `LegacyRuleAdapter`
- `RuleExecutionFacade`
- Finding-preserving `evaluate_adapted`

Assessment behaviour is unchanged. See
[rule-platform-migration.md](rule-platform-migration.md).

## Phase 4.1.2

Assessment methodology for dimensions, taxonomy, evidence, confidence, scoring
design, prioritization, and CTO report structure. No production rules or scoring
wired into assessment. See
[../assessment-framework/README.md](../assessment-framework/README.md).

## Phase 4.2.1

Initial Architecture Intelligence pack `architecture.core` (7 production SharedRules).
Discoverable via CLI/MCP; merged into `codestrata assess` only when
`[rules] enabled` and `[rules.architecture] enabled`. See
[architecture/README.md](architecture/README.md).

## Phase 4.2.2

Language Evidence Provider Foundation: normalized providers collect facts;
shared architecture rules remain language-independent. Pipeline disabled by
default. See [evidence-providers/README.md](evidence-providers/README.md).

## Phase 4.2.4

Architecture assessment section integration. See [architecture-assessment/README.md](architecture-assessment/README.md).

## Phase 4.2.5

Architecture CTO report integration: assessment section → report adapter →
`report.json` / HTML. See [architecture-reporting/README.md](architecture-reporting/README.md).

## Phase 4.3.1

Technical Debt domain foundation: taxonomy, assessment section contracts,
feature gates, empty/disabled sections. No production debt rules yet. See
[technical-debt/README.md](technical-debt/README.md).

## Phase 4.3.2

Complexity evidence collectors (Language Evidence Platform): Python `ast` and
Java structural scan. Explicit metric availability; `.codestrata` excluded. See
[technical-debt/complexity-evidence.md](technical-debt/complexity-evidence.md).

## Phase 4.3.3

Technical Debt complexity SharedRules (`technical_debt.core`) consume complexity
evidence and emit deterministic findings. See
[technical-debt/complexity-rules.md](technical-debt/complexity-rules.md).

## Phase 4.3.4

Technical Debt complexity assessment vertical: assess orchestration, feature
gates, section artifact, and dogfood review. See
[technical-debt/complexity-assessment.md](technical-debt/complexity-assessment.md).

## Phase 4.3.5

Technical Debt assessment synthesis: deterministic themes, concentration facts,
conclusions, and recommendations from the production-primary inventory. See
[technical-debt/synthesis.md](technical-debt/synthesis.md).

## Phase 4.3.6

Technical Debt CTO report integration: assessment section → report adapter →
`report.json` / HTML. See
[technical-debt-reporting/README.md](technical-debt-reporting/README.md).

## Phase 4.4.1

Dependency Intelligence domain foundation: engineering-role taxonomy,
assessment section contracts, feature gates, empty/disabled sections. No
manifest parsing or production dependency rules yet. See
[dependency/README.md](dependency/README.md).

## Phase 4.4.2

Dependency Evidence Platform: deterministic Maven/Gradle/Python manifest
collectors and `dependency-evidence.json`. See
[dependency/evidence.md](dependency/evidence.md).

## Phase 4.4.6

Dependency CTO report integration: assessment section → report adapter →
`report.json` / HTML (`assessment.dependency`, anchor `dependency-assessment`).
See [dependency/report.md](dependency/report.md).

## Phase 4.5.1

Security Intelligence domain foundation: taxonomy, assessment lifecycle,
feature gates, empty/disabled sections, deterministic
`security-assessment.json`. No security scanning yet. See
[security/README.md](security/README.md) and
[../architecture/analysis-intelligence-conventions.md](../architecture/analysis-intelligence-conventions.md).

## Phase 4.5.3

Security hygiene rules (`security.core` 1.0.0) consume repository-sensitive
evidence and emit shared Findings into `security-assessment` **1.1.0**.
No inventory, synthesis, or CTO report integration. See
[security/hygiene-rules.md](security/hygiene-rules.md).

## Phase 4.5.6

Security Intelligence report integration: presentation-only
`SecurityReportAdapter` projects `SecurityAssessmentSection` into
`report.security` 1.0.0 for optional `assessment.security` in `report.json`
and HTML `#security-assessment`. Gate
`[report.sections.security] enabled = false` by default. No re-analysis,
scores, or compliance claims. See [security/report.md](security/report.md).

## Phase 4.6.1

Test Intelligence domain foundation: taxonomy, assessment lifecycle, feature
gates, empty/disabled sections, deterministic `testing-assessment.json`. No
test discovery, framework detection, or Findings yet. See
[testing/README.md](testing/README.md).

## Phase 4.6.2

Repository Test Evidence (platform): deterministic
`repository-testing-evidence.json` **1.0.0** for repository-observable testing
structure and configuration facts. Disabled by default via
`[evidence.repository_testing]`. Not owned by Test Intelligence; no Findings,
rules, assessment, report, or test execution. See
[repository-test-evidence.md](repository-test-evidence.md).

## Phase 4.6.3

Test Hygiene rules (`testing.core` 1.0.0) consume repository-testing evidence
and emit shared Findings into `testing-assessment` **1.0.0**. Four rules
registered (TEST-001/002/003/005); TEST-004 deferred. No inventory, synthesis,
or CTO report integration. See [testing/hygiene-rules.md](testing/hygiene-rules.md).

## Phase 4.9.1

Performance Intelligence domain foundation: taxonomy, assessment lifecycle,
feature gates, empty/disabled sections, deterministic
`performance-assessment.json`. No evidence, rules, Findings, inventory
population, synthesis, or reporting yet. See
[performance/README.md](performance/README.md).

## Phase 4.9.2

Repository Performance Evidence: platform
`repository-performance-evidence` **1.0.0** for repository-observable
performance signals (eight families). Disabled by default; independent of
`[analysis.performance]`. No Findings, rules, scoring, inventory population,
synthesis, or reporting. See
[repository-performance-evidence.md](repository-performance-evidence.md).

## Phase 4.9.3

Performance Hygiene Rules: `performance.core` **1.0.0** with **20** observation-
only SharedRules (PERF-001 … PERF-072). Consumes in-memory
`AggregatedRepositoryPerformanceEvidence` only; emits shared Findings with
`FindingCategory.PERFORMANCE`. Disabled by default. No inventory, synthesis,
scoring, reporting, or new collectors. See
[performance/hygiene-rules.md](performance/hygiene-rules.md).

## Phase 4.9.4

Performance Assessment Inventory: `performance-assessment` **1.1.0** projects
deterministic inventories (`finding_inventory`, `rule_inventory`,
`severity_inventory`, `confidence_inventory`, `performance_family_inventory`)
over Hygiene Findings and rule-execution facts. No synthesis, scoring,
reporting, new evidence, or new rules. See
[performance/inventory.md](performance/inventory.md).

## Phase 4.9.5

Deterministic Performance Synthesis: `performance-assessment` **1.2.0** /
synthesis **1.0.0** derives themes, conclusions, recommendations, and an
overall posture summary from inventories, Findings, and rule-execution facts
only. No report integration, AI, scoring, new evidence, or new rules. See
[performance/synthesis.md](performance/synthesis.md).

## Phase 4.9.6

Performance Report Integration: presentation-only `report.performance`
**1.0.0** projects in-memory `PerformanceAssessmentSection` into
`assessment.performance` (`report.json`) and HTML **Performance Intelligence**
(`#performance-assessment`). Disabled by default. No re-analysis, AI, scoring,
or report-side analytical logic. See
[performance/report.md](performance/report.md).
