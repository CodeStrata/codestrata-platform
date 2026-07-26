# Phase 4.4.3A — Dependency Unresolved-Version Precision Correction

**Date:** 2026-07-24  
**Artifacts:** `reports/dogfood-phase-4-4-3a/` (gitignored)

## Root cause

`dependency.unresolved-version` treated Dependency Evidence
`unresolved_expressions` / collector non-resolution as proven repository absence.
For Gradle `${webjars*Version}`, the collector never inspected
`gradle.properties`, ext/extra, catalogs, or convention plugins — so
“collector unresolved” ≠ “repository unresolved.”

## Chosen resolution contract

**Preferred minimal approach:**

- Findings require `version_resolution_status == proven_unresolved`
- Maven local `pom.xml` property inspection remains the supported contract for
  proven unresolved / resolved
- Gradle interpolations are recorded as
  `unsupported_version_resolution:gradle_interpolation_uninspected` (+ diagnostics)
  with partial coverage — **not** findings
- Unfetched Maven parent/BOM remains unsupported coverage, not proven unresolved

## Acceptance dogfood

### CodeStrata

| Metric | Value |
| ------ | ----- |
| Dependency findings | 2 |
| `dependency.unresolved-version` | 1 — fixture `${missing.version}` (**true positive / proven**) |
| `dependency.duplicate-declaration` | 1 — fixture `httpx` duplicate |
| Evidence | `partially_succeeded`; unresolved_expression_count=1; unsupported=5 |
| Repeat-run | finding IDs + evidence fingerprint identical |

### Spring Petclinic

| Metric | Value |
| ------ | ----- |
| Dependency findings | **0** (was 3 Gradle unresolved findings in 4.4.3) |
| Evidence | `partially_succeeded`; unresolved_expression_count=0; unsupported=8 |
| Diagnostics | 3 `version_resolution_unsupported:gradle_property_or_dynamic:…${webjars*Version}` |
| Unsupported constructs | include `unsupported_version_resolution:gradle_interpolation_uninspected` |

Petclinic `${webjars*Version}` retained as **coverage diagnostics**, not findings.

## Disposition vs 4.4.3

| Item | 4.4.3 | 4.4.3A |
| ---- | ----- | ------ |
| CodeStrata `${missing.version}` | finding | finding (kept) |
| Petclinic Gradle `${webjars*}` | 3 findings | 0 findings + diagnostics |

## Acceptance recommendation

**Accept 4.4.3A.** Precision defect corrected without Gradle execution or remote
parent/BOM resolution.
