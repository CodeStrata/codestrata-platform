# Changelog

All notable changes to CodeStrata are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
  engine/platform boundary tests; [docs/public-export.md](docs/public-export.md)
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
* Docs: [docs/configuration-profiles.md](docs/configuration-profiles.md)

* Phase 5.19 runtime performance controls (`analysis.runtime`): shared source-text
  cache, bounded file-read workers, source-file/char limits, and peak-RSS timing
* Deterministic benchmark harness (`scripts/bench_runtime_performance.py`) and
  report under `reports/performance-benchmark/`
* Docs: [docs/runtime-performance.md](docs/runtime-performance.md)

### Changed

* Report generation renders HTML once (no double-render) when timing is present
* Architecture and technical-debt packs reuse a shared source-text map when enabled
* `load_settings` applies execution-profile defaults and environment overlays
* Root CLI help points at quick-start / CLI reference / troubleshooting docs
* Release-readiness docs use `codestrata-*.whl` (not legacy package names)

## [0.1.0] - 2026-07-22

### Added

* CLI (`codestrata version`, `codestrata scan`, `codestrata assess`) with local and GitHub sources
* Phase 1 analysis: detection, analyzers, optional PMD static analysis
* Repository Inventory, Repository Graph, Engineering Knowledge Graph
* Knowledge Pipeline and Assessment Graph
* Dependency and version extraction (Maven / npm manifests)
* Deterministic Rule Engine → `findings.json`
* Deterministic Recommendation Engine → `recommendations.json`
* Optional one-call Bedrock AI enrichment → `ai-enrichment.json`
* HTML Report v2 (`report.html`) and companion `report.json`
* Deterministic mode (zero AI calls) and AI mode (exactly one call)
* Open-source documentation, examples, and community files for the MVP release

### Notes

* Deterministic findings and recommendations are the source of truth.
* AI enrichment is interpretive only and does not mutate deterministic artifacts.
