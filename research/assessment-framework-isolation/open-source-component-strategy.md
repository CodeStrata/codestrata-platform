# Open-source Component Strategy

Status: implementation decision record  
Date: 2026-08-12

## Decision question

What is the smallest CodeStrata-owned layer that creates the highest product
impact while preserving a credible path to a commercial offering?

The answer is **not another scanner suite**. CodeStrata should own the user
intent model, evidence contract, coverage semantics, claim reasoning,
traceability, and decision report. It should reuse existing CodeStrata
collectors and integrate mature external tools through stable formats and
process boundaries.

This is a technical licensing screen, not legal advice. A release that embeds
or redistributes a third-party component still needs a dependency-specific
legal review, retained notices, version pinning, and trademark review.

## Evaluation method

Each candidate was screened for:

1. Product leverage: capability gained versus CodeStrata code owned.
2. Boundary fit: collector, importer, assessment engine, UI, or report.
3. Commercial-use posture: license grant and redistribution obligations.
4. Operational weight: runtime, database, services, network, and install cost.
5. Evidence quality: structured output, provenance, locations, coverage, and
   limitations.
6. Replaceability: whether CodeStrata can retain its contracts if the component
   changes or disappears.
7. Project health: active maintenance, adoption, releases, and documentation.

## Component decisions

| Candidate | License observed | What it already solves | Decision |
|---|---|---|---|
| Existing CodeStrata 0.2.0 evidence collectors | CodeStrata repository license | Dependency declarations, testing structure, language, complexity, cloud, performance, sensitive and AI-readiness observations | **Adopt now.** Wrap them; do not rewrite them. |
| React JSON Schema Form (RJSF) | Apache-2.0 | React forms generated from JSON Schema, validation, widgets, themes | **Adopt for the plan editor.** Keep a custom goal-first wizard above it; expose RJSF as the advanced plan editor. |
| AJV | MIT | Browser-side JSON Schema 2020-era validation | **Adopt transitively with RJSF.** Server-side Pydantic validation remains authoritative. |
| Trivy | Apache-2.0 | Repository vulnerabilities, misconfiguration, secrets, licenses, and SBOM; JSON/SARIF-like structured output | **Optional executable adapter.** Highest-leverage external evidence pack; discover locally and never auto-install or enable secret scanning. |
| Syft | Apache-2.0 | Multi-ecosystem SBOM generation with CycloneDX and SPDX output | **Optional specialist adapter after CycloneDX import.** Prefer Trivy for the first broad pack and Syft where SBOM depth is the goal. |
| OSV-Scanner | Apache-2.0 | Source dependency vulnerability and license scanning, including an offline mode | **Optional vulnerability adapter.** Its network/offline behavior must be explicit in plan preview. |
| Gitleaks | MIT | Secret detection with SARIF output | **Optional adapter, off by default.** Normalize through SARIF and never retain secret text. |
| OpenSSF Scorecard | Apache-2.0; published API data has its own permissive data license | Repository security-practice checks and remediation | **Optional remote-repository pack.** Preserve check-level results and inconclusive states; do not repeat its aggregate score as a universal quality score. |
| ScanCode Toolkit | Apache-2.0 overall, with separately licensed datasets and third-party material | Deep license, copyright, package, and dependency inventory | **Integrate by exported artifact, not vendoring.** Its notice/data-license surface needs a separate release review. |
| DefectDojo Community | BSD-3-Clause | Many security scanner parsers, deduplication, remediation workflow, reporting | **Study parsers and offer an interoperability bridge; do not fork the application.** Django, database, and security-only domain weight are disproportionate for local repository assessment. |
| SARIF Tools / Microsoft SARIF SDK | MIT | SARIF inspection and object models | **Use selectively.** Python SARIF Tools is useful for offline validation and developer tooling; the .NET SDK is not a runtime fit. CodeStrata owns only its small normalization mapping. |
| CycloneDX Python Library | Apache-2.0 | Standards-compliant CycloneDX object model and validation | **Adopt when CycloneDX import/export enters the slice.** Do not invent an SBOM model. |
| Open Policy Agent | Apache-2.0 | General policy evaluation over structured input | **Extension point, not the initial assessment engine.** OPA is valuable for organization policy gates, but claim/argument/evidence outcomes and traceability remain CodeStrata semantics. |
| Compliance Trestle | Apache-2.0 | OSCAL authoring, validation, transformation, and compliance-as-code workflows | **Interoperate for regulated profiles; do not embed now.** Full OSCAL is beyond the repository baseline. |
| Semgrep Community Edition | LGPL-2.1 | Broad multi-language custom static analysis | **External executable or SARIF import only pending legal review.** Do not vendor or fork into the commercial core. |
| Faraday | GPL-3.0 | Vulnerability normalization and multi-user management | **Do not embed or fork.** Its reciprocal license and server footprint do not fit this product slice. |
| MegaLinter | AGPL-3.0; bundled linters have their own licenses | Orchestrates a very broad, containerized linter catalog and produces multiple reports including SARIF | **Useful optional executor, not a CodeStrata component or fork.** Invoke a user-installed/containerized version or import SARIF. The AGPL and transitive tool inventory make redistribution a separate legal/product decision. |
| Trunk Check / Trunk Code Quality | Public plugin/config repositories are MIT; the complete product/CLI distribution terms are not established by those repos | Fast changed-file meta-linting, tool installation, hold-the-line behavior, editor/CI integration | **Do not make it a foundation.** Detect an existing Trunk configuration and import its artifacts where available. The current Trunk product is hosted/commercial and its public positioning has shifted toward merge queue and flaky tests, creating product and continuity risk. |
| pre-commit | MIT framework; every configured hook and downloaded environment has an independent license | Reproducible multi-language hook discovery, environment provisioning, and execution | **Adopt as an evidence source and optional executor, not as the evidence model.** Inspect `.pre-commit-config.yaml` by default. Execution requires explicit approval because hooks are arbitrary code, can modify files, and may download runtimes. Prefer hook-native JSON/SARIF artifacts; otherwise retain bounded logs as raw evidence. |
| Super-Linter | MIT orchestrator; bundled linters retain independent licenses | Curated containerized multi-language linting with parallel execution | **Preferred permissive meta-linter alternative for optional execution experiments.** Still keep it outside the core because of container weight and transitive licenses; normalize emitted artifacts rather than its internal model. |
| RepoWise | AGPL-3.0 or separate commercial license | Dependency graph, git intelligence, 49 deterministic health detectors, file scores, trends, and refactoring plans | **Optional process adapter now.** Invoke a separately installed CLI in JSON mode, preserve the native artifact, and normalize measurements separately from detector findings. Do not copy, import, vendor, or restate its calibrated score as CodeStrata truth. |

