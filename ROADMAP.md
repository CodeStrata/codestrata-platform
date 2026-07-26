# CodeStrata Roadmap

## Phase 2 — Core Platform Foundation (complete)

Assessment, knowledge store, MCP, agents, incremental assessment.

## Phase 3 — Enterprise Knowledge Graph (complete)

YAML-based enterprise architecture model.

## Phase 4 — Analysis Intelligence

- **4.1 Shared Rule Platform** — implemented (infrastructure; disabled by default)
- **4.1.1 Rule Platform Integration Bridge** — complete (adapter + facade; assess unchanged)
- **4.1.2 CodeStrata Assessment Framework** — complete (methodology and contracts; no production scoring/rules)
- **4.2 Architecture Intelligence** — Complete (4.2.1–4.2.5; precision corrections accepted)
  - **4.2.1** Initial Architecture Rule Pack — Complete (`architecture.core` 1.0.0)
  - **4.2.1a** Architecture Rule Precision Hardening — Complete
  - **4.2.2** Language Evidence Provider Foundation — Complete
  - **4.2.3** Architecture Conclusions and Aggregation — Complete
  - **4.2.4** Architecture Assessment Integration — Complete
  - **4.2.5** CTO Report Integration — Complete
- **4.3 Technical Debt Intelligence** — Complete (4.3.1–4.3.6)
  - **4.3.1** Technical Debt Domain Foundation — Complete
  - **4.3.2** Complexity Evidence — Complete
  - **4.3.3** Complexity Rules & Findings — Complete
  - **4.3.4** Complexity Assessment Vertical and Dogfood — Complete
  - **4.3.4A** Complexity Precision and Inventory Usability — Complete
  - **4.3.5** Debt Assessment Synthesis — Complete
  - **4.3.6** Debt Report Integration — Complete
- **4.4 Dependency Intelligence** — Complete through CTO report integration
  - **4.4.1** Dependency Domain Foundation — Complete
  - **4.4.2** Dependency Evidence Platform — Complete
  - **4.4.3** Dependency Rules & Findings — Complete
  - **4.4.3A** Unresolved-version precision correction — Complete
  - **4.4.4** Dependency Inventory and Assessment Usability — Complete
  - **4.4.5** Dependency Assessment Synthesis — Complete
  - **4.4.6** Dependency CTO Report Integration — Complete
- **4.5 Security Intelligence** — Complete through report integration
  - **4.5.1** Security Domain Foundation — Complete
  - **4.5.2** Repository Security-Relevant Evidence Foundation — Complete
  - **4.5.3** Repository Security Hygiene Rules — Complete
  - **4.5.4** Security Assessment Inventory — Complete
  - **4.5.5** Deterministic Security Synthesis — Complete
  - **4.5.6** Security Intelligence Report Integration — Complete
- **4.6 Test Intelligence** — In Progress
  - **4.6.1** Test Intelligence Domain Foundation — Complete
  - **4.6.2** Repository Test Evidence Foundation — Complete (platform evidence; disabled by default)
  - **4.6.3** Test Hygiene Rules — Complete (`testing.core`; TEST-004 deferred)
  - **4.6.4** Test Assessment Inventory — Complete (`testing-assessment` 1.1.0)
  - **4.6.5** Deterministic Test Synthesis — Complete (`testing-assessment` 1.2.0)
  - **4.6.6** Test Report Integration — Complete (`report.testing` 1.0.0; default off)
- **4.7 Cloud Intelligence** — In Progress
  - **4.7.1** Cloud Intelligence Domain Foundation — Complete (`cloud-assessment` 1.0.0; analytically empty; default off)
  - **4.7.2** Cloud Repository Evidence — Complete (`repository-cloud-evidence` 1.0.0; platform evidence; default off)
  - **4.7.3** Cloud Intelligence Rules — Complete (`cloud.core` 1.0.0; 11 hygiene rules; default off)
  - **4.7.4** Cloud Assessment Inventory — Complete (`cloud-assessment` 1.1.0; default off)
  - **4.7.5** Deterministic Cloud Synthesis — Complete (`cloud-assessment` 1.2.0; default off)
  - **4.7.6** Cloud Report Integration — Complete (`report.cloud` 1.0.0; default off)
