# Security Assessment Synthesis

Schema: `security-assessment` **1.3.0**. Synthesis version: **1.0.0**.

Deterministic, template-driven themes, conclusions, recommendations, and
concentration facts derived from the completed Security assessment inventory.

## Contract

Consumes inventory only:

- production-primary and all finding projections
- evidence summary / diagnostics
- rule inventory
- hotspot inventory
- limitations

Does **not** re-read files, recollect evidence, rerun rules, interpret redacted
previews, or emit scores.

## Configuration

```toml
[assessment.sections.security]
enabled = false
include_synthesis = true
```

Assessment remains disabled by default. When assessment is enabled, synthesis
defaults on and can be disabled independently without removing inventory fields.

## Lifecycle

| Condition | Synthesis status |
| --------- | ---------------- |
| `include_synthesis = false` | `not_requested` |
| pack / section disabled | `disabled` |
| assessment insufficient / failed / not_applicable | `insufficient_evidence` |
| usable inventory, zero findings | `empty` (bounded no-production themes) |
| usable inventory with findings/hotspots | `succeeded` |
| synthesis exception | `failed` (inventory preserved) |

## Theme catalog (triggers)

| Kind | Trigger |
| ---- | ------- |
| `security_hygiene_landscape` | Always when generated |
| `evidence_coverage` | Always when generated |
| `credential_and_secret_hygiene` | credential-literal or placeholder findings |
| `private_key_exposure` | private-key-material findings |
| `transport_security_configuration` | TLS / hostname verification disabled |
| `authentication_configuration` | authentication-disabled findings |
| `permissive_cors_configuration` | permissive-cors-origin findings |
| `debug_configuration` | debug-enabled findings |
| `placeholder_credentials` | placeholder-credential findings |
| `test_fixture_observations` | test findings and all > production |
| `unknown_role_observations` | unknown-role findings |
| `finding_concentration` | hotspots present |
| `partial_evidence_coverage` | partial evidence or evidence diagnostics |
| `unsupported_analysis_scope` | accepted limitations present |
| `no_production_findings` | production count 0 with executed rules |

## Conclusion / recommendation catalogs

Conclusions and recommendations are enum-bounded and cite supporting theme,
finding, rule, hotspot, or diagnostic IDs. Recommendations are deduplicated by
kind. Effort / business impact remain `"unknown"`.

Zero-production wording:

> No production-role findings were emitted by the N enabled Security hygiene
> rules within the supported repository evidence scope.

Must **not** say: security passed, secure, no vulnerabilities, low risk,
compliant.

## Concentration facts

Descriptive counts/shares only (`findings_by_rule`, `findings_by_category`,
`findings_by_source_role`, `findings_by_severity`, `production_finding_ratio`,
`top_hotspot_finding_count`, `locations_with_multiple_findings`). Not scores.

## Privacy

No raw credentials, private-key content, absolute paths, or fingerprint values
in customer-facing narrative text.

## Deferred

CTO report / HTML / report.json projection, CLI/MCP, new rules/scanners, CVE,
SAST/DAST, compliance mappings, prioritization engines.
