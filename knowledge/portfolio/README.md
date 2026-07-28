# Portfolio Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `portfolio`

## Purpose

Define multi-repository and estate-level engineering knowledge.

## Why this domain exists

Executive and platform decisions require aggregation beyond a single repository.

## Scope

**In scope**

- Portfolio composition and concentration concepts
- Cross-repo risk themes
- Shared technology and dependency concepts
- Estate modernization prioritization concepts

**Out of scope**

- Single-repo deep analysis (other domains)
- HR / team topology products
- Platform persistence schemas

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [modernization](../modernization/README.md) | Estate wave planning |
| [cost](../cost/README.md) | Spend concentration |
| [security](../security/README.md) | Systemic security themes |
| [dependency](../dependency/README.md) | Shared library risk |
| [architecture](../architecture/README.md) | Common architectural patterns |

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

Remain concept-level; Platform portfolio features consume this knowledge later.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
