# AI Readiness Assessment Inventory

Phase **4.8.4** — deterministic inventory projection for AI Readiness Intelligence.
Schema advanced to **1.2.0** in Phase **4.8.5** when synthesis fields were added.

## Contract

| Item | Value |
| ---- | ----- |
| Schema | `ai-readiness-assessment` **1.2.0** (inventories + synthesis) |
| Input | Existing AI Readiness Hygiene Findings + rule execution facts |
| Output | Inventories on `AiReadinessAssessmentSection` |
| Consumed by | Synthesis (4.8.5) and future report |

## Inventories

| Inventory | Contents |
| --------- | -------- |
| `finding_inventory` | Sorted finding IDs + counts by rule / severity / confidence |
| `rule_inventory` | Registered hygiene rules with execution status and finding counts |
| `severity_inventory` | Deterministic severity buckets |
| `confidence_inventory` | Deterministic confidence buckets |
| `capability_family_inventory` | API boundaries, documentation/metadata, data retrieval, AI integrations, tool/MCP, workflow/agents, observability/governance |

Finding **IDs only** — Findings are not duplicated into the assessment artifact.

Capability family coverage is derived from Finding rule IDs and metadata
(for example `api_boundary_kinds`, `families` on AI-060/AI-061). Inventory
never re-collects repository AI-readiness evidence.

## Explicit non-scope (inventory phase)

- No new evidence collectors
- No new rules
- No readiness scores / hotspots
- Synthesis is Phase **4.8.5** — see [synthesis.md](synthesis.md)
- No report / CLI / MCP / AI integration

## Gates

Reuse existing AI Readiness gates (default off). No new inventory config flag.

```toml
[evidence.repository_ai_readiness]
enabled = true

[rules]
enabled = true

[rules.ai_readiness]
enabled = true

[analysis.ai_readiness]
enabled = true
```
