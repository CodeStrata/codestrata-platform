# Report Quality Benchmark

Status: executable product-quality contract  
Date: 2026-08-13

## Benchmark question

How can CodeStrata make a defensible “at least as useful” claim when specialist
tools have different detectors, languages, licenses, and goals?

It cannot promise detector parity with every tool. The defensible target is:

> For the evidence sources the user selects, CodeStrata must preserve at least
> the producer's actionable result and add standardized coverage, provenance,
> cross-source traceability, explicit gaps, and a verification-oriented action
> report without weakening or inventing the producer's claim.

## Representative product classes

| Class | Representative | Mechanism CodeStrata must preserve or exceed |
|---|---|---|
| Meta-linter | MegaLinter | Language/tool selection, many output reporters, SARIF interoperability, local/CI execution boundary |
| Developer orchestrator | Trunk Check | Repository-aware applicability, visible tool choice, reproducible configuration |
| Hook framework | pre-commit | User-authored hook composition, explicit arbitrary-code boundary, independent hook licenses |
| Syntax analyzer | Semgrep CE | Source-located finding, rule identity, severity, remediation, JSON/SARIF export |
| Security posture | OpenSSF Scorecard | Check-level reason, risk, details, remediation, structured inconclusive state, no one-size-fits-all claim |
| Quality gate | SonarQube | Versioned conditions evaluated separately from measurements |
| Code health | RepoWise | Deterministic biomarker identity, file measurement, severity, reason, health impact, coverage, concrete remediation |

## Required CodeStrata report gates

Every end-to-end benchmark report must pass all gates below.

1. **Choice fidelity** — report records the exact packs, collectors,
   capabilities, biomarkers, thresholds, imports, scope, and assessment head.
2. **Producer fidelity** — producer ID/version, native artifact hash, rule or
   biomarker ID, original severity, locations, and producer-specific details are
   retained when available.
3. **Type separation** — raw artifacts, measurements, observations, producer
   findings, assessment claims, findings, risks, and actions are not collapsed
   into one score or undifferentiated issue list.
4. **Coverage honesty** — planned population, examined population, failures,
   unsupported inputs, truncation, and absence-conclusion basis are explicit.
5. **Action quality** — every material finding has a concrete action,
   rationale, priority, and a re-run or acceptance verification step.
6. **Traceability** — evidence → claim → finding → risk/action edges validate
   against stable identifiers.
7. **Interoperability** — canonical JSON, evidence JSONL, HTML, and SARIF are
   generated from the same result; imported SARIF remains source-located.
8. **Failure isolation** — unavailable or failed tools become visible gaps and
   do not erase successful evidence from other activities.
9. **No false universality** — a clean result from a partial producer or
   unsupported language cannot become “the repository is healthy.”
10. **Usable initiation** — a user can start from a GitHub URL, see detected
    languages, apply recommended packs, tune individual mechanisms, preview
    execution boundaries, and open the report without editing YAML.

## Honest comparative position

| Axis | Current CodeStrata target | Comparative judgment |
|---|---|---|
| Built-in linter breadth | Reuse language providers plus SARIF/process adapters | Below MegaLinter's scanner breadth; intentionally does not rebuild its 63-language tool distribution |
| Health-detector depth | Transparent native structural thresholds plus optional RepoWise artifact adapter | Native collector is below RepoWise; selected RepoWise output is preserved and gains cross-source reporting |
| Repository auto-fit | Detect languages and recommend versioned packs | Comparable initiation principle to Trunk, without automatic installation or hidden execution |
| Custom composition | Packs, collector capabilities, biomarkers, thresholds, patterns, imports, attestations | Broader evidence-type control than a linter-only configuration |
| Coverage and negative claims | Mandatory typed coverage; absence requires a complete successful population | Stronger default trust contract than flat finding lists |
| Cross-tool reporting | One normalized evidence ledger and trace graph | Primary differentiator over independent tool reports |
| Decision rules | Separate versioned assessment heads | Directionally comparable to quality gates; research-backed domain heads remain follow-on work |

## Primary sources

- MegaLinter catalog, flavors, reporters, SARIF, and AGPL-3.0:
  https://megalinter.io/latest/
- Trunk Code Quality overview:
  https://docs.trunk.io/code-quality/overview
- pre-commit multi-language framework and MIT license:
  https://github.com/pre-commit/pre-commit
- Semgrep Community Edition JSON/SARIF findings and remediation:
  https://semgrep.dev/products/community-edition/
- OpenSSF Scorecard checks, structured results, remediation, scoring, and
  explicit non-goals: https://github.com/ossf/scorecard
- SonarQube quality gates:
  https://docs.sonarsource.com/sonarqube/latest/user-guide/quality-gates
- RepoWise health detector, benchmark, CLI JSON, and licensing disclosures:
  https://github.com/repowise-dev/repowise

These sources establish product mechanisms and vendor/project claims. They do
not establish that CodeStrata has superior detector accuracy. Accuracy claims
require shared corpora, ground truth, matched versions, and repeatable
measurements; that is a separate validation program.
