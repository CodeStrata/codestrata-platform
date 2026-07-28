# Cost Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `cost`

## Purpose

Define engineering cost and efficiency knowledge (FinOps-adjacent concepts).

## Why this domain exists

Engineering choices create lasting cost; assessments should surface waste drivers.

## Scope

**In scope**

- Cost drivers tied to architecture and cloud choices
- Waste and efficiency concepts
- Right-sizing and utilization concepts
- Cost visibility and attribution concepts

**Out of scope**

- Invoice reconciliation
- Procurement contracts
- Exact price quotes

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [cloud](../cloud/README.md) | Primary spend surface |
| [performance](../performance/README.md) | Inefficiency increases cost |
| [architecture](../architecture/README.md) | Design choices lock cost |
| [portfolio](../portfolio/README.md) | Spend concentration across systems |

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

Keep currency- and vendor-neutral; reference FinOps materials in REFERENCES.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
