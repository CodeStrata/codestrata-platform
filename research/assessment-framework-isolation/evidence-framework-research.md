# Evidence Framework Research

Status: pre-requirements research synthesis  
Date: 2026-08-12  
Scope: local-first repository evidence planning, collection, normalization,
assessment, and reporting

## Research question

How should CodeStrata let a user decide what evidence to collect, collect it
through heterogeneous mechanisms, preserve it faithfully, assess it without
overclaiming, and turn it into standardized reports that guide action?

This research deliberately precedes requirements and implementation. It uses
primary standards, official tool documentation, research publications, and two
local codebases: CodeStrata 0.2.0 and Repowise.

## Executive conclusion

The isolated product must not begin with an assessment category or a scanner.
It must begin with a user goal and an explicit evidence plan.

The robust model is:

```text
intent -> questions -> evidence plan -> collection activities
       -> raw observations -> normalized evidence ledger
       -> claims and assessment arguments -> findings/risks/actions
       -> audience-specific reports
```

Five boundaries are required:

1. Evidence intent and planning.
2. Collection and import.
3. Evidence normalization, provenance, and storage.
4. Assessment reasoning.
5. Reporting and action presentation.

The plan and the result must be distinct, as must an observation, a finding,
a risk, a claim, and a recommendation. Absence of detected evidence must never
be silently converted into evidence of absence.

## What users may be trying to learn

Users do not naturally begin with "run the architecture head." They begin with
a decision, concern, or question. The following intent classes cover the most
common repository and adjacent evidence needs found in the reviewed standards
and tools.

### 1. Inventory and comprehension

- What languages, frameworks, build systems, deployable units, APIs, data
  stores, infrastructure definitions, and generated artifacts exist?
- What components depend on what?
- Where are architectural boundaries, entry points, and externally visible
  interfaces?
- Which parts of the repository were and were not examined?

Likely evidence includes manifests, lockfiles, AST facts, source locations,
dependency and call graphs, configuration documents, and component identity.

### 2. Change and modernization feasibility

- What blocks a framework, runtime, language, database, or cloud migration?
- Which APIs and libraries are incompatible with a target state?
- What is the blast radius and likely sequencing of a change?
- Which claims can be made from source alone, and what requires build or
  runtime validation?

Likely evidence includes version declarations, API usage, dependency paths,
build constraints, data access patterns, configuration, tests, ownership,
change history, and target-specific compatibility checks.

### 3. Maintainability and code health

- Where is change unusually difficult or risky?
- Which files or symbols combine complexity, churn, coupling, duplication,
  low coverage, or concentrated ownership?
- Are trends improving or deteriorating?

Repowise demonstrates one implementation through prebuilt biomarkers over AST,
git, graph, duplication, and coverage inputs. Its strengths are pure detector
contracts, path-level suppression, calibrated scoring, and actionable output.
Its limitation for CodeStrata's intended architecture is that collection,
interpretation, scoring, persistence, and dashboard semantics remain tightly
coupled in a single health layer.

### 4. Security and software supply chain

- Are known insecure constructs, dangerous workflows, secrets, or weak
  configurations present?
- What components are present, how were they identified, and are they
  reachable?
- Are builds, releases, and source revisions traceable and reproducible?
- Which secure-development practices have supporting evidence?

Likely evidence includes SARIF, SBOM/VEX, source patterns, data-flow paths,
workflow configuration, signatures, SLSA provenance, attestations, and hosting
metadata. OpenSSF Scorecard is especially instructive because it documents
detection limitations and inconclusive results rather than treating every
miss as a negative fact.

### 5. Testing and verification

- What tests exist, what behavior do they exercise, and what is their result?
- What source or requirement coverage is demonstrated?
- What testing claims cannot be made because results were not imported or
  execution was not performed?
- Does a modernization preserve a defined set of behaviors?

Likely evidence includes test source, framework/configuration facts, JUnit-like
results, line/branch coverage, mutation or fuzzing results, golden outputs,
build logs, and explicit human attestations.

### 6. Delivery and operational performance

- How quickly and safely does software move from change to production?
- What fails in production and how quickly is it restored?
- Where are runtime latency, errors, saturation, or resource bottlenecks?
- Which runtime observations correlate with repository entities?

