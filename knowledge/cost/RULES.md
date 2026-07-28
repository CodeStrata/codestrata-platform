# Cost — Rules

**Status:** Foundation  
**Domain:** `cost`

## Objective

Define the purpose of engineering rules for **Cost**.

## What rules are

Rules encode reusable engineering judgment that can be evaluated against
repository or portfolio evidence to produce findings.

## Purpose in this domain

Surface cost-risk and efficiency signals inferable from engineering evidence.

## Rule design principles

1. Evidence-based — no finding without supporting signals.
2. Deterministic where CodeStrata assesses automatically.
3. Stable identifiers and severity philosophy (to be aligned in migration).
4. Domain-scoped — do not smuggle unrelated domain concerns.

## Rule categories (outline)

<!-- TODO: Author category taxonomy for cost without listing implemented rule IDs. -->

| Category | Intent |
| -------- | ------ |
| Hygiene | Baseline engineering hygiene |
| Risk | Material risk if unaddressed |
| Readiness | Blocks or enables modernization / maturity |

## Non-goals

- Enumerate currently implemented CodeStrata rules (later migration).
- Embed Python predicates or analyzer code.

## Related

- [FINDINGS.md](FINDINGS.md)
- [RECOMMENDATIONS.md](RECOMMENDATIONS.md)
- [../README.md](../README.md)

## Catalog & Concept IDs (Phase 8.9.4)

- Concept IDs for this domain: [CONCEPTS.md](CONCEPTS.md)
- Permanent Rule Catalog: [../RULE_CATALOG.md](../RULE_CATALOG.md)
- Traceability chain: [../TRACEABILITY.md](../TRACEABILITY.md)

Runtime rule implementations remain in the CodeStrata Engine. This Knowledge
folder does not contain executable rules.

