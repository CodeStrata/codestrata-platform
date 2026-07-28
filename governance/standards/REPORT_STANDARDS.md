# Report Standards

**Status:** Foundation  
**Authority:** Standards

## Objective

Define standards for customer-facing assessment reports (HTML / JSON).

## Scope

Engine reporting (`engine/src/codestrata/reporting/`). Platform may store and
serve artifacts but does not redefine report meaning here.

## 1. Principles

1. Deterministic findings and Priority Actions remain authoritative.
2. AI / advisor sections are clearly labeled as interpretation.
3. Evidence must be reachable from findings and recommendations.
4. Reports must not leak secrets (paths may be sanitized per policy).

## 2. Artifacts

| Artifact | Role |
| -------- | ---- |
| HTML report (v2) | Leadership + engineering readable assessment |
| `report.json` | Machine contract (schema **1.2**, additive evolution) |
| Evidence / graphs | Supporting artifacts |

JSON compatibility and versioning:
[`../playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md`](../playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md)
§2. Schema file:
`engine/src/codestrata/resources/schemas/assessment/codestrata.io/v1.2/AssessmentReport.json`.

Breaking report shape requires a new schema version — do not break 1.2 clients.

## 3. Branding & design

- Product name: **CodeStrata** (see [BRANDING_GUIDELINES.md](BRANDING_GUIDELINES.md))
- Visual rules: [`../assets/DESIGN-SYSTEM.md`](../assets/DESIGN-SYSTEM.md)
  (single authority; do not fork styles)

## 4. Accessibility & print

<!-- TODO: Accessibility checklist (headings, contrast, print CSS). -->

## 5. References

- [engine/docs/report-generation.md](../../engine/docs/report-generation.md)
- [engine/src/codestrata/reporting/branding.py](../../engine/src/codestrata/reporting/branding.py)
- [004_PRODUCT_PRINCIPLES.md](../constitution/004_PRODUCT_PRINCIPLES.md)
