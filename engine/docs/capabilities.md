# Capabilities

| Capability | Status |
| ---------- | ------ |
| Repository assessment | Available |
| Engineering knowledge store | Available |
| MCP + agents | Available |
| Incremental assessment (opt-in) | Available |
| Engineering Knowledge Graph (YAML; Platform) | Available (optional) |
| Shared Rule Platform (4.1) | Available (disabled by default) |
| Rule Platform Integration Bridge (4.1.1) | Available (compatibility layer) |
| Assessment Framework methodology (4.1.2) | Documented |
| Architecture Intelligence pack (4.2.1) | Available (`architecture.core`; assess opt-in) |
| Language Evidence Providers (4.2.2) | Available (disabled by default; `codestrata evidence`) |
| Architecture Conclusions (4.2.3) | Available (disabled by default; `codestrata architecture conclusions`) |
| Architecture Assessment Integration (4.2.4) | Available (disabled by default; `architecture-assessment.json`) |
| Architecture CTO Report Integration (4.2.5) | Available (disabled by default; `assessment.architecture` in report) |
| Technical Debt Domain Foundation (4.3.1) | Available (domain/config only; disabled by default) |
| Complexity Evidence (4.3.2) | Available (Python/Java collectors; Language Evidence owned) |
| Technical Debt Complexity Rules (4.3.3) | Available (SharedRule pack; pack disabled by default) |
| Technical Debt Assessment Vertical (4.3.4 / 4.3.4A) | Available (production-primary inventory + hotspots; dogfood accepted) |
| Technical Debt Assessment Synthesis (4.3.5) | Available (themes/conclusions/recommendations; section opt-in) |
| Technical Debt CTO Report Integration (4.3.6) | Available (disabled by default; `assessment.technical_debt` in report) |
| Dependency Intelligence Domain Foundation (4.4.1) | Available (domain/config only; disabled by default) |
| Dependency Evidence Platform (4.4.2) | Available (disabled by default; `dependency-evidence.json`) |
| Dependency Hygiene Rules (4.4.3) | Available (disabled by default; SharedRules → Findings) |
| Dependency unresolved-version precision (4.4.3A) | Available (proven-unresolved only; Gradle interpolations are diagnostics) |
| Dependency Inventory / Assessment Usability (4.4.4) | Available (disabled by default; production-primary `dependency-assessment.json` 1.1.0+) |
| Dependency Assessment Synthesis (4.4.5) | Available (disabled by default; themes/conclusions/recommendations on schema 1.2.0) |
| Dependency CTO Report Integration (4.4.6) | Available (disabled by default; `assessment.dependency` in report) |
| Security Intelligence Domain Foundation (4.5.1) | Available (domain/config only; disabled by default; no scanning) |
| Repository-Sensitive Evidence (4.5.2) | Available (disabled by default; `repository-sensitive-evidence.json` 1.1.0; no Findings/rules) |
| Security Hygiene Rules (4.5.3) | Available (disabled by default; `security.core` → Findings; pack unchanged in 4.5.4) |
| Security Assessment Inventory (4.5.4) | Available (disabled by default; inventories/hotspots on schema 1.3.0) |
| Security Assessment Synthesis (4.5.5) | Available (disabled by default; `include_synthesis=true` when section enabled; no scores/report) |
| Security report | Available (disabled by default; `assessment.security` in report) |
| Test Intelligence Domain Foundation (4.6.1) | Available (domain/config only; disabled by default; no scanning) |
| Repository Test Evidence (4.6.2) | Available (disabled by default; `repository-testing-evidence.json` 1.0.0; platform evidence) |
| Test Hygiene Rules (4.6.3) | Available (disabled by default; `testing.core` → Findings; TEST-004 deferred) |
| Test Assessment Inventory (4.6.4) | Available (disabled by default; inventories on schema 1.2.0) |
| Test Assessment Synthesis (4.6.5) | Available (disabled by default; `include_synthesis=true` when section enabled; no scores/report) |
| Test report | Available (disabled by default; `assessment.testing` in report) |
| Cloud Intelligence Domain Foundation (4.7.1) | Available (domain/config only; disabled by default; no scanning) |
| Repository Cloud Evidence (4.7.2) | Available (disabled by default; `repository-cloud-evidence.json` 1.0.0; platform evidence) |
| Cloud Hygiene Rules (4.7.3) | Available (disabled by default; `cloud.core` 1.0.0; 11 rules; Findings only) |
| Cloud Assessment Inventory (4.7.4) | Available (disabled by default; `cloud-assessment` 1.1.0; inventories only) |
| Cloud Assessment Synthesis (4.7.5) | Available (disabled by default; `include_synthesis=true` when analysis enabled; no scores) |
| Cloud report (4.7.6) | Available (disabled by default; `assessment.cloud` in report) |
| AI Readiness Domain Foundation (4.8.1) | Available (domain/config only; disabled by default; no scanning) |
| Repository AI-Readiness Evidence (4.8.2) | Available (disabled by default; `repository-ai-readiness-evidence.json` 1.0.0; platform evidence) |
| AI Readiness Hygiene Rules (4.8.3) | Available (disabled by default; `ai_readiness.core` 1.0.0; 17 rules; Findings only) |
| AI Readiness Assessment Inventory (4.8.4) | Available (disabled by default; `ai-readiness-assessment` 1.1.0; inventories) |
| AI Readiness Assessment Synthesis (4.8.5) | Available (disabled by default; `include_synthesis=true` when analysis enabled; no scores) |
| AI Readiness Report Integration (4.8.6) | Available (disabled by default; `report.ai_readiness` 1.0.0; presentation only) |
| Performance Domain Foundation (4.9.1) | Available (domain/config only; disabled by default; no scanning) |
| Repository Performance Evidence (4.9.2) | Available (disabled by default; `repository-performance-evidence.json` 1.0.0; platform evidence) |
| Performance Hygiene Rules (4.9.3) | Available (disabled by default; `performance.core` 1.0.0; 20 rules; Findings only) |
| Performance Assessment Inventory (4.9.4) | Available (disabled by default; `performance-assessment` 1.1.0; inventories) |
| Performance Assessment Synthesis (4.9.5) | Available (disabled by default; `include_synthesis=true` when analysis enabled; no scores) |
| Performance Report Integration (4.9.6) | Available (disabled by default; `report.performance` 1.0.0; presentation only) |
| Dimension scoring / CTO report | Designed (4.1.2); not implemented |
| Analysis Intelligence packs (remaining) | In progress / planned (4.2–4.10) |
| GitHub PR review | Deferred (Phase 6) |
