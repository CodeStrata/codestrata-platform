# Performance Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `performance`

## Purpose

Define performance and scalability engineering knowledge for assessments.

## Why this domain exists

Performance risks affect user experience, cost, and cloud sizing decisions.

## Scope

**In scope**

- Latency, throughput, and capacity concepts
- Hotspot and inefficiency patterns
- Caching, I/O, and concurrency concepts at assessment depth
- Scalability readiness concepts

**Out of scope**

- Live load-test orchestration
- APM vendor configuration
- Hardware procurement

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [architecture](../architecture/README.md) | Bottlenecks from structure |
| [cloud](../cloud/README.md) | Elasticity and managed services |
| [cost](../cost/README.md) | Performance waste becomes spend |
| [technical-debt](../technical-debt/README.md) | Inefficient code as debt |

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

Prefer evidence-backed static signals first; dynamic profiling remains future.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
