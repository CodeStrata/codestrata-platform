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
- **System Verification SV.6:** pipeline verification under
  `platform/verification/engineering_intelligence/` (not shipped in the Platform
  runtime package). Uses the permanent catalog
  `validation/repository-catalog/catalog.json` and canonical Engine assessments.
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
  verification, shared event identity, and event sinks.
- Slice 8.1 adds the **Community Data Lake foundation** (still fail-closed /
  unwired): Platform domain
  `codestrata_platform.community_cloud_api.data_lake` plus private OpenTofu
  module `infrastructure/modules/community-data-lake/` (single private bucket,
  `raw/` + `quarantine/` prefixes). Bucket existence does not enable durable
  ingestion; writer IAM is not attached to Lambda.
- Slice 8.2 adds the **immutable raw-JSON storage contract** (still unwired):
  canonical byte-exact JSON serialization, a resolved
  `ImmutableRawStorageObject` model, fail-closed existing-object conflict
  classification, and a production-capable (but unconnected)
  `CommunityDataLakeS3Store` adapter under
  `codestrata_platform.community_cloud_api.data_lake.infrastructure` — the
  only module in this package tree allowed to import `boto3`. No endpoint,
  `app.py`, or `deployment/wiring.py` calls it, and no exactly-once delivery
  is claimed. See
  [platform/docs/community-cloud-api/immutable-raw-storage.md](platform/docs/community-cloud-api/immutable-raw-storage.md).
- Slice 8.3 evolves the envelope's canonical serialized shape (still unwired)
  from Slice 8.1's flat fields to a nested `acceptance` / `client` /
  `identity` / `source_contract` contract — still envelope schema `1.0`, a
  pre-persistence foundation refinement made before any durable write, not a
  runtime migration — and adds a typed per-stream registry
  (`envelope_registry.py`, `source_contracts.py`, `streams/`) plus
  high-level builders (`envelope_builders.py`) for constructing an envelope
  from an already-validated endpoint request model. No endpoint, `app.py`,
  or `deployment/wiring.py` calls any of it, no durable event-identity
  store was added, and no version anywhere was bumped. See
  [platform/docs/community-cloud-api/data-lake-event-envelope.md](platform/docs/community-cloud-api/data-lake-event-envelope.md).
- Slice 8.4 gives the `assessment_metadata` stream its own versioned
  partition policy (`StreamPartitionPolicy`, `1.0`) and a stream-specific
  storage-object projector, plus generic (stream-agnostic) partitioning
  machinery a later slice will reuse for the remaining four streams. The
  accepted path stays the generic Hive path only (`stream=` /
  `schema_version=` / `year=` / `month=` / `day=`) — no extra dimension was
  added, to avoid cardinality blow-up and identity fingerprinting. No
  endpoint, `app.py`, or `deployment/wiring.py` calls any of it, and no
  version bumped except the new partition policy. See
  [platform/docs/community-cloud-api/assessment-metadata-data-lake.md](platform/docs/community-cloud-api/assessment-metadata-data-lake.md).
- Slice 8.5 reuses that exact same generic partitioning machinery for a
  second stream, `telemetry`: its own versioned partition policy
  (`community-telemetry-partition-policy`, `1.0`) and
  `project_telemetry_storage_object()`. The accepted path again stays the
  generic Hive path only; the only new S3 metadata key is
  `codestrata-client-type` (`event_type` stays private-payload-only, never
  a path dimension or metadata key, since it is an analytics vocabulary
  expected to evolve). No endpoint, `app.py`, or `deployment/wiring.py`
  calls any of it. See
  [platform/docs/community-cloud-api/telemetry-data-lake.md](platform/docs/community-cloud-api/telemetry-data-lake.md).
- Slice 8.6 reuses that same generic partitioning machinery for a third
  stream, `cli_event`: its own versioned partition policy
  (`community-cli-event-partition-policy`, `1.0`) and
  `project_cli_event_storage_object()`. The accepted path again stays the
  generic Hive path only, and this time **no** new S3 metadata key is
  added at all (`operation`/`lifecycle`/`result` stay private-payload-only;
  `client_type` is redundant since the CLI client is always
  `codestrata_cli`). No endpoint, `app.py`, `deployment/wiring.py`, the CLI
  emitter, or the telemetry runtime calls any of it. See
  [platform/docs/community-cloud-api/cli-event-data-lake.md](platform/docs/community-cloud-api/cli-event-data-lake.md).
