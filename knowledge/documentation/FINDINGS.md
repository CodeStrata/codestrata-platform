# Documentation — Findings

**Status:** Foundation  
**Domain:** `documentation`

## Objective

Define what a **Finding** represents within **Documentation**.

## Definition

A finding is a discrete, evidence-backed engineering issue or risk signal in this
domain. Findings are facts (or bounded inferences from evidence), not narratives.

## Domain meaning

Documentation gaps that increase operational or change risk.

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
| Test presence |
| Test structure |
| Framework |
| Unit testing |
| Integration testing |
| End-to-end testing |
| Contract testing |
| Smoke testing |
| Performance testing |
| Test distribution |
| Test isolation |
| Disabled test |
| Ignored test |
| Flaky-test indicator |
| Test configuration |
| Fixture |
| Mocking |
| Coverage configuration |
| Build integration |
| Continuous integration |
| Maintainability |
| Modernization safety net |
| Miscellaneous |
| Unknown |

