# Testing rules

Shared Rule Platform harness notes plus Test Intelligence hygiene entry.

## Test Intelligence hygiene (Phase 4.6.3)

Pack `testing.core` registers four hygiene rules (`testing.test-001`,
`testing.test-002`, `testing.test-003`, `testing.test-005`). `testing.test-004`
is deferred. Rules consume `AggregatedRepositoryTestingEvidence` only.

Authoritative docs:

- [testing/hygiene-rules.md](testing/hygiene-rules.md)
- [testing/README.md](testing/README.md)

Focused unit tests:
`tests/application/rules/testing/test_test_hygiene_rules.py`.

## RuleTestHarness (generic)

```python
from aimf.application.rules.harness import RuleTestHarness
from aimf.domain.rules.enums import RuleResultStatus

harness = RuleTestHarness([MyRule()])
result = harness.execute_one(MyRule())
harness.assert_status("my.category.rule-id", result, RuleResultStatus.MATCHED)
harness.assert_match_count(result, 1)
findings = harness.map_findings(result)
```

Internal fixtures (`fixture.always-match`, …) live in
`aimf.application.rules.fixtures` and must be registered with
`production=False`.

For Test Hygiene unit tests, prefer in-memory
`AggregatedRepositoryTestingEvidence` fixtures and `rule.evaluate(context)`
(see security hygiene tests for the same pattern).
