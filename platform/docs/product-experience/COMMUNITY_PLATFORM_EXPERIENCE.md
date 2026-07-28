# Community versus Platform Experience

**Phase:** 9.1 audit  
**Normative boundary:** [`governance/constitution/006_COMMUNITY_PLATFORM_BOUNDARIES.md`](../../../governance/constitution/006_COMMUNITY_PLATFORM_BOUNDARIES.md)

## One-line split

> **Engine** helps a team understand and improve a repository.  
> **Platform** helps an organization persist, connect, retrieve, and reason across repositories.

## Community Engine — must remain useful alone

| Capability | Status today |
| ---------- | ------------ |
| Install CLI package | Yes |
| `init` / `doctor` / `assess --no-ai` | Yes (when config valid) |
| Deterministic findings & recommendations | Yes |
| HTML + JSON reports | Yes |
| Optional Modernization Advisor | Yes (`--with-ai`) |
| Local knowledge store (SQLite) | Yes (intentional) |
| MCP (optional extra) | Yes when enabled |
| Shared rules / evidence / architecture helpers | Yes (advanced) |

**Must not require:** Platform API, Postgres, RAG, Portfolio, EI, Presentation, Strategic Roadmap.

## Platform — commercial additions

| Capability | Notes |
| ---------- | ----- |
| Multi-tenant REST `/api/v1` | API key + Postgres |
| Ingestion of Engine artifacts | Bridge |
| CEIM / Engineering Snapshot | Canonical persistence |
| Knowledge Graph | Persistent |
| Retrieval + Answering | Flags |
| Portfolio + Portfolio RAG/Ask | Flags |
| Executive Intelligence | Flag |
| On-read Presentation / Roadmap | Flags |
| CLI extensions `ai`, `enterprise`, `repository` | Entry points |
| MCP RAG / enterprise tools | Extensions |

## Messaging gaps

1. Root CLI help does not explain Community vs Platform.
2. `enterprise` naming suggests a third product.
3. HTML “Community Edition” footer uses “CodeStrata AI”.
4. Users may think onboard/RAG/`repository` are Community core.

## Source retention

Engine uses local workspace/output dirs; Platform artifact storage is tenant-scoped when enabled. Customer-facing “we don’t retain source” needs an explicit, accurate statement per edition (P1 docs).

## Inheritance for Community repos

Export should carry applicable Governance + Knowledge references; not Platform-only playbooks or commercial API docs as required reading.