- **4.8 AI Readiness Intelligence** — Complete
  - **4.8.1** AI Readiness Intelligence Domain Foundation — Complete (`ai-readiness-assessment` 1.0.0; analytically empty; default off)
  - **4.8.2** AI Readiness Repository Evidence — Complete (`repository-ai-readiness-evidence` 1.0.0; platform evidence; default off)
  - **4.8.3** AI Readiness Intelligence Rules — Complete (`ai_readiness.core` 1.0.0; 17 hygiene rules; default off)
  - **4.8.4** AI Readiness Assessment Inventory — Complete (`ai-readiness-assessment` 1.1.0; default off)
  - **4.8.5** Deterministic AI Readiness Synthesis — Complete (`ai-readiness-assessment` 1.2.0; default off)
  - **4.8.6** AI Readiness Report Integration — Complete (`report.ai_readiness` 1.0.0; default off)
- **4.9 Performance Intelligence** — Complete
  - **4.9.1** Performance Intelligence Domain Foundation — Complete (`performance-assessment` 1.0.0; analytically empty; default off)
  - **4.9.2** Performance Repository Evidence — Complete (`repository-performance-evidence` 1.0.0; platform evidence; default off)
  - **4.9.3** Performance Intelligence Rules — Complete (`performance.core` 1.0.0; 20 hygiene rules; default off)
  - **4.9.4** Performance Assessment Inventory — Complete (`performance-assessment` 1.1.0; default off)
  - **4.9.5** Deterministic Performance Synthesis — Complete (`performance-assessment` 1.2.0; default off)
  - **4.9.6** Performance Report Integration — Complete (`report.performance` 1.0.0; default off)
- **4.10 Modernization Intelligence** — not started

## Phase 5 — Repository Knowledge Layer

Canonical knowledge documents, chunks, and provider-neutral vector storage for
future indexing and retrieval. Independent of the Phase 2 engineering knowledge
store (SQLite).

- **5.1 Repository Knowledge Foundation** — Complete
  (`knowledge-document` / `knowledge-chunk` / `vector-record` 1.0.0;
  `InMemoryVectorStore`; `[knowledge].enabled` default off; no embeddings,
  pgvector, indexing, or retrieval yet)
- **5.2 Knowledge Document Projection and Deterministic Chunking** — Complete
  (`knowledge-corpus` / `knowledge-projection` / `deterministic-chunker` 1.0.0;
  in-memory projectors + chunker; `[knowledge.projection]` / `[knowledge.chunking]`
  default off; optional `repository-knowledge-corpus.json`; no embeddings or
  vector-store writes)
- **5.3 Embedding and Knowledge Indexing Pipeline** — Complete
  (`embedding-result` / `knowledge-index-manifest` / `knowledge-index-result` 1.0.0;
  `DeterministicEmbeddingProvider`; `KnowledgeIndexer` + incremental manifests;
  in-memory `VectorStore` upserts; `[knowledge.embedding]` / `[knowledge.indexing]`
  default off; no Bedrock/OpenAI, retrieval, or RAG)
- **5.4 PostgreSQL + pgvector Provider** — Complete
  (`PgVectorStore`; schema `knowledge_documents` / `knowledge_chunks` /
  `knowledge_vectors`; HNSW cosine index; `[knowledge.vector_store]` supports
  `provider = "pgvector"`; storage-only swap; no retrieval, hybrid search,
  reranking, or RAG)
- **5.4.1 Pgvector Local Operations and Configuration Hardening** — Complete
  (Docker Compose `pgvector/pgvector:pg16`; `CodeStrata_*` env resolution;
  secret redaction; no silent memory fallback; persistence validation;
  [vector-store-setup.md](docs/repository-knowledge/vector-store-setup.md))
