# Modernization Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `modernization`

## Purpose

Define modernization strategy knowledge: sequencing, waves, and transformation patterns.

## Why this domain exists

Assessments must connect findings to coherent modernization action, not isolated fixes.

## Scope

**In scope**

- Modernization patterns (rehost, refactor, rearchitect, replace — conceptual)
- Wave planning and dependency ordering concepts
- Strangler and incremental modernization concepts
- Readiness and risk tradeoff concepts

**Out of scope**

- Project management tooling
- Staffing plans
- Vendor selection scorecards as products

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [architecture](../architecture/README.md) | Target-state structure |
| [technical-debt](../technical-debt/README.md) | Debt burn-down |
| [cloud](../cloud/README.md) | Cloud migration |
| [dependency](../dependency/README.md) | Platform upgrades |
| [portfolio](../portfolio/README.md) | Estate-level sequencing |

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

Keep pattern language stable; implementation roadmaps remain product surfaces.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
