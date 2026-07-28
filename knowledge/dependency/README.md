# Dependency Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `dependency`

## Purpose

Define knowledge about third-party and internal dependency health.

## Why this domain exists

Dependencies dominate supply-chain risk, upgrade cost, and modernization feasibility.

## Scope

**In scope**

- Dependency inventory concepts
- Version freshness and abandonment concepts
- Transitive risk and lockfile hygiene
- License risk concepts at engineering (not legal-advice) level

**Out of scope**

- Full legal license opinions
- Live vulnerability feed operations
- Package registry implementation

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [security](../security/README.md) | Vulnerable dependencies |
| [technical-debt](../technical-debt/README.md) | Stale stacks as debt |
| [modernization](../modernization/README.md) | Upgrade and replacement waves |
| [architecture](../architecture/README.md) | Shared libraries and coupling |

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

Stay ecosystem-agnostic in concepts; language ecosystems appear in REFERENCES.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
