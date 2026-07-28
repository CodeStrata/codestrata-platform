# Cost — Findings

**Status:** Foundation  
**Domain:** `cost`

## Objective

Define what a **Finding** represents within **Cost**.

## Definition

A finding is a discrete, evidence-backed engineering issue or risk signal in this
domain. Findings are facts (or bounded inferences from evidence), not narratives.

## Domain meaning

Patterns likely to create avoidable cost or poor cost visibility.

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