Repository inspection alone cannot answer these questions. DORA's current
model uses multiple throughput and instability measures and warns against a
single metric or context-free comparison. OpenTelemetry distinguishes traces,
metrics, logs, and profiles and supplies correlation context. These should be
importable evidence families, not simulated from source heuristics.

### 7. Process, ownership, and developer experience

- Is knowledge dangerously concentrated?
- Where do review, build, test, or delivery bottlenecks occur?
- What is the relationship between repository structure and team behavior?
- What makes development difficult according to developers themselves?

Likely evidence includes git history, code review and CI events, ownership,
issue/workflow data, surveys, and interviews. SPACE demonstrates that developer
productivity is multidimensional and cannot be represented by one activity
metric. Human declarations must remain distinguishable from tool observations.

### 8. Governance, compliance, and assurance

- Which policies, controls, or requirements apply?
- What was planned, what was actually assessed, and by which method?
- What evidence supports or contradicts each claim?
- What exceptions, suppressions, risks, and remediation commitments exist?

OSCAL provides the strongest architectural precedent: catalogs define controls,
profiles select and tailor them, assessment plans define scope and activities,
assessment results record observations/findings/risks, and POA&M records action.
NIST recognizes EXAMINE, INTERVIEW, and TEST as distinct assessment methods.
CodeStrata should generalize this separation beyond compliance use cases.

## How users may define evidence gathering

No single authoring mechanism is sufficient. The product needs a tiered model.

### Level 1: Goal-first guided setup

The local UI asks what decision the user is preparing to make, identifies the
subject and constraints, and recommends an evidence profile. It should expose
plain-language questions before tool names.

Examples:

- "Can this application move from Java 8 to Java 21?"
- "Where should we reduce change risk first?"
- "What evidence supports release readiness?"
- "What do we know, and not know, about runtime scalability?"

This follows Goal-Question-Metric reasoning: measurement is selected in service
of a defined goal rather than collected indiscriminately.

### Level 2: Composable evidence packs

Users choose versioned packs such as repository inventory, dependencies,
architecture, code health, testing, supply chain, delivery, or runtime. A pack
is a composition of collectors with declared inputs, outputs, cost, data access,
limitations, and compatible assessment profiles.

CodeQL query suites and OpenRewrite declarative recipes demonstrate reusable
selection, composition, inclusion/exclusion, metadata, preconditions, and
configuration. CodeStrata should adopt these ideas without adopting their
domain-specific languages as its universal contract.

### Level 3: Declarative collector configuration

Advanced users can configure collectors through versioned YAML generated and
round-tripped by the UI. Useful declarative collector types include:

- File/path and manifest inspection.
- Structured document queries.
- Source pattern and AST queries.
- Repository graph queries.
- External artifact imports.
- Command adapters with explicit sandbox and output contracts.
- Manual declarations or attestations.

Semgrep demonstrates approachable pattern rules with stable IDs, languages,
paths, messages, severity, metadata, positive/negative patterns, and tests.
OPA/Rego demonstrates policies over schema-validated structured input. These
should inform separate collector-query and assessment-policy contracts.

### Level 4: Collector SDK

Some observations require code. A collector plugin must declare:

- Stable ID, version, publisher, and implementation digest.
- Supported subjects, languages, and evidence types.
- Required inputs and permissions.
- Whether it reads source, git history, network, build output, or runtime data.
- Determinism and expected side effects.
- Cost/time bounds and cancellation behavior.
- Output schema and normalization adapter.
- Coverage semantics and known limitations.
- Test fixtures and compatibility range.

The plugin returns observations and diagnostics. It must not assign assessment
conclusions unless it is explicitly an assessment-policy plugin.

### Level 5: Imports and attestations

Users must be able to import existing artifacts without lossy conversion:

- SARIF static-analysis results.
- CycloneDX or SPDX component data.
- SLSA/in-toto provenance.
- Test and coverage results.
- OpenTelemetry metrics, logs, traces, and profiles.
- OSCAL controls, profiles, plans, and results where applicable.
- Human declarations, interviews, reviewed documents, and signed attestations.

Imported artifacts remain raw source entities and also produce normalized
observations linked back to the source artifact.

