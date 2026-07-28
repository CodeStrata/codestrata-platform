# Architecture Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `architecture`

## Purpose

Capture how systems are structured, layered, coupled, and evolved.

## Why this domain exists

Architecture quality drives change cost, risk concentration, and modernization sequencing.

## Scope

**In scope**

- Structural patterns and anti-patterns
- Component / service boundaries and coupling
- Technology topology and architectural fitness
- Architecture conclusions that inform findings

**Out of scope**

- Cloud provider configuration details (see cloud)
- Security control catalogs (see security)
- Portfolio rollups (see portfolio)

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [technical-debt](../technical-debt/README.md) | Structural debt often surfaces as architecture findings |
| [modernization](../modernization/README.md) | Architecture posture shapes modernization waves |
| [dependency](../dependency/README.md) | Dependency graphs inform architectural risk |
| [performance](../performance/README.md) | Hotspots may reflect architectural bottlenecks |
| [portfolio](../portfolio/README.md) | Multi-repo architecture themes aggregate here |

## Domain documents

| Document | Role |
| -------- | ---- |
| [CONCEPTS.md](CONCEPTS.md) | Stable Concept IDs for this domain |
| [RULES.md](RULES.md) | Purpose of engineering rules in this domain |
| [FINDINGS.md](FINDINGS.md) | What findings mean here |
| [RECOMMENDATIONS.md](RECOMMENDATIONS.md) | Recommendation philosophy |
| [MATURITY_MODEL.md](MATURITY_MODEL.md) | Intended maturity structure |
| [REFERENCES.md](REFERENCES.md) | External standards and references |

## Future evolution

Expand pattern catalogs and maturity dimensions without encoding rule IDs here.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
