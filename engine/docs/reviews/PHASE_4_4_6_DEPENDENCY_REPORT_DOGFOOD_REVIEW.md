# Phase 4.4.6 — Dependency CTO Report Integration Dogfood Review

**Date:** 2026-07-24  
**Artifacts:** `reports/dogfood-phase-4-4-6/` (gitignored)  
**Report section:** `report.dependency` **1.0.0**  
**Customer JSON schema:** **1.2** (additive `assessment.dependency`; no bump)

## Recommendation

**Accept Phase 4.4.6.** Presentation-only adapter projects the accepted
in-memory `DependencyAssessmentSection` into CTO JSON/HTML without re-analysis.
Production and test/fixture observations remain separated. Repeat runs produce
identical dependency report sections. Report gate defaults off and is independent
of Architecture / Technical Debt report sections.

## CodeStrata

| Field | Value |
| ----- | ----- |
| Assessment status | `succeeded` |
| Report section status | `succeeded` |
| Production findings (report) | 0 |
| Test/fixture observations | 2 (shown separately) |
| HTML anchor | `dependency-assessment` |
| Repeat-run dependency section | **byte-identical** |

### Executive summary

- Includes required zero-production wording.
- Identifies two test/fixture findings as non-production-primary.
- Includes declared-only wording; does not claim healthy/secure/low risk.

### Landscape

Declarations, active/management/plugin counts labeled separately and reconciled
with the assessment inventory (37 declarations collected; 12 production active;
25 test/fixture declarations).

### Production vs test

- Production subsection: none-detected statement; **no** fabricated remediation cards.
- Test/fixture subsection: two findings with source role `test`.

## Spring Petclinic

| Field | Value |
| ----- | ----- |
| Assessment status | `succeeded` |
| Report section status | `succeeded` |
| Findings | 0 |
| Declarations collected | 65 |
| Production active | 47 |
| Production plugins | 18 |
| Unsupported resolution (coverage) | 6 |
| Repeat-run dependency section | **byte-identical** |

### Coverage

Gradle interpolation remains diagnostics/coverage (`unsupported_resolution_coverage`),
not unresolved-version findings or remediation recommendations.

### Landscape separation

Active dependencies and build plugins are labeled separately (47 vs 18); not
merged into an unexplained total.

## Explicit non-claims verified

- No healthy/secure/current/low-risk language in executive summary
- No unresolved-version finding/recommendation for Petclinic Gradle interpolations
- No absolute filesystem paths in dependency report JSON/HTML
- No embedding of raw `dependency-evidence.json`

## Explicit limitations

Declared-only; no transitive resolution; no registries; no CVE/license; no
scores/priorities; no AI narrative; report disabled by default.