## Build-versus-adopt verdict

### CodeStrata must own

- Goal/question/audience-oriented evidence plans.
- Collector manifests, preview, permissions, cost, and blind-spot disclosure.
- The normalized evidence envelope and explicit coverage/absence semantics.
- Claim/argument/evidence assessment profiles and conservative outcomes.
- Evidence-to-claim-to-finding-to-action traceability.
- Audience-oriented decision reports and the local workflow shell.

These are the differentiating trust and usability contracts. Outsourcing them
would make CodeStrata a thin scanner dashboard and recreate arbitrary scoring.

### CodeStrata should adopt or adapt

- Its existing typed collectors for built-in repository facts.
- RJSF/AJV for the advanced plan form.
- SARIF first as the universal static-analysis import seam.
- CycloneDX and SPDX for supply-chain evidence rather than proprietary SBOM
  structures.
- Optional local CLI adapters for Trivy, Syft, OSV-Scanner, Gitleaks, and
  OpenSSF Scorecard.
- Existing repository orchestration through pre-commit/Trunk configuration,
  with MegaLinter or Super-Linter available as explicit container adapters.
- DefectDojo compatibility rather than its application architecture.
- OPA as an optional policy evaluator behind the assessment-profile interface.

### CodeStrata should not own

- Vulnerability databases.
- General-purpose SAST engines or language rule ecosystems.
- Secret signatures.
- Package discovery across every ecosystem.
- A proprietary scanner result format for evidence already representable in
  SARIF, CycloneDX, SPDX, or OSCAL.
- A hosted workflow system in this local-first epic.

