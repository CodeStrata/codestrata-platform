# Evidence Framework Isolation Product Requirements

Status: expanded epic implementation contract  
Date: 2026-08-13  
Research authority: `evidence-framework-research.md` and
`open-source-component-strategy.md`

## Product outcome

A user can define what repository evidence they want, understand how CodeStrata
will obtain it, run the plan locally, inspect raw and normalized observations,
apply a versioned assessment profile, and receive a standardized report whose
claims and recommended actions are traceable to evidence and explicit coverage.

## Scope of this epic

Deliver a complete local-first evidence configuration and reporting product.
The isolation contracts remain the kernel, but success requires the user to
discover, select, configure, run, and compare real evidence capabilities—not
merely a small demonstration registry. Existing CodeStrata 0.2.0 collectors
must be reused without rewriting their extraction logic.

The epic includes:

- Versioned evidence-plan, collector-manifest, evidence-envelope, coverage,
  assessment-result, and report-view contracts.
- A collector registry and separate assessment-profile registry.
- Built-in generic collectors and at least one standard artifact importer.
- A local evidence store with portable artifacts and a rebuildable index.
- A local web studio for plan authoring, preview, execution, evidence review,
  and report review.
- A deterministic assessment engine using explicit claim requirements.
- Self-contained HTML, JSON, evidence JSONL, and SARIF outputs.
- Tests proving isolation, traceability, coverage semantics, determinism, and
  end-to-end UI/API behavior.

The epic excludes hosted accounts, multi-user collaboration, portfolios,
scheduling, remote policy distribution, and automatic publication.

## 2026-08-13 correction to the original implementation cut

The first implementation proved isolation but did not satisfy the product
outcome. Five hard-coded collector cards, an inert `packs` tuple, disconnected
language providers, and a single baseline assessment were insufficient.

This epic is complete only when:

- Evidence packs are versioned, resolvable compositions that add applicable
  activities to a plan.
- The Studio detects repository languages and recommends applicable packs.
- Python, Java, JavaScript/TypeScript, PHP, and C# language providers are
  selectable through the same catalog as other collectors.
- Users can select individual provider capabilities and code-health biomarkers.
- Structural measurements, threshold crossings, producer findings, assessment
  findings, and actions remain distinguishable in normalized evidence.
- RepoWise is integrated through a separately installed executable and JSON
  artifact boundary because its AGPL-3.0 engine cannot be copied into a future
  proprietary commercial core without a separate license.
- SARIF remains the broad interoperability seam for MegaLinter, Super-Linter,
  Semgrep, Trivy, CodeQL, pre-commit hooks, and other analyzers.
- Reports reproduce the selected packs, collectors, capabilities, biomarkers,
  thresholds, coverage, provenance, findings, risks, and prioritized actions.
- Representative Python, Java, and JavaScript/PHP repository runs prove the
  URL-to-report flow and compare the new output with unchanged CodeStrata 0.2.0.

The quality target is not the unprovable claim that CodeStrata detects every
issue found by every scanner. CodeStrata must match or exceed representative
meta-tools on configuration transparency, normalized interoperability,
coverage disclosure, provenance, traceability, and actionability. Specialist
detector recall remains attributable to the selected producer.

## Leverage constraint

Before CodeStrata implements a new collector, parser, policy runtime, form
renderer, or report interchange, it must pass a build-versus-adopt review:

- Search for maintained open-source components and standard formats.
- Compare product leverage, integration weight, replaceability, and evidence
  quality.
- Record the code license, data/rule licenses, notice obligations, commercial
  use posture, and trademark considerations.
- Prefer a standard artifact importer or optional executable adapter when the
  capability is not a CodeStrata differentiator.
- Build only the intent, trust, reasoning, traceability, and UX contracts that
  CodeStrata needs to control.

The initial component decisions are recorded in
`open-source-component-strategy.md`. They are architecture inputs, not a legal
opinion.

## Personas

### Explorer

Wants a high-quality default without learning scanner names or editing YAML.

### Practitioner

