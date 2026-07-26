# Phase 4.4.4 — Dependency Inventory and Assessment Usability Dogfood Review

**Date:** 2026-07-24  
**Artifacts:** `reports/dogfood-phase-4-4-4/` (gitignored)  
**Schema:** `assessment.dependency` **1.1.0**

## Recommendation

**Accept Phase 4.4.4.** Production-primary inventory is usable, totals reconcile,
fixture findings stay out of the primary view, and Petclinic Gradle
interpolations remain diagnostics (not findings). No synthesis or CTO report
integration was added.

## CodeStrata

| Field | Value |
| ----- | ----- |
| Assessment status | `succeeded` |
| Evidence status | `partially_succeeded` (preserved in coverage/diagnostics) |
| Section version | `1.1.0` |
| Primary findings (`finding_ids`) | **0** |
| All findings (`all_finding_ids`) | **2** (test/fixture only) |
| Production parse failures | 0 |
| Test/fixture parse failures | 0 |
| Repeat-run artifact identity | **byte-identical** |

### Declarations by source role

| Role | Total | Active | Management | Plugin | Test/dev kind |
| ---- | ----- | ------ | ---------- | ------ | ------------- |
| production | 12 | 12 | 0 | 0 | 0 |
| test | 25 | 20 | 1 | 4 | 4 |
| unknown | 0 | 0 | 0 | 0 | 0 |

### Manifests

9 manifests (1 production `pyproject.toml`; 8 test/fixture). Ecosystems:
`python`, `maven`, `gradle`.

### Findings inspection

| Rule | Path role | Disposition |
| ---- | --------- | ----------- |
| `dependency.unresolved-version` (`com.example:missing-prop`) | test/fixture | True positive; **not** in production-primary view |
| `dependency.duplicate-declaration` (`httpx`) | test/fixture | True positive; **not** in production-primary view |

### Top test hotspots

1. `tests/.../fixtures/maven/pom.xml` — 1 finding, diagnostics present  
2. `tests/.../fixtures/python/requirements-extra.txt` — 1 finding  

Production hotspot: `pyproject.toml` — 0 findings.

### Diagnostics

8 diagnostic records (all test/fixture): dynamic Gradle, Maven parent not
fetched, unresolved expression, requirements directive — **not** findings.

## Spring Petclinic

| Field | Value |
| ----- | ----- |
| Assessment status | `succeeded` |
| Evidence status | `partially_succeeded` |
| Primary findings | **0** |
| All findings | **0** |
| Declarations | 65 production (active 47 / plugin 18; test-kind declarations 19) |
| Manifests | `build.gradle` + `pom.xml` (both production, partially_succeeded) |
| Proven unresolved | 0 |
| Unsupported resolution (summary) | 6 |
| Production parse failures | 0 |
| Repeat-run artifact identity | **byte-identical** |

### Hotspots

1. `build.gradle` — 0 findings, 9 diagnostics (includes unsupported Gradle
   interpolation)  
2. `pom.xml` — 0 findings, 2 diagnostics (parent/plugin-management)

### Gradle interpolation acceptance

Unsupported Gradle `${webjars*Version}` remains
`unsupported_gradle_resolution` diagnostics — **zero findings**.

## Reconciliation

- CodeStrata: `12 + 25 = 37` declarations = evidence `declarations_collected`
- Petclinic: `65` declarations = evidence total
- Kind inventories separate active runtime/test from plugins (and management
  where present)
- Primary finding count = production finding inventory = console
  “Dependency assessment findings”
- Complete finding inventory = raw `dependency.*` findings
- No absolute paths in `dependency-assessment.json`
- No themes / conclusions / recommendations / scores in the section

## Explicit limitations (unchanged product scope)

Declared-only; no transitive resolution; no build-tool execution; no registry
lookups; static Gradle only; no npm; no framework/`DependencyRole`
classification; no CVE/license/lifecycle analysis; no CTO report integration.
