> **Engineering concepts:** see [`knowledge/`](../../../../knowledge/) for the canonical domain Knowledge. This document retains **implementation** contracts (schemas, pack IDs, lifecycle). Do not treat it as the conceptual source of truth.

# AI Readiness Intelligence Domain Foundation

## Objective

Register AI Readiness Intelligence as a first-class assessment capability that is
analytically empty. The platform must support lifecycle states, deterministic
serialization, and independent feature gates without performing AI readiness
analysis or executing AI/LLM workloads.

## Architecture

```
Evidence (future)
  → Rules (future)
  → AI Readiness Assessment
  → Inventory (future)
  → Synthesis (future)
  → Report (future)
```

Shared Finding remains the finding model. `RuleCategory.AI_READINESS` maps to
`FindingCategory.AI_READINESS`. No `AiReadinessFinding` type exists.

## Assessment contract

| Constant | Value |
| -------- | ----- |
| Section ID | `assessment.ai_readiness` |
| Schema name | `ai-readiness-assessment` |
| Schema version | `1.0.0` |
| Artifact | `ai-readiness-assessment.json` |
| Artifact schema ID | `codestrata.ai_readiness_assessment` |
| Pack ID | `ai_readiness.core` @ `1.0.0` |

Lifecycle states: `disabled`, `not_requested`, `succeeded`,
`insufficient_evidence`, `partially_succeeded`, `failed`, `not_applicable`.

Foundation helpers (`assemble_empty`, `assemble_disabled`, …) support lifecycle
fixtures. Orchestration writes `ai-readiness-assessment.json` only when
`[analysis.ai_readiness].enabled` is true, using `assemble_empty`.

## Deterministic identifiers

Prefixes: `ai-readiness-assessment:`, `ai-readiness-limitation:`,
`ai-readiness-diagnostic:`, `ai-readiness-trace:`. Stable inputs produce stable
IDs; no UUIDs, timestamps, or absolute paths.

## Explicit non-claims

Succeeded assessments (including zero findings) do not mean the repository is
AI ready, agent ready, RAG-ready, or suitable for automated LLM workflows.

## Deferred beyond 4.8.1

Evidence collectors (4.8.2), rules (4.8.3), and inventory (4.8.4) are complete.
Still deferred: synthesis, report adapter, readiness scores, AI/LLM execution,
CLI/MCP.