Wants to choose evidence packs, scope, imports, exclusions, and assessment
questions through the local UI.

### Evidence author

Wants versioned YAML, JSON Schema validation, custom declarative collectors,
and reproducible results.

### Collector author

Wants a narrow SDK that emits observations and diagnostics without depending
on assessment or reporting packages.

### Assessment author

Wants to define claims, accepted evidence, sufficiency, limitations, and actions
without implementing collection or rendering.

## Required product language

The product must use these terms consistently:

- Plan: requested goal, scope, collectors, imports, and profile.
- Activity: one planned collector or import execution.
- Observation: raw or normalized evidence; not yet a judgment.
- Evidence: an observation used to support or contradict a claim.
- Claim: a bounded statement evaluated by an assessment profile.
- Finding: an assessment result that requires attention.
- Risk: possible adverse consequence associated with findings and context.
- Action: a concrete response with verification guidance.
- Coverage: planned population and activities versus what was actually examined.
- Report: a projection of the canonical result for an audience.

## Functional requirements

### PR-01: Goal-first local studio

The user can start a local-only web studio from the CodeStrata CLI for a selected
repository. The first screen asks what decision or question the user is trying
to support and offers researched starter profiles.

Acceptance:

- The server binds to `127.0.0.1` by default.
- No network request, upload, telemetry permission, or platform credential is
  required when a local folder is selected.
- The first screen accepts a credential-free public GitHub HTTPS URL and an
  optional branch or tag, creates a bounded shallow local snapshot, and pins
  the plan to the resolved commit before evidence selection.
- GitHub acquisition is explicit and must not execute hooks, submodules, Git
  LFS downloads, or repository code. Private authentication and arbitrary Git
  hosts remain outside this initial boundary.
- A user can complete the full workflow without editing a file or typing a
  second CLI command.
- The generated plan can be downloaded or saved as YAML.

### PR-02: Versioned evidence plan

The plan schema must express:

- Schema version and stable plan ID.
- Goal, questions, audience, repository subject, and revision intent.
- Includes/excludes and sensitivity policy.
- Selected evidence packs and collector activities.
- Imports and manual attestations.
- Assessment profile and report views.
- Execution limits and external-access policy.

Acceptance:

- YAML and JSON representations validate to the same Pydantic contract.
- Unknown fields fail with a precise path and message.
- Plan serialization is deterministic.
- The UI can load a previously saved plan and round-trip it without semantic
  loss.

### PR-03: Collector manifests and registry

Every collector exposes a manifest independently of execution:

- Stable ID/version, label, description, and publisher.
- Input and permission requirements.
- Supported subjects and output evidence types.
- Estimated cost class and deterministic/side-effect declarations.
- Coverage semantics and known limitations.
- Configuration schema.

Acceptance:

- The studio can render the collector catalog without importing assessment or
  reporting modules.
- Invalid duplicate IDs or incompatible versions fail at registry construction.
- A dry-run preview reports applicable, inapplicable, unavailable, and blocked
  collectors before execution.

### PR-04: Built-in evidence mechanisms

The vertical slice must include:

1. Repository inventory collector: files, languages where determinable,
   manifests, and repository revision.
2. File/pattern collector: user-selected globs and bounded text/regex patterns
   with source locations.
3. Dependency-declaration collector adapter using proven CodeStrata 0.2.0
   behavior where feasible.
4. Test-structure collector adapter using proven CodeStrata 0.2.0 behavior where
   feasible.
5. SARIF 2.1 importer preserving the raw document while normalizing results,
   locations, rule IDs, levels, fingerprints, and suppressions.
6. Manual declaration/attestation input clearly marked as declared evidence.
7. A discoverable optional Trivy manifest demonstrating how third-party tools
   join the framework without becoming a required dependency or running before
   explicit confirmation.
8. Repository tool-orchestration inventory for `.pre-commit-config.yaml`,
   `.trunk/trunk.yaml`, and MegaLinter configuration. Detection is safe by
   default; executing arbitrary hooks or containers requires a separately
   confirmed activity.

