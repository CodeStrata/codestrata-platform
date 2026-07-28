# 006 — Community & Platform Boundaries

**Status:** Foundation  
**Authority:** Constitution

## Objective

Define the hard and soft boundaries between CodeStrata Engine (Community) and
CodeStrata Platform (Commercial).

## Scope

Packaging, dependency direction, export/publish, and capability ownership.
Does not define pricing or licensing legal text.

## 1. Dependency direction

```text
Platform ──depends on──▶ Engine
Engine    ──must not──▶ Platform
```

Enforced by architecture tests under [tests/architecture/](../../tests/architecture/).

## 2. Capability ownership

| Capability | Engine | Platform |
| ---------- | ------ | -------- |
| Deterministic assessment | Yes | Consumes via ingestion |
| HTML / JSON reports | Yes | May store artifacts |
| Local knowledge store | Yes (intentional) | No (PostgreSQL) |
| Multi-tenant REST API | No | Yes |
| RAG / Answering | Extension / CLI bridges | Yes (canonical) |
| Portfolio / Executive Intelligence | No | Yes |
| Persistent Knowledge Graph | Limited / optional YAML paths | Yes (Engineering Knowledge Graph) |

<!-- TODO: Keep this table aligned with PLATFORM_CAPABILITY_INVENTORY. -->

## 3. Export & public mirrors

Public Engine/examples/plugin repos are generated from this monorepo.
See [platform/README.md](../../platform/README.md) maintainer handbook and
[public-export-manifest.yaml](../../public-export-manifest.yaml).

**Rule:** Do not publish Platform commercial packages as Community.

## 4. Extension model

Engine extension API allows Platform (and others) to register CLI/MCP capabilities
without reversing dependency direction.
See [engine/docs/extension-architecture.md](../../engine/docs/extension-architecture.md).

## 5. Audience principle

> Community / Engine helps teams understand and improve software.  
> Platform helps leaders understand, govern, and modernize an engineering organization.

### Engine (Community) surfaces (conceptual)

- repository assessment
- local execution and local knowledge store
- deterministic findings and recommendations
- Engineering Assessment reports
- local MCP / extensibility

### Platform (Commercial) surfaces (conceptual)

- multi-tenant persistence and APIs
- portfolio / executive intelligence
- RAG answering at scale
- organization workflows, auth, and policy controls

Detailed capability inventory remains implementation documentation:
[platform/docs/architecture/PLATFORM_CAPABILITY_INVENTORY.md](../../platform/docs/architecture/PLATFORM_CAPABILITY_INVENTORY.md).

## 6. Governance inheritance

Community repositories inherit applicable `governance/standards/` and
`governance/constitution/` documents, plus applicable `knowledge/` references.
Platform-only playbooks remain private with this monorepo.

## 7. References

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [platform/docs/architecture/PLATFORM_ARCHITECTURE.md](../../platform/docs/architecture/PLATFORM_ARCHITECTURE.md)
- [engine/docs/community-edition.md](../../engine/docs/community-edition.md)
- [knowledge/ASSESSMENT_CONCEPTS.md](../../knowledge/ASSESSMENT_CONCEPTS.md)
