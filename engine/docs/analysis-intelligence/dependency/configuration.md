# Dependency Intelligence Configuration

All Dependency Intelligence gates default to **disabled**.

```toml
[rules]
enabled = false

[rules.dependency]
enabled = false
# Per-rule toggles default enabled when the pack is on:
# unresolved_version.enabled = true
# mutable_version.enabled = true
# unbounded_requirement.enabled = true
# conflicting_exact_versions.enabled = true
# duplicate_declaration.enabled = true

[evidence.dependency]
enabled = false

[assessment.sections.dependency]
enabled = false
# include_findings = true
# include_coverage = true
# include_limitations = true
# include_traceability = true
# include_execution_summary = true
# include_synthesis = true

[report.sections.dependency]
enabled = false
# include_executive_summary = true
# include_landscape = true
# include_production_health = true
# include_test_observations = true
# include_hotspots = true
# include_conclusions = true
# include_recommendations = true
# include_coverage = true
# include_limitations = true
# include_traceability = true
```

## Behavior

| Section | Pack | Evidence | Result |
| ------- | ---- | -------- | ------ |
| false | * | * | No dependency section artifact |
| true | false | * | `disabled` section (evidence artifact may still write) |
| true | true | false | `insufficient_evidence`; rules not applicable |
| true | true | true (no supported manifests) | `insufficient_evidence` |
| true | true | true (production parse failures) | `partially_succeeded` + inventories |
| true | true | true (production usable; test/fixture failures or unsupported constructs OK) | `succeeded` + production-primary findings |
| true | true | true (evidence collection failed) | `failed` |

Primary `finding_ids` are production-only. Complete inventory is in
`all_finding_ids`. See [assessment-inventory.md](assessment-inventory.md).

When `include_synthesis = true` (default), themes/conclusions/recommendations are
attached after inventory assembly. See [synthesis.md](synthesis.md).
`include_synthesis = false` yields `synthesis.status = not_requested`.

Pack enablement requires both `rules.enabled` and `rules.dependency.enabled`.
Evidence remains an independent gate (`evidence.dependency.enabled`).

Customer-facing CTO report integration is gated separately by
`report.sections.dependency.enabled` (default **false**). Enabling the report
section does not enable Architecture or Technical Debt report sections, and does
not recollect evidence or re-run rules. When enabled, the in-memory
`DependencyAssessmentSection` is adapted into `assessment.dependency` in
`report.json` and an HTML section with stable anchor `dependency-assessment`.

Enabling Dependency Intelligence does not enable Architecture or Technical Debt
gates.
