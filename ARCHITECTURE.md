# CodeStrata Architecture

**Audience:** Monorepo maintainers and integrators.  
**Version:** 0.1.0

This document is the **ecosystem / monorepo architecture map** for
`codestrata-platform`. It is not the public documentation portal architecture.

| Document | Role |
| -------- | ---- |
| **This file** | Monorepo layout, Engine↔Platform boundary, implementation map |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Public docs portal (VitePress) architecture |
| [`governance/constitution/`](governance/constitution/) | Normative product principles |
| [`knowledge/`](knowledge/) | Engineering knowledge concepts |
| [`docs/`](docs/) | Public Community documentation portal |

**Normative principles:** [governance/constitution/](governance/constitution/)  
**Engineering concepts:** [knowledge/](knowledge/)

> Product direction historically tracked in [ROADMAP.md](ROADMAP.md) is marked as an
> **archive candidate** — prefer [CHANGELOG.md](CHANGELOG.md) for completed work and
> governance reports for audits.

## Monorepo layout

```text
codestrata-platform/          # private source of truth
├── engine/                   # Community Engine → public codestrata-engine
├── examples/                 # real-world showcases → public codestrata-examples
├── test-fixtures/            # internal language samples (not in examples export)
├── docs/                     # Public documentation portal → codestrata-docs
├── cursor-plugin/            # Community Cursor extension → codestrata-cursor
├── vscode-plugin/            # Community VS Code extension → codestrata-vscode
├── platform/                 # private Platform (RAG, KG, commercial EI, Community Cloud API)
├── infrastructure/           # private OpenTofu AWS deployment (extractable → codestrata-infrastructure)
├── scripts/                  # verify_release, export, security, showcase wrappers
├── public-export-manifest.yaml
└── tests/architecture/       # engine↔platform + commercial intelligence boundary tests
```

Public mirrors are generated; see [platform/README.md](platform/README.md)
(maintainer handbook — export / validate / publish).
Engine runtime must not depend on `platform/`. Security posture:
[engine/docs/security/threat-model.md](engine/docs/security/threat-model.md).

### Commercial Engineering Intelligence boundary

- **Engine / Community Edition:** single-repository assessment only
  (`report.json`, schema 1.2). No portfolio / multi-repository commercial report.
- **Platform:** owns `codestrata_platform.intelligence_reporting` (dataset
  ingestion, aggregation, technology/capability/patterns/modernization, quality,
  drill-downs, website-safe export, OSS demonstration under `platform/demo/`).
- **Public export:** `public-export-manifest.yaml` excludes `platform/**`.
- Details: [platform/docs/intelligence-reporting/commercial-boundary.md](platform/docs/intelligence-reporting/commercial-boundary.md).

### Community Cloud API boundary

- **Platform** owns the versioned Community Cloud HTTP API
  (`codestrata_platform.community_cloud_api`, root `/api/v1`).
- **Engine / Community Edition** remain unaware of this package; future clients
  call over HTTP only (no Platform imports in Community).
- **Infrastructure** (`infrastructure/`) owns private serverless deployment for
  Community Cloud (API Gateway HTTP API → one Lambda → ASGI app). Application
  logic stays in Platform; cloud resources stay in `infrastructure/`.
- Slice 7.14 creates a **production infrastructure foundation**: health is
  deployable; ingestion remains fail-closed without production credential
  verification, shared event identity, and event sinks. Community Data Lake
  resources are deferred to a future `infrastructure/modules/data-lake` module.
- The Slice 7.14 deployment proves that the Community Cloud API can be packaged
  and served through serverless infrastructure. It does not enable durable
  Community event ingestion because production credential verification, shared
  event identity, and event sinks are not yet configured.
- Slice 7.15 (final Epic 7 slice) verifies the combined request pipeline with
  in-memory adapters only; it adds no product capabilities and does not start
  Epic 8.
