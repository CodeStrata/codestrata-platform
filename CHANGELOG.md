# Changelog

All notable changes to CodeStrata are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-08-14

Community Edition patch freeze on accepted candidate `e818ae6f`. Publication
(CLI registry, Marketplace, backend deploy) remains a separate step.

### Engine / CLI 0.2.1

* Consent v2 (lifecycle + privacy-safe assessment intelligence)
* Privacy protections and transparency documentation alignment
* Report favicon (embedded data URI)
* Public report feedback CSP/acknowledgement fix (Platform + Reports Worker)

### VS Code 0.2.2

* Shared Engine CLI consent (v2) via telemetry CLI; session `--telemetry-allow`
  is not consent
* Marketplace/README/PRIVACY wording aligned to Epic 20 contract

### Operations (not CLI package contents)

* Insights first-load reliability (authenticated session gate + loading state)
* Clean-runner CI gates for Insights and Reports Worker

### Validation notes

* Five representative frozen repos matched baselines exactly
* Full 22-repo corpus rerun not required (presentation / UX / delivery / CI only
  after Construction exit)
* No graph telemetry; no numeric assessment score collection; no source upload

## [0.2.0] - 2026-08-11

Community Edition cut. Publication (GitHub Release, CLI registry, Marketplace)
is a separate step and is not implied by this changelog.

### Added

* Deterministic multi-head Engineering Assessment with Assessment Overview
* Community report publishing with opaque public report URLs
* Privacy-first telemetry consent and Community Sentiment
* Insights and Community Cloud
* VS Code extension as Marketplace distribution (source private)
* Documentation and data-collection transparency pages
* Provider platform (Bedrock live E2E passed; OpenAI/OpenRouter supported with
  qualification — owner live E2E not completed)
* System Verification SV.1–SV.16 release-artifact evidence for the curated
  22-repository public OSS release-validation dataset
* Platform Engineering Intelligence, website-safe export, Community Cloud API
  foundation, and infrastructure packaging verification (no AWS apply)

### Changed

* Engine Community package version set to 0.2.0 for the release cut
* Platform runtime dependency constraint updated to `codestrata>=0.2.0`

### Added

* Phase 6.2 GitHub Repository Acquisition: assess clones GitHub URLs into a
  unique ephemeral temp workspace (shallow `--depth 1`); always cleanup in
  `finally` (success, failure, interrupt); local checkouts never deleted —
  Engine assessment pipeline unchanged
* Phase 6.5 Extensibility & Integration: `EXTENSION_API_VERSION`; Analyzer /
  Assess AI / ReportRenderer contracts; registry-backed assess providers
  (Bedrock/OpenAI parity); `[extensions.analyzers].enabled` allowlist;
  `codestrata extensions list`; `doctor --extensions`; reserved namespaces
  docs — Engine deterministic pipeline unchanged
* Phase 6.4 Developer Workflow: `codestrata init`, `codestrata doctor`,
  `codestrata examples`; assess `--quiet` / `--json-summary`; richer
  `codestrata version`; sample GitHub Action; Quick start docs — Engine
  assessment pipeline unchanged
* Phase 6.3 Customer Report Experience: `CustomerReportDocument` presentation
  model; Key Takeaways; Engineering Modernization Assessment; Priority Actions;
  TOC; cover metadata (report/engine/advisor versions); print stylesheet; HTML
  report version 3.0 — Engine assessment pipeline unchanged
* Phase 6.1 Modernization Advisor: unify assess `--with-ai` on
  `AiEnrichmentResult`; Bedrock + OpenAI provider factory; advisor metadata
  (model, provider, advisor/prompt version, generated timestamp); HTML/JSON
  consume the same domain model; CTO/VP advisor persona; fail-soft preserved

### Changed

* Phase 5.27.4 scripts architecture review: remove phase dogfood scripts and
  CLI-duplicate `mvp_acceptance.py`; add canonical `scripts/verify_release.py`;
  rename showcase wrappers to `fetch_example.py` / `run_showcase.py`; fix
  `clean_install_smoke.py` to build the Engine package from `engine/` and to
  exercise Engine MCP via `mcp tools` (not Platform-only `repository_health`)
* Phase 5.27.3 root documentation and roadmap review: root `README.md` is the
  private monorepo entry point; `ROADMAP.md` slimmed to current direction
  (Phase 5 complete, Phase 6.1–6.5 MVP, post-MVP deferred); root `docs/`
  already removed (export policy in `platform/README.md`)

### Added

* Phase 5.27.3 root documentation folder review: remove redundant root `docs/`
  (export policy merged into `platform/README.md`; completed AIMF rename archive
  deleted)
* Phase 5.27.2 archive review: delete one-time Phase 4 acceptance/dogfood
  reviews and superseded design drafts; keep rename record only
* Phase 5.27.1 Platform maintainer handbook: convert `platform/README.md` into
  the private ecosystem operations guide (layout, export, validation, release)
* Phase 5.27 public repository documentation review: rewrite Engine, Examples,
  and Platform READMEs for open-source clarity (audience, ecosystem map,
  export-safe paths, showcase portable scripts)
