# Security Intelligence Configuration

All Security Intelligence gates default to **disabled**.

```toml
[rules]
enabled = false

[rules.security]
enabled = false

[assessment.sections.security]
enabled = false
# include_findings = true
# include_coverage = true
# include_limitations = true
# include_traceability = true
# include_execution_summary = true
# include_synthesis = true

[report.sections.security]
enabled = false
# include_executive_summary = true
# include_coverage = true
# include_findings = true
# include_themes = true
# include_hotspots = true
# include_conclusions = true
# include_recommendations = true
# include_diagnostics = true
# include_limitations = true
# include_traceability = true
```

The report gate is independent of assessment/rules/evidence. Enabling
`report.sections.security` does **not** run Security assessment.

Repository-sensitive evidence is a **separate** platform gate:

```toml
[evidence.repository_sensitive]
enabled = false
```

Enabling Security assessment/rules does **not** enable repository-sensitive
evidence, and enabling evidence does **not** execute Security rules.

Per-rule toggles (default enabled when the pack is on):

```toml
[rules.security.private_key_material]
enabled = true
# credential_literal, placeholder_credential, tls_verification_disabled,
# hostname_verification_disabled, authentication_disabled,
# permissive_cors_origin, debug_enabled
```

## Behavior

| Assessment gate | Pack gate | Evidence | Result |
| --------------- | --------- | -------- | ------ |
| false | * | * | No `security-assessment.json` |
| true | false | * | `disabled` section |
| true | true | missing | `insufficient_evidence` |
| true | true | present | Inventory + synthesis (`1.3.0`) |

When inventory is enabled, `finding_ids` are production-primary;
`all_finding_ids` includes every Security finding. Status reflects evidence and
rule completeness, not finding presence. Set `include_synthesis = false` to keep
inventory without themes/conclusions/recommendations.

Enabling Security gates does not enable Architecture, Technical Debt, or
Dependency gates.