- **5.5 Repository Retrieval Engine** — Complete
  (`repository-retrieval-request/result` 1.0.0; `RepositoryRetriever`;
  deterministic query prep, filters, dedupe, diversity, citations;
  `[knowledge.retrieval]` default off; memory/pgvector parity; no answers,
  hybrid search, reranking, RAG, MCP, or production embeddings)
- **5.6 Grounded Repository Answer Engine** — Complete
  (`grounded-answer-*` / `answer-statement` / `answer-citation` 1.0.0;
  `GroundedAnswerEngine`; `AnswerProvider` + `DeterministicExtractiveAnswerProvider`;
  citation/grounding validation; `[knowledge.answering]` default off;
  no Bedrock/OpenAI/Anthropic/local LLM, hybrid retrieval, reranking, MCP,
  or production embeddings)
- **5.7 Repository Intelligence MCP Server** — Complete
  (`mcp-tool-response` / `mcp-health-response` / `mcp-server-manifest` 1.0.0;
  `repository_*` tools over retriever/answer engine/knowledge queries;
  stdio + streamable-http; `[mcp]` default off; localhost HTTP; read-only;
  no production AI, hybrid retrieval, mutation, public hosting, or auth)
- **5.8 Production AI Providers (Bedrock + OpenAI)** — Complete
  (`Bedrock`/`OpenAI` embedding + answer providers; independent
  `[ai].embedding_provider` / `[ai].answer_provider`; `AIProviderRegistry`;
  shared grounded-answer prompts; index embedding fingerprints; `codestrata ai *`;
  MCP uses factories; no Anthropic/Azure/Gemini/Ollama, hybrid, rerank,
  memory, agents, UI, REST, mutation, or silent provider fallback)
- **5.8.1 Externalize and Version AI Prompts** — Complete
  (versioned `prompts/grounded-repository-answer/1.0.0/` resources;
  deterministic loader/renderer; prompt text removed from Python)
- **5.9 Hybrid Retrieval** — Complete
  (`mode = vector|lexical|hybrid`; BM25-lite lexical over chunk text;
  Reciprocal Rank Fusion; diagnostics; default remains vector-only;
  no reranking, graph expansion, or conversational memory)
- **5.10 Modernization Roadmap Engine** — Complete
  (`modernization-roadmap` / `report.roadmap` 1.0.0; Stabilize→Secure→Modernize→Optimize;
  groups existing findings/recommendations into initiatives; deterministic
  priority/effort/risk/dependencies; `[report.sections.roadmap]` default off;
  `codestrata roadmap inspect|phases|initiatives|generate`; no AI generation, Jira,
  dates, cost estimates, portfolio planning, UI, or repository mutation)
- **5.11 Repository Onboarding** — Complete
  (`repository-onboarding-manifest` 1.0.0; `codestrata onboard <repository>`;
  orchestrates existing assess → findings/recs → knowledge → embed/index →
  reports; persists onboarding manifest; `--force-reindex` / `--skip-report` /
  `--skip-index` / `--provider`; no duplicated assessment logic)
- **5.12 Report Contract Hardening** — Complete
  (stable ordering/dedupe; top-level report `manifest`; volatile-field isolation;
  enum normalization; `codestrata report validate`; golden + repeated-run tests;
  leadership HTML empty-state/hierarchy polish; schema remains 1.2 additive)
- **5.13 End-to-End MVP Acceptance Harness** — Complete
  (`codestrata acceptance run|status`; live onboard → validate → grounded Q&A → MCP
  health → determinism for CodeStrata / Spring Petclinic / synthetic-multilang;
  `scripts/mvp_acceptance.py`; `reports/mvp-acceptance/summary.{json,md}`;
  non-zero exit on any repository failure; no new assessment logic)
- **5.14 MVP Packaging and Release Readiness** — Complete
  (hardened `pyproject.toml`; packaged schemas/prompts/defaults/assets;
  optional extras `bedrock`/`openai`/`mcp`/`development`; wheel+sdist;
  `scripts/clean_install_smoke.py`; `codestrata release check`;
  `docs/release-readiness.md`; no PyPI publish)
