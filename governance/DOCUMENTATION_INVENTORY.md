# Documentation Inventory

**Status:** Phase 8.9.3 consolidation
**Scope:** Source Markdown in the monorepo (excludes `.venv/`, `.git/`,
`.export-staging/`, `.codestrata-examples/`, `reports/`, prompt packs).

## Canonical authorities

| Authority | Path | Owns |
| --------- | ---- | ---- |
| Governance | `governance/` | How CodeStrata is designed, built, evolved |
| Knowledge | `knowledge/` | What CodeStrata knows about software engineering |

Implementation and user docs **reference** these authorities; they must not
restate normative principles or domain concepts as competing sources of truth.

## Classification summary

| Category | Count |
| -------- | ----- |
| Developer Documentation | 197 |
| Engineering Knowledge | 113 |
| Governance | 26 |
| Operational Documentation | 13 |
| User Documentation | 39 |
| **Total** | **388** |

## Inventory by category

### Developer Documentation

- `.pytest_cache/README.md`
- `ARCHITECTURE.md`
- `CONTRIBUTING.md`
- `engine/.pytest_cache/README.md`
- `engine/CODE_OF_CONDUCT.md`
- `engine/CONTRIBUTING.md`
- `engine/docs/README.md`
- `engine/docs/agent-framework.md`
- `engine/docs/ai-enrichment.md`
- `engine/docs/analysis-intelligence/README.md`
- `engine/docs/analysis-intelligence/ai-readiness/README.md`
- `engine/docs/analysis-intelligence/ai-readiness/configuration.md`
- `engine/docs/analysis-intelligence/ai-readiness/hygiene-rules.md`
- `engine/docs/analysis-intelligence/ai-readiness/inventory.md`
- `engine/docs/analysis-intelligence/ai-readiness/report.md`
- `engine/docs/analysis-intelligence/ai-readiness/synthesis.md`
- `engine/docs/analysis-intelligence/architecture-assessment/README.md`
- `engine/docs/analysis-intelligence/architecture-assessment/artifacts.md`
- `engine/docs/analysis-intelligence/architecture-assessment/assembly.md`
- `engine/docs/analysis-intelligence/architecture-assessment/cli.md`
- `engine/docs/analysis-intelligence/architecture-assessment/conclusions.md`
- `engine/docs/analysis-intelligence/architecture-assessment/configuration.md`
- `engine/docs/analysis-intelligence/architecture-assessment/domain-model.md`
- `engine/docs/analysis-intelligence/architecture-assessment/examples.md`
- `engine/docs/analysis-intelligence/architecture-assessment/findings.md`
- `engine/docs/analysis-intelligence/architecture-assessment/limitations-and-future-work.md`
- `engine/docs/analysis-intelligence/architecture-assessment/mcp.md`
- `engine/docs/analysis-intelligence/architecture-assessment/schema-and-versioning.md`
- `engine/docs/analysis-intelligence/architecture-assessment/statuses.md`
- `engine/docs/analysis-intelligence/architecture-assessment/strengths.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/README.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/architecture.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/cli.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/clustering.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/confidence.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/configuration.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/domain-model.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/examples.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/finding-relationships.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/materiality.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/mcp.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/policies.md`
- `engine/docs/analysis-intelligence/architecture-reporting/README.md`
- `engine/docs/analysis-intelligence/architecture-reporting/architecture-report-model.md`
- `engine/docs/analysis-intelligence/architecture-reporting/assessment-adapter.md`
- `engine/docs/analysis-intelligence/architecture-reporting/cli.md`
- `engine/docs/analysis-intelligence/architecture-reporting/compatibility.md`
- `engine/docs/analysis-intelligence/architecture-reporting/conclusions.md`
- `engine/docs/analysis-intelligence/architecture-reporting/configuration.md`
- `engine/docs/analysis-intelligence/architecture-reporting/examples.md`
- `engine/docs/analysis-intelligence/architecture-reporting/executive-summary.md`
- `engine/docs/analysis-intelligence/architecture-reporting/findings.md`
- `engine/docs/analysis-intelligence/architecture-reporting/html-section.md`
- `engine/docs/analysis-intelligence/architecture-reporting/limitations-and-future-work.md`
- `engine/docs/analysis-intelligence/architecture-reporting/mcp.md`
- `engine/docs/analysis-intelligence/architecture-reporting/report-json.md`
- `engine/docs/analysis-intelligence/architecture-reporting/strengths.md`
- `engine/docs/analysis-intelligence/architecture/README.md`
- `engine/docs/analysis-intelligence/architecture/configuration.md`
- `engine/docs/analysis-intelligence/architecture/evidence.md`
- `engine/docs/analysis-intelligence/architecture/examples.md`
- `engine/docs/analysis-intelligence/architecture/migration.md`
- `engine/docs/analysis-intelligence/architecture/rule-pack.md`
- `engine/docs/analysis-intelligence/architecture/rules.md`
- `engine/docs/analysis-intelligence/architecture/severity.md`
- `engine/docs/analysis-intelligence/cloud/README.md`
- `engine/docs/analysis-intelligence/cloud/configuration.md`
- `engine/docs/analysis-intelligence/cloud/hygiene-rules.md`
- `engine/docs/analysis-intelligence/cloud/inventory.md`
- `engine/docs/analysis-intelligence/cloud/report.md`
- `engine/docs/analysis-intelligence/cloud/synthesis.md`
- `engine/docs/analysis-intelligence/dependency/README.md`
- `engine/docs/analysis-intelligence/dependency/assessment-inventory.md`
- `engine/docs/analysis-intelligence/dependency/configuration.md`
- `engine/docs/analysis-intelligence/dependency/evidence-ownership.md`
- `engine/docs/analysis-intelligence/dependency/evidence.md`
- `engine/docs/analysis-intelligence/dependency/hygiene-rules.md`
- `engine/docs/analysis-intelligence/dependency/report.md`
- `engine/docs/analysis-intelligence/dependency/synthesis.md`
- `engine/docs/analysis-intelligence/evidence-providers/README.md`
- `engine/docs/analysis-intelligence/evidence-providers/adding-a-provider.md`
- `engine/docs/analysis-intelligence/evidence-providers/architecture.md`
- `engine/docs/analysis-intelligence/evidence-providers/capabilities.md`
- `engine/docs/analysis-intelligence/evidence-providers/cli.md`
- `engine/docs/analysis-intelligence/evidence-providers/configuration.md`
- `engine/docs/analysis-intelligence/evidence-providers/contracts.md`
- `engine/docs/analysis-intelligence/evidence-providers/csharp.md`
- `engine/docs/analysis-intelligence/evidence-providers/examples.md`
- `engine/docs/analysis-intelligence/evidence-providers/java.md`
- `engine/docs/analysis-intelligence/evidence-providers/javascript.md`
- `engine/docs/analysis-intelligence/evidence-providers/mcp.md`
- `engine/docs/analysis-intelligence/evidence-providers/normalized-evidence.md`
- `engine/docs/analysis-intelligence/evidence-providers/php.md`
- `engine/docs/analysis-intelligence/evidence-providers/provenance.md`
- `engine/docs/analysis-intelligence/evidence-providers/provider-registry.md`
- `engine/docs/analysis-intelligence/evidence-providers/python.md`
- `engine/docs/analysis-intelligence/evidence.md`
- `engine/docs/analysis-intelligence/incremental-rules.md`
- `engine/docs/analysis-intelligence/performance/README.md`
- `engine/docs/analysis-intelligence/performance/configuration.md`
- `engine/docs/analysis-intelligence/performance/hygiene-rules.md`
- `engine/docs/analysis-intelligence/performance/inventory.md`
- `engine/docs/analysis-intelligence/performance/report.md`
- `engine/docs/analysis-intelligence/performance/synthesis.md`
- `engine/docs/analysis-intelligence/repository-ai-readiness-evidence.md`
- `engine/docs/analysis-intelligence/repository-cloud-evidence.md`
- `engine/docs/analysis-intelligence/repository-performance-evidence.md`
- `engine/docs/analysis-intelligence/repository-sensitive-evidence.md`
- `engine/docs/analysis-intelligence/repository-test-evidence.md`
- `engine/docs/analysis-intelligence/rule-authoring.md`
- `engine/docs/analysis-intelligence/rule-lifecycle.md`
- `engine/docs/analysis-intelligence/rule-platform-migration.md`
- `engine/docs/analysis-intelligence/security/README.md`
- `engine/docs/analysis-intelligence/security/assessment-inventory.md`
- `engine/docs/analysis-intelligence/security/configuration.md`
- `engine/docs/analysis-intelligence/security/hygiene-rules.md`
- `engine/docs/analysis-intelligence/security/ownership-boundaries.md`
- `engine/docs/analysis-intelligence/security/report.md`
- `engine/docs/analysis-intelligence/security/synthesis.md`
- `engine/docs/analysis-intelligence/shared-rule-platform.md`
- `engine/docs/analysis-intelligence/suppression.md`
- `engine/docs/analysis-intelligence/technical-debt-reporting/README.md`
- `engine/docs/analysis-intelligence/technical-debt/README.md`
- `engine/docs/analysis-intelligence/technical-debt/complexity-assessment.md`
- `engine/docs/analysis-intelligence/technical-debt/complexity-evidence.md`
- `engine/docs/analysis-intelligence/technical-debt/complexity-rules.md`
- `engine/docs/analysis-intelligence/technical-debt/rule-pack.md`
- `engine/docs/analysis-intelligence/technical-debt/synthesis.md`
- `engine/docs/analysis-intelligence/testing-rules.md`
- `engine/docs/analysis-intelligence/testing/README.md`
- `engine/docs/analysis-intelligence/testing/configuration.md`
- `engine/docs/analysis-intelligence/testing/hygiene-rules.md`
- `engine/docs/analysis-intelligence/testing/inventory.md`
- `engine/docs/analysis-intelligence/testing/report.md`
- `engine/docs/analysis-intelligence/testing/synthesis.md`
- `engine/docs/architecture-guide.md`
- `engine/docs/architecture/README.md`
- `engine/docs/architecture/ai-enrichment.md`
- `engine/docs/architecture/analysis-intelligence-conventions.md`
- `engine/docs/architecture/assess-runtime-graphs.md`
- `engine/docs/architecture/assessment-graph.md`
- `engine/docs/architecture/html-report-v2.md`
- `engine/docs/architecture/recommendation-engine.md`
- `engine/docs/architecture/rule-engine.md`
- `engine/docs/assessment-framework/README.md`
- `engine/docs/assessment-framework/examples.md`
- `engine/docs/assessment-framework/report-structure.md`
- `engine/docs/assessment-graph.md`
- `engine/docs/capabilities.md`
- `engine/docs/coding-standards.md`
- `engine/docs/contributor-guide.md`
- `engine/docs/decisions/0001-initial-architecture.md`
- `engine/docs/extension-architecture.md`
- `engine/docs/images/README.md`
- `engine/docs/incremental-assessment.md`
- `engine/docs/knowledge-store.md`
- `engine/docs/modernization-roadmap.md`
- `engine/docs/recommendation-engine.md`
- `engine/docs/report-contract.md`
- `engine/docs/report-generation.md`
- `engine/docs/repository-graph.md`
- `engine/docs/repository-knowledge/README.md`
- `engine/docs/repository-onboarding.md`
- `engine/docs/rule-engine.md`
- `engine/docs/runtime-performance.md`
- `engine/docs/runtime.md`
- `engine/examples/README.md`
- `platform/README.md`
- `platform/docs/README.md`
- `platform/docs/architecture/PLATFORM_ARCHITECTURE.md`
- `platform/docs/architecture/PLATFORM_CAPABILITY_INVENTORY.md`
- `platform/docs/getting-started.md`
- `platform/docs/knowledge_graph/README.md`
- `platform/docs/knowledge_graph/cli.md`
- `platform/docs/knowledge_graph/entities.md`
- `platform/docs/knowledge_graph/examples.md`
- `platform/docs/knowledge_graph/graph-building.md`
- `platform/docs/knowledge_graph/incremental-rebuild.md`
- `platform/docs/knowledge_graph/mcp.md`
- `platform/docs/knowledge_graph/provenance.md`
- `platform/docs/knowledge_graph/querying.md`
- `platform/docs/knowledge_graph/relationships.md`
- `platform/docs/knowledge_graph/repository-resolution.md`
- `platform/docs/knowledge_graph/schema-versioning.md`
- `platform/docs/knowledge_graph/security.md`
- `platform/docs/knowledge_graph/validation.md`
- `platform/docs/knowledge_graph/workspace.md`
- `platform/docs/rag/README.md`
- `platform/docs/rag/ai-providers.md`
- `platform/docs/rag/embedding-and-indexing.md`
- `platform/docs/rag/grounded-answering.md`
- `platform/docs/rag/metadata-and-traceability.md`
- `platform/docs/rag/projection-and-chunking.md`
- `platform/docs/rag/provider-decision.md`
- `platform/docs/rag/retrieval.md`
- `platform/docs/rag/vector-store-setup.md`
- `platform/docs/rag/vector-store.md`

