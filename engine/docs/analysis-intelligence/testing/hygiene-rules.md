# Test Hygiene Rules

Phase **4.6.3** — `testing.core` @ **1.0.0**

Rules consume **only** in-memory `AggregatedRepositoryTestingEvidence`.
They do not re-read repository files, execute tests, measure runtime coverage,
or invent release-readiness conclusions.

Human aliases **TEST-001** … **TEST-005** map to machine IDs
`testing.test-00N`.

## Configuration

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

All gates default to **disabled**. Rules never trigger evidence collection.
Evidence may run without rules.

Per-rule toggles (default enabled when the pack is on):

```toml
[rules.testing.test_001]
enabled = true
[rules.testing.test_002]
enabled = true
[rules.testing.test_003]
enabled = true
[rules.testing.test_005]
enabled = true
```

There is no `test_004` toggle — that rule is deferred and not registered.

## Rule catalog

| Alias | Rule ID | Trigger | Severity | Category |
| ----- | ------- | ------- | -------- | -------- |
| TEST-001 | `testing.test-001` | Confirmed disabled/skipped/ignored/quarantined/expected-failure markers | INFORMATIONAL → LOW (≥3) → MEDIUM (≥10) | `testing.disabled_test` |
| TEST-002 | `testing.test-002` | Material unconfirmed candidate ratio (≥20 considered, ≥10 unconfirmed, ratio ≥0.25) | INFORMATIONAL (&lt;0.35) / LOW | `testing.test_structure` |
| TEST-003 | `testing.test-003` | Declared/configured test framework without matching structural observation (language-aligned) | LOW | `testing.framework` |
| TEST-004 | `testing.test-004` | **Deferred** — not registered | — | — |
| TEST-005 | `testing.test-005` | Coverage configuration present, CI inspected, no test/coverage invocation fact | INFORMATIONAL | `testing.coverage_configuration` |

## Precision notes

### TEST-001

- Counts unique marker evidence IDs for disabled / ignored / skipped /
  conditional-skip / quarantined / expected-failure types.
- Focused/exclusive markers are **not** included.
- Hotspot paths (paths with ≥2 markers) appear in the summary (up to 5).
- Does **not** claim markers are obsolete, failing, or unjustified.

### TEST-002

- Considers candidates whose role is **not** fixture, support, configuration,
  coverage-config, report, or non-test.
- Suppresses small repositories and low unconfirmed ratios to avoid noise.
- Does **not** claim unconfirmed paths are broken tests.

### TEST-003

- Compares declared/configured **test** frameworks to structurally observed
  frameworks by family (JUnit / JUnit Jupiter are equivalent).
- Requires overlapping inspected language / candidate language hints for the
  framework ecosystem (suppresses cross-language false positives).
- Suppresses when `candidate_files_inspected == 0`.
- Does **not** claim the framework is unused.

### TEST-004 (deferred)

Observed-without-declaration is deferred. Parent/centralized builds,
transitive dependencies, and monorepo ownership cannot be bounded reliably
from repository-testing evidence alone.

### TEST-005

- Requires coverage configuration facts (or coverage_configurations &gt; 0).
- Requires `ci_files_inspected &gt; 0`.
- Suppresses when any CI test/coverage invocation fact exists, or when no CI
  files were inspected.
- Does **not** claim CI never runs tests or that coverage is uncollected.

## Exclusions

- Fixture / support / report candidates (TEST-002 considered set)
- Coverage plugins as “test frameworks” for TEST-003 (`jacoco`, `coverage_py`, …)
- Evidence diagnostics (never become Findings)
- Runtime coverage percentages (never collected)

## Finding identity

Finding IDs use `finding:{rule_id}:{digest}` from stable subject keys.
Shuffle of input marker/candidate order must not change Finding IDs.

## Privacy

Findings may include relative paths, marker type/text projections, and
framework identity. Absolute filesystem paths and source/fixture bodies are
never serialized.

## Assessment

Hygiene Findings project into `testing-assessment` **1.0.0** via
`TestAssessmentAssembler.assemble(...)`. No inventories, themes, conclusions,
recommendations, synthesis, scores, or report integration in this phase.

Zero findings does **not** mean the repository is well tested or release ready.

## Deferred

- TEST-004 observed-without-declaration
- Inventories / hotspots / synthesis
- `report.sections.testing`
- CLI/MCP surfaces
- Test execution and runtime coverage measurement
