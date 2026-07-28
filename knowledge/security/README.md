# Security Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `security`

## Purpose

Define security engineering knowledge for application and repository assessment.

## Why this domain exists

Security findings must be evidence-based, prioritized, and actionable for modernization.

## Scope

**In scope**

- Application security concepts and hygiene
- Secret handling and sensitive data concepts
- Authn/authz and trust-boundary concepts
- Secure SDLC expectations at assessment depth

**Out of scope**

- Penetration-test procedures
- SOC runbooks
- Product security of CodeStrata itself (see governance)

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [compliance](../compliance/README.md) | Controls map to obligations |
| [dependency](../dependency/README.md) | Vulnerable and unmaintained dependencies |
| [cloud](../cloud/README.md) | Shared responsibility and cloud IAM concepts |
| [ai](../ai/README.md) | AI-specific security readiness |

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

Prefer standard taxonomies (OWASP/NIST) via REFERENCES; avoid duplicating full catalogs here.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