- **5.15 Full Regression Suite Stabilization** — Complete
  (full `pytest` / `ruff check .` / `mypy src` green; testing-assessment
  schema docs/tests aligned to **1.2.0**; report related_finding_id remapping
  parity; `docs/mvp-regression.md`; `reports/mvp-regression/summary.json`)
- **5.16 Complete CodeStrata Rename** — Complete
  (`src/aimf` → `src/codestrata`; CLI `codestrata`; `codestrata.toml`;
  `.codestrata/`; `CODESTRATA_*`; dist name `codestrata`; knowledge schema v3
  `codestrata_version`; `docs/rename-codestrata.md`; no AIMF CLI/package)
- **5.17 PHP Support** — Complete
  (Composer metadata + Dependency Evidence; `language.php.core`; Laravel /
  Symfony / CodeIgniter / Laminas detection; architecture import graph for
  `.php`; PHPUnit testing evidence; Architecture/Security/Testing packs include
  `php`; `examples/sample-php-app`; dogfood vs open-source PHP repos)
- **5.17.1 PHP Assessment Parity** — Complete
  (`language.php.complexity` brace-scan collector; Technical Debt + Dependency
  hygiene packs include `php`; Composer unbounded `*` + `dev-*` mutable
  hygiene; assess loads `.php` for complexity; docs/limitations updated)
- **5.18 C# / .NET Support** — Complete
  (NuGet PackageReference / packages.config / Directory.Packages.props metadata
  + Dependency Evidence; `language.csharp.core` + `language.csharp.complexity`;
  .NET Framework / .NET Core / modern .NET, ASP.NET MVC/Core, Web API, Blazor,
  EF/EF Core, WCF, xUnit/NUnit/MSTest detection; architecture `using`/namespace
  graph for `.cs`; Architecture/Security/Testing/TD/Dependency packs include
  `csharp`; `examples/sample-csharp-app`; dogfood vs open-source .NET repos)
- **5.19 Performance and Scalability** — Complete
  (deterministic bench harness for small/medium/large + JS/PHP/C#/Java/Python;
  shared source-text cache + bounded `max_read_workers`; single HTML render;
  additive timing telemetry; configurable `analysis.runtime` limits;
  `docs/runtime-performance.md`; `reports/performance-benchmark/`)
- **5.20 Configuration and Execution Profiles** — Complete
  (profiles: community / local / enterprise / bedrock / openai; precedence
  CLI > env > TOML > profile defaults; `codestrata config profile|validate|
  effective`; secret-safe effective dumps; docs/configuration-profiles.md)
- **5.21 Documentation and Developer Experience** — Complete
  (quick start, installation, architecture, CLI, MCP, report interpretation,
  troubleshooting, contributor guide, end-to-end tutorial; Java/Python
  samples; doc validation tests; DX help/exit-code polish)
- **5.22 Community Edition Packaging** — Complete
  (CE scope doc + checklist; NOTICE/SUPPORT; release notes draft; README
  badges/feature matrix; sample reports for five languages; release-readiness
  wheel-name fix; packaging validation)
- **5.23 Monorepo Organization and Public Export Automation** — Complete
  (`engine/` / `examples/` / `platform/` / plugin placeholders;
  `public-export-manifest.yaml`; export + validate scripts; engine↔platform
  boundary tests; sync documentation)
- **5.24 Security and Production Hardening** — Complete
- **5.24.1 Platform Capability Reconciliation** — Complete (RAG/KG owned by
  `platform/`; university workspace deleted; Engine↔Platform entry points)
  (dependency audit; security_check script; symlink-safe scanning; AI/Enterprise
  defaults; Community export excludes Enterprise KG runtime; threat model +
  SECURITY.md; hardening tests)

## Phase 5 (deferred) — Language and Build Ecosystem Expansion

Broader language/build coverage beyond PHP and C# / .NET (deferred).

## Phase 6 — Engineering Workflow Intelligence

GitHub PR review and workflow integrations.

## Phase 7 — Platform Expansion

Dashboards, additional transports, ecosystem integrations.
