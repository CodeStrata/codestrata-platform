# Phase 4.6.3 — Test Hygiene Rules Review

**Date:** 2026-07-25  
**Artifacts:** `reports/dogfood-phase-4-6-3/` (gitignored)  
**Pack:** `testing.core` **1.0.0**  
**Evidence:** `repository-testing-evidence` **1.0.0**  
**Assessment:** `testing-assessment` **1.0.0**

## Recommendation

**Accept Phase 4.6.3.** Four high-confidence Test Hygiene rules consume
repository-testing evidence only, emit shared Findings with
`FindingCategory.TESTING`, and project into the existing Test assessment
container. TEST-004 remains deferred. No inventory, synthesis, report
integration, or test execution was added.

Evidence quality review:
[PHASE_4_6_3_TEST_EVIDENCE_QUALITY_REVIEW.md](PHASE_4_6_3_TEST_EVIDENCE_QUALITY_REVIEW.md)

## Implemented rules

| Alias | Rule ID | Status |
| ----- | ------- | ------ |
| TEST-001 | `testing.test-001` | Implemented |
| TEST-002 | `testing.test-002` | Implemented |
| TEST-003 | `testing.test-003` | Implemented |
| TEST-004 | `testing.test-004` | **Deferred** (declaration ownership) |
| TEST-005 | `testing.test-005` | Implemented |

## CodeStrata dogfood

| Field | Value |
| ----- | ----- |
| Assessment status | `succeeded` |
| Rules planned / executed | 4 / 4 |
| Matched / not matched | 2 / 2 |
| Findings | **2** |
| By rule | `testing.test-001` ×1, `testing.test-002` ×1 |
| Severities | medium (001), informational (002) |
| Confidence | high (001), medium (002) |
| TEST-003 / TEST-005 | not matched (expected) |
| Repeat-run assessment | **byte-identical** |

### Finding review

| Finding | Classification | Notes |
| ------- | -------------- | ----- |
| TEST-001 (34 markers) | **Valid** | Real skip/disabled/xfail markers in the tree. Concentration includes Phase 4.6.2 evidence unit-test fixtures that embed marker tokens — still repository-true, severity medium is conservative for count ≥ 10. Does not claim obsolescence or failure. |
| TEST-002 (material unconfirmed) | **Valid** | Many `tests/**/__init__.py` and naming-only candidates. Wording correctly describes discovery uncertainty, not “missing tests”. |

## Spring Petclinic dogfood

| Field | Value |
| ----- | ----- |
| Assessment status | `succeeded` |
| Rules planned / executed | 4 / 4 |
| Matched / not matched | 1 / 3 |
| Findings | **1** |
| By rule | `testing.test-001` ×1 |
| Severity / confidence | medium / high |
| TEST-002 | not matched (3 unconfirmed < thresholds) |
| TEST-003 | not matched (JUnit declared + observed) |
| TEST-005 | not matched (CI invocations present) |
| Repeat-run assessment | **byte-identical** |

### Finding review

| Finding | Classification | Notes |
| ------- | -------------- | ----- |
| TEST-001 (16 `@Disabled`) | **Valid** | Profile/DB-gated Spring tests commonly use `@Disabled`. Neutral wording; does not judge justification. One `enabled=false` hit on `MysqlTestApplication` is Spring-config adjacent noise within the aggregate — not a material false positive for the finding. |

## Manual false-positive review summary

| Check | Result |
| ----- | ------ |
| Material false positives accepted? | **No** |
| Duplicate findings | None (one finding per matched rule) |
| Too vague | No — metrics and paths bounded |
| Incorrect severity | No — max medium; informational for TEST-002 |
| Incorrect confidence | No — high for exact markers; medium for ratios |
| Privacy (no abs paths / bodies / secrets) | Pass |
| Zero findings language | N/A for these dogfoods; assembler uses neutral wording when empty |

## Quality checks

| Check | Result |
| ----- | ------ |
| Focused rules + testing assessment tests | Pass (see completion response) |
| Full pytest | Pass except known unrelated sandbox `.git/config` PermissionError if present |
| Ruff / mypy | Pass on changed packages |

## Confirmation

- Rules consume `AggregatedRepositoryTestingEvidence` only (no rescans)
- No test execution / runtime coverage / remote CI / AI
- No assessment inventory / synthesis / report section
- Gates remain independent
- No git commit
