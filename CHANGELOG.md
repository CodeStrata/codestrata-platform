# Changelog

All notable changes to CodeStrata are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
* Docs: [engine/docs/runtime-performance.md](engine/docs/runtime-performance.md)

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
