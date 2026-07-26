# Security Intelligence

Phase 4.5 of CodeStrata Analysis Intelligence.

| Sub-milestone | Status |
| ------------- | ------ |
| 4.5.1 Domain Foundation | Complete |
| 4.5.2 Repository Security-Relevant Evidence | Complete (platform evidence; schema 1.1.0) |
| 4.5.3 Repository Security Hygiene Rules | Complete (`security.core`) |
| 4.5.4 Security Assessment Inventory | Complete (`security-assessment` 1.2.0) |
| 4.5.5 Deterministic Security Synthesis | Complete (`security-assessment` 1.3.0) |
| 4.5.6 Report Integration | Complete (`report.security` 1.0.0) |

Design authority and architecture conventions:
[analysis-intelligence-conventions.md](../../architecture/analysis-intelligence-conventions.md).

## Guiding principle

> Security Intelligence consumes reusable platform evidence and does not own
> repository parsing or generic evidence truth.

Phase **4.5.2** introduces platform evidence under
`[evidence.repository_sensitive]` (artifact
`repository-sensitive-evidence.json`). It records repository-visible candidates
and redacted configuration literals only.

Phase **4.5.3** adds `security.core` hygiene rules that consume that evidence and
emit shared Findings. See [hygiene-rules.md](hygiene-rules.md).

Phase **4.5.4** organizes those Findings and evidence into a deterministic
assessment inventory (`security-assessment` 1.2.0). See
[assessment-inventory.md](assessment-inventory.md).

Phase **4.5.5** adds deterministic synthesis (themes / conclusions /
recommendations) on schema **1.3.0**. See [synthesis.md](synthesis.md).

Phase **4.5.6** projects the assessment into customer reports via a
presentation-only adapter. See [report.md](report.md).

## Gates

```toml
[evidence.repository_sensitive]
enabled = false

[rules]
enabled = true

[rules.security]
enabled = true

[assessment.sections.security]
enabled = true

[report.sections.security]
enabled = false
```

Gates default to **disabled**. Enabling assessment/rules does not fabricate
findings without evidence. Enabling evidence does not run Security rules.
Enabling the report gate does not trigger assessment execution.

See also:

- [domain-foundation.md](domain-foundation.md)
- [taxonomy.md](taxonomy.md)
- [ownership-boundaries.md](ownership-boundaries.md)
- [configuration.md](configuration.md)
- [hygiene-rules.md](hygiene-rules.md)
- [assessment-inventory.md](assessment-inventory.md)
- [synthesis.md](synthesis.md)
- [report.md](report.md)
- [../repository-sensitive-evidence.md](../repository-sensitive-evidence.md)