Acceptance:

- A user can enable, disable, configure, and scope each mechanism in the UI.
- Collector failure does not erase successful evidence from other collectors.
- Empty successful output, unsupported input, and execution failure produce
  different coverage states.
- Source text secrets are not copied into evidence by default.

### PR-05: Normalized evidence envelope

All mechanisms emit a common envelope around a typed payload.

Required fields:

- Evidence ID/schema version/kind.
- Run, activity, collector, and subject identities.
- Method and production mode.
- Producer version and collection time.
- Locations and raw-source references.
- Parent evidence and derivation metadata.
- Coverage/completeness and limitations.
- Confidence basis when asserted.
- Sensitivity/redaction metadata.
- Typed payload and digest.

Acceptance:

- IDs are stable for logically identical evidence at the same repository
  revision and collector version.
- Payload digest changes when material evidence changes.
- Derived evidence cannot reference missing parents.
- A negative/absence observation is rejected unless the record includes the
  searched population and successful coverage basis.

### PR-06: Portable local evidence store

Each run writes:

- `plan.yaml`
- `run.json`
- `evidence.jsonl`
- `coverage.json`
- `assessment.json`
- `report.html`
- `report.sarif` when location findings exist
- content-addressed raw artifacts

Acceptance:

- Output is written to a staging directory and promoted only after mandatory
  contracts validate.
- Raw artifacts are immutable and addressed by SHA-256.
- A partial run remains inspectable and declares its partial status.
- No hosted database is required.

### PR-07: Research-grounded assessment profiles

An assessment profile must declare goals, questions, claims, applicability,
accepted evidence, sufficiency, coverage floors, contradiction handling,
limitations, and action templates.

The first profile must be a conservative repository evidence baseline, not a
universal quality score. It may evaluate whether requested inventory,
dependency, source-pattern, testing, and imported-analysis evidence is present
and sufficiently covered. It must not infer runtime performance, test passage,
exploitability, compliance, or modernization effort from repository presence
alone.

Acceptance:

- Profile logic depends only on normalized evidence and coverage contracts.
- Claim outcomes include supported, partially supported, contradicted,
  insufficient evidence, not assessed, and not applicable.
- Every supported/contradicted claim references evidence IDs.
- Every insufficient result references missing requirements or coverage.
- Actions reference claims/findings and include an explicit verification step.

### PR-08: Canonical assessment result

The assessment result contains:

- Plan/run/profile identity.
- Scope and actual activities.
- Claim arguments and outcomes.
- Findings, risks, and actions.
- Coverage and limitations.
- Evidence references and traceability edges.
- Change baseline fields for later comparison.

Acceptance:

- Report rendering requires no collector implementations.
- Re-running reporters cannot change claim results.
- All traceability references validate.

### PR-09: Standardized reports

Default outputs are:

- Self-contained accessible HTML.
- Canonical JSON assessment.
- Normalized JSONL evidence ledger.
- SARIF 2.1 for representable source-located findings.

The HTML report includes decision brief, plan/scope, coverage, claims,
limitations, findings, actions, evidence explorer, and traceability.

Acceptance:

- Zero findings with incomplete coverage is visibly labeled inconclusive, not
  clean.
- Each action links to its finding/claim and underlying evidence.
- Each evidence row exposes producer, method, location, limitations, and raw
  reference.
- HTML works when opened directly from disk without a server.
- SARIF validates against the supported SARIF 2.1 shape and uses stable rule and
  result identities.

### PR-10: Observable, interruptible execution

The studio shows activity-level queued, running, completed, skipped, blocked,
failed, and cancelled states.

Acceptance:

- Status updates are available through a stable application event contract.
- Cancelling stops new activities and preserves completed evidence.
- Errors include the activity, cause, impact on coverage, and suggested next
  step.
- UI status messages are programmatically exposed for assistive technology.

## UX requirements

### UX-01: Progressive control

Defaults are goal-first and recommended. Advanced users can reveal packs,
collectors, scope, imports, claims, and output settings without switching tools.

