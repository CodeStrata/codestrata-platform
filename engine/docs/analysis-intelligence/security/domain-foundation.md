# Security Domain Foundation (Phase 4.5.1)

## Objective

Register Security Intelligence as a first-class assessment capability that is
analytically empty. The platform must support lifecycle states, deterministic
serialization, and independent feature gates without performing repository
security analysis.

## Architecture

```
Repository Inventory
  → (no Security Evidence collector in 4.5.1)
  → SecurityAssessmentSection (empty / disabled / …)
  → security-assessment.json
```

Shared Finding remains the finding model. `RuleCategory.SECURITY` maps to
`FindingCategory.SECURITY`. No `SecurityFinding` type exists.

## Assessment contract

| Constant | Value |
| -------- | ----- |
| Section ID | `assessment.security` |
| Schema name | `security-assessment` |
| Schema version | `1.3.0` (synthesis since 4.5.5; inventory since 4.5.4) |
| Artifact | `security-assessment.json` |
| Artifact schema ID | `codestrata.security_assessment` |
| Pack ID | `security.core` @ `1.0.0` |

Lifecycle states: `disabled`, `not_requested`, `succeeded`,
`insufficient_evidence`, `partially_succeeded`, `failed`, `not_applicable`.

Collections (`finding_ids`, `finding_summaries`, …) are empty in this phase.

## Explicit non-claims

A succeeded-empty assessment must **not** be read as:

- no security issues exist
- the repository is secure
- no secrets were found
- security risk is low

Foundation limitations state that rules and evidence collection are not
implemented.

## Deferred

Deterministic synthesis, presentation-only report adapter, CLI/MCP, CVE/OWASP
mapping, SAST, and runtime analysis. Phase 4.5.4 inventories organize Facts only.