- Slice 8.7 reuses that same generic partitioning machinery for a fourth
  stream, `extension_event`: its own versioned partition policy
  (`community-extension-event-partition-policy`, `1.0`) and
  `project_extension_event_storage_object()`. The accepted path again stays
  the generic Hive path only; Option B reuses `codestrata-client-type` for
  `vscode_extension`/`cursor_extension` (never `editor` or `operation` in
  path or metadata). No endpoint, `app.py`, `deployment/wiring.py`, or
  extension emitter calls any of it, and extension collection is not claimed
  operational via the data lake. See
  [platform/docs/community-cloud-api/extension-event-data-lake.md](platform/docs/community-cloud-api/extension-event-data-lake.md).
- Slice 8.8 reuses that same generic partitioning machinery for a fifth
  stream, `ai_usage`: its own versioned partition policy
  (`community-ai-usage-partition-policy`, `1.0`) and
  `project_ai_usage_storage_object()`. The accepted path again stays the
  generic Hive path only; Option B reuses `codestrata-client-type` for
  `codestrata_cli`/`vscode_extension`/`cursor_extension` (never
  `capability`, `provider_family`, or `model_family` in path or metadata).
  Adds three AI catalog version fields on policy and diagnostics. No
  endpoint, `app.py`, `deployment/wiring.py`, Engine AI provider, or client
  emitter calls any of it, and AI usage collection is not claimed
  operational via the data lake. Slice 8.9 (malformed-event quarantine)
  implements persistence under `quarantine/` without endpoint wiring; see
  [platform/docs/community-cloud-api/data-lake-quarantine.md](platform/docs/community-cloud-api/data-lake-quarantine.md).
  Slice 8.10 formalizes data retention and lifecycle policies
  (`community-data-lake-retention-policy:1.0`) aligned with OpenTofu
  lifecycle defaults — still unwired; does not claim production data is
  stored or deleted. See
  [platform/docs/community-cloud-api/data-lake-retention.md](platform/docs/community-cloud-api/data-lake-retention.md).
  Slice 8.11 formalizes encryption at rest
  (`community-data-lake-encryption-policy:1.0`, SSE-S3 / AES256 only; KMS
  deferred) — still unwired; does not claim production data is stored. See
  [platform/docs/community-cloud-api/data-lake-encryption.md](platform/docs/community-cloud-api/data-lake-encryption.md).
  Slice 8.12 formalizes restricted IAM access control
  (`community-data-lake-access-policy:1.0`, least-privilege writer policy
  document with stable SIDs, prefix-scoped Put/Get, delete Deny on both
  prefixes, `DenyInsecureTransport`, no ListBucket, no KMS IAM) — writer
  policy remains unattached. See
  [platform/docs/community-cloud-api/data-lake-access-control.md](platform/docs/community-cloud-api/data-lake-access-control.md).
  Slice 8.13 formalizes storage abstraction
  (`community-data-lake-storage-policy:1.0`, typed projected-object port,
  explicit factory with production-default unavailable adapter, in-memory
  test-only, S3 capable but unwired). **Slice 8.14** adds integration
  verification under `platform/verification/community_data_lake/` (five
  streams, quarantine, adapter matrix, privacy, infrastructure contract,
  production fail-closed). Report:
  `platform/reports/verification/community-data-lake-verification.json`.
  **Slice 8.15** (Epic 8 completion verification) confirms boundary,
  version registry, package inventory, and production fail-closed posture under
  `platform/verification/community_data_lake_completion/`. Report:
  `platform/reports/verification/community-data-lake-completion-verification.json`.
  **Epic 8 is complete.** Production ingestion remains **not operational**
  (`enable_ingestion_wire = false`; endpoints unwired). **Epic 9 is complete**
  for v0.2.0: Engine runtime (9.1–9.12), VS Code runtime (9.13), cross-client
  verification (9.14), and completion verification (9.15) under
  [`verification/privacy_first_telemetry_completion/`](verification/privacy_first_telemetry_completion/README.md).
  Production telemetry transmission remains **unavailable by default** (not
  collecting). Cursor telemetry is not integrated. **Epic 10** anonymous
  analytics: Slice **10.1** contract
  (`community-anonymous-analytics-policy:1.0` /
  `community-anonymous-analytics-schema:1.0`) and Slice **10.2** local anonymous
  installation identity
  (`community-anonymous-installation-identity-policy:1.0` /
  `community-anonymous-installation-identity-schema:1.0`) and Slice **10.3**
  local runtime analytics
  (`community-runtime-analytics-policy:1.0` /
  `community-runtime-analytics-schema:1.0`) and Slice **10.4** assessment
  analytics construction APIs
  (`community-assessment-analytics-policy:1.0` /
  `community-assessment-analytics-schema:1.0`), Slice **10.5** repository
  aggregate analytics construction APIs
  (`community-repository-aggregate-analytics-policy:1.0` /
  `community-repository-aggregate-analytics-schema:1.0`), and Slice **10.6** AI
  analytics construction APIs
  (`community-ai-analytics-policy:1.0` /
  `community-ai-analytics-schema:1.0`) under
  `codestrata.telemetry.analytics` — no analytics transmission; analytics
  payloads are not persisted; assessment, repository aggregate, and AI analytics
  are not wired into assess or AI execution.
  See
  [engine/docs/telemetry-anonymous-analytics.md](engine/docs/telemetry-anonymous-analytics.md),
  [engine/docs/telemetry-installation-identity.md](engine/docs/telemetry-installation-identity.md),
  [engine/docs/telemetry-runtime-analytics.md](engine/docs/telemetry-runtime-analytics.md),
  [engine/docs/telemetry-assessment-analytics.md](engine/docs/telemetry-assessment-analytics.md),
  [engine/docs/telemetry-repository-aggregate-analytics.md](engine/docs/telemetry-repository-aggregate-analytics.md),
  and
  [engine/docs/telemetry-ai-analytics.md](engine/docs/telemetry-ai-analytics.md). Slice **10.7** adds VS Code anonymous analytics (`community-vscode-anonymous-analytics-policy:1.0` / `community-vscode-anonymous-analytics-schema:1.0`) — local construction, identity-free, unavailable sink; see [vscode-plugin/docs/analytics.md](vscode-plugin/docs/analytics.md). Slice **10.8** adds anonymous analytics privacy verification (`anonymous-analytics-privacy-verification` @ `1.0.0`) under [verification/anonymous_analytics_privacy/](verification/anonymous_analytics_privacy/). **Epic 10 is complete** for v0.2.0: Slice **10.9** adds Epic 10 completion verification (`anonymous-analytics-completion-verification` @ `1.0.0`) under [verification/anonymous_analytics_completion/](verification/anonymous_analytics_completion/README.md), which live re-runs Slice 10.8 rather than trusting a stale report. Analytics remain contracts-only; production analytics collection is **not operational**.
  See
  [platform/docs/community-cloud-api/data-lake-storage-abstraction.md](platform/docs/community-cloud-api/data-lake-storage-abstraction.md).
  See
  [platform/docs/community-cloud-api/ai-usage-data-lake.md](platform/docs/community-cloud-api/ai-usage-data-lake.md).
