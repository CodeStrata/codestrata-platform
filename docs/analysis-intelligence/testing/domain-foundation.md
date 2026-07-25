# Test Intelligence Domain Foundation (Phase 4.6.1)

## Objective

Register Test Intelligence as a first-class assessment capability. Phase 4.6.1
was analytically empty (lifecycle + gates only). Later phases add evidence
consumption and hygiene rules without changing the assessment schema identity.

## Architecture

```
Repository Inventory
  → AggregatedRepositoryTestingEvidence (platform; Phase 4.6.2)
  → testing.core SharedRules (Phase 4.6.3)
  → TestAssessmentSection
  → testing-assessment.json
```

Shared Finding remains the finding model. `RuleCategory.TESTING` maps to
`FindingCategory.TESTING`. No `TestFinding` type exists.

Platform `evidence.repository_testing` is **not** owned by Test Intelligence.
See [../repository-test-evidence.md](../repository-test-evidence.md).

Hygiene rules documentation: [hygiene-rules.md](hygiene-rules.md).

## Assessment contract

| Constant | Value |
| -------- | ----- |
| Section ID | `assessment.testing` |
| Schema name | `testing-assessment` |
| Schema version | `1.0.0` |
| Artifact | `testing-assessment.json` |
| Artifact schema ID | `codestrata.testing_assessment` |
| Pack ID | `testing.core` @ `1.0.0` |

Lifecycle states: `disabled`, `not_requested`, `succeeded`,
`insufficient_evidence`, `partially_succeeded`, `failed`, `not_applicable`.

Foundation helpers (`assemble_empty`, `assemble_disabled`, …) remain for
lifecycle fixtures. Hygiene findings use `assemble(...)`.

## Deterministic identifiers

Prefixes: `test-assessment:`, `test-limitation:`, `test-diagnostic:`,
`test-trace:`. Stable inputs produce stable IDs; no UUIDs, timestamps, or
absolute paths.

## Explicit non-claims

Succeeded assessments (including zero findings) do not mean the repository is
well tested, that testing passed, or that the application is release ready.

## Deferred beyond 4.6.3

Inventories, synthesis, report integration, CLI/MCP, TEST-004,
test execution, runtime coverage measurement.