## Evidence forms the model must preserve

An evidence record is an envelope around a typed payload, not one universal
flat dictionary. The following payload forms are required.

1. Presence or identity fact: a component, framework, file, API, or control.
2. Located occurrence: path, region, symbol, manifest key, or configuration
   pointer.
3. Relationship: dependency, call, ownership, co-change, data flow, or
   derivation edge.
4. Measurement: scalar, unit, method, population, aggregation, and bounds.
5. Distribution or series: histogram, trend, time series, or sampled profile.
6. Event or execution trace: build, test, deployment, incident, or runtime
   sequence.
7. Artifact: report, SBOM, log, image, binary, document, or generated output.
8. Test result: subject, expected behavior, actual behavior, environment, and
   outcome.
9. Attestation or declaration: issuer, subject, statement, signature or review
   state, and validity period.
10. Derived observation: transformation and parent evidence IDs.
11. Absence claim: only valid when a collector declares a searched population,
    method, successful coverage, and detection capability.
12. Unknown, not-applicable, not-requested, unsupported, failed, or redacted
    state: these states are evidence about coverage and must not collapse into
    an empty list.

Every normalized envelope needs:

- Stable evidence ID and schema version.
- Run, plan, collector, and activity IDs.
- Subject and subject revision.
- Evidence type and payload schema.
- Origin method: inspect/examine, execute/test, interview/declaration, import,
  or derivation.
- Producer identity and implementation version/digest.
- Collection time and environment.
- Locations and source artifact references.
- Parent evidence and derivation chain.
- Scope, population, coverage, and completeness.
- Confidence/quality basis and limitations.
- Sensitivity, redaction, and retention classification.
- Payload and content digest.

W3C PROV's Entity/Activity/Agent and derivation relationships are the conceptual
foundation. CycloneDX adds useful technique, occurrence, call-stack, and
per-method confidence patterns. SLSA demonstrates verifiable where/when/how
provenance for produced artifacts.

## Default local storage

The default should be inspectable, portable, queryable, append-friendly, and
recoverable without a hosted service.

```text
.codestrata-artifacts/evidence/<repository-id>/<run-id>/
  plan.yaml                    # exact user intent and requested activities
  run.json                     # run manifest, versions, timings, status
  evidence.jsonl               # canonical normalized evidence envelopes
  coverage.json                # planned vs actual collection matrix
  assessment.json              # claims, arguments, findings, risks, actions
  report.html                  # self-contained local report/UI projection
  report.sarif                 # location-based findings when representable
  raw/
    <sha256>.<extension>       # immutable imported/generated source artifacts
  schemas/
    ...                        # schema IDs or bundled schemas needed to read run
```

An optional local SQLite index should power the UI across runs. It is a
rebuildable index, not the sole source of truth. Canonical JSON/JSONL and raw
artifacts remain portable. Large binary or third-party payloads are stored by
digest and referenced from evidence records.

This differs intentionally from Repowise's SQLite-only health store. CodeStrata
needs durable exchange artifacts, provenance chains, and reproducible reports,
while still benefiting from SQLite query speed.

## Assessment reasoning model

An assessment profile is not a folder of rules. It is a versioned argument
contract containing:

- Goal, audience, and decision supported.
- Questions and claims that may be evaluated.
- Applicable subjects and preconditions.
- Evidence requirements and accepted evidence types.
- Minimum coverage and freshness requirements.
- Rules for contradictions, missing data, and multiple sources.
- Reasoning or decision policies.
- Confidence derivation and explicit defeaters.
- Finding, risk, and action mappings.
- Claim limitations and forbidden inferences.
- Reference framework and source attribution.
- Validation fixtures and change history.

Goal-Question-Metric provides the top-down selection logic. ISO/IEC 25010
provides a reference quality model but must not imply that repository evidence
can evaluate every product quality. ISO/IEC/IEEE 15026 assurance cases provide
the claim-argument-evidence structure. OSCAL provides catalog/profile/plan/result
separation. OWASP SAMM demonstrates questions with explicit quality criteria
and improvement roadmaps.

Scores are optional projections, not the primary result. A high-quality result
must be able to say:

