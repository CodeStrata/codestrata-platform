# Phase 4.4 — Dependency Intelligence

## Status

| Sub-milestone | Status |
| ------------- | ------ |
| 4.4.1 Dependency Domain Foundation | Implemented |
| 4.4.2 Dependency Evidence Platform | Implemented |
| 4.4.3 Dependency Rules & Findings | Implemented |
| 4.4.3A Unresolved-version precision | Implemented |
| 4.4.4 Dependency Inventory / Assessment Usability | Implemented |
| 4.4.5 Assessment Synthesis | Implemented |
| 4.4.6 CTO Report Integration | Not started |

## Goals

Provide deterministic, evidence-backed dependency analysis that:

- reuses the Shared Rule Platform and shared `Finding` model
- keeps Architecture and Technical Debt Intelligence behavior unchanged
- separates package-manager facts (Dependency Evidence) from engineering
  interpretation (Dependency Intelligence)
- never invents CVE matches, license verdicts, version-freshness scores,
  upgrade candidates, financial cost, or remediation priority in foundation
  phases
- remains disabled by default until explicitly enabled

## Evidence ownership

| Concern | Owner |
| ------- | ----- |
| Manifest / lockfile discovery and parsing | **Dependency Evidence** (4.4.2) |
| Normalized dependency facts (coords, versions, scopes) | **Dependency Evidence** (4.4.2) |
| Engineering-role taxonomy and assessment interpretation | **Dependency Intelligence** |
| Vulnerability / advisory interpretation | **Security Intelligence** (future; may consume the same evidence) |
| License policy interpretation | Future capability (not Dependency Intelligence foundation) |

Phase 4.4.2 implements Dependency Evidence for Maven/Gradle/Python manifests.
No npm support, registry calls, CVEs, or licenses.

## Design decisions (4.4.1)

### 1. Shared Finding model — reuse with category mapping

**Decision:** Continue using the shared Phase 3 `Finding` model for future
dependency findings. Do not create a dependency-specific finding type.

**Changes:**

- Confirm `FindingCategory.DEPENDENCY = "dependency"` (already present)
- Add `RuleCategory.DEPENDENCY = "dependency"`
- Map `RuleCategory.DEPENDENCY` → `FindingCategory.DEPENDENCY`

Dependency-specific meaning will live in:

- `rule_id` namespace `dependency.*`
- taxonomy metadata (`dependency.*` roles)
- assessment-section projection (`DependencyFindingReference`)

### 2. No universal IntelligencePack abstraction

**Decision:** Do not introduce a generic pack plugin framework in 4.4.1.

Mirror Architecture / Technical Debt packages under `domain/dependency/` and
`application/dependency/` until a second independent pack proves duplication
pain.

### 3. Assessment section reserved early; empty by design

**Decision:** Introduce `assessment.dependency` section contracts now so later
evidence and rule packs have a stable artifact/schema target.

Phase 4.4.1 produces only:

- `disabled` sections (feature gate off)
- `not_requested` constructors (section not requested)
- `succeeded` empty sections (gate on, no rules registered yet)
- `insufficient_evidence` constructors (evidence unavailable)

No production rules, conclusions, recommendations, scoring, inventories, or
report narrative.

### 4. Taxonomy is engineering roles, not package-manager scopes

**Decision:** `DependencyRole` enumerates technology-neutral engineering roles
(`dependency.runtime_framework`, `dependency.test_library`, …) including
`dependency.unknown`.

Maven scopes, npm `devDependencies`, Python extras, and similar terms belong to
Dependency Evidence normalization — not this taxonomy.

### 5. Forbidden speculative fields

The assessment model **must not** include (until owning phases exist):

- frameworks / dependency inventories / versions
- themes / conclusions / recommendations
- upgrade candidates / vulnerabilities / licenses / CVEs
- financial cost / effort / priority scores

Limitations explicitly document these absences.

### 6. Feature gates (all default false)

Follow repository conventions (not a separate `assessment.packs.*` tree):

```toml
[rules.dependency]
enabled = false

[assessment.sections.dependency]
enabled = false
```

Pack enablement requires `rules.enabled` and `rules.dependency.enabled`.
Section enablement is independent and controls whether
`dependency-assessment.json` is written.

## Package layout (4.4.1)

```
src/codestrata/domain/dependency/
  ids.py
  taxonomy.py
  assessment/
    enums.py
    identifiers.py
    models.py

src/codestrata/application/dependency/assessment/
  assembler.py
  factory.py
  artifacts.py
```

## Compatibility

- Architecture and Technical Debt packages and defaults remain unchanged
- Report schema unchanged (no dependency report key)
- Existing findings continue to deserialize; `FindingCategory.DEPENDENCY` was
  already present
- Additive settings only

## Intentionally not implemented in 4.4.1

- Manifest / lockfile parsing of any ecosystem
- Dependency Evidence models or collectors
- Package normalization / version comparison / ranges
- Dependency SharedRules or findings
- Themes, conclusions, recommendations, scores
- CVE / license / registry / network data
- CTO JSON/HTML report integration
- CLI/MCP dependency commands
- Generic IntelligencePack abstraction

## Next milestones (preview)

1. Security Intelligence may later consume the same Dependency Evidence
2. npm evidence collection and transitive resolution remain deferred

## Design decisions (4.4.6) — Report integration

- Presentation-only adapter: `DependencyAssessmentSection` →
  `DependencyReportSection`
- Gate: `report.sections.dependency.enabled` (default false; independent)
- Customer JSON: additive `assessment.dependency` under schema **1.2** (no bump)
- HTML stable anchor: `dependency-assessment` (after Technical Debt)
- Production hygiene vs test/fixture observations remain separated
- Hotspot order is presentation order, not priority
- No re-analysis, registries, scores, CVE/license, or AI narrative

## Design decisions (4.4.5) — Synthesis

- Schema bump `1.1.0` → `1.2.0` (additive themes/conclusions/recommendations)
- Inventory-only synthesizer; no reparse / recollect / rule re-evaluation
- Production-primary health conclusions; test/fixture remain observations
- Unsupported Gradle resolution stays coverage, not findings
- No scores, priorities, CVE/license, upgrade-target, or AI narrative
- Gate: `assessment.sections.dependency.include_synthesis` (default true when section enabled)

## Design decisions (4.4.4) — Inventory usability

- Schema bump `1.0.0` → `1.1.0` (additive inventories only)
- Production-primary finding view; complete `all_finding_*` inventory
- Manifest / hotspot inventories with presentation ordering (not priority)
- Assessment status reflects production usability; test/fixture failures stay `succeeded`
- No themes, conclusions, recommendations, scores, or report adapters

## Design decisions (4.4.2) — Dependency Evidence

### 1. Evidence owns parsing

Collectors live under `domain/evidence/dependency/` and
`application/evidence/dependency/`. Dependency Intelligence assessment may
receive only fingerprints / pipeline labels — never reparses manifests.

### 2. Declared ≠ resolved

Evidence records repository-declared coordinates and raw version expressions.
Unresolved `${property}` values and dynamic Gradle DSL are diagnostics, not
guessed facts.

### 3. Gate

```toml
[evidence.dependency]
enabled = false
```

See [evidence.md](../analysis-intelligence/dependency/evidence.md).