## Minimum/high-impact release cut

The highest-impact first release is smaller than the original mechanism list:

1. Wrap the existing CodeStrata inventory/dependency/testing collectors.
2. Add a declarative file/pattern observation for user-specific questions.
3. Add SARIF import so many existing tools become evidence sources immediately.
4. Define the generic collector manifest so optional executable adapters can be
   added without changing assessment or reporting.
5. Ship the plan schema, plan preview, evidence ledger, conservative baseline
   profile, traceable HTML/JSON report, and local studio.
6. Demonstrate one discovered optional external adapter (Trivy) without making
   it a required dependency or executing it without explicit confirmation.

CycloneDX import, broader pinned Trivy evidence packs, OPA profiles, OSCAL
export, and a large parser catalog are follow-on components. Their extension
seams belong in this release; their full functionality does not.

## Commercialization guardrails

- Prefer MIT, BSD, and Apache-2.0 components for embedded/runtime dependencies.
- Maintain `THIRD_PARTY_NOTICES`, license texts, package versions, source links,
  and whether code or data is redistributed.
- Treat data/rule licenses independently from engine licenses.
- Keep LGPL/GPL and source-available tools behind a separately installed
  executable or artifact-import boundary until counsel approves distribution.
- Never use a project name or logo in a way that implies endorsement.
- Make network access, credentials, source sent, and local caches visible in
  plan preview per activity.
- Pin tested tool and artifact schema versions; preserve raw outputs so mappings
  can be replayed after an adapter upgrade.

## Primary sources

- RJSF repository and Apache-2.0 declaration: https://github.com/rjsf-team/react-jsonschema-form
- JSON Forms alternative and MIT declaration: https://github.com/eclipsesource/jsonforms
- AJV repository and MIT declaration: https://github.com/ajv-validator/ajv
- Trivy repository and Apache-2.0 declaration: https://github.com/aquasecurity/trivy
- Syft repository and Apache-2.0 declaration: https://github.com/anchore/syft
- OSV-Scanner repository and Apache-2.0 license: https://github.com/google/osv-scanner
- Gitleaks repository, SARIF support, and MIT license: https://github.com/gitleaks/gitleaks
- OpenSSF Scorecard repository and Apache-2.0 declaration: https://github.com/ossf/scorecard
- ScanCode Toolkit licensing disclosure: https://github.com/aboutcode-org/scancode-toolkit
- DefectDojo repository and BSD-3-Clause declaration: https://github.com/DefectDojo/django-DefectDojo
- Microsoft SARIF SDK and MIT license: https://github.com/microsoft/sarif-sdk
- SARIF Tools package metadata and MIT declaration: https://pypi.org/project/sarif-tools/
- CycloneDX Python Library: https://github.com/CycloneDX/cyclonedx-python-lib
- OPA repository and Apache-2.0 declaration: https://github.com/open-policy-agent/opa
- Compliance Trestle repository and Apache-2.0 declaration: https://github.com/oscal-compass/compliance-trestle
- Semgrep repository and LGPL-2.1 declaration: https://github.com/semgrep/semgrep
- Faraday repository and GPL-3.0 declaration: https://github.com/infobyte/faraday
- MegaLinter repository and AGPL-3.0 declaration: https://github.com/oxsecurity/megalinter
- pre-commit repository and MIT declaration: https://github.com/pre-commit/pre-commit
- Trunk public plugin catalog and MIT declaration: https://github.com/trunk-io/plugins
- Trunk current product positioning: https://github.com/trunk-io
- Super-Linter repository and MIT declaration: https://github.com/super-linter/super-linter
- RepoWise repository, AGPL-3.0 declaration, JSON health CLI, detector scope,
  and published limitations: https://github.com/repowise-dev/repowise
- MegaLinter language/flavor/reporter catalog: https://megalinter.io/latest/
- Semgrep Community Edition structured JSON/SARIF output:
  https://semgrep.dev/products/community-edition/
- OpenSSF Scorecard structured results, heuristics, remediation, and explicit
  one-size-fits-all non-goal: https://github.com/ossf/scorecard
- SonarQube quality-gate conditions:
  https://docs.sonarsource.com/sonarqube/latest/user-guide/quality-gates
