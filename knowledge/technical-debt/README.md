# Technical Debt Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `technical-debt`

## Purpose

Define how CodeStrata conceptualizes technical debt as an engineering concern.

## Why this domain exists

Debt explains drag on delivery and must be distinguished from security or pure bugs.

## Scope

**In scope**

- Debt categories (structural, code, test, process-adjacent)
- Complexity and maintainability concepts
- Debt prioritization concepts
- Interest vs principal metaphors used carefully

**Out of scope**

- Financial accounting models
- Sprint planning tools
- Style-guide nitpicks without engineering impact

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [architecture](../architecture/README.md) | Structural debt |
| [performance](../performance/README.md) | Debt that becomes runtime cost |
| [documentation](../documentation/README.md) | Knowledge debt |
| [modernization](../modernization/README.md) | Debt burn-down in waves |
| [portfolio](../portfolio/README.md) | Debt concentration across repos |

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

Align categories with findings taxonomy; avoid scoring formulas in this foundation phase.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
