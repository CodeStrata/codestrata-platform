# Phase 4.6.3 — Test Evidence Quality Review

**Date:** 2026-07-25  
**Inputs:** Phase 4.6.2 dogfood artifacts under `reports/dogfood-phase-4-6-2/`  
**Evidence schema:** `repository-testing-evidence` **1.0.0**

## Purpose

Classify repository-testing evidence areas before enabling Test Hygiene rules.
Rules must consume high-confidence signals only. No silent evidence semantics
changes were made solely to enable rules.

## Snapshot (latest dogfood)

| Metric | CodeStrata | Spring Petclinic |
| ------ | ---------- | ---------------- |
| Status | `succeeded` | `succeeded` |
| Candidates / confirmed | 259 / 174 | 20 / 17 |
| Unconfirmed (by confirmation_level) | 85 (ratio ≈ 0.33) | 3 (ratio ≈ 0.15) |
| Unconfirmed roles | mostly `unit_test` `__init__.py` + fixtures | jmeter / support helpers |
| Marker facts | 28 | 16 (`disabled`) |
| Frameworks declared | pytest, jest, junit, coverage_py | junit, junit_jupiter, jacoco |
| Frameworks observed | pytest, unittest, junit | junit, junit_jupiter |
| Coverage configurations | 1 (`pyproject.toml`) | 1 (`pom.xml` JaCoCo) |
| CI files inspected / invocation facts | 0 / 0 | 3 / 2 |

## Classification

### Reliable enough for rules

| Area | Notes |
| ---- | ----- |
| Disabled/skipped markers (`marker_facts`) | Language-scoped tokens; locations bounded; counts reconcile. Suitable for **TEST-001**. |
| Candidate vs structurally_confirmed | Confirmation levels are explicit. Suitable for ratio rule with thresholds (**TEST-002**). |
| Declared test frameworks (build/manifest) | Distinct `declared` / `configured` bases. Suitable for **TEST-003** when limited to true test frameworks (not coverage plugins). |
| Coverage configuration facts | Path + tool identity without percentages. Suitable for **TEST-005** when CI was inspected. |
| CI invocation facts | Normalized commands with redaction; Maven/Gradle wrappers supported. Suitable for **TEST-005** negation. |

### Needs stronger confirmation

| Area | Notes |
| ---- | ----- |
| Framework structural observation breadth | Observation is per-file token presence; many observations can dilute uniqueness. Rules must compare **framework families**, not raw observation counts. |
| Declared vs observed language alignment | Example: CodeStrata declares `jest` via `examples/sample-js-app` while primary inspected language is Python. **TEST-003** must require overlapping inspected languages / candidates for the framework’s ecosystem. |
| Unconfirmed candidates under `tests/` | Many `__init__.py` and package markers are naming/directory candidates, not failed tests. Exclude fixture/support/config roles from the material-unconfirmed ratio. |

### Informational only

| Area | Notes |
| ---- | ----- |
| Fixture / support candidates | Metadata-only; do not drive Findings. |
| Coverage report *references* without config | Presence alone does not imply CI gap. |
| Diagnostics for unsupported encoding | Lifecycle signal; not Findings. |
| Limitations | Always informational. |

### Deferred

| Area | Reason |
| ---- | ------ |
| **TEST-004** (observed without declaration) | Parent/centralized builds, transitive deps, and monorepo ownership cannot be bounded reliably from Phase 4.6.2 evidence alone. Implementing would create material false positives. |
| Runtime coverage % | Explicitly out of evidence contract. |
| Assertion / effectiveness signals | Not collected. |
| Remote CI history | Not collected. |
| Fixture content quality | Intentionally not serialized. |

## Rule enablement decisions

| Rule | Decision | Rationale |
| ---- | -------- | --------- |
| TEST-001 (`testing.test-001`) | **Implement** | Marker facts are high-confidence and explainable. |
| TEST-002 (`testing.test-002`) | **Implement** | Material unconfirmed ratio with min count/ratio; exclude fixtures/support. |
| TEST-003 (`testing.test-003`) | **Implement** | Declared test frameworks without family observation, with language/completeness gates. |
| TEST-004 (`testing.test-004`) | **Defer** | Declaration ownership ambiguity. |
| TEST-005 (`testing.test-005`) | **Implement** | Coverage config + inspected CI without invocation; suppress when no CI. |

## Evidence corrections (explicit, if any)

No evidence-schema changes are required for this phase.

Precision improvements already present from Phase 4.6.2 dogfood follow-up
(language-scoped structural tokens; `Visit.java` IT false-positive fix;
junk-file exclusion) remain in force and are prerequisites for these rules.

## Dogfood expectation preview

| Rule | CodeStrata | Petclinic |
| ---- | ---------- | --------- |
| TEST-001 | Likely (28 markers) | Likely (16 `@Disabled`) |
| TEST-002 | Likely (material unconfirmed under `tests/`) | Unlikely (3 unconfirmed, low ratio) |
| TEST-003 | Possible for `jest` if JS evidence incomplete; suppress if language gate fails | Unlikely (junit observed) |
| TEST-005 | Suppress (no CI inspected) | Suppress (CI invocations present) |