### Engineering Knowledge

- `engine/docs/analysis-intelligence/ai-readiness/domain-foundation.md`
- `engine/docs/analysis-intelligence/ai-readiness/taxonomy.md`
- `engine/docs/analysis-intelligence/architecture-assessment/coverage.md`
- `engine/docs/analysis-intelligence/architecture-assessment/limitations.md`
- `engine/docs/analysis-intelligence/architecture-assessment/recommendations.md`
- `engine/docs/analysis-intelligence/architecture-assessment/traceability.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/coverage-and-limitations.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/limitations.md`
- `engine/docs/analysis-intelligence/architecture-conclusions/recommendations.md`
- `engine/docs/analysis-intelligence/architecture-reporting/coverage.md`
- `engine/docs/analysis-intelligence/architecture-reporting/limitations.md`
- `engine/docs/analysis-intelligence/architecture-reporting/recommendations.md`
- `engine/docs/analysis-intelligence/architecture-reporting/traceability.md`
- `engine/docs/analysis-intelligence/architecture/limitations.md`
- `engine/docs/analysis-intelligence/architecture/recommendations.md`
- `engine/docs/analysis-intelligence/cloud/domain-foundation.md`
- `engine/docs/analysis-intelligence/cloud/taxonomy.md`
- `engine/docs/analysis-intelligence/dependency/taxonomy.md`
- `engine/docs/analysis-intelligence/evidence-providers/coverage.md`
- `engine/docs/analysis-intelligence/evidence-providers/limitations.md`
- `engine/docs/analysis-intelligence/performance/domain-foundation.md`
- `engine/docs/analysis-intelligence/performance/taxonomy.md`
- `engine/docs/analysis-intelligence/security/domain-foundation.md`
- `engine/docs/analysis-intelligence/security/taxonomy.md`
- `engine/docs/analysis-intelligence/testing/domain-foundation.md`
- `engine/docs/analysis-intelligence/testing/taxonomy.md`
- `engine/docs/assessment-framework/community-enterprise-boundary.md`
- `engine/docs/assessment-framework/coverage.md`
- `engine/docs/assessment-framework/dimensions.md`
- `engine/docs/assessment-framework/evidence-and-confidence.md`
- `engine/docs/assessment-framework/executive-narrative.md`
- `engine/docs/assessment-framework/limitations.md`
- `engine/docs/assessment-framework/methodology.md`
- `engine/docs/assessment-framework/modernization-prioritization.md`
- `engine/docs/assessment-framework/positive-evidence.md`
- `engine/docs/assessment-framework/recommendations.md`
- `engine/docs/assessment-framework/rule-taxonomy.md`
- `engine/docs/assessment-framework/scoring.md`
- `engine/docs/assessment-framework/severity-and-business-impact.md`
- `engine/docs/assessment-framework/traceability.md`
- `knowledge/README.md`
- `knowledge/ai/FINDINGS.md`
- `knowledge/ai/MATURITY_MODEL.md`
- `knowledge/ai/README.md`
- `knowledge/ai/RECOMMENDATIONS.md`
- `knowledge/ai/REFERENCES.md`
- `knowledge/ai/RULES.md`
- `knowledge/architecture/FINDINGS.md`
- `knowledge/architecture/MATURITY_MODEL.md`
- `knowledge/architecture/README.md`
- `knowledge/architecture/RECOMMENDATIONS.md`
- `knowledge/architecture/REFERENCES.md`
- `knowledge/architecture/RULES.md`
- `knowledge/cloud/FINDINGS.md`
- `knowledge/cloud/MATURITY_MODEL.md`
- `knowledge/cloud/README.md`
- `knowledge/cloud/RECOMMENDATIONS.md`
- `knowledge/cloud/REFERENCES.md`
- `knowledge/cloud/RULES.md`
- `knowledge/compliance/FINDINGS.md`
- `knowledge/compliance/MATURITY_MODEL.md`
- `knowledge/compliance/README.md`
- `knowledge/compliance/RECOMMENDATIONS.md`
- `knowledge/compliance/REFERENCES.md`
- `knowledge/compliance/RULES.md`
- `knowledge/cost/FINDINGS.md`
- `knowledge/cost/MATURITY_MODEL.md`
- `knowledge/cost/README.md`
- `knowledge/cost/RECOMMENDATIONS.md`
- `knowledge/cost/REFERENCES.md`
- `knowledge/cost/RULES.md`
- `knowledge/dependency/FINDINGS.md`
- `knowledge/dependency/MATURITY_MODEL.md`
- `knowledge/dependency/README.md`
- `knowledge/dependency/RECOMMENDATIONS.md`
- `knowledge/dependency/REFERENCES.md`
- `knowledge/dependency/RULES.md`
- `knowledge/documentation/FINDINGS.md`
- `knowledge/documentation/MATURITY_MODEL.md`
- `knowledge/documentation/README.md`
- `knowledge/documentation/RECOMMENDATIONS.md`
- `knowledge/documentation/REFERENCES.md`
- `knowledge/documentation/RULES.md`
- `knowledge/modernization/FINDINGS.md`
- `knowledge/modernization/MATURITY_MODEL.md`
- `knowledge/modernization/README.md`
- `knowledge/modernization/RECOMMENDATIONS.md`
- `knowledge/modernization/REFERENCES.md`
- `knowledge/modernization/RULES.md`
- `knowledge/performance/FINDINGS.md`
- `knowledge/performance/MATURITY_MODEL.md`
- `knowledge/performance/README.md`
- `knowledge/performance/RECOMMENDATIONS.md`
- `knowledge/performance/REFERENCES.md`
- `knowledge/performance/RULES.md`
- `knowledge/portfolio/FINDINGS.md`
- `knowledge/portfolio/MATURITY_MODEL.md`
- `knowledge/portfolio/README.md`
- `knowledge/portfolio/RECOMMENDATIONS.md`
- `knowledge/portfolio/REFERENCES.md`
- `knowledge/portfolio/RULES.md`
- `knowledge/security/FINDINGS.md`
- `knowledge/security/MATURITY_MODEL.md`
- `knowledge/security/README.md`
- `knowledge/security/RECOMMENDATIONS.md`
- `knowledge/security/REFERENCES.md`
- `knowledge/security/RULES.md`
- `knowledge/technical-debt/FINDINGS.md`
- `knowledge/technical-debt/MATURITY_MODEL.md`
- `knowledge/technical-debt/README.md`
- `knowledge/technical-debt/RECOMMENDATIONS.md`
- `knowledge/technical-debt/REFERENCES.md`
- `knowledge/technical-debt/RULES.md`

