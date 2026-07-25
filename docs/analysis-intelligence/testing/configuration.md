# Test Intelligence Configuration

All Test Intelligence gates default to **disabled**.

```toml
[rules]
enabled = false

[rules.testing]
enabled = false
# Optional per-rule toggles (default true when pack enabled):
# [rules.testing.test_001]
# enabled = true
# [rules.testing.test_002]
# enabled = true
# [rules.testing.test_003]
# enabled = true
# [rules.testing.test_005]
# enabled = true

[assessment.sections.testing]
enabled = false
# include_findings = true
# include_coverage = true
# include_limitations = true
# include_traceability = true
# include_execution_summary = true
```

There is **no** `[report.sections.testing]` yet and **no** `include_synthesis`
option yet. There is no `test_004` toggle (deferred rule).

Platform repository test evidence is independent of these Test Intelligence
gates:

```toml
[evidence.repository_testing]
enabled = false
```

See [../repository-test-evidence.md](../repository-test-evidence.md) and
[hygiene-rules.md](hygiene-rules.md).

## Gate matrix

| Assessment gate | Pack gate (`rules` + `rules.testing`) | Evidence | Result |
| --------------- | ------------------------------------- | -------- | ------ |
| false | * | * | No `testing-assessment.json` |
| true | false | * | `disabled` section |
| true | true | missing/unusable | `insufficient_evidence` |
| true | true | usable | `succeeded` (hygiene findings, possibly zero) |

Enabling Test gates does not enable Architecture, Technical Debt, Dependency, or
Security gates. Enabling evidence does not enable rules or assessment.
Existing configs without Testing settings remain valid.
