# Intelligence Platform Architecture

Descriptive conventions established by Architecture (4.2), Technical Debt (4.3),
Dependency (4.4), Security foundation (4.5.1), repository-sensitive evidence
(4.5.2), Security hygiene rules (4.5.3), Security assessment inventory (4.5.4),
and Security synthesis (4.5.5).

This document does **not** introduce a generic `IntelligencePack` abstraction.

## Flow

```
Repository Inventory
    → reusable platform evidence
    → capability-specific rules
    → shared Findings
    → assessment inventory / section
    → deterministic synthesis (when implemented)
    → presentation-only report adapter (when implemented)
```

## Reusable evidence ownership

Evidence platforms own parsing and normalized facts (for example Dependency
Evidence for manifests, and Repository-Sensitive Evidence for potentially
sensitive artifacts / configuration literals). Intelligence verticals consume
evidence; they do not reparse repositories as a second source of truth.

Security Intelligence (4.5.1+) intentionally does **not** own a generic
Security Evidence collector. Phase 4.5.2 adds platform
`evidence.repository_sensitive` for repository-visible security-relevant facts.
Phase 4.5.3 Security hygiene rules consume that evidence and emit shared
Findings — without treating evidence collection as a vulnerability conclusion.
Phase 4.5.4 organizes those Findings into a deterministic assessment inventory
(`security-assessment` 1.2.0+). Phase 4.5.5 adds deterministic synthesis on
schema **1.3.0** without scores or report projection.

## Shared Finding ownership

All intelligence verticals emit or project the shared Finding model.
Capability-specific finding types are forbidden.

Category mapping examples:

- `RuleCategory.ARCHITECTURE` → `FindingCategory.ARCHITECTURE`
- `RuleCategory.TECHNICAL_DEBT` → `FindingCategory.TECHNICAL_DEBT`
- `RuleCategory.DEPENDENCY` → `FindingCategory.DEPENDENCY`
- `RuleCategory.SECURITY` → `FindingCategory.SECURITY`

## Assessment lifecycle

Sections support explicit statuses such as `disabled`, `not_requested`,
`succeeded`, `insufficient_evidence`, `partially_succeeded`, `failed`, and
`not_applicable`. Empty or disabled sections remain deterministic and do not
claim absence of risk.

## Production / test separation

Where inventories exist (Technical Debt, Dependency, Security), production is
the primary health view; test/fixture observations remain labeled separately.
Unknown-role Security findings are never treated as production.

## Deterministic identifiers and serialization

IDs are derived from stable semantic facts (hashes of canonical payloads), not
timestamps, absolute paths, UUIDs, or memory addresses. Artifacts serialize with
stable ordering for byte-identical repeated runs.

## Synthesis boundaries

Synthesis is inventory-derived and deterministic. It must not invent scores,
financial impact, upgrade targets, or AI narrative. Security synthesis in 4.5.5
is inventory-derived and template-driven only.

## Report adapter boundaries

Report adapters are presentation-only. They consume in-memory assessment
sections, do not recollect evidence or re-run rules, and are gated independently
(`report.sections.*`). Security report gate ships in 4.5.6 as
`report.sections.security` (default false).

## Feature gates

Each vertical uses independent opt-in gates, typically:

- `rules.<capability>.enabled`
- `assessment.sections.<capability>.enabled`
- optional evidence and report gates when those phases land

Defaults are disabled and backward compatible.

## Schema versioning

Assessment section schemas version independently per capability
(`assessment.architecture`, `assessment.technical_debt`,
`assessment.dependency`, `assessment.security`). Customer `report.json` schema
bumps only when required; additive keys are preferred.

## Traceability

Sections retain bounded edges from section → pack / coverage / limitations
(and later findings, themes, conclusions, recommendations).

## Failure isolation

Capability assembly failures must warn, mark the section failed/unavailable, and
continue the remaining assessment.

## Dogfood and acceptance

Each vertical dogfoods against CodeStrata and a reference repository (for
example Spring Petclinic), records repeated-run identity, and documents explicit
limitations before acceptance.