- Details: [platform/docs/community-cloud-api/README.md](platform/docs/community-cloud-api/README.md),
  [verification-e2e.md](platform/docs/community-cloud-api/verification-e2e.md),
  [infrastructure/README.md](infrastructure/README.md),
  [request-validation.md](platform/docs/community-cloud-api/request-validation.md),
  [payload-size-limits.md](platform/docs/community-cloud-api/payload-size-limits.md),
  [structured-logging.md](platform/docs/community-cloud-api/structured-logging.md),
  [retry-safe-event-identifiers.md](platform/docs/community-cloud-api/retry-safe-event-identifiers.md).

Current product direction: [ROADMAP.md](ROADMAP.md).
Completed releases: [CHANGELOG.md](CHANGELOG.md).

## Purpose

CodeStrata analyzes application repositories and produces evidence-based modernization
assessments. Deterministic analysis discovers technologies, graphs, findings, and
recommendations. Optional AI enrichment adds a narrative over that evidence—never
inventing facts.

## Engineering philosophy

> **Deterministic analysis first. AI reasoning second.**

Normative statement and AI rules:
[governance/constitution/002_ENGINEERING_CONSTITUTION.md](governance/constitution/002_ENGINEERING_CONSTITUTION.md),
[governance/constitution/007_AI_PHILOSOPHY.md](governance/constitution/007_AI_PHILOSOPHY.md).

Benefits: repeatable analysis, explainable findings, lower hallucination risk,
budgeted token use, clear separation between facts and interpretation, and useful
output when AI is unavailable or fails.

## End-to-end assess pipeline

```text
                    codestrata.toml / CLI
                           │
                           ▼
              Local path or GitHub clone
                           │
                           ▼
         Phase 1 AnalysisService (detect + analyzers + optional PMD)
                           │
                           ▼
              Repository Inventory → Repository Graph
                           │
                           ▼
         Knowledge Pipeline ← Engineering Knowledge Graph
                           │
                           ▼
                   Assessment Graph
                           │
                           ▼
              Rule Engine → findings.json
                           │
                           ▼
         Recommendation Engine → recommendations.json
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
     HTML Report v2 + report.json   optional AI enrichment
                                        │
                                        ▼
                                 advisor.json
```

Topic docs: [engine/docs/runtime.md](engine/docs/runtime.md) (includes performance
controls) and siblings under [engine/docs/](engine/docs/).

## Design principles

### Separation of responsibilities

| Layer | Responsibility |
| ----- | -------------- |
| Scanners | Acquire source (local / GitHub). Assess uses ephemeral temp clones for GitHub URLs and always cleans them up; local paths are never deleted. |
| Detectors / analyzers | Phase 1 facts and analyzer findings |
| StaticAnalysisService | External providers (PMD today) |
| Inventory / graphs | Repository Graph, EKG, Assessment Graph |
| Rule Engine | Deterministic Phase 3 findings |
| Recommendation Engine | Deterministic Phase 3 recommendations |
| AI enrichment | Exactly one Bedrock call; narrative only |
| Knowledge store | Durable repository identity, snapshots, runs, immutable artifacts (SQLite) |
| Reporting | HTML Report v2 + JSON artifacts |
| Application | `AssessmentApplicationService` orchestration; knowledge ports/session; Agent Framework |
| CLI | Config, thin adapters, artifact retention |
| MCP | FastMCP tools/resources/prompts over application services |

### Evidence and immutability

* Findings and recommendations carry structured evidence and stable IDs.
* Graphs are immutable projections; rules never mutate them.
* AI may reference finding/recommendation IDs; it must not rewrite those artifacts.

## Modes

| Mode | AI calls | Artifacts |
| ---- | -------- | --------- |
| Deterministic (`--no-ai`) | 0 | Graphs, findings, recommendations, HTML/JSON |
| AI (`--with-ai`) | exactly 1 | Same + `advisor.json` on success |

AI enrichment failure warns and keeps deterministic output (CLI exit 0).

## Phase 1 analysis (shared)

```text
Repository
    → Technology detection
    → CompositeAnalyzer (ordered analyzers)
    → optional StaticAnalysisService (PMD)
    → Phase 1 RecommendationEngine
    → AnalysisResult
```

