# Dependency Assessment Synthesis (Phase 4.4.5)

Deterministic themes, conclusions, and recommendations derived from the
Dependency assessment inventory (schema `1.2.0`).

## Contract

| Input | Source |
| ----- | ------ |
| Finding references | `all_finding_summaries` |
| Hotspots / manifests | inventory projections |
| Declaration / aggregation inventories | section inventories |
| Evidence / diagnostics summaries | section summaries |
| Pack/section status | assessment gates |

Synthesis **does not** reparse manifests, recollect Dependency Evidence, or
reevaluate hygiene rules.

| Output | Attached on section |
| ------ | ------------------- |
| Themes | `themes` / `theme_ids` |
| Concentration facts | `concentration_facts` |
| Conclusions | `conclusions` / `conclusion_ids` |
| Recommendations | `recommendations` / `recommendation_ids` |
| Bundle | `synthesis` |

Section schema: `assessment.dependency` @ `1.2.0`.

```toml
[assessment.sections.dependency]
enabled = true
include_synthesis = true
```

`include_synthesis = false` yields `synthesis.status = not_requested` with empty
outputs.

## Themes

Derived only when inventory facts support them (no empty rule themes):

| Kind | Scope |
| ---- | ----- |
| `dependency_landscape` | repository |
| `manifest_distribution` | repository |
| `declaration_hygiene` | production (when production findings exist) |
| `version_resolution_coverage` | coverage |
| per-rule hygiene themes | production or test_observation |
| `test_fixture_hygiene` | test_observation |
| `build_plugin_landscape` | production |
| `partial_ecosystem_coverage` | coverage (npm relevance only) |

## Concentration facts

Transparent counts/proportions only (not scores):

| Kind | Notes |
| ---- | ----- |
| `ecosystem_share` | declaration distribution by ecosystem |
| `plugin_share` / `dependency_management_share` / `active_share` | production declaration shares |
| `top_manifest_finding_share` | only when production findings > 0; threshold **0.40** |

Finding-concentration conclusions are not emitted when production findings are
zero.

## Conclusion kinds

| Kind | Audience |
| ---- | -------- |
| `dependency_landscape_identified` | repository |
| `no_production_hygiene_findings` | production_health |
| `production_hygiene_findings_present` | production_health |
| per-rule present kinds | production_health |
| `test_fixture_findings_present` | test_observation |
| `unsupported_resolution_coverage` | coverage |
| `production_collection_partial` | coverage |
| `declared_dependencies_only` | coverage |
| `unsupported_ecosystem_coverage` | coverage (npm relevance only) |
| `disabled` / `insufficient_evidence` | status |

Zero production findings does **not** claim zero dependency risk.

## Recommendations

Every recommendation cites ≥ 1 conclusion. Actions are factual/conditional.
Effort/business impact remain `unknown`. No upgrade-target or latest-version
advice.

## Production / test / coverage separation

- Production findings drive production-health conclusions and primary remediations.
- Test/fixture findings produce only test_observation outputs.
- Unsupported Gradle interpolation remains coverage (not unresolved findings).

## Traceability

Edges include `section_to_theme|conclusion|recommendation`,
`conclusion_to_theme|finding|hotspot|manifest|diagnostic`,
`recommendation_to_conclusion`.