* Phase 5.26.4 final documentation clarification: rename Analysis Intelligence
  conventions doc; add Platform `docs/getting-started.md`
* Phase 5.26.3 documentation audit and curation: archive historical reviews /
  design / AIMF rename under `docs/archive/` (later removed in 5.27.2–5.27.3);
  move RAG docs to `platform/docs/rag/`; root `CONTRIBUTING.md`; Engine docs
  index ownership cleanup
* Phase 5.26.2 separate test fixtures from community examples: move
  `sample-*-app` and `sample-reports` to `test-fixtures/`; public
  `codestrata-examples` is real-world showcases only
* Phase 5.25 real-world open-source showcase framework: manifests with pinned
  commit SHAs, safe fetch under `.codestrata-examples/`, opt-in showcase assess,
  THIRD_PARTY attribution, curated expected-results, offline unit tests
* Phase 5.24.2 legacy AIMF and generated-artifact cleanup: remove root
  `src/aimf` duplicate models; tighten public-export excludes; fix
  AssessmentCommandResult Pydantic after-validator warning
* Phase 5.24.1 Platform capability reconciliation: move implemented RAG and
  persistent Knowledge Graph into `platform/`; Engine keeps assessment contracts
  and extension entry points only; delete fictional university workspace;
  Platform packaging + architecture/no-university tests
* Phase 5.24 security and production hardening: threat model, security
  architecture notes, production checklist; `scripts/security_check.py`;
  symlink-safe repository walk; Community export excludes Enterprise KG
  runtime; `codestrata.extensions` hook; security tests
* Phase 5.23 monorepo organization: `engine/`, `examples/`, `platform/`,
  `cursor-plugin/`, `vscode-plugin/` placeholders; public export manifest;
  `scripts/export-public-repos.py` and `scripts/validate-public-exports.py`;
  engine/platform boundary tests; export policy now in [platform/README.md](platform/README.md)
* Phase 5.22 Community Edition packaging: CE scope, public release checklist,
  NOTICE/SUPPORT, 0.1.0 release notes draft, sample reports for five languages,
  README badges and Community vs Enterprise matrix
* Phase 5.21 documentation and developer experience: quick start, installation,
  architecture guide, CLI reference, report interpretation, troubleshooting,
  contributor guide, end-to-end tutorial; Java + Python sample apps; documentation
  validation tests (`tests/docs`)
* Phase 5.20 execution profiles (`community`, `local`, `enterprise`, `bedrock`,
  `openai`) with CLI > env > TOML > profile-default precedence
* `codestrata config profile|validate|effective|show` (secret-safe dumps)
* Docs: [engine/docs/configuration-profiles.md](engine/docs/configuration-profiles.md)

* Phase 5.19 runtime performance controls (`analysis.runtime`): shared source-text
  cache, bounded file-read workers, source-file/char limits, and peak-RSS timing
* Deterministic benchmark harness (`scripts/bench_runtime_performance.py`) and
  report under `reports/performance-benchmark/`
* Docs: [engine/docs/runtime.md](engine/docs/runtime.md)

### Changed

* Report generation renders HTML once (no double-render) when timing is present
* Architecture and technical-debt packs reuse a shared source-text map when enabled
* `load_settings` applies execution-profile defaults and environment overlays
* Root CLI help points at quick-start / CLI reference / troubleshooting docs
* Release-readiness docs use `codestrata-*.whl` (not legacy package names)

## [0.1.0] - 2026-07-22

### Added

* CLI (`codestrata version`, `codestrata scan`, `codestrata assess`) with local and GitHub sources
* Analysis: detection, analyzers, optional PMD static analysis
* Repository Inventory, Repository Graph, Engineering Knowledge Graph
* Knowledge Pipeline and Assessment Graph
* Dependency and version extraction (Maven / npm manifests)
* Deterministic Rule Engine → `findings.json`
* Deterministic Recommendation Engine → `recommendations.json`
* Optional one-call Bedrock AI enrichment → `advisor.json`
* HTML Report (`report.html`) and companion `report.json`
* Deterministic mode (zero AI calls) and AI mode (exactly one call)
* Multi-language detection and evidence: Java, JavaScript/TypeScript, Python, PHP, C#/.NET
* Local knowledge store, optional MCP server extra, and Agent Framework
* Execution profiles (`community`, `local`, `enterprise`, `bedrock`, `openai`)
* Open-source documentation, examples, and community files for the Community Edition release

### Notes

* Deterministic findings and recommendations are the source of truth.
* AI enrichment is interpretive only and does not mutate deterministic artifacts.
* Community defaults include repository assessment, local graphs, deterministic
  rules, and HTML/JSON reports. Engineering Knowledge Graph organizational
  features and Platform services (SSO, billing, multi-tenancy) are not Community
  defaults.
* This release uses the **CodeStrata** package and CLI exclusively.
* Known limitations: alpha software status; many analysis packs are feature-gated
  and off by default; broader executive/CTO report methodology may be ahead of
  runtime presentation.
