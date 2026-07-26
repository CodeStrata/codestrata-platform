# AI Readiness Intelligence

Phase 4.8 of CodeStrata Analysis Intelligence.

| Sub-milestone | Status |
| ------------- | ------ |
| 4.8.1 Domain Foundation | Complete (`ai-readiness-assessment` **1.0.0**; analytically empty) |
| 4.8.2 Repository AI-Readiness Evidence | Complete (`repository-ai-readiness-evidence` **1.0.0**; platform evidence; disabled by default) |
| 4.8.3 AI Readiness Hygiene Rules | Complete (`ai_readiness.core` **1.0.0**; 17 hygiene rules; disabled by default) |
| 4.8.4 Assessment Inventory | Complete (`ai-readiness-assessment` **1.1.0**; inventories; disabled by default) |
| 4.8.5 Deterministic Synthesis | Complete (`ai-readiness-assessment` **1.2.0**; disabled by default) |
| 4.8.6 Report Integration | Complete (`report.ai_readiness` **1.0.0**; disabled by default) |

Design authority:
[analysis-intelligence-conventions.md](../../architecture/analysis-intelligence-conventions.md).

## Purpose

AI Readiness Intelligence analyzes repository-observable signals that support
future AI/agent enablement assessments. Phase **4.8.6** projects the existing
AI Readiness Assessment into HTML/JSON report presentation — no readiness
scores, re-analysis, or AI execution.

## Capability identity

| Constant | Value |
| -------- | ----- |
| Capability | `ai_readiness` |
| Section ID | `assessment.ai_readiness` |
| Schema | `ai-readiness-assessment` **1.2.0** |
| Artifact | `ai-readiness-assessment.json` |
| Schema ID | `codestrata.ai_readiness_assessment` |
| Pack | `ai_readiness.core` @ `1.0.0` (17 hygiene rules) |
| Synthesis | **1.0.0** |

Package: `codestrata.domain.ai_readiness` / `codestrata.application.ai_readiness` /
`codestrata.application.rules.ai_readiness`.

Platform evidence (independent): see
[../repository-ai-readiness-evidence.md](../repository-ai-readiness-evidence.md).

Hygiene rules: [hygiene-rules.md](hygiene-rules.md).

Inventory: [inventory.md](inventory.md).

Synthesis: [synthesis.md](synthesis.md).

Report: [report.md](report.md).

## Shared Finding integration

`FindingCategory.AI_READINESS` and `RuleCategory.AI_READINESS` map together. No
`AiReadinessFinding` type exists. Rules emit shared Findings with
Informational/Low severity and observation-only remediation notes. Assessment
inventories and synthesis reference Finding IDs only.

## Gates

```toml
[analysis.ai_readiness]
enabled = true
# include_synthesis = true

[evidence.repository_ai_readiness]
enabled = true

[rules]
enabled = true

[rules.ai_readiness]
enabled = true

[report.sections.ai_readiness]
enabled = true
```

All default to **false**. Enabling `[rules.ai_readiness]` does not enable
`[analysis.ai_readiness]`. When analysis is on and the pack is enabled,
assessment writes `ai-readiness-assessment.json` **1.2.0** with inventories and
synthesis (when `include_synthesis` is true). Enabling
`[report.sections.ai_readiness]` projects that section into `report.json` /
HTML without re-running analysis. Evidence collection is
independent.

See [domain-foundation.md](domain-foundation.md),
[configuration.md](configuration.md), [inventory.md](inventory.md),
[synthesis.md](synthesis.md), and [report.md](report.md).

## Explicit non-claims

Matched Findings and non-empty inventories/synthesis do **not** mean the
repository is AI ready, agent ready, RAG-ready, or governed for LLM usage.
Empty or unusable evidence yields no Findings (rules not applicable). Zero
findings with `succeeded` assessment status and `empty` synthesis status is
valid inventory output.