`codestrata scan` reports `AnalysisResult` as text/JSON/HTML under `reports/`.
`codestrata assess` continues into graphs → Phase 3 rules → recommendations → optional
AI → HTML Report v2.

### Analyzer order

1. RepositoryMetricsAnalyzer
2. BuildDiscoveryAnalyzer
3. BuildMetadataAnalyzer
4. DependencyDiscoveryAnalyzer
5. DependencyMetadataAnalyzer
6. DependencyHealthAnalyzer
7. CicdDiscoveryAnalyzer
8. SecurityAnalyzer
9. ArchitectureAnalyzer
10. CloudReadinessAnalyzer

### Static analysis (PMD)

```text
PMD XML → parser → observations → mapping/visibility → groups → Finding cards
```

Profiles: `focused` · `standard` · `comprehensive`. Critical/high findings are
never suppressed from HTML.

Future providers implement `StaticAnalysisProvider` and normalize into CodeStrata
observations/findings without changing orchestration ownership.

## Graphs

| Graph | Role |
| ----- | ---- |
| Repository Graph | Observations about one repository |
| Engineering Knowledge Graph | Reusable concepts (no repo identity) |
| Assessment Graph | Per-run projection/reference join |

See [docs/repository-graph.md](engine/docs/repository-graph.md) and
[docs/assessment-graph.md](engine/docs/assessment-graph.md).

## Rules and recommendations

```text
Assessment Graph → Rule Engine → findings.json
                              → Recommendation Engine → recommendations.json
```

No AI in either engine. Details: [docs/rule-engine.md](engine/docs/rule-engine.md),
[docs/recommendation-engine.md](engine/docs/recommendation-engine.md).

## AI enrichment

One Bedrock Converse call over a compact, budgeted context. Output validates
referenced finding and recommendation IDs. See [docs/ai-enrichment.md](engine/docs/ai-enrichment.md).

Legacy `ModernizationAssessmentAgent` / `AIRecommendationResult` remain for
compatibility and bridging into report contracts; the assess path uses
`AiEnrichmentService` for the one-call enrichment artifact.

## HTML Report v2

Presentation-only view-model + renderer. Sections separate deterministic findings
and recommendations from optional AI enrichment. See
[docs/report-generation.md](engine/docs/report-generation.md).

## Knowledge store (Phase 2B)

`AssessmentApplicationService` persists completed assessments side-by-side with
existing report artifacts:

```text
CLI → AssessmentApplicationService
        → full assessment pipeline (unchanged)
        → KnowledgeStore (snapshots, runs, content-addressed blobs)
        → existing report generation
```

Schema version 2 indexes repositories, snapshots, assessment runs, and artifact
metadata. Payloads live under `.codestrata/knowledge/blobs/` (SHA-256, atomic write).
Reports are never read back into the store. Persistence finalization failure
fails the assessment; incomplete runs are never “latest completed.” Default
assessment remains full recomputation; incremental execution is opt-in only
(see Phase 2F below).

## Repository Knowledge Layer (Phase 5.1–5.9) — Platform

RAG projection, embeddings, vector storage, retrieval, and grounded answering
are implemented in the private **Platform** package. Community Engine keeps
assessment contracts and extension entry points only.

Phase 6.5 formalizes Community-light extension contracts (`EXTENSION_API_VERSION`),
opt-in analyzer allowlists, registry-backed assess AI providers, and the
`ReportRenderer` protocol over `CustomerReportDocument`. See
[engine/docs/extension-architecture.md](engine/docs/extension-architecture.md).

See [platform/docs/rag/](platform/docs/rag/) (monorepo) and
[engine/docs/mcp/overview.md](engine/docs/mcp/overview.md) for assessment MCP.

### Query services (Increment 3)

`KnowledgeQueryService` (`codestrata.application.knowledge.queries`) is the
transport-neutral read API for durable knowledge. Future FastMCP, REST, CLI, and
agent adapters must call this service — not SQLite, blob paths, or report files.
Authoritative findings/recommendations are Phase 3 stable IDs. Snapshot
comparison uses persisted manifests. Graph component queries load immutable
graph JSON in memory with bounded depth (max 3).

