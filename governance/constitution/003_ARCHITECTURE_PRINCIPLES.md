# 003 — Architecture Principles

**Status:** Foundation  
**Authority:** Constitution

## Objective

Codify architectural principles that all CodeStrata changes must honor.

## Scope

Normative principles for Engine and Platform. Implementation inventory remains in
existing architecture documents (do not duplicate diagrams here).

## 1. System separation

| Component | Responsibility |
| --------- | -------------- |
| CodeStrata Engine | Deterministic assessment, reports, Community CLI/MCP |
| CodeStrata Platform | Persistence, RAG, Knowledge Graph, commercial REST APIs |
| Plugins | Presentation / IDE adapters (future) |

**Hard rule:** Engine runtime must not import Platform.

## 2. Canonical intelligence pipeline

<!-- TODO: Link a single canonical pipeline diagram once Governance migration completes. -->

Working reference: End-to-end assess pipeline in
[ARCHITECTURE.md](../../ARCHITECTURE.md).

Platform commercial pipeline principles (reference, do not restate):

- Ingestion → Intelligence → Engineering Snapshot (CEIM) → Knowledge Graph →
  Retrieval / Answering → Portfolio → Executive Intelligence → Presentation /
  Strategic Roadmap

## 3. Layer rules

| Layer | May depend on | Must not |
| ----- | ------------- | -------- |
| Domain | — | Application, infrastructure, API |
| Application | Domain | Persistence adapters leaking into APIs |
| Infrastructure | Application contracts / Domain as needed | Bypass Application for business rules |
| API / CLI / MCP | Application services | Domain or persistence leakage into transport |

<!-- TODO: Formalize import-direction tests checklist under standards. -->

## 4. Provider neutrality

AI and embedding providers are pluggable capabilities. Product behavior must
remain correct with deterministic / offline paths.

## 5. Persistence principles

- CodeStrata Platform production database: **PostgreSQL**.
- SQLite is not a Platform production database (Engine local knowledge store is
  intentional and separate).

<!-- TODO: Point to finalized SQLite status note after RC documentation migration. -->

## 6. Presentation purity

Presentation and Strategic Roadmap layers are on-read / derived where designed
as such — do not introduce silent persistence without an explicit architecture
decision.

## 7. References

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [platform/docs/architecture/PLATFORM_ARCHITECTURE.md](../../platform/docs/architecture/PLATFORM_ARCHITECTURE.md)
- [platform/docs/architecture/PLATFORM_CAPABILITY_INVENTORY.md](../../platform/docs/architecture/PLATFORM_CAPABILITY_INVENTORY.md)
- [engine/docs/architecture/](../../engine/docs/architecture/)
- [tests/architecture/](../../tests/architecture/)