- **Epic 11, Slice 11.1** adds a characterization-only AI provider
  compatibility baseline (`ai-provider-compatibility-baseline` @ `1.0.0`)
  under
  [engine/verification/ai_provider_baseline/](engine/verification/ai_provider_baseline/README.md).
  It freezes and inventories the *existing* Bedrock/OpenAI assess provider
  architecture (`AIModelProvider` ABC, `AssessAIProviderRegistry`, default
  models/timeouts, error mapping, fail-soft, `codestrata ai doctor`) and
  records compatibility requirements and known limitations (for example,
  `[ai.bedrock]`/`[ai.openai]` `timeout_seconds`/`max_retries` settings exist
  but are not wired into the assess provider factory) for future Slice
  11.2+ work. It introduces no new provider interface, provider platform, or
  registry redesign, migrates no providers, and does not add OpenRouter.
  Slice 11.2 (below) owns the unwired common contracts that follow this baseline.
- **Epic 11, Slice 11.2** adds Common AI Provider Contracts
  (`community-ai-provider-contract:1.0`) as a new, **unwired** sibling
  package: [engine/src/codestrata/ai/provider_contracts/](engine/docs/ai-provider-contracts.md).
  It defines provider-neutral, SDK-free domain types (typed requests/results,
  bounded errors, usage metadata, a minimal synchronous `AIProvider`
  protocol, and an explicit deterministic registry) that remain compatible
  with every Slice 11.1 requirement (CR-1..CR-6), enforced by
  [engine/verification/ai_provider_contracts/](engine/verification/ai_provider_contracts/README.md)
  (`ai-provider-contract-verification` @ `1.0.0`). It migrates no providers,
  wires nothing into the assessment product path, adds no default provider
  or model, and does not add OpenRouter.