- Supported.
- Partially supported.
- Contradicted.
- Insufficient evidence.
- Not assessed.
- Not applicable.

## Default reporting

Reporting consumes the canonical assessment result; it does not rerun rules or
invent new conclusions.

The default HTML report should contain:

1. Decision brief: what the assessment can and cannot support.
2. Scope and evidence plan: requested versus actually performed.
3. Coverage and limitations: unknowns, failures, exclusions, and stale inputs.
4. Claims and confidence: the argument and supporting/contradicting evidence.
5. Findings: stable identity, impact, evidence, status, and suppression state.
6. Prioritized actions: why, expected outcome, prerequisites, verification step,
   and supporting findings.
7. Evidence explorer: filters by type, source, location, collector, and claim.
8. Traceability: action -> finding/risk -> claim -> evidence -> raw source.
9. Change from previous run: new, existing, resolved, and changed coverage.
10. Machine-readable exports and source/framework attribution.

SARIF is the default interoperability output for source-located static findings,
including stable fingerprints and suppressions. It is not a universal evidence
store. CycloneDX/SPDX, SLSA, OpenTelemetry, and OSCAL inputs should remain in
their native formats with normalized links rather than being forced into SARIF.

## Local-first UX requirements discovered by research

The UI should be an evidence studio, not a skin over CLI flags.

### Journey

1. Choose or describe the decision.
2. Select the repository/revision and assessment profile.
3. Review recommended evidence packs.
4. Inspect data access, estimated cost, coverage, and limitations.
5. Customize collectors, scope, imports, and exclusions.
6. Validate and preview the exact plan before execution.
7. Run while observing collector-level status and diagnostics.
8. Inspect raw and normalized evidence before assessment.
9. Review claims, findings, uncertainty, and actions.
10. Compose/export an audience-specific report.

### Interaction principles

- Simple defaults first; advanced controls remain available through progressive
  disclosure.
- Every UI choice round-trips to a versioned YAML plan.
- Changing a profile shows the resulting collector and claim changes before
  applying them.
- Validation errors identify the exact field and suggest a correction.
- Execution status is available visually and through accessible status roles.
- The UI never equates zero findings with a clean assessment when coverage is
  incomplete.
- Users can inspect why a collector was recommended, skipped, failed, or marked
  inapplicable.
- The review screen makes collection permissions and external data access
  explicit before execution.
- UI and CLI/API consume the same application contracts.

GOV.UK's task and check-answers patterns support explicit review before a
multi-step action. WCAG 2.2 requires labeled inputs, predictable context changes,
error identification/suggestions, keyboard access, and programmatically exposed
status messages.

## Findings from the local systems

### Repowise

Useful patterns:

- Pure biomarker detector protocol over a prepared context.
- Prebuilt and named profiles.
- Repo and path-level enable/disable and severity overrides.
- Clear separation of missing coverage from low coverage in some biomarkers.
- Deterministic suggestions, trend views, and local dashboard.

Limitations for this epic:

- The user mostly tunes preselected biomarkers rather than defining evidence
  intent.
- Detector outputs are already health findings, not neutral observations.
- The health context is a fixed aggregate of AST, graph, git, coverage, and
  duplication inputs.
- SQLite is the sole health source of truth.
- Scoring categories and caps are product decisions inside the collection layer.

### CodeStrata 0.2.0

Useful patterns:

- Domain-specific evidence models with stable IDs and source locations.
- Existing provenance, evidence confidence, coverage, finding confidence,
  consolidation, correlation, recommendation, and traceability contracts.
- Explicit partial/not-claimed coverage areas.
- Local deterministic assessment and self-contained HTML/JSON artifacts.

Isolation problems:

- Evidence contracts are fragmented by domain and do not share one envelope.
- There is no user-authored evidence plan or generic collector manifest.
- Assessment areas are declared in code rather than selected through a
  research-grounded profile.
- The 5,000-line assessment service coordinates scanning, evidence collection,
  rules, heads, AI, reporting, persistence, publishing, platform integration,
  and benchmarking.
- Reporting adapters depend on domain-specific assessment products rather than
  one canonical claims/results contract.

The implementation should wrap and adapt proven 0.2.0 collectors first. It
should not discard them or attempt a big-bang rewrite.

