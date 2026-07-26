# AI Readiness Intelligence Configuration

All AI Readiness Intelligence gates default to **disabled**.

```toml
[analysis.ai_readiness]
enabled = false
# include_findings = true
# include_coverage = true
# include_limitations = true
# include_traceability = true
# include_execution_summary = true
# include_synthesis = true
```

Platform evidence (independent of analysis; default off):

```toml
[evidence.repository_ai_readiness]
enabled = false
# max_files = 500
# max_file_chars = 500000
# max_file_bytes = 2000000
```

Hygiene rules (independent of analysis; default off; Phase 4.8.3):

```toml
[rules]
enabled = false

[rules.ai_readiness]
enabled = false
# Per-rule toggles (default enabled when the pack is on):
# [rules.ai_readiness.ai_001]
# enabled = true
```

Report presentation (independent; default off; Phase 4.8.6):

```toml
[report.sections.ai_readiness]
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

Enabling `[rules.ai_readiness]` does **not** enable `[analysis.ai_readiness]`.
Rules consume in-memory evidence only and never trigger collection. Enabling
the report gate projects an existing in-memory assessment section into
`assessment.ai_readiness` (`report.json`) and the HTML **AI Readiness
Intelligence** section; it does not run assessment or regenerate synthesis.

When `[analysis.ai_readiness]` is enabled and the pack is on, Phase **4.8.5**
writes `ai-readiness-assessment.json` (**1.2.0**) with inventories and
deterministic synthesis over existing Findings and rule-execution facts.
Set `include_synthesis = false` to keep inventories without themes /
conclusions / recommendations.

## Gate matrix

| `analysis.ai_readiness.enabled` | Result |
| ------------------------------- | ------ |
| false | No `ai-readiness-assessment.json` |
| true (pack off) | Disabled section with empty inventories |
| true (pack on) | Inventory + synthesis section (`ai-readiness-assessment` **1.2.0**) |

| `analysis.ai_readiness.include_synthesis` | Result |
| ----------------------------------------- | ------ |
| true (default) | Themes, conclusions, recommendations, posture summary |
| false | Synthesis status `not_requested` |

| `evidence.repository_ai_readiness.enabled` | Result |
| ------------------------------------------ | ------ |
| false | No `repository-ai-readiness-evidence.json` |
| true | Platform evidence artifact (`repository-ai-readiness-evidence` **1.0.0**) |

| `rules.enabled` + `rules.ai_readiness.enabled` | Result |
| ---------------------------------------------- | ------ |
| false | No AI Readiness Findings; analysis may still write a disabled/empty inventory section |
| true | Evaluate `ai_readiness.core` against in-memory evidence; merge Findings |

| `report.sections.ai_readiness.enabled` | Result |
| -------------------------------------- | ------ |
| false | No `assessment.ai_readiness` / no HTML AI Readiness section |
| true (assessment available) | Project `report.ai_readiness` **1.0.0** into JSON/HTML |
| true (assessment unavailable) | Report status `unavailable`; remaining report kept |

Enabling AI Readiness gates does not enable Architecture, Technical Debt,
Dependency, Security, Test, or Cloud gates. Existing configs without AI
Readiness settings remain valid.

See [inventory.md](inventory.md), [synthesis.md](synthesis.md),
[report.md](report.md),
[hygiene-rules.md](hygiene-rules.md),
[domain-foundation.md](domain-foundation.md), and
[../repository-ai-readiness-evidence.md](../repository-ai-readiness-evidence.md).