- **Epic 11, Slice 11.3** adds Standardized Provider and Model Configuration
  (`community-ai-provider-configuration:1.0`) to the same **unwired** sibling
  package: [engine/src/codestrata/ai/provider_contracts/](engine/docs/ai-provider-configuration.md).
  It defines a privacy-preserving representation of provider/model
  configuration (`AIProviderConfiguration`, `ProviderCredentialRequirement`,
  `LegacyConfigurationInput`, and pure provider/model resolution functions
  that mirror `resolve_assess_model_id`'s exact CLI>env>file>default
  precedence without reading `os.environ`), remaining compatible with every
  Slice 11.1 requirement (CR-1..CR-6), enforced by
  [engine/verification/ai_provider_configuration/](engine/verification/ai_provider_configuration/README.md)
  (`ai-provider-configuration-verification` @ `1.0.0`). It migrates no
  providers, wires nothing into the assessment product path, changes no
  default, precedence, or config key, and does not add OpenRouter.
- **Epic 11, Slice 11.4** adds Standardized Execution, Errors, Timeouts, and
  Retries (`community-ai-provider-execution:1.0`) to the same **unwired**
  sibling package:
  [engine/src/codestrata/ai/provider_contracts/](engine/docs/ai-provider-execution.md).
  It defines bounded `TimeoutPolicy`/`AIProviderRetryPolicy`/`BackoffPolicy`
  value objects, a pure `decide_retry()` retry-decision function, safe
  `ProviderErrorClassification`, and an `AIProviderExecutor` that runs one
  `AIProviderRequest` against one `AIProvider` with injected clock/sleeper
  (`DEFAULT_RETRY_POLICY` has `maximum_attempts=1`, matching CR-1's existing
  "exactly one invoke" behavior exactly), remaining compatible with every
  Slice 11.1 requirement (CR-1..CR-6), enforced by
  [engine/verification/ai_provider_execution/](engine/verification/ai_provider_execution/README.md)
  (`ai-provider-execution-verification` @ `1.0.0`). It migrates no
  providers, wires the executor into nothing in the assessment product
  path, enforces no real wall-clock timeout itself, and does not add
  OpenRouter.
- **Epic 11, Slice 11.5** adds Provider Usage Metadata and Capability
  Discovery (`community-ai-provider-capability:1.0` /
  `community-ai-provider-usage:1.0`) to the same **unwired** sibling
  package:
  [engine/src/codestrata/ai/provider_contracts/](engine/docs/ai-provider-capabilities.md).
  It defines a static, declared-only `ProviderCapabilityProfile` per known
  Engine provider (bedrock: no native structured JSON, prompt-only;
  openai: native JSON mode; neither streams; both mark timeout/retry
  policy support as `not_wired_to_runtime`; both report usage/token
  accounting) and extends `ProviderUsageMetadata` (Slice 11.2) with an
  optional `completion_status` field aligned to `ProviderExecutionStatus`,
  remaining compatible with every Slice 11.1 requirement (CR-1..CR-6) and
  with Slices 11.2/11.3/11.4, enforced by
  [engine/verification/ai_provider_capabilities/](engine/verification/ai_provider_capabilities/README.md)
  (`ai-provider-capability-verification` @ `1.0.0`). It migrates no
  providers, wires nothing into the assessment product path, changes no
  runtime provider behavior, and does not add OpenRouter.