### Governance

- `governance/README.md`
- `governance/ai/CURSOR_INSTRUCTIONS.md`
- `governance/ai/PROMPT_TEMPLATE.md`
- `governance/ai/REVIEW_CHECKLIST.md`
- `governance/assets/DESIGN-SYSTEM.md`
- `governance/assets/README.md`
- `governance/constitution/001_PRODUCT_VISION.md`
- `governance/constitution/002_ENGINEERING_CONSTITUTION.md`
- `governance/constitution/003_ARCHITECTURE_PRINCIPLES.md`
- `governance/constitution/004_PRODUCT_PRINCIPLES.md`
- `governance/constitution/005_SECURITY_PRIVACY_PRINCIPLES.md`
- `governance/constitution/006_COMMUNITY_PLATFORM_BOUNDARIES.md`
- `governance/constitution/007_AI_PHILOSOPHY.md`
- `governance/playbooks/CUSTOMER_DEMO_CHECKLIST.md`
- `governance/playbooks/DESIGN_PARTNER_ONBOARDING.md`
- `governance/playbooks/DOGFOOD_CHECKLIST.md`
- `governance/playbooks/INTERNAL_RELEASE_CHECKLIST.md`
- `governance/playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md`
- `governance/playbooks/RC_CHECKLIST.md`
- `governance/release/COMMUNITY_RELEASE_CHECKLIST.md`
- `governance/release/EXTRACTION_HARDENING.md`
- `governance/release/README.md`
- `governance/release/RELEASE_SURFACE_INVENTORY.md`
- `governance/metrics/COMMUNITY_METRICS.md`
- `governance/adr/ADR-001-platform-openapi-source-of-truth.md`
- `governance/standards/API_STANDARDS.md`
- `governance/standards/BRANDING_GUIDELINES.md`
- `governance/standards/CODING_STANDARDS.md`
- `governance/standards/DOCUMENTATION_STANDARDS.md`
- `governance/standards/NAMING_CONVENTIONS.md`
- `governance/standards/REPORT_STANDARDS.md`
- `governance/standards/TESTING_STANDARDS.md`

