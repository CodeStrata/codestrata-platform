# Cloud Intelligence Configuration

All Cloud Intelligence gates default to **disabled**.

```toml
[analysis.cloud]
enabled = false
# include_findings = true
# include_coverage = true
# include_limitations = true
# include_traceability = true
# include_execution_summary = true
# include_synthesis = true
```

Cloud Hygiene rules (Phase 4.7.3):

```toml
[rules]
enabled = false

[rules.cloud]
enabled = false
# Per-rule toggles default enabled when the pack is on:
# cloud_001 … cloud_061
```

Report presentation (Phase 4.7.6; independent; default off):

```toml
[report.sections.cloud]
enabled = false
# include_executive_summary = true
# include_coverage = true
# include_inventory = true
# include_execution_summary = true
# include_themes = true
# include_conclusions = true
# include_recommendations = true
# include_findings = true
# include_diagnostics = true
# include_limitations = true
# include_traceability = true
```

Platform cloud evidence (Phase 4.7.2) is independent:

```toml
[evidence.repository_cloud]
enabled = false
```

## Gate matrix

| `analysis.cloud.enabled` | Result |
| ------------------------ | ------ |
| false | No `cloud-assessment.json` |
| true (pack off) | `disabled` section with empty inventories |
| true (pack on) | Inventories + synthesis over Cloud Hygiene Findings (`cloud-assessment` **1.2.0**) |

| `analysis.cloud.include_synthesis` | Result |
| --------------------------------- | ------ |
| true (default when analysis on) | Themes / conclusions / recommendations |
| false | `synthesis.status = not_requested` |

| `report.sections.cloud.enabled` | Result |
| ------------------------------- | ------ |
| false | No `assessment.cloud` / `#cloud-assessment` |
| true (assessment available) | Project Cloud Assessment into `report.json` + HTML |
| true (no assessment) | Warning; section omitted |

| `evidence.repository_cloud.enabled` | Result |
| ----------------------------------- | ------ |
| false | No `repository-cloud-evidence.json` |
| true | Collect technology/deployment evidence |

| `rules.enabled` + `rules.cloud.enabled` | Result |
| ---------------------------------------- | ------ |
| false | No Cloud Hygiene evaluation |
| true | Evaluate `cloud.core` against in-memory evidence; merge Findings |

Enabling Cloud gates does not enable Architecture, Technical Debt, Dependency,
Security, or Test gates. Existing configs without Cloud settings remain valid.

See [hygiene-rules.md](hygiene-rules.md), [inventory.md](inventory.md),
[synthesis.md](synthesis.md), and [report.md](report.md).
