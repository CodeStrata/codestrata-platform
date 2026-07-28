# Engineering Rule Catalog

**Status:** Canonical (Phase 8.9.4)
**Authority:** Knowledge (catalog) · Engine (runtime implementation)

## Purpose

Permanent catalog of Engineering Intelligence rules. The catalog **references**
Engine runtime rules; it does **not** duplicate detection logic.

## Identifiers

| ID kind | Example | Owner |
| ------- | ------- | ----- |
| Catalog Rule ID | `AR-001` | This catalog |
| Runtime Rule ID | `architecture.dependency-cycle` | CodeStrata Engine |
| Concept ID | `ARCH-CON-001` | Knowledge |

Runtime implementations remain under `engine/src/codestrata/`.

## Status values

| Status | Meaning |
| ------ | ------- |
| `implemented` | Shared Rule Platform production rule |
| `implemented-legacy` | Assessment Graph builtin (`codestrata-rule-*`) |
| `planned` | Concept exists; no runtime rule yet |

## Summary

| Metric | Count |
| ------ | ----- |
| Catalog entries | 89 |
| SharedRule (implemented) | 77 |
| Legacy builtins | 12 |

Machine-readable mirror: [catalog/rules.json](catalog/rules.json).

## Domain: `ai`

| Catalog ID | Rule Name | Runtime Rule ID | Concept ID | Status | Implementation | Tests | Report usage |
| ---------- | --------- | --------------- | ---------- | ------ | -------------- | ----- | ------------ |
| `AIR-001` | API or service boundary signals detected | `ai_readiness.ai-001` | `AI-CON-001` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-002` | Structured API specification detected | `ai_readiness.ai-002` | `AI-CON-001` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-003` | Limited API or service boundary evidence | `ai_readiness.ai-003` | `AI-CON-001` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-004` | Architecture or ADR documentation detected | `ai_readiness.ai-010` | `AI-CON-002` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-005` | Limited supporting documentation evidence | `ai_readiness.ai-011` | `AI-CON-002` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-006` | Data access repository signals detected | `ai_readiness.ai-020` | `AI-CON-003` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-007` | Search or retrieval signals detected | `ai_readiness.ai-021` | `AI-CON-003` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-008` | Vector or embeddings signals detected | `ai_readiness.ai-022` | `AI-CON-003` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-009` | LLM SDK or AI framework signals detected | `ai_readiness.ai-030` | `AI-CON-004` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-010` | Prompt assets detected | `ai_readiness.ai-031` | `AI-CON-004` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-011` | RAG pipeline signals detected | `ai_readiness.ai-032` | `AI-CON-004` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-012` | Tool or MCP integration signals detected | `ai_readiness.ai-040` | `AI-CON-005` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-013` | Workflow or agent boundary signals detected | `ai_readiness.ai-041` | `AI-CON-005` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-014` | Observability or governance signals detected | `ai_readiness.ai-050` | `AI-CON-006` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-015` | AI-related assets without observability evidence | `ai_readiness.ai-051` | `AI-CON-006` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-016` | Broad AI-readiness evidence foundations | `ai_readiness.ai-060` | `AI-CON-007` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |
| `AIR-017` | Limited AI-readiness evidence foundations | `ai_readiness.ai-061` | `AI-CON-007` | `implemented` | `engine/src/codestrata/application/rules/ai_readiness/rules.py` | `engine/tests/application/rules/ai_readiness/` | Finding via Shared Rule Platform when pack enabled |

## Domain: `architecture`

| Catalog ID | Rule Name | Runtime Rule ID | Concept ID | Status | Implementation | Tests | Report usage |
| ---------- | --------- | --------------- | ---------- | ------ | -------------- | ----- | ------------ |
| `AR-001` | Architecture dependency cycle | `architecture.dependency-cycle` | `ARCH-CON-001` | `implemented` | `engine/src/codestrata/application/rules/architecture/rules.py` | `engine/tests/application/rules/architecture/` | Finding via Shared Rule Platform when pack enabled |
| `AR-002` | Invalid dependency direction | `architecture.invalid-dependency-direction` | `ARCH-CON-002` | `implemented` | `engine/src/codestrata/application/rules/architecture/rules.py` | `engine/tests/application/rules/architecture/` | Finding via Shared Rule Platform when pack enabled |
| `AR-003` | Layer boundary violation | `architecture.layer-boundary-violation` | `ARCH-CON-003` | `implemented` | `engine/src/codestrata/application/rules/architecture/rules.py` | `engine/tests/application/rules/architecture/` | Finding via Shared Rule Platform when pack enabled |
| `AR-004` | Excessive cross-module coupling | `architecture.excessive-cross-module-coupling` | `ARCH-CON-004` | `implemented` | `engine/src/codestrata/application/rules/architecture/rules.py` | `engine/tests/application/rules/architecture/` | Finding via Shared Rule Platform when pack enabled |
| `AR-005` | Architectural component concentration | `architecture.component-concentration` | `ARCH-CON-005` | `implemented` | `engine/src/codestrata/application/rules/architecture/rules.py` | `engine/tests/application/rules/architecture/` | Finding via Shared Rule Platform when pack enabled |
| `AR-006` | Framework leakage across boundaries | `architecture.framework-leakage` | `ARCH-CON-006` | `implemented` | `engine/src/codestrata/application/rules/architecture/rules.py` | `engine/tests/application/rules/architecture/` | Finding via Shared Rule Platform when pack enabled |
| `AR-007` | Enterprise architecture standard mismatch | `architecture.enterprise-standard-mismatch` | `ARCH-CON-007` | `implemented` | `engine/src/codestrata/application/rules/architecture/rules.py` | `engine/tests/application/rules/architecture/` | Finding via Shared Rule Platform when pack enabled |

## Domain: `cloud`

| Catalog ID | Rule Name | Runtime Rule ID | Concept ID | Status | Implementation | Tests | Report usage |
| ---------- | --------- | --------------- | ---------- | ------ | -------------- | ----- | ------------ |
| `CR-001` | Multiple cloud providers detected | `cloud.cloud-001` | `CLOUD-CON-001` | `implemented` | `engine/src/codestrata/application/rules/cloud/rules.py` | `engine/tests/application/rules/cloud/` | Finding via Shared Rule Platform when pack enabled |
| `CR-002` | Cloud platform detected | `cloud.cloud-002` | `CLOUD-CON-001` | `implemented` | `engine/src/codestrata/application/rules/cloud/rules.py` | `engine/tests/application/rules/cloud/` | Finding via Shared Rule Platform when pack enabled |
| `CR-003` | Containerization detected | `cloud.cloud-010` | `CLOUD-CON-002` | `implemented` | `engine/src/codestrata/application/rules/cloud/rules.py` | `engine/tests/application/rules/cloud/` | Finding via Shared Rule Platform when pack enabled |
| `CR-004` | Kubernetes deployment detected | `cloud.cloud-011` | `CLOUD-CON-002` | `implemented` | `engine/src/codestrata/application/rules/cloud/rules.py` | `engine/tests/application/rules/cloud/` | Finding via Shared Rule Platform when pack enabled |
| `CR-005` | Infrastructure as Code present | `cloud.cloud-020` | `CLOUD-CON-003` | `implemented` | `engine/src/codestrata/application/rules/cloud/rules.py` | `engine/tests/application/rules/cloud/` | Finding via Shared Rule Platform when pack enabled |
| `CR-006` | Multiple IaC technologies detected | `cloud.cloud-021` | `CLOUD-CON-003` | `implemented` | `engine/src/codestrata/application/rules/cloud/rules.py` | `engine/tests/application/rules/cloud/` | Finding via Shared Rule Platform when pack enabled |
| `CR-007` | Serverless deployment detected | `cloud.cloud-030` | `CLOUD-CON-004` | `implemented` | `engine/src/codestrata/application/rules/cloud/rules.py` | `engine/tests/application/rules/cloud/` | Finding via Shared Rule Platform when pack enabled |
| `CR-008` | Cloud deployment pipeline detected | `cloud.cloud-040` | `CLOUD-CON-005` | `implemented` | `engine/src/codestrata/application/rules/cloud/rules.py` | `engine/tests/application/rules/cloud/` | Finding via Shared Rule Platform when pack enabled |
| `CR-009` | Managed cloud services detected | `cloud.cloud-050` | `CLOUD-CON-006` | `implemented` | `engine/src/codestrata/application/rules/cloud/rules.py` | `engine/tests/application/rules/cloud/` | Finding via Shared Rule Platform when pack enabled |
| `CR-010` | Cloud-native repository indicators | `cloud.cloud-060` | `CLOUD-CON-007` | `implemented` | `engine/src/codestrata/application/rules/cloud/rules.py` | `engine/tests/application/rules/cloud/` | Finding via Shared Rule Platform when pack enabled |
| `CR-011` | Cloud deployment assets without runtime platform evidence | `cloud.cloud-061` | `CLOUD-CON-007` | `implemented` | `engine/src/codestrata/application/rules/cloud/rules.py` | `engine/tests/application/rules/cloud/` | Finding via Shared Rule Platform when pack enabled |

## Domain: `dependency`

| Catalog ID | Rule Name | Runtime Rule ID | Concept ID | Status | Implementation | Tests | Report usage |
| ---------- | --------- | --------------- | ---------- | ------ | -------------- | ----- | ------------ |
| `DEP-001` | Unresolved dependency version | `dependency.unresolved-version` | `DEP-CON-001` | `implemented` | `engine/src/codestrata/application/rules/dependency/rules.py` | `engine/tests/application/rules/dependency/` | Finding via Shared Rule Platform when pack enabled |
| `DEP-002` | Mutable dependency version | `dependency.mutable-version` | `DEP-CON-002` | `implemented` | `engine/src/codestrata/application/rules/dependency/rules.py` | `engine/tests/application/rules/dependency/` | Finding via Shared Rule Platform when pack enabled |
| `DEP-003` | Unbounded requirement | `dependency.unbounded-requirement` | `DEP-CON-003` | `implemented` | `engine/src/codestrata/application/rules/dependency/rules.py` | `engine/tests/application/rules/dependency/` | Finding via Shared Rule Platform when pack enabled |
| `DEP-004` | Conflicting exact dependency versions | `dependency.conflicting-exact-versions` | `DEP-CON-004` | `implemented` | `engine/src/codestrata/application/rules/dependency/rules.py` | `engine/tests/application/rules/dependency/` | Finding via Shared Rule Platform when pack enabled |
| `DEP-005` | Duplicate dependency declaration | `dependency.duplicate-declaration` | `DEP-CON-005` | `implemented` | `engine/src/codestrata/application/rules/dependency/rules.py` | `engine/tests/application/rules/dependency/` | Finding via Shared Rule Platform when pack enabled |

## Domain: `documentation`

| Catalog ID | Rule Name | Runtime Rule ID | Concept ID | Status | Implementation | Tests | Report usage |
| ---------- | --------- | --------------- | ---------- | ------ | -------------- | ----- | ------------ |
| `TST-001` | Disabled or skipped tests detected | `testing.test-001` | `DOC-CON-010` | `implemented` | `engine/src/codestrata/application/rules/testing/rules.py` | `engine/tests/application/rules/testing/` | Finding via Shared Rule Platform when pack enabled |
| `TST-002` | Material test candidates lack structural confirmation | `testing.test-002` | `DOC-CON-011` | `implemented` | `engine/src/codestrata/application/rules/testing/rules.py` | `engine/tests/application/rules/testing/` | Finding via Shared Rule Platform when pack enabled |
| `TST-003` | Declared test framework lacks structural observation | `testing.test-003` | `DOC-CON-011` | `implemented` | `engine/src/codestrata/application/rules/testing/rules.py` | `engine/tests/application/rules/testing/` | Finding via Shared Rule Platform when pack enabled |
| `TST-004` | Coverage configuration without CI test invocation | `testing.test-005` | `DOC-CON-012` | `implemented` | `engine/src/codestrata/application/rules/testing/rules.py` | `engine/tests/application/rules/testing/` | Finding via Shared Rule Platform when pack enabled |

## Domain: `legacy`

| Catalog ID | Rule Name | Runtime Rule ID | Concept ID | Status | Implementation | Tests | Report usage |
| ---------- | --------- | --------------- | ---------- | ------ | -------------- | ----- | ------------ |
| `LEG-001` | Missing README | `codestrata-rule-missing-readme` | `DOC-CON-001` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |
| `LEG-002` | Missing LICENSE | `codestrata-rule-missing-license` | `DOC-CON-002` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |
| `LEG-003` | Missing tests | `codestrata-rule-missing-tests` | `DOC-CON-011` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |
| `LEG-004` | Large repository | `codestrata-rule-large-repository` | `TD-CON-010` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |
| `LEG-005` | Maven Wrapper missing | `codestrata-rule-maven-wrapper-missing` | `DEP-CON-010` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |
| `LEG-006` | Java detected | `codestrata-rule-java-detected` | `ARCH-CON-010` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |
| `LEG-007` | Spring Boot detected | `codestrata-rule-spring-boot-detected` | `ARCH-CON-011` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |
| `LEG-008` | Unsupported Spring Boot version | `codestrata-rule-unsupported-spring-boot-version` | `DEP-CON-011` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |
| `LEG-009` | Node engine detected | `codestrata-rule-node-engine-detected` | `ARCH-CON-012` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |
| `LEG-010` | Missing Node engine | `codestrata-rule-missing-node-engine` | `DEP-CON-012` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |
| `LEG-011` | NPM lockfile missing | `codestrata-rule-npm-lockfile-missing` | `DEP-CON-013` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |
| `LEG-012` | Missing CI workflow | `codestrata-rule-missing-ci-workflow` | `DOC-CON-012` | `implemented-legacy` | `engine/src/codestrata/services/rule_engine/rules/builtin.py` | `engine/tests/ (legacy / bridge coverage varies)` | n/a |

## Domain: `performance`

| Catalog ID | Rule Name | Runtime Rule ID | Concept ID | Status | Implementation | Tests | Report usage |
| ---------- | --------- | --------------- | ---------- | ------ | -------------- | ----- | ------------ |
| `PERF-001` | Data access framework or repository patterns detected | `performance.perf-001` | `PERF-CON-001` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-002` | Multiple data access framework kinds detected | `performance.perf-002` | `PERF-CON-001` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-003` | Data access without observable batching or timeout controls | `performance.perf-003` | `PERF-CON-001` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-004` | Thread sleep signals detected | `performance.perf-010` | `PERF-CON-002` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-005` | Synchronous I/O signals detected | `performance.perf-011` | `PERF-CON-002` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-006` | Caching signals detected | `performance.perf-020` | `PERF-CON-003` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-007` | Data access without observable caching signals | `performance.perf-021` | `PERF-CON-003` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-008` | Concurrency or async signals detected | `performance.perf-030` | `PERF-CON-004` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-009` | Executor concurrency or executor configuration detected | `performance.perf-031` | `PERF-CON-004` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-010` | Concurrency without observable executor configuration | `performance.perf-032` | `PERF-CON-004` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-011` | Resource management signals detected | `performance.perf-040` | `PERF-CON-005` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-012` | Data or blocking signals without resource management evidence | `performance.perf-041` | `PERF-CON-005` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-013` | Frontend bundle tooling signals detected | `performance.perf-050` | `PERF-CON-006` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-014` | Frontend lazy loading or code splitting detected | `performance.perf-051` | `PERF-CON-006` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-015` | Limited frontend bundle or lazy-loading evidence | `performance.perf-052` | `PERF-CON-006` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-016` | Observability or profiling signals detected | `performance.perf-060` | `PERF-CON-007` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-017` | Performance assets without observability evidence | `performance.perf-061` | `PERF-CON-007` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-018` | Performance configuration control signals detected | `performance.perf-070` | `PERF-CON-008` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-019` | Broad performance evidence foundations | `performance.perf-071` | `PERF-CON-008` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |
| `PERF-020` | Limited performance evidence foundations | `performance.perf-072` | `PERF-CON-008` | `implemented` | `engine/src/codestrata/application/rules/performance/rules.py` | `engine/tests/application/rules/performance/` | Finding via Shared Rule Platform when pack enabled |

## Domain: `security`

| Catalog ID | Rule Name | Runtime Rule ID | Concept ID | Status | Implementation | Tests | Report usage |
| ---------- | --------- | --------------- | ---------- | ------ | -------------- | ----- | ------------ |
| `SE-001` | Private key material in repository | `security.private-key-material` | `SEC-CON-001` | `implemented` | `engine/src/codestrata/application/rules/security/rules.py` | `engine/tests/application/rules/security/` | Finding via Shared Rule Platform when pack enabled |
| `SE-002` | Credential literal in configuration | `security.credential-literal` | `SEC-CON-002` | `implemented` | `engine/src/codestrata/application/rules/security/rules.py` | `engine/tests/application/rules/security/` | Finding via Shared Rule Platform when pack enabled |
| `SE-003` | Placeholder credential in configuration | `security.placeholder-credential` | `SEC-CON-002` | `implemented` | `engine/src/codestrata/application/rules/security/rules.py` | `engine/tests/application/rules/security/` | Finding via Shared Rule Platform when pack enabled |
| `SE-004` | TLS verification disabled | `security.tls-verification-disabled` | `SEC-CON-003` | `implemented` | `engine/src/codestrata/application/rules/security/rules.py` | `engine/tests/application/rules/security/` | Finding via Shared Rule Platform when pack enabled |
| `SE-005` | Hostname verification disabled | `security.hostname-verification-disabled` | `SEC-CON-003` | `implemented` | `engine/src/codestrata/application/rules/security/rules.py` | `engine/tests/application/rules/security/` | Finding via Shared Rule Platform when pack enabled |
| `SE-006` | Authentication disabled | `security.authentication-disabled` | `SEC-CON-004` | `implemented` | `engine/src/codestrata/application/rules/security/rules.py` | `engine/tests/application/rules/security/` | Finding via Shared Rule Platform when pack enabled |
| `SE-007` | Permissive CORS origin | `security.permissive-cors-origin` | `SEC-CON-005` | `implemented` | `engine/src/codestrata/application/rules/security/rules.py` | `engine/tests/application/rules/security/` | Finding via Shared Rule Platform when pack enabled |
| `SE-008` | Debug enabled | `security.debug-enabled` | `SEC-CON-006` | `implemented` | `engine/src/codestrata/application/rules/security/rules.py` | `engine/tests/application/rules/security/` | Finding via Shared Rule Platform when pack enabled |

## Domain: `technical-debt`

| Catalog ID | Rule Name | Runtime Rule ID | Concept ID | Status | Implementation | Tests | Report usage |
| ---------- | --------- | --------------- | ---------- | ------ | -------------- | ----- | ------------ |
| `TD-001` | Large callable | `technical_debt.large-callable` | `TD-CON-001` | `implemented` | `engine/src/codestrata/application/rules/technical_debt/rules.py` | `engine/tests/application/rules/technical_debt/` | Finding via Shared Rule Platform when pack enabled |
| `TD-002` | Excessive branching | `technical_debt.excessive-branching` | `TD-CON-002` | `implemented` | `engine/src/codestrata/application/rules/technical_debt/rules.py` | `engine/tests/application/rules/technical_debt/` | Finding via Shared Rule Platform when pack enabled |
| `TD-003` | Deep nesting | `technical_debt.deep-nesting` | `TD-CON-003` | `implemented` | `engine/src/codestrata/application/rules/technical_debt/rules.py` | `engine/tests/application/rules/technical_debt/` | Finding via Shared Rule Platform when pack enabled |
| `TD-004` | Excessive parameters | `technical_debt.excessive-parameters` | `TD-CON-004` | `implemented` | `engine/src/codestrata/application/rules/technical_debt/rules.py` | `engine/tests/application/rules/technical_debt/` | Finding via Shared Rule Platform when pack enabled |
| `TD-005` | Oversized type | `technical_debt.oversized-type` | `TD-CON-005` | `implemented` | `engine/src/codestrata/application/rules/technical_debt/rules.py` | `engine/tests/application/rules/technical_debt/` | Finding via Shared Rule Platform when pack enabled |

## Domains without runtime rules yet

Concepts exist for `cost`, `compliance`, `modernization`, and `portfolio`.
Catalog Rule IDs will be assigned when Engine packs are implemented.

## Related

- [TRACEABILITY.md](TRACEABILITY.md)
- [CONCEPTS.md](CONCEPTS.md)
- [ASSESSMENT_CONCEPTS.md](ASSESSMENT_CONCEPTS.md)