### MCP adapter (Phase 2C)

`codestrata mcp serve` starts a stdio FastMCP server named **CodeStrata**. Tools and
resources are thin adapters over `KnowledgeQueryService` and
`AssessmentApplicationService`. See [docs/mcp-server.md](engine/docs/mcp-server.md).

### Agent Framework (Phase 2D / 2E)

`codestrata.application.agents` provides deterministic orchestration
(`AgentOrchestrator`, Knowledge / Assessment / Validation agents) over the same
application services. Phase 2E adds thin adapters:

- CLI: `codestrata agent review|assess|validate|compare|modernization-review`
- MCP: five `*_with_agents` tools

MCP and agents are sibling interfaces — agents must not call MCP internally.
Existing `codestrata assess` and the 20 granular MCP tools remain unchanged.

See [docs/agent-framework.md](engine/docs/agent-framework.md).

```text
CLI / MCP / REST
        │
        ├───────────────┐
        │               │
        ▼               ▼
Agent Framework    Application Services
        │               ▲
        └───────────────┘
```

### Incremental planning (Phase 2F.1)

`codestrata.application.incremental` classifies candidate vs previous manifests, analyzes
bounded impact, applies a conservative reuse policy, and emits a deterministic
`IncrementalAssessmentPlan`.

### Incremental execution (Phase 2F.2)

`IncrementalAssessmentExecutor` optionally executes eligible plans via inventory
merge + stage rebuild through the existing assessment pipeline, or falls back to
a normal full assessment. **`codestrata assess` remains a full rebuild by default**;
execution requires explicit opt-in.

### Incremental operations (Phase 2F.3)

Post-execution validation, semantic equivalence, metrics, explainability, and
persisted `IncrementalExecutionRecord` provenance. Controlled rollout via
`[incremental].rollout_mode` (default `off`; production target `opt_in`).

Thin adapters:

- CLI: `codestrata incremental plan|assess|explain`
- MCP: four additive incremental tools

```text
IncrementalAssessmentPlan
        → IncrementalAssessmentExecutor
        → Complete normal assessment result
        → Validation + metrics + explanations
        → IncrementalExecutionRecord → CLI / MCP
```

Details: [docs/incremental-assessment.md](engine/docs/incremental-assessment.md),
[docs/knowledge-store.md](engine/docs/knowledge-store.md).

### Engineering Knowledge Graph (Platform)

YAML-declared organization architecture (organizations, applications, ownership,
standards) linked to CodeStrata repositories and assessments. Optional
CodeStrata Platform capability (CLI group `enterprise` retained for
compatibility); disabled by default. No graph database.

```text
Declared YAML → validate → Engineering Knowledge Graph → CLI / MCP queries
```

Details: [platform/docs/knowledge_graph/README.md](platform/docs/knowledge_graph/README.md),
[ROADMAP.md](ROADMAP.md).

### Shared Rule Platform (Phase 4.1)

Transport-neutral rule infrastructure for future Analysis Intelligence packs.
Distinct from the Assessment Graph `RuleEngine` used by `codestrata assess`.
Disabled by default; not wired into the default assessment pipeline.

```text
RuleExecutionContext → Registry → Planner → Executor → Finding mapper
```

Details: [docs/analysis-intelligence/shared-rule-platform.md](engine/docs/analysis-intelligence/shared-rule-platform.md).

### Rule Platform Integration Bridge (Phase 4.1.1)

`LegacyRuleAdapter` and `RuleExecutionFacade` connect the Assessment Graph
`RuleEngine` to the Shared Rule Platform without changing `codestrata assess`.
Adapted legacy evaluation preserves Finding IDs. See
[engine/docs/analysis-intelligence/shared-rule-platform.md](engine/docs/analysis-intelligence/shared-rule-platform.md).

### Assessment Framework

