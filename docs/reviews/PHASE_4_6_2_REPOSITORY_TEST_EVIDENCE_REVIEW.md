# Phase 4.6.2 — Repository Test Evidence Review

**Date:** 2026-07-25  
**Artifacts:** `reports/dogfood-phase-4-6-2/` (gitignored)  
**Schema:** `repository-testing-evidence` **1.0.0**  
**Artifact:** `repository-testing-evidence.json`  
(`codestrata.repository_testing_evidence`)

## Recommendation

**Accept Phase 4.6.2.** Platform evidence collects deterministic
repository-observable testing structure and configuration facts only.
No Test rules, Findings, assessment inventory, synthesis, report integration,
test execution, or runtime coverage measurement were added.

Repository Test Evidence records supported repository-observable testing
structure and configuration facts. It does not execute tests or evaluate test
quality.

## Evidence ownership

| Concern | Owner |
| ------- | ----- |
| Discovery / structural / build / CI / coverage-config facts | Platform `repository_testing` evidence |
| Test Intelligence interpretation | Deferred (future Test rules) |
| Findings / severity / remediation | Not in this phase |

Collectors do not import `aimf.domain.testing` / `aimf.application.testing`
and do not emit Findings.

## CodeStrata dogfood

| Field | Value |
| ----- | ----- |
| Status | `succeeded` |
| Schema / version | `repository-testing-evidence` / `1.0.0` |
| Bundle ID | `test-evidence:7ba4cc54a5d4e748` |
| Candidate test files | 259 |
| Structurally confirmed | 174 |
| Test directories / roles | primarily `tests/**` → `unit_test`; fixtures → `test_fixture` |
| Frameworks declared | `coverage_py`, `jest`, `junit`, `pytest` (6 declared facts) |
| Frameworks structurally observed | 175 |
| Build configuration facts | 6 |
| Marker facts | 28 (`skipped`, `conditional_skip`, `expected_failure`, `focused`, `disabled`) |
| Fixture / support candidates | 17 |
| Coverage configurations | 1 (`pyproject.toml`) |
| CI invocation facts | 0 (no local CI workflow files in inventory) |
| Diagnostics | 0 |
| Limitations | 13 (standard bounded set) |
| Repeat-run record identity | **stable** `bundle_id` / fingerprint / record IDs |
| Repeat-run bytes | Inventory size can vary between assess runs (`repository_files_considered`); with a fixed inventory, serialization is **byte-identical** |

Manual notes:

- Candidates are under `tests/` plus example/fixture manifests; `.aimf/` excluded.
- `Visit.java`-style false `*IT.java` collisions are not present.
- `.DS_Store` under `tests/` is not a candidate.
- No absolute paths, fixture bodies, Findings, or coverage percentages in the artifact.
- Production `src/main` paths are not misclassified as test candidates.

## Spring Petclinic dogfood

| Field | Value |
| ----- | ----- |
| Status | `succeeded` |
| Schema / version | `repository-testing-evidence` / `1.0.0` |
| Bundle ID | `test-evidence:c843ec248daf2b3a` |
| Candidate test files | 20 |
| Structurally confirmed | 17 |
| Roles | `unit_test`, `integration_test` |
| Frameworks declared | `jacoco`, `junit`, `junit_jupiter` |
| Frameworks structurally observed | 26 (JUnit / JUnit Jupiter only after language-scoped tokens) |
| Build configuration facts | 5 (Maven/Gradle test + JaCoCo) |
| Marker facts | 16 (`disabled` / `@Disabled`) |
| Fixture / support candidates | 0 |
| Coverage configurations | 1 (`pom.xml` JaCoCo) |
| CI invocation facts | 2 — `./mvnw -B verify`, `./gradlew build` |
| Diagnostics | 0 |
| Limitations | 13 |
| Repeat-run artifact | **byte-identical** (stable inventory) |

Manual notes:

- `*IntegrationTests.java` classified as `integration_test`; production
  `Visit.java` is **not** a candidate.
- Marker facts remain evidence-only (not Findings).
- CI commands retain tool identity without secret values.
- Language-scoped structural tokens prevent Java `visit(` from matching Mocha `it(`.

## Manual evidence and leakage review

| Check | Result |
| ----- | ------ |
| Candidate ≠ confirmed without structural tokens | Pass |
| Declared vs structurally_observed preserved | Pass |
| Production files not misclassified (`Visit.java`, Controllers) | Pass |
| Skipped/disabled markers are not Findings | Pass |
| No fixture / test-data content serialized | Pass |
| No absolute paths | Pass |
| No env/CI secret values | Pass |
| No runtime coverage % | Pass |
| No release-readiness / quality claims | Pass |
| No Test Findings emitted by evidence | Pass |
| Security evidence ownership unchanged | Pass |

## Quality checks

| Check | Result |
| ----- | ------ |
| Focused `tests/application/evidence/repository_testing` | **18 passed** |
| Full pytest suite | **1466 passed**, 1 unrelated sandbox `PermissionError` writing temp `.git/config` in scanner test |
| Ruff (new/modified evidence packages) | Pass |
| mypy (new/modified evidence packages) | Pass |
| Deterministic fixed-inventory serialization | Pass (byte-identical) |

## Confirmation

- No Test Intelligence rules executed by this evidence phase
- No shared Findings emitted by collectors
- No Test assessment inventory / synthesis / report integration added
- No test execution or runtime coverage measurement
- Architecture / Technical Debt / Dependency / Security gates unchanged in behavior
- `[evidence.repository_testing]` remains disabled by default
- Independent of `[rules.testing]` / `[assessment.sections.testing]`
- No git commit created for this phase

## Deferred scope

Test rules, Findings, assessment inventory, hotspots, synthesis, conclusions,
recommendations, report integration, CLI/MCP presentation, mutation testing,
assertion quality, flakiness prediction, remote CI history, and AI interpretation.
