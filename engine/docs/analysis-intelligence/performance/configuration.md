# Performance Intelligence Configuration

All Performance Intelligence gates default to **disabled**.

```toml
[analysis.performance]
enabled = false
# include_findings = true
# include_coverage = true
# include_limitations = true
# include_traceability = true
# include_execution_summary = true
# include_synthesis = true
```

Platform evidence (independent of analysis; default off; Phase 4.9.2):

```toml
[evidence.repository_performance]
enabled = false
# max_files = 500
# max_file_chars = 500000
# max_file_bytes = 2000000
```

Hygiene rules (independent of analysis; default off; Phase 4.9.3):

```toml
[rules]
enabled = true

[rules.performance]
enabled = true
# perf_001 … perf_072 toggles default enabled when the pack is on
```

Report presentation (independent of analysis; default off; Phase 4.9.6):

```toml
[report.sections.performance]
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

When `[analysis.performance]` is enabled and the pack is on, Phase **4.9.5**
writes `performance-assessment.json` (**1.2.0**) via `assemble(...)` with
deterministic inventories and synthesis over Hygiene Findings and
rule-execution facts. Set `include_synthesis = false` to keep inventories
without themes / conclusions / recommendations. When the pack is off, the
section is written as `disabled`. When `[report.sections.performance]` is
enabled and an in-memory assessment section exists, Phase **4.9.6** projects
it into `assessment.performance` / HTML **Performance Intelligence**.

## Gate matrix

| `analysis.performance.enabled` | Result |
| ------------------------------ | ------ |
| false | No `performance-assessment.json` |
| true (pack off) | Disabled section (`performance-assessment` **1.2.0**) |
| true (pack on) | Inventory + synthesis from Findings + execution facts |

| `analysis.performance.include_synthesis` | Result |
| ---------------------------------------- | ------ |
| true (default when analysis enabled) | Themes, conclusions, recommendations, posture |
| false | Inventories only; synthesis status `not_requested` |

| `evidence.repository_performance.enabled` | Result |
| ----------------------------------------- | ------ |
| false | No `repository-performance-evidence.json` |
| true | Platform evidence artifact (`repository-performance-evidence` **1.0.0**) |

| `rules.enabled` + `rules.performance.enabled` | Result |
| --------------------------------------------- | ------ |
| false | No performance hygiene Findings |
| true | Evaluate `performance.core` against in-memory evidence |

| `report.sections.performance.enabled` | Result |
| ------------------------------------- | ------ |
| false | No `assessment.performance` / HTML Performance section |
| true (assessment section available) | Project in-memory section into report presentation |
| true (no assessment section) | Report status `unavailable`; other report content kept |

Enabling evidence or rules does **not** enable `[analysis.performance]`.
Enabling the report gate does **not** enable analysis. Enabling Performance
gates does not enable Architecture, Technical Debt, Dependency, Security,
Test, Cloud, or AI Readiness gates. Existing configs without Performance
settings remain valid.

See [report.md](report.md), [synthesis.md](synthesis.md), [inventory.md](inventory.md),
[hygiene-rules.md](hygiene-rules.md), [domain-foundation.md](domain-foundation.md),
[taxonomy.md](taxonomy.md), and
[repository-performance-evidence.md](../repository-performance-evidence.md).