Methodology for dimensions, rule taxonomy, evidence/confidence, scoring design,
business impact vs severity, modernization waves, and CTO report structure.
Documentation for Community contributors lives under Engine shared-rule and
report docs (no separate assessment-framework tree in the Community export).
See [engine/docs/analysis-intelligence/shared-rule-platform.md](engine/docs/analysis-intelligence/shared-rule-platform.md)
and [engine/docs/report-generation.md](engine/docs/report-generation.md).

### Architecture Intelligence

Initial production pack `architecture.core` (v1.0.0) registers seven SharedRules.
Precision hardening includes architectural-unit selection (nested packages
collapsed), dependency normalization (parent/child, type-only, init/registration),
separated extraction vs classification coverage, and tighter coupling/direction
applicability. Discoverable via `codestrata rules` / MCP. Merged into `codestrata assess`
only when `[rules] enabled` and `[rules.architecture] enabled`.

Language Evidence Providers collect and normalize language facts for reuse by
shared architecture rules. The provider pipeline is **disabled by default**
(`[evidence.language] enabled = false`); when disabled, assessment behavior is
unchanged.

```text
paths + source texts → ArchitectureAnalysisView
        → RuleExecutionFacade.execute_shared
        → RuleFindingMapper → Finding (merged with legacy RuleEngine)

opt-in:
providers → AggregatedLanguageEvidence → ArchitectureAnalysisView
```

Details: [engine/docs/analysis-intelligence/shared-rule-platform.md](engine/docs/analysis-intelligence/shared-rule-platform.md)
and [engine/docs/rule-engine.md](engine/docs/rule-engine.md).

Architecture Conclusions: deterministic grouping and interpretation of
architecture findings into explainable conclusions and consolidated
recommendations. Disabled by default
(`[analysis.architecture_conclusions] enabled = false`). Findings remain
unchanged.

An optional Architecture Assessment section (`architecture-assessment.json`)
is composed from existing findings and optional conclusions. Disabled by
default (`[assessment.sections.architecture] enabled = false`).

That section can be projected into customer `report.json` and HTML via
`ArchitectureReportAdapter` (`assessment.architecture`). Disabled by default
(`[report.sections.architecture] enabled = false`). Schema remains additive.
No scoring or AI narrative. See
[engine/docs/report-generation.md](engine/docs/report-generation.md).

## Repository authentication

Private GitHub access uses credential **references** in config (`token_env`),
never secret values in TOML. Runtime credentials stay out of domain models and
reports. Authentication applies only to remote clones.

## Package layout (simplified)

```text
src/codestrata/
├── cli/                 # Typer: version, scan, assess, agent, incremental, mcp
├── config/
├── application/         # assessment, knowledge queries, agents, incremental planning
├── infrastructure/      # SQLite knowledge store, blobs, in-memory vector store
├── interfaces/          # FastMCP (and future REST) adapters
├── models/              # Phase 1 domain DTOs
├── domain/              # graphs, findings, recommendations, repository knowledge
├── services/            # analysis, inventory, knowledge, assessment
├── static_analysis/     # PMD provider boundary
├── ai/                  # enrichment + legacy agent / providers
├── reporters/           # codestrata scan reporters
├── reporting/           # assess HTML/JSON (incl. html_v2/)
└── repository_auth/
```

## Configuration

Primary file: `codestrata.toml` (repository, AWS, AI, static analysis, reporting).
Secrets belong in environment / `.env` (gitignored), never in committed config.

## Retention

Completed assess/scan runs keep the latest **three** per repository name; older
run directories are pruned after successful writes. Report retention does **not**
delete knowledge-store rows or blobs (knowledge retention is deferred).

## Out of scope for v0.1.0

* Multi-step agent / MCP tool loops for enrichment
* Lockfile-complete dependency resolution
* Assisted code refactoring
* Hosted SaaS control plane

## Related documents

* [README.md](README.md) — product overview and quick start
* [docs/](engine/docs/) — canonical topic documentation
* [CHANGELOG.md](CHANGELOG.md) — release notes
* [examples/README.md](examples/README.md) — commands and expected outputs