## Architecture decisions supported by the research

1. Evidence plan is a first-class, versioned artifact.
2. Collector and assessment-policy plugins are different extension types.
3. Observations are collected before findings exist.
4. Raw imported/generated artifacts are immutable and content-addressed.
5. A generic evidence envelope wraps typed payloads.
6. Coverage is modeled per planned activity and population.
7. Assessment uses explicit claim-argument-evidence contracts.
8. Reporters are projections of a canonical result.
9. Native interoperability formats are preserved.
10. Local HTML/UI plus YAML/JSON artifacts are the default experience.
11. Existing 0.2.0 collectors are adapted behind manifests before replacement.
12. Enterprise services consume the same artifacts but do not define the local
    framework.

## Non-goals for the first isolated vertical slice

- Exhaustively implementing every evidence family.
- Claiming runtime, operational, or organizational facts from source alone.
- Creating a universal rule language in the first iteration.
- Replacing mature tools such as CodeQL, Semgrep, OTel, or SBOM generators.
- A hosted multi-user control plane.
- Portfolio aggregation, identity, scheduling, or policy distribution.
- Automatically publishing repository evidence.

## Source register

| Source | Contribution |
| --- | --- |
| https://www.cs.umd.edu/~basili/publications/technical/T89.pdf | Goal-Question-Metric: select measurement from goals and questions. |
| https://www.iso.org/standard/78176.html | ISO/IEC 25010:2023 product-quality reference model and measurement use. |
| https://www.iso.org/standard/73567.html | Claims supported through argumentation and evidence. |
| https://www.iso.org/standard/80625.html | Assurance-case structure terminology. |
| https://www.w3.org/TR/prov-o/ | Entity/activity/agent provenance and derivation. |
| https://pages.nist.gov/OSCAL/learn/concepts/layer/ | Catalog, profile, implementation, assessment-plan/results, and POA&M separation. |
| https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/assessment-plan/ | Planned scope, subjects, activities, methods, tools, and rules of engagement. |
| https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/assessment-results/ | Observations, findings, risks, tools, logs, and remediation in assessment results. |
| https://csrc.nist.gov/pubs/sp/800/53/a/r5/final | Tailorable assessment methods and procedures. |
| https://csrc.nist.gov/projects/ssdf | Outcome-based, risk-tailored practices and community profiles. |
| https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html | Static findings, locations, fingerprints, suppressions, code flows, and baselines. |
| https://cyclonedx.org/guides/sbom/evidence | Component evidence techniques, occurrences, confidence, reachability, and native artifacts. |
| https://slsa.dev/spec/v1.2/provenance | Verifiable where/when/how artifact provenance. |
| https://opentelemetry.io/docs/concepts/signals/ | Runtime traces, metrics, logs, and profiles as separate correlated signals. |
| https://semgrep.dev/docs/writing-rules/rule-syntax | Approachable declarative source-pattern rule authoring. |
| https://docs.github.com/en/code-security/tutorials/customize-code-scanning/create-query-suites | Reusable query selection, inclusion/exclusion, precision, and packs. |
| https://docs.openrewrite.org/reference/yaml-format-reference | Declarative composition, preconditions, metadata, and configuration. |
| https://www.openpolicyagent.org/docs/policy-language | Declarative policy over schema-validated structured data. |
| https://owaspsamm.org/assessment/ | Questions, quality criteria, maturity assessment, and improvement roadmap. |
| https://github.com/ossf/scorecard/blob/main/docs/checks.md | Check methods, scoring, remediation, limitations, and inconclusive evidence. |
| https://dora.dev/guides/dora-metrics/ | Multimetric, context-sensitive delivery performance and action loop. |
| https://www.microsoft.com/en-us/research/publication/the-space-of-developer-productivity-theres-more-to-it-than-you-think/ | Multidimensional developer productivity and mixed evidence. |
| https://docs.sonarsource.com/sonarqube-cloud/standards | Separation of rule selection (profile) and post-analysis threshold policy (gate). |
| https://design-system.service.gov.uk/patterns/check-answers/ | Explicit review before committing a multi-step configuration. |
| https://www.w3.org/TR/WCAG22/ | Accessible, predictable forms, error assistance, and status messages. |

