# Community Insights Ingestion Hardening (Slice 15.4)

Hardens privacy-safe Community analytics ingestion contracts for future
Insights Dashboard use. **Production transmission remains disabled.**

## Operational activation

**Decision: `activation_ready_but_production_disabled`**

- `enable_ingestion_wire = false`
- Writer IAM unattached
- Fail-soft sinks / feature gates preserved
- Additive contracts are ready for a later deployment gate

## CR dispositions

| CR | Result |
| --- | --- |
| CR-15.3-001 | Optional `repository.package_ecosystem` closed enum on assessment_metadata |
| CR-15.3-002 | `openrouter` added to provider_family catalogs (family only) |
| CR-15.3-003 | VS Code reads Engine shared identity file; no machineId; transmission off |

## Flow

CLI / VS Code → privacy-safe projection → local validation → Community Cloud API →
server revalidation → lake envelope → accepted writer **or** quarantine

No second analytics pipeline. No aggregations. No dashboard.

**Policy:** `community-insights-ingestion-policy:1.0`