- **Epic 11, Slice 11.6** migrates the **OpenAI** provider onto the Slice
  11.2–11.5 contracts, the first wired use of that package:
  [engine/src/codestrata/ai/provider_adapters/openai/](engine/docs/ai-provider-openai.md).
  A 12-module adapter implements the `AIProvider` protocol behind a single
  credential boundary (`client.py` is the only module importing the `openai`
  SDK or reading `os.environ`) and runs under `AIProviderExecutor` pinned to
  `DEFAULT_RETRY_POLICY` (`maximum_attempts=1`, preserving CR-1) and
  `DEFAULT_TIMEOUT_POLICY` (60s, declarative). `OpenAIAIModelProvider`
  remains the public assess-path class and becomes a thin compatibility
  wrapper that translates non-success outcomes back into the same legacy
  exceptions, so `AiEnrichmentService` fail-soft, report schema 1.2, and CLI
  exit behavior are unchanged. Enforced by
  [engine/verification/openai_provider_migration/](engine/verification/openai_provider_migration/README.md)
  (`openai-provider-migration-verification` @ `1.0.0`).
- **Epic 11, Slice 11.7** migrates the **AWS Bedrock** provider onto the same
  contracts:
  [engine/src/codestrata/ai/provider_adapters/bedrock/](engine/docs/ai-provider-bedrock.md).
  Bedrock remains the default provider (`amazon.nova-lite-v1:0`). Converse
  request semantics, AWS credential/profile/region precedence, and botocore
  `retries={"max_attempts": 1}` are preserved. `BedrockAIModelProvider` is a
  thin compatibility wrapper over `BedrockProvider` + `AIProviderExecutor`
  (also `maximum_attempts=1`). Enforced by
  [engine/verification/bedrock_provider_migration/](engine/verification/bedrock_provider_migration/README.md)
  (`bedrock-provider-migration-verification` @ `1.0.0`). Both OpenAI and
  Bedrock now run on the provider platform behind the same
  `AssessAIProviderRegistry`.
- **Epic 11, Slice 11.8** is cross-provider contract verification
  ([engine/docs/ai-provider-platform.md](engine/docs/ai-provider-platform.md);
  [engine/verification/ai_provider_cross_provider/](engine/verification/ai_provider_cross_provider/README.md),
  schema `ai-provider-cross-provider-verification` @ `1.0.0`). It proves both
  providers satisfy shared Slice 11.2–11.5 contracts while recording intentional
  differences (Chat Completions vs Converse; API key vs AWS chain; JSON mode vs
  prompt instruction). **Registry decision B:** compatibility registry retained
  — `AssessAIProviderRegistry` remains assess-authoritative; contracts
  `AIProviderRegistry` stays unwired.
- **Epic 11, Slice 11.9** implements the OpenRouter adapter
  ([engine/docs/ai-provider-openrouter.md](engine/docs/ai-provider-openrouter.md);
  [engine/verification/openrouter_provider/](engine/verification/openrouter_provider/README.md),
  schema `openrouter-provider-verification` @ `1.0.0`). `ProviderId.OPENROUTER`
  is additive under contract 1.0.
- **Epic 11, Slice 11.10** adds operational OpenRouter configuration and
  authentication
  ([engine/docs/ai-provider-openrouter-configuration.md](engine/docs/ai-provider-openrouter-configuration.md);
  [engine/verification/openrouter_configuration/](engine/verification/openrouter_configuration/README.md),
  schema `openrouter-configuration-verification` @ `1.0.0`). OpenRouter is
  assess-registered as an **explicit, non-default** provider (`[ai.openrouter]`,
  `OPENROUTER_API_KEY` / `CODESTRATA_OPENROUTER_MODEL_ID`). Bedrock remains
  default; OpenAI/Bedrock behavior unchanged. Doctor local readiness is Slice 11.11.
