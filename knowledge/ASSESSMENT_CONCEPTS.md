# Assessment Concepts

**Status:** Canonical (migrated Phase 8.9.3)  
**Authority:** Engineering Knowledge

## Purpose

Define cross-cutting assessment concepts shared by all Knowledge domains:
methodology, dimensions, evidence, confidence, coverage, and statement
classifications.

Domain-specific concepts live under each domain folder. Implementation
contracts (schemas, pack IDs, CLI flags) remain under `engine/docs/`.

## Intent

**CodeStrata Engine (Community)** helps developers and small teams understand a
repository, identify credible engineering risks, and act on local
recommendations.

**CodeStrata Platform (Commercial / Enterprise capabilities)** helps engineering
leaders understand portfolios, connect findings to business systems, prioritize
investment, and govern standards.

One methodology serves both. Repository-only assessment remains valid.
Enterprise / portfolio context remains optional enrichment.

Edition boundaries (normative product split):
[governance/constitution/006_COMMUNITY_PLATFORM_BOUNDARIES.md](../governance/constitution/006_COMMUNITY_PLATFORM_BOUNDARIES.md).

## Traceability chain

```text
Executive Question
    ↓
Assessment Dimension
    ↓
Assessment Principle / Control Area
    ↓
Rule (stable ID + version)
    ↓
Evidence (origin + strength + provenance)
    ↓
Finding (observed condition)
    ↓
Recommendation (potential action)
    ↓
Score (with coverage + confidence)
    ↓
Business Risk / Priority
    ↓
Modernization Initiative / Wave
    ↓
Executive / CTO Report Section
```

## Statement classifications

Every claim in a report or narrative must be one of:

| Label | Meaning |
| ----- | ------- |
| **observed** | Directly extracted from repository artifacts |
| **derived** | Deterministically calculated from observed evidence |
| **declared** | Provided by metadata/config; not independently verified |
| **inferred** | Reasonable conclusion with explicit uncertainty |
| **unavailable** | Needed evidence was not present |
| **not assessed** | Dimension or control was out of scope for this run |

Do not present inferred or declared facts as observed.

## Assessment outcomes for a control or area

| Outcome | Meaning |
| ------- | ------- |
| `strong` | Positive evidence of good practice |
| `adequate` | Meets expectations without notable risk |
| `needs_attention` | Material issues exist; remediation advised |
| `weak` | Significant deficiencies |
| `critical` | Severe conditions requiring urgent attention |
| `not_assessed` | Not in scope or unsupported |
| `insufficient_evidence` | In scope, but evidence too thin to score |

Absence of matched findings must **not** auto-promote an area to `strong`.

## Methodology principles

1. **Evidence before judgment.** No score or narrative without cited evidence or an explicit “not assessed / unavailable” label.
2. **Deterministic analysis before AI.** AI may interpret later; it must not invent findings or break traceability.
3. **Explainable scores.** Every score answers why, what evidence, what was not assessed, what would change it.
4. **Missing evidence is not failure.** Prefer `insufficient_evidence` / `not_assessed` over punitive zeros.
5. **No findings ≠ excellence.** Coverage and positive evidence are required to claim strength.
6. **Confidence and coverage accompany every score.**
7. **Technical severity and business impact are separate.**
8. **Repository vs enterprise provenance stays distinct.**
9. **Findings describe observed conditions;** recommendations describe actions.
10. **Priorities consider dependencies and (when available) business context.**
11. **Do not claim runtime, production, cost, or organizational facts that static analysis cannot prove.**
12. **No opaque weighted averages** without documented rationale.
13. **Severe findings must not be hidden** by averages.
14. **Executive summaries must not exaggerate certainty.**

Aligns with Governance:
[007_AI_PHILOSOPHY.md](../governance/constitution/007_AI_PHILOSOPHY.md),
[004_PRODUCT_PRINCIPLES.md](../governance/constitution/004_PRODUCT_PRINCIPLES.md).

## Assessment dimensions (catalog)

Stable identifiers use `dimension.<slug>`.

