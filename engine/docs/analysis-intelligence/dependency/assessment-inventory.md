# Dependency Assessment Inventory (Phase 4.4.4)

Schema: `assessment.dependency` **1.2.0** (`dependency-assessment.json`).

Production-primary inventory projection over Dependency Evidence and shared
dependency Findings, plus Phase 4.4.5 deterministic synthesis. **No** composite
scores, CVE/license fields, framework/`DependencyRole` classification, or CTO
report integration.

## Contract

Consumes (does not reparse):

1. `AggregatedDependencyEvidence`
2. Shared `Finding` objects from `dependency.*` hygiene rules

### Primary vs complete findings

| Field | Scope |
| ----- | ----- |
| `finding_ids` / `finding_summaries` | **Production** only |
| `all_finding_ids` / `all_finding_summaries` | Production + test/fixture + unknown |

Test-only findings never influence production-primary totals or health status.

### Inventories

- `evidence_summary` — transparent evidence counters + fingerprint
- `declaration_inventory` — role-partitioned; active vs management vs plugin
- `manifest_inventory` — one entry per discovered/supported manifest
- `aggregation_inventory` — by ecosystem, manifest type, kind, role, resolution
- `finding_inventory` — role-partitioned finding counts
- `hotspot_inventory` — manifest-level hotspots (presentation order, not priority)
- `diagnostics_summary` — diagnostics are **not** findings

### Hotspot presentation ordering (not a priority score)

1. production → test → unknown
2. highest finding severity
3. distinct matched rule count
4. finding count
5. manifest path

### Status semantics (production usability)

| Status | When |
| ------ | ---- |
| `disabled` | Pack gate off |
| `not_requested` | Section not requested |
| `insufficient_evidence` | Evidence off / missing / no supported manifests |
| `failed` | Evidence collection unusable (`failed`) |
| `partially_succeeded` | **Production** manifest parse failures |
| `succeeded` | Production evidence usable (even if test/fixture failures or unsupported-but-diagnosed constructs remain) |

Evidence-level `partially_succeeded` is preserved in coverage/diagnostics and
does not by itself force assessment partial status.