- **Epic 11, Slice 11.11** adds OpenRouter doctor local readiness and mocked
  end-to-end integration verification
  ([engine/docs/ai-provider-openrouter-doctor.md](engine/docs/ai-provider-openrouter-doctor.md);
  [engine/verification/openrouter_doctor_integration/](engine/verification/openrouter_doctor_integration/README.md),
  schema `openrouter-doctor-integration-verification` @ `1.0.0`). Doctor never
  calls OpenRouter, never validates keys/models remotely, and never constructs
  a network client.
- **Epic 11, Slice 11.12** is authoritative privacy, failure-isolation, and
  architecture-boundary verification across bedrock/openai/openrouter
  ([engine/docs/ai-provider-security-boundaries.md](engine/docs/ai-provider-security-boundaries.md);
  [engine/verification/ai_provider_privacy_boundaries/](engine/verification/ai_provider_privacy_boundaries/README.md),
  schema `ai-provider-privacy-boundary-verification` @ `1.0.0`). No live
  provider calls or real credentials. Decision B and Bedrock default preserved.
  Slice 11.13 completion verification is complete
  ([engine/verification/ai_provider_platform_completion/](engine/verification/ai_provider_platform_completion/README.md),
  schema `ai-provider-platform-completion-verification` @ `1.0.0`). Epic 11 is complete
  for v0.2.0 release-readiness; Epic 12 is not started.
- The Slice 7.14 deployment proves that the Community Cloud API can be packaged
  and served through serverless infrastructure. It does not enable durable
  Community event ingestion because production credential verification, shared
  event identity, and event sinks are not yet configured.
- Slice 7.15 (final Epic 7 slice) verifies the combined request pipeline with
  in-memory adapters only; it adds no product capabilities and does not start
  Epic 8.
- **System Verification SV.7:** full six-route Community Cloud API verification
  under `platform/verification/community_cloud_api/` (not shipped in the Platform
  runtime package). Report:
  `platform/reports/verification/community-cloud-api-verification.json`.
- **System Verification SV.8:** website-safe Engineering Intelligence export
  verification under `platform/verification/website_export/` (not shipped in the
  Platform runtime package). Reuses the verified SV.6 five-repository EIR.
  Report: `platform/reports/verification/website-export-verification.json`.
- **System Verification SV.9:** Platform deployment foundation verification under
  `infrastructure/verification/` (private; extractable with infrastructure).
  Verifies OpenTofu module/production root, API Gateway HTTP API, one Lambda +
  ECR packaging, IAM/logging, and in-process fail-closed production foundation.
  Report:
  `infrastructure/reports/verification/platform-deployment-foundation-verification.json`.
  Does not run `tofu apply`, push images, call AWS, or start SV.10.
- **System Verification SV.14:** cross-schema compatibility verification under
  `platform/verification/cross_schema_compatibility/` (assessment 1.2, product
  contracts 1.0, verification reports 1.0.0). Verification-only; does not start
  SV.15.
- **System Verification SV.15:** deterministic output verification under
  `platform/verification/deterministic_outputs/` (order/path/hash-seed
  independence; approved volatile fields documented).
- **System Verification SV.16:** release artifact verification under
  `verification/release_artifacts/` (wheel/sdist, clean install, public/private
  boundaries, OpenTofu fmt/validate gate, checksums). Does not tag v0.2.0 or
  start SV.17.
- Details: [platform/docs/community-cloud-api/README.md](platform/docs/community-cloud-api/README.md),
  [verification-e2e.md](platform/docs/community-cloud-api/verification-e2e.md),
  [infrastructure/README.md](infrastructure/README.md),
  [request-validation.md](platform/docs/community-cloud-api/request-validation.md),
  [payload-size-limits.md](platform/docs/community-cloud-api/payload-size-limits.md),
  [structured-logging.md](platform/docs/community-cloud-api/structured-logging.md),
  [retry-safe-event-identifiers.md](platform/docs/community-cloud-api/retry-safe-event-identifiers.md),
  [website-export.md](platform/docs/intelligence-reporting/website-export.md).

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
