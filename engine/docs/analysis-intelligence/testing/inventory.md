# Test Assessment Inventory

Phase 4.6.4 — deterministic inventory projection for Test Intelligence.

## Contract

| Item | Value |
| ---- | ----- |
| Schema | `testing-assessment` **1.1.0** |
| Input | Existing Test Assessment facts + shared Findings + rule execution facts |
| Output | Inventories on `TestAssessmentSection` |
| Consumed by | Synthesis (4.6.5) and future report (4.6.6) |

## Inventories

| Inventory | Contents |
| --------- | -------- |
| `finding_inventory` | Sorted finding IDs + counts by rule / severity / confidence |
| `rule_inventory` | Registered hygiene rules with execution status and finding counts |
| `severity_inventory` | Deterministic severity buckets |
| `confidence_inventory` | Deterministic confidence buckets |

Finding **IDs only** — Findings are not duplicated into the assessment artifact.

Rule inventory summarizes applicable (registered) vs matched / not_matched /
not_applicable / failed execution statuses.

## Explicit non-scope

- No new evidence collectors
- No new rules
- No synthesis, themes, conclusions, or recommendations
- No hotspots
- No report / CLI / MCP / AI integration

## Gates

Reuse existing Test gates (default off). No new inventory config flag.

```toml
[evidence.repository_testing]
enabled = true

[rules]
enabled = true

[rules.testing]
enabled = true

[assessment.sections.testing]
enabled = true
```