### Operational Documentation

- `CHANGELOG.md`
- `ROADMAP.md`
- `engine/SECURITY.md`
- `engine/docs/COMMUNITY_EDITION_CHECKLIST.md`
- `engine/docs/RELEASE_NOTES-0.1.0.md`
- `engine/docs/mvp-acceptance.md`
- `engine/docs/mvp-regression.md`
- `engine/docs/release-readiness.md`
- `engine/docs/roadmap.md`
- `engine/docs/security/README.md`
- `engine/docs/security/architecture.md`
- `engine/docs/security/production-hardening-checklist.md`
- `engine/docs/security/threat-model.md`

### User Documentation

- `README.md`
- `cursor-plugin/PLACEHOLDER.md`
- `cursor-plugin/README.md`
- `engine/README.md`
- `engine/SUPPORT.md`
- `engine/docs/cli-reference.md`
- `engine/docs/community-edition.md`
- `engine/docs/configuration-profiles.md`
- `engine/docs/installation.md`
- `engine/docs/mcp-server.md`
- `engine/docs/mcp/README.md`
- `engine/docs/mcp/client-examples.md`
- `engine/docs/mcp/overview.md`
- `engine/docs/mcp/repository-knowledge/README.md`
- `engine/docs/mcp/security.md`
- `engine/docs/mcp/setup.md`
- `engine/docs/mcp/tools.md`
- `engine/docs/mcp/troubleshooting.md`
- `engine/docs/quick-start.md`
- `engine/docs/report-interpretation.md`
- `engine/docs/troubleshooting.md`
- `engine/docs/tutorial.md`
- `examples/README.md`
- `examples/expected-results/README.md`
- `examples/expected-results/dotnet-eshop/summary.md`
- `examples/expected-results/laravel-realworld/summary.md`
- `examples/expected-results/spring-petclinic/summary.md`
- `examples/real-world/MANIFEST_SCHEMA.md`
- `examples/real-world/README.md`
- `examples/real-world/THIRD_PARTY.md`
- `test-fixtures/README.md`
- `test-fixtures/sample-csharp-app/README.md`
- `test-fixtures/sample-java-app/README.md`
- `test-fixtures/sample-js-app/README.md`
- `test-fixtures/sample-php-app/README.md`
- `test-fixtures/sample-python-app/README.md`
- `test-fixtures/sample-reports/README.md`
- `vscode-plugin/PLACEHOLDER.md`
- `vscode-plugin/README.md`

## Consolidation actions (this phase)

1. Migrated assessment methodology concepts into `knowledge/ASSESSMENT_CONCEPTS.md`.
2. Migrated Community/Enterprise audience principles into Governance `006`.
3. Pointed `engine/docs/coding-standards.md` at Governance coding standards.
4. Replaced duplicated conceptual assessment-framework docs with stubs.
5. Replaced domain taxonomy docs with Knowledge pointers; enriched domain FINDINGS.
6. Retained installation, CLI, security ops, architecture implementation inventories.
7. Left `.export-staging/` untouched (generated).
8. Updated indexes (`README`, `CONTRIBUTING`, Engine/Platform docs READMEs) to cite authorities.