| ID | Title | Maps primarily to Knowledge domain |
| -- | ----- | ---------------------------------- |
| `dimension.architecture` | Architecture | [architecture/](architecture/) |
| `dimension.maintainability` | Maintainability | [technical-debt/](technical-debt/), [documentation/](documentation/) |
| `dimension.technical-debt` | Technical Debt | [technical-debt/](technical-debt/) |
| `dimension.security` | Security | [security/](security/) |
| `dimension.performance-scalability` | Performance and Scalability | [performance/](performance/) |
| `dimension.reliability-resilience` | Reliability and Resilience | [architecture/](architecture/), [cloud/](cloud/) |
| `dimension.testability-quality` | Testability and Quality Engineering | [documentation/](documentation/) (testing concepts) |
| `dimension.operability-observability` | Operability and Observability | [cloud/](cloud/), [documentation/](documentation/) |
| `dimension.cloud-platform-readiness` | Cloud and Platform Readiness | [cloud/](cloud/) |
| `dimension.data-integration` | Data and Integration Architecture | [architecture/](architecture/) |
| `dimension.developer-experience` | Developer Experience | [documentation/](documentation/) |
| `dimension.modernization-readiness` | Modernization Readiness | [modernization/](modernization/) |
| `dimension.ai-enablement` | AI Enablement Readiness | [ai/](ai/) |

<!-- TODO: Expand per-dimension executive/engineering questions in domain docs. -->

Detailed historical write-ups that mixed methodology with implementation notes
were consolidated from `engine/docs/assessment-framework/`. Remaining files there
are stubs or implementation-adjacent developer docs.

## Evidence origins

| Origin | Meaning |
| ------ | ------- |
| `observed` | Extracted from source, config, lockfiles, or repository structure |
| `derived` | Deterministically calculated from observed evidence |
| `declared` | From configuration/metadata; not independently verified |
| `enterprise-declared` | From Enterprise / Platform declared context |
| `imported` | From an approved external artifact (e.g., advisory DB snapshot) |
| `runtime-imported` | From telemetry/profiling (future) |
| `externally-verified` | Confirmed by a trusted third-party integration (future) |

## Evidence strength

Strength is about how directly evidence supports a conclusion—not severity.

| Strength | Meaning |
| -------- | ------- |
| `direct` | Primary observation that alone supports the finding |
| `strong` | Multiple consistent direct signals |
| `supporting` | Corroborates but is not sufficient alone |
| `contextual` | Background that frames interpretation |
| `weak` | Suggestive only; high uncertainty |

## Evidence handling requirements

- **Provenance:** Every evidence item cites a safe location or subject reference.
- **Completeness:** Note when expected sources were missing.
- **Contradiction:** Prefer explicit conflict notes over silent overwrite.
- **Stale evidence:** Imported catalogs must carry version/as-of metadata when used.
- **Invalid evidence:** Reject credential-bearing URLs and secret-like payloads.
- **Deduplication:** Deterministic fingerprinting.
- **Excerpts:** Bounded; prefer fingerprints over large source dumps.
- **Citations:** Reports link evidence → finding → rule.

## Confidence

**Confidence** = certainty in the assessment conclusion. It is **not** severity.

| Level | Meaning |
| ----- | ------- |
| `low` | Thin, incomplete, or highly heuristic evidence |
| `medium` | Adequate supporting evidence with residual uncertainty |
| `high` | Strong, consistent, well-scoped evidence |

## Coverage

**Coverage** describes what was assessed vs what remained out of scope or
unavailable. Coverage must be stated alongside confidence whenever scores or
executive claims are made.


## Recommendation hierarchy

| Level | Scope | Example |
| ----- | ----- | ------- |
| 1. Finding-level remediation | Single finding | Remove committed secret; rotate credentials |
| 2. Component-level improvement | Module/service | Extract shared library to break cycle |
| 3. Application-level initiative | One application | Upgrade framework to supported line |
| 4. Portfolio-level modernization | Multiple apps | Shared identity platform migration |
| 5. Governance / standards | Org policy | Adopt approved logging standard |

Engine / Community typically emits levels 1–3. Platform portfolio capabilities commonly add 4–5.

## Honesty about current product surfaces

CodeStrata Engine produces repository inventory, graphs, deterministic findings,
recommendations, and an Engineering Assessment HTML report. Full dimension
scoring, business-impact scoring, and CTO report structures described in
methodology are **Knowledge targets** where not yet wired in runtime.

Runtime behavior is documented under `engine/docs/` (developer/user docs), not
here.

## Related

- [README.md](README.md) — Knowledge index
- [CONCEPTS.md](CONCEPTS.md) — Concept ID framework
- [RULE_CATALOG.md](RULE_CATALOG.md) — Catalog ↔ Runtime ↔ Concept crosswalk
- [TRACEABILITY.md](TRACEABILITY.md) — End-to-end logical mapping
- Domain folders — domain-specific findings/recommendations/maturity
- [governance/README.md](../governance/README.md)
