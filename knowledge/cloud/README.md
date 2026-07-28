# Cloud Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `cloud`

## Purpose

Define engineering knowledge about cloud readiness, portability, and cloud-native posture.

## Why this domain exists

Cloud decisions affect operability, cost, resilience, and modernization paths.

## Scope

**In scope**

- Cloud readiness and portability signals
- Cloud-native patterns and constraints
- Infrastructure-as-code hygiene concepts
- Managed service and deployment topology concepts

**Out of scope**

- Vendor billing APIs (see cost)
- Identity threat models (see security)
- Compliance attestations (see compliance)

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [architecture](../architecture/README.md) | Cloud topology is an architectural concern |
| [cost](../cost/README.md) | Cloud choices drive spend and waste |
| [security](../security/README.md) | Cloud shared-responsibility boundaries |
| [performance](../performance/README.md) | Elasticity and latency characteristics |
| [modernization](../modernization/README.md) | Cloud migration waves |

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

Add provider-neutral concepts first; provider-specific references stay in REFERENCES.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
