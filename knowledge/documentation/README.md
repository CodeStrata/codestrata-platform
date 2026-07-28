# Documentation Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `documentation`

## Purpose

Define engineering documentation quality knowledge for repositories and systems.

## Why this domain exists

Documentation quality affects onboarding, AI grounding, compliance evidence, and change safety.

## Scope

**In scope**

- Architecture and operational doc expectations
- API and module documentation concepts
- Runbook and decision-record concepts
- Documentation freshness and ownership concepts

**Out of scope**

- CodeStrata user docs portal content (product documentation)
- Marketing copy
- Governance prose

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [ai](../ai/README.md) | Docs enable grounded answers |
| [compliance](../compliance/README.md) | Policies and evidence docs |
| [architecture](../architecture/README.md) | Architecture decision records |
| [modernization](../modernization/README.md) | Migration runbooks |

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

Separate engineering-doc knowledge from CodeStrata product documentation.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
