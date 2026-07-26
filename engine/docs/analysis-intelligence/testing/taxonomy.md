# TestCategory Taxonomy

Phase 4.6.1 future-facing taxonomy only. No rules or findings are emitted for
these categories yet.

Serialized values use the `testing.<category>` namespace.

| Category | Value |
| -------- | ----- |
| Test presence | `testing.test_presence` |
| Test structure | `testing.test_structure` |
| Framework | `testing.framework` |
| Unit testing | `testing.unit_testing` |
| Integration testing | `testing.integration_testing` |
| End-to-end testing | `testing.end_to_end_testing` |
| Contract testing | `testing.contract_testing` |
| Smoke testing | `testing.smoke_testing` |
| Performance testing | `testing.performance_testing` |
| Test distribution | `testing.test_distribution` |
| Test isolation | `testing.test_isolation` |
| Disabled test | `testing.disabled_test` |
| Ignored test | `testing.ignored_test` |
| Flaky-test indicator | `testing.flaky_test_indicator` |
| Test configuration | `testing.test_configuration` |
| Fixture | `testing.fixture` |
| Mocking | `testing.mocking` |
| Coverage configuration | `testing.coverage_configuration` |
| Build integration | `testing.build_integration` |
| Continuous integration | `testing.continuous_integration` |
| Maintainability | `testing.maintainability` |
| Modernization safety net | `testing.modernization_safety_net` |
| Miscellaneous | `testing.miscellaneous` |
| Unknown | `testing.unknown` |

Unknown or unrecognized inputs coerce to `testing.unknown`.

## Explicit exclusions

Taxonomy does **not** include defect probability, release readiness, test
effectiveness scores, runtime coverage percentages, mutation scores, quality
grades, or risk ratings.
