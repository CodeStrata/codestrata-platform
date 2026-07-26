# Cloud Assessment Inventory

Phase **4.7.4** — deterministic inventory projection for Cloud Intelligence.

## Contract

| Item | Value |
| ---- | ----- |
| Schema | `cloud-assessment` **1.1.0** (inventories; synthesis added in **1.2.0**) |
| Input | Existing Cloud Hygiene Findings + rule execution facts |
| Output | Inventories on `CloudAssessmentSection` |
| Consumed by | Synthesis (4.7.5) and future report |

## Inventories

| Inventory | Contents |
| --------- | -------- |
| `finding_inventory` | Sorted finding IDs + counts by rule / severity / confidence |
| `rule_inventory` | Registered hygiene rules with execution status and finding counts |
| `severity_inventory` | Deterministic severity buckets |
| `confidence_inventory` | Deterministic confidence buckets |
| `technology_family_inventory` | Platforms, containers, orchestration, IaC, serverless, managed services, deployment pipelines |

Finding **IDs only** — Findings are not duplicated into the assessment artifact.

Technology family coverage is derived from Finding rule IDs and metadata
(for example `container_kinds`, `platforms`). Inventory never re-collects
repository-cloud evidence.

## Explicit non-scope (inventory phase)

- No new evidence collectors
- No new rules
- No hotspots / readiness scores
- No report / CLI / MCP / AI integration

Synthesis (themes / conclusions / recommendations) is Phase **4.7.5** —
see [synthesis.md](synthesis.md).

## Gates

Reuse existing Cloud gates (default off). No new inventory config flag.

```toml
[evidence.repository_cloud]
enabled = true

[rules]
enabled = true

[rules.cloud]
enabled = true

[analysis.cloud]
enabled = true
```
