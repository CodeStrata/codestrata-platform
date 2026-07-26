# Cloud Intelligence Domain Foundation (Phase 4.7.1)

## Objective

Register Cloud Intelligence as a first-class assessment capability that is
analytically empty. The platform must support lifecycle states, deterministic
serialization, and independent feature gates without performing cloud analysis.

## Architecture

```
Evidence (future)
  → Rules (future)
  → Cloud Assessment
  → Inventory (future)
  → Synthesis (future)
  → Report (future)
```

Shared Finding remains the finding model. `RuleCategory.CLOUD` maps to
`FindingCategory.CLOUD`. No `CloudFinding` type exists.

## Assessment contract

| Constant | Value |
| -------- | ----- |
| Section ID | `assessment.cloud` |
| Schema name | `cloud-assessment` |
| Schema version | `1.0.0` |
| Artifact | `cloud-assessment.json` |
| Artifact schema ID | `codestrata.cloud_assessment` |
| Pack ID | `cloud.core` @ `1.0.0` |

Lifecycle states: `disabled`, `not_requested`, `succeeded`,
`insufficient_evidence`, `partially_succeeded`, `failed`, `not_applicable`.

Foundation helpers (`assemble_empty`, `assemble_disabled`, …) support lifecycle
fixtures. Orchestration writes `cloud-assessment.json` only when
`[analysis.cloud].enabled` is true, using `assemble_empty`.

## Deterministic identifiers

Prefixes: `cloud-assessment:`, `cloud-limitation:`, `cloud-diagnostic:`,
`cloud-trace:`. Stable inputs produce stable IDs; no UUIDs, timestamps, or
absolute paths.

## Explicit non-claims

Succeeded assessments (including zero findings) do not mean the repository is
cloud ready, portable, or deployment-ready for any cloud provider.

## Deferred beyond 4.7.1

Evidence collectors, cloud detection, rules, inventory, synthesis, report
adapter, CLI/MCP, AI.
