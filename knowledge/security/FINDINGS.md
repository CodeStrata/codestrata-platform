# Security — Findings

**Status:** Foundation  
**Domain:** `security`

## Objective

Define what a **Finding** represents within **Security**.

## Definition

A finding is a discrete, evidence-backed engineering issue or risk signal in this
domain. Findings are facts (or bounded inferences from evidence), not narratives.

## Domain meaning

Security weaknesses, sensitive exposure risks, and insecure practices.

## Required conceptual attributes

| Attribute | Intent |
| --------- | ------ |
| Identity | Stable conceptual identity within the domain |
| Severity | Relative urgency / impact |
| Evidence | Links to supporting signals |
| Scope | Repo / component / portfolio applicability |
| Limitation | What was not assessed |

<!-- TODO: Align attribute names with canonical product terminology (Finding, Evidence, Confidence, Coverage, Limitation). -->

## What findings are not

- Recommendations (see [RECOMMENDATIONS.md](RECOMMENDATIONS.md))
- Maturity scores
- AI-generated speculation without evidence

## Related

- [RULES.md](RULES.md)
- [MATURITY_MODEL.md](MATURITY_MODEL.md)

## Conceptual categories (migrated)

Category names consolidated from Engine taxonomy docs (Phase 8.9.3).
Serialized values remain implementation contracts.

| Category |
| -------- |
| Credential |
| Secret |
| Private key |
| Certificate |
| Configuration |
| Transport security |
| Authentication |
| Authorization |
| Cryptography |
| Repository exposure |
| Dependency security |
| Logging |
| Session |
| Input validation |
| Miscellaneous |
| Unknown |

