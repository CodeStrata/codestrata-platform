# Phase 4.4.2 — Dependency Evidence Dogfood Review

**Date:** 2026-07-24  
**Artifacts:** `reports/dogfood-phase-4-4-2/` (gitignored)

## Recommendation

**Accept Phase 4.4.2 Dependency Evidence Platform** as an evidence-only milestone.
Manifests are discovered and parsed deterministically; unsupported and unresolved
constructs remain explicit. No rules, findings, or CTO report content were
introduced.

## CodeStrata

| Field | Value |
| ----- | ----- |
| Status | `partially_succeeded` |
| Manifests supported | 9 (2 excluded under ignore markers) |
| Declarations | 37 |
| Ecosystems | Python 22, Gradle 8, Maven 7 |
| Source-role | source 12, test 25 (fixture trees under `tests/`) |
| Unsupported constructs | 5 |
| Unresolved expressions | 1 (`${missing.version}`) |
| Repeated-run identity | identical |

Notable CodeStrata manifests: root `pyproject.toml` (12 decls, succeeded) plus
fixture Maven/Gradle/requirements trees used by unit tests.

## Spring Petclinic

| Field | Value |
| ----- | ----- |
| Status | `partially_succeeded` |
| Manifests | `pom.xml`, `build.gradle` |
| Declarations | 65 (Maven 38, Gradle 27) |
| Source-role | source 65 |
| Unsupported | parent not fetched; pluginManagement; dynamic Gradle `${…}` webjar lines |
| Unresolved | 3 Gradle `${webjars*Version}` coordinates |

Correctly does **not** invent parent-POM or transitive dependencies.

## Unsupported / unresolved inventory (representative)

- Maven parent not fetched
- Maven `pluginManagement` noted
- Gradle `project(...)` / `files(...)` dynamic constructs
- Gradle `${property}` version interpolations
- requirements `--index-url` directive (no URL retrieval)

## Confirmation

- No dependency rules or findings
- No DependencyRole classification of packages
- No CVEs, licenses, registry calls, or npm support
- No absolute user paths in artifacts
