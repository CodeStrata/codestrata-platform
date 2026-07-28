> **Engineering concepts:** see [`knowledge/`](../../../../knowledge/) for the canonical domain Knowledge. This document retains **implementation** contracts (schemas, pack IDs, lifecycle). Do not treat it as the conceptual source of truth.

# Performance Intelligence Domain Foundation

## Objective

Register Performance Intelligence as a first-class assessment capability that is
analytically empty. The platform must support lifecycle states, deterministic
serialization, and independent feature gates without performing performance
analysis, profiling, or scoring.

## Architecture

```
Evidence (future)
  → Rules (future)
  → Performance Assessment
  → Inventory (future)
  → Synthesis (future)
  → Report (future)
```

Shared Finding remains the finding model. `RuleCategory.PERFORMANCE` maps to
`FindingCategory.PERFORMANCE`. No `PerformanceFinding` type exists.

## Assessment contract

| Constant | Value |
| -------- | ----- |
| Section ID | `assessment.performance` |
| Schema name | `performance-assessment` |
| Schema version | `1.0.0` |
| Artifact | `performance-assessment.json` |
| Artifact schema ID | `codestrata.performance_assessment` |
| Pack ID | `performance.core` @ `1.0.0` |

Lifecycle states: `disabled`, `not_requested`, `succeeded`,
`insufficient_evidence`, `partially_succeeded`, `failed`, `not_applicable`.

Foundation helpers (`assemble_empty`, `assemble_disabled`, …) support lifecycle
fixtures. There is no hygiene `assemble()` path. Orchestration writes
`performance-assessment.json` only when `[analysis.performance].enabled` is
true, using `assemble_empty(pack_enabled=True,
reason="no_performance_rules_registered")`.

Inventory and synthesis fields exist as empty placeholders only.

## Deterministic identifiers

Prefixes: `performance-assessment:`, `performance-limitation:`,
`performance-diagnostic:`, `performance-trace:`. Stable inputs produce stable
IDs; no UUIDs, timestamps, or absolute paths.

## Explicit non-claims

Succeeded assessments (including zero findings) do not mean the repository is
performant, scalable, free of latency risk, or suitable for high load.

## Deferred beyond 4.9.1

Evidence collectors (4.9.2), rules (4.9.3), inventory population (4.9.4),
synthesis generation (4.9.5), report adapter (4.9.6), performance scores,
profiling execution, CLI/MCP.
