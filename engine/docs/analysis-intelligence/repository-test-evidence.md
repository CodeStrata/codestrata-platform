# Repository Test Evidence

Phase **4.6.2** — reusable repository-observable testing structure and
configuration evidence.

Repository Test Evidence records supported repository-observable testing
structure and configuration facts. It does not execute tests or evaluate test
quality.

This is **platform evidence**, not a Test Intelligence capability package.

## Ownership

| Concern | Owner |
| ------- | ----- |
| Test-file / fixture / coverage-config / CI discovery | **Repository Test Evidence** |
| Structural framework / marker indicators | **Repository Test Evidence** |
| Declared build/manifest test tooling | **Repository Test Evidence** |
| Test quality / pass-fail / severity / remediation | Test Intelligence (`testing.core` hygiene rules, Phase 4.6.3) |
| Test execution / runtime coverage % | Explicitly out of scope |

Collectors must **not** import `codestrata.domain.testing`,
`codestrata.application.testing`, Findings, or report adapters, and must **not**
emit Findings.

**Test Hygiene rules (Phase 4.6.3)** consume this evidence in-memory only and
never re-read repository files. See
[testing/hygiene-rules.md](testing/hygiene-rules.md).

Other Analysis Intelligence verticals may also consume these facts later.
Evidence remains independently gated.

## Configuration

```toml
[evidence.repository_testing]
enabled = false
```

Disabled by default. Independent of `[rules.testing]` and
`[assessment.sections.testing]`.

## Artifact

`repository-testing-evidence.json`

| Field | Value |
| ----- | ----- |
| Schema name | `repository-testing-evidence` |
| Schema version | `1.0.0` |
| Artifact schema id | `codestrata.repository_testing_evidence` |

## Bundle contents

- file candidates (discovery bases + confirmation level)
- structural test facts
- framework facts (declared / structurally observed / configured / invoked)
- test-type facts
- build configuration facts
- marker facts (disabled / skipped / focused — never Findings)
- fixture facts (path metadata only)
- coverage facts (configuration / report references — no percentages)
- CI test invocation facts
- coverage summary
- diagnostics (never Findings)
- limitations
- deterministic fingerprint / bundle id

## Boundaries

| In scope | Out of scope |
| -------- | ------------ |
| Repository-visible paths and manifests | Running tests |
| Convention-based discovery | Judging test quality |
| Bounded structural tokens | Assertion effectiveness |
| Declared tooling in build files | Secret/CVE conclusions |
| Local CI workflow command projections | Remote CI history |
| Coverage configuration presence | Runtime coverage % |

## Discovery

Conventional directories (examples): `tests/`, `src/test/`, `__tests__/`,
`cypress/`, `playwright/`, `e2e/`, `fixtures/`, `testdata/`.

Filename conventions (examples): `test_*.py`, `*_test.py`, `*Test.java`,
`*IT.java`, `*.test.ts`, `*_test.go`.

Weak production names alone (`Controllers.java`, `service.py`) are **not**
candidates.

Default ignore markers exclude generated/vendor noise such as
`node_modules/`, `target/`, `vendor/`, `.venv/`, `__pycache__/`, `reports/`.

Discovery bases (directory, filename, fixture convention, …) are preserved on
candidates.

## Candidate vs confirmed

Discovery yields `discovered_candidate`. Content inspection may raise
confirmation to `structurally_inspected` or `structurally_confirmed`. Filename
discovery alone never claims a confirmed test.

## Frameworks and build

Declared frameworks come from manifests (`pom.xml`, `package.json`,
`pyproject.toml`, `requirements*.txt`, Gradle, `.csproj`, …).

Structurally observed frameworks come from bounded tokens inside candidate
files (`def test_`, `@Test`, `describe(`, `func Test`, …).

The same framework family may appear under both `declared` and
`structurally_observed` bases when both exist.

## Markers

Collects disabled / ignored / skipped / focused / conditional-skip /
expected-failure markers as facts. Markers are **not** Findings and are not
judged as justified or unjustified.

## Fixtures

Fixture/support/test-data paths are recorded as metadata candidates. Fixture
**content is never serialized**.

## Coverage configuration

Recognizes coverage configuration / report-reference artifacts (for example
`.coveragerc`, Jacoco-named paths, nyc/jest coverage configs). Does **not**
record runtime coverage percentages.

## CI

Local workflow files (for example `.github/workflows/*.yml`) may contribute
test-command invocation facts, including `continue-on-error` / conditional
signals when present. Command projections redact `TOKEN=` / `PASSWORD=` /
`SECRET=` / `API_KEY=` values. Absolute paths are not serialized.

## Summary / diagnostics / limitations

Coverage counters describe inspected repository-observable testing candidates
only. Zero evidence does **not** establish that tests are absent or that the
repository is release ready.

Diagnostics cover unsupported / oversized / unreadable / truncated cases.
Standard limitations document snapshot-only scope, no execution, no pass/fail,
no runtime coverage, convention-based types, markers not judged, fixture
content not evaluated, and no release-readiness conclusion.

## Privacy

No absolute filesystem paths. Secret-like assignments in command projections
are redacted. Fixture and oversized file bodies are not persisted.

## Lifecycle

| Status | Meaning |
| ------ | ------- |
| `not_applicable` | Gate disabled |
| `succeeded` | Usable facts without blocking diagnostics |
| `partially_succeeded` | Usable facts plus load/inspection diagnostics |
| `insufficient_evidence` | Empty inventory (orchestration) |
| `failed` | Collection failure / unusable inputs |
| `skipped` | Reserved |

## Explicit deferred scope

Test Intelligence inventories, synthesis, CTO report integration, test
execution, runtime coverage measurement, remote CI history, test-to-source
mapping, quality scoring, CLI/MCP commands, and TEST-004
(observed-without-declaration).

Hygiene Findings from `testing.core` (Phase 4.6.3) consume this evidence but
do not change the evidence schema or ownership.
