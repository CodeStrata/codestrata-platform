# Test Intelligence

Phase 4.6 of CodeStrata Analysis Intelligence.

| Sub-milestone | Status |
| ------------- | ------ |
| 4.6.1 Domain Foundation | Complete (`testing-assessment` 1.0.0 → inventory bump in 4.6.4) |
| 4.6.2 Repository Test Evidence | Complete (platform `repository-testing-evidence` 1.0.0; not Test-owned) |
| 4.6.3 Test Hygiene Rules | Complete (`testing.core` 1.0.0; four rules; TEST-004 deferred) |
| 4.6.4 Assessment Inventory | Complete (`testing-assessment` **1.1.0**) |
| 4.6.5 Deterministic Synthesis | Complete (`testing-assessment` **1.2.0**; synthesis **1.0.0**) |
| 4.6.6 Report Integration | Complete (`report.testing` **1.0.0**; default off) |

Design authority:
[intelligence-platform.md](../../architecture/intelligence-platform.md).

## Purpose

Test Intelligence analyzes repository-observable testing structure,
configuration, and hygiene indicators using typed platform evidence.

Phase **4.6.3** registers the `testing.core` SharedRule pack. Rules consume
`AggregatedRepositoryTestingEvidence` only and emit shared Findings into
`testing-assessment.json`.

Phase **4.6.6** projects the completed Test Assessment into `report.json` and
the HTML report via a presentation-only adapter. See [report.md](report.md).

Still out of scope: CLI/MCP Test helpers, TEST-004, test execution, and runtime
coverage measurement.

## Capability identity

| Constant | Value |
| -------- | ----- |
| Capability | `testing` |
| Section ID | `assessment.testing` |
| Schema | `testing-assessment` **1.2.0** |
| Artifact | `testing-assessment.json` |
| Schema ID | `codestrata.testing_assessment` |
| Pack | `testing.core` @ `1.0.0` |
| Report | `report.testing` **1.0.0** (`assessment.testing` / `#testing-assessment`) |

Package: `aimf.domain.testing` (not `test`, to avoid tooling conflicts).

## Shared Finding integration

`FindingCategory.TESTING` and `RuleCategory.TESTING` map together. No
`TestFinding` type exists. Hygiene findings carry taxonomy metadata such as
`testing_category` / `taxonomy_id`.

## Hygiene rules (4.6.3)

| Alias | Rule ID | Intent |
| ----- | ------- | ------ |
| TEST-001 | `testing.test-001` | Disabled / skipped markers |
| TEST-002 | `testing.test-002` | Material unconfirmed candidates |
| TEST-003 | `testing.test-003` | Declared framework without observation |
| TEST-004 | `testing.test-004` | Deferred (not registered) |
| TEST-005 | `testing.test-005` | Coverage config without CI invocation |

See [hygiene-rules.md](hygiene-rules.md).

## Gates

```toml
[evidence.repository_testing]
enabled = true

[rules]
enabled = true

[rules.testing]
enabled = true

[assessment.sections.testing]
enabled = true

[report.sections.testing]
enabled = true
```

Test Intelligence gates and platform evidence gates all default to **false**.
`include_synthesis` defaults to **true** when the assessment section is enabled.
`[report.sections.testing]` defaults to **false** and is independent of
assessment/rules/evidence gates.

See [../repository-test-evidence.md](../repository-test-evidence.md).

### Gate matrix

| Assessment | Rules pack | Evidence | Result |
| ---------- | ---------- | -------- | ------ |
| off | * | * | No `testing-assessment.json` |
| on | off | * | `disabled` section + artifact |
| on | on | missing/unusable | `insufficient_evidence` |
| on | on | usable | `succeeded` with hygiene findings (possibly zero) + inventories |

Enabling Test gates does not enable Architecture, Technical Debt, Dependency, or
Security gates. Enabling evidence does not enable rules or assessment.

## Explicit non-claims

A succeeded assessment (including zero findings) must **not** be read as:

- tests are sufficient
- the repository is well tested
- testing passed
- no testing issues
- release ready

## Deferred

CLI/MCP Test helpers, TEST-004, test execution, runtime coverage.

See also:

- [report.md](report.md)
- [synthesis.md](synthesis.md)
- [inventory.md](inventory.md)
- [hygiene-rules.md](hygiene-rules.md)
- [domain-foundation.md](domain-foundation.md)
- [taxonomy.md](taxonomy.md)
- [configuration.md](configuration.md)
- [../repository-test-evidence.md](../repository-test-evidence.md)
- [../../reviews/PHASE_4_6_6_TEST_REPORT_INTEGRATION_REVIEW.md](../../reviews/PHASE_4_6_6_TEST_REPORT_INTEGRATION_REVIEW.md)
- [../../reviews/PHASE_4_6_5_TEST_SYNTHESIS_REVIEW.md](../../reviews/PHASE_4_6_5_TEST_SYNTHESIS_REVIEW.md)
- [../../reviews/PHASE_4_6_4_TEST_ASSESSMENT_INVENTORY_REVIEW.md](../../reviews/PHASE_4_6_4_TEST_ASSESSMENT_INVENTORY_REVIEW.md)
- [../../reviews/PHASE_4_6_3_TEST_HYGIENE_RULES_REVIEW.md](../../reviews/PHASE_4_6_3_TEST_HYGIENE_RULES_REVIEW.md)
