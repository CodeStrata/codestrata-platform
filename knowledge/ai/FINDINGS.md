# AI Readiness — Findings

**Status:** Foundation  
**Domain:** `ai`

## Objective

Define what a **Finding** represents within **AI Readiness**.

## Definition

A finding is a discrete, evidence-backed engineering issue or risk signal in this
domain. Findings are facts (or bounded inferences from evidence), not narratives.

## Domain meaning

Readiness, grounding, and AI-safety related engineering issues.

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
| API and service boundaries |
| Documentation and metadata quality |
| Data access patterns |
| Search and retrieval readiness |
| RAG-enabling assets |
| Tool / MCP integration |
| Workflow and agent boundaries |
| Existing AI/LLM integrations |
| Observability and governance |
| Miscellaneous |
| Unknown |

