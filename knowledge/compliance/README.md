# Compliance Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `compliance`

## Purpose

Define compliance-oriented engineering knowledge for assessments.

## Why this domain exists

Regulated contexts need explicit control concepts without turning CodeStrata into an auditor.

## Scope

**In scope**

- Control and evidence concepts
- Policy-as-code adjacent expectations
- Auditability and change-trace concepts
- Mapping engineering findings to control families (conceptually)

**Out of scope**

- Legal advice
- Certification issuance
- Full regulatory text reproduction

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [security](../security/README.md) | Many controls are security controls |
| [documentation](../documentation/README.md) | Evidence and policy docs |
| [ai](../ai/README.md) | AI usage constraints |
| [portfolio](../portfolio/README.md) | Compliance posture across estates |

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

Reference frameworks in REFERENCES; do not hardcode jurisdiction-specific law here.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