### UX-02: Plan preview

Before running, the user sees:

- What will be read or executed.
- What leaves the machine (default: nothing).
- Estimated activity cost.
- Expected evidence and assessment questions.
- Known blind spots.

### UX-03: Review before execution

The user confirms a human-readable summary of the plan. The action is explicit;
changing a control does not automatically begin collection.

### UX-04: Evidence-first inspection

The user can inspect observations and coverage before viewing assessment claims.
Raw, normalized, and derived evidence are visually distinguished.

### UX-05: No false certainty

Unknown, unsupported, failed, excluded, redacted, not requested, and not
applicable are presented as distinct states using text and icons, not color
alone.

### UX-06: Action guidance

Actions state what to do, why it matters, what evidence motivated it, expected
outcome, prerequisites, and how to verify completion.

### UX-07: Accessibility

The primary workflow targets WCAG 2.2 AA: keyboard operation, visible focus,
semantic labels, error identification and suggestions, predictable changes,
non-color status, and accessible live progress.

## Isolation requirements

### IR-01

`evidence_framework.domain` imports neither CLI, reporting, AI, platform,
telemetry transport, nor persistence implementations.

### IR-02

Collectors depend on collector contracts and domain models, not assessment or
reporting packages.

### IR-03

Assessment profiles depend on normalized evidence and coverage, not scanner or
filesystem implementations.

### IR-04

Reporters depend on the canonical assessment result, not collectors or rules.

### IR-05

The local web interface calls application services used by CLI/API tests; it
must not duplicate assessment behavior in JavaScript.

### IR-06

Existing 0.2.0 behavior is reached through adapters. The epic does not change
legacy assessment output unless an explicit compatibility adapter is invoked.

## Quality requirements

### QR-01: Determinism

Given the same plan, repository revision, collector versions, imports, and
environment-relevant inputs, the ordered evidence identities and assessment
result are stable apart from declared timestamps/run IDs.

### QR-02: Bounded execution

Collectors declare and honor file-size, result-count, and time bounds. Pattern
collection rejects unsafe or unbounded configurations.

### QR-03: Security and privacy

- Bind locally by default.
- Deny outbound network by default.
- Never execute arbitrary plan commands in the first slice.
- Redact source snippets by default for sensitive evidence.
- Prevent path traversal in repository and artifact handling.
- Escape all report and UI content.

### QR-04: Compatibility

The existing `codestrata assess` command and 0.2.0 report contract continue to
work unchanged.

### QR-05: Testability

Tests cover model validation, stable IDs, collector registry, plan preview,
coverage state transitions, SARIF import/export, assessment outcomes,
traceability, storage promotion, HTTP API, UI static assets, and a complete
fixture-repository run.

## Epic acceptance scenario

Using only the local studio, a user:

1. Selects a fixture repository.
2. Chooses "Understand modernization evidence" and accepts the recommended
   baseline profile.
3. Adds a custom source-pattern observation and a SARIF import.
4. Reviews the plan, permissions, expected evidence, and limitations.
5. Runs collection and observes each activity.
6. Opens the evidence explorer and verifies provenance and coverage.
7. Opens the assessment and sees supported, partial, and insufficient claims.
8. Opens an action and traces it back to a claim, finding, and source evidence.
9. Exports/saves the plan and opens the self-contained HTML report from disk.
10. Re-runs the saved plan and receives stable evidence identities.

The scenario passes only if the report is useful without AI and explicitly
states what cannot be concluded.

## Implementation sequence

1. Freeze schemas and dependency rules with tests.
2. Implement plan/catalog/preview contracts.
3. Implement normalized evidence and local artifact store.
4. Implement generic collectors and SARIF import.
5. Implement baseline assessment profile and canonical result.
6. Implement HTML/JSON/SARIF reporters.
7. Implement local HTTP application and evidence studio.
8. Add adapters to proven 0.2.0 dependency/testing collection where feasible.
9. Run the epic acceptance scenario and compatibility suite.
