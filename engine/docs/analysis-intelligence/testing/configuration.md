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
# include_synthesis = true
```

Report presentation (independent; default off):

```toml
[report.sections.testing]
enabled = false
# include_executive_summary = true
# include_coverage = true
# include_inventory = true
# include_execution_summary = true
# include_themes = true
# include_conclusions = true
# include_recommendations = true
# include_diagnostics = true
# include_limitations = true
# include_traceability = true
```

There is no `test_004` toggle (deferred rule). `include_synthesis` defaults to
**true** when the assessment section is enabled. Enabling the report gate does
not run assessment, rules, or evidence collection.

Platform repository test evidence is independent of these Test Intelligence
gates:

```toml
[evidence.repository_testing]
enabled = false
```

See ../repository-test-evidence.md and
hygiene-rules.md.

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
