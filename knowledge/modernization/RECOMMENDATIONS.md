# Modernization — Recommendations

**Status:** Foundation  
**Domain:** `modernization`

## Objective

Explain recommendation philosophy for **Modernization**.

## Definition

A recommendation is a prioritized engineering action that addresses one or more
findings (or a coherent finding theme) in this domain.

## Philosophy in this domain

Sequenced actions that enable safe progressive modernization.

## Principles

1. Actionable — a team can execute or plan the work.
2. Traceable — ties back to findings and evidence.
3. Proportionate — effort matches risk and value.
4. Sequencing-aware — respects dependencies where relevant.

## Recommendation shapes (outline)

| Shape | When to use |
| ----- | ----------- |
| Remediate | Fix a concrete defect or hygiene gap |
| Harden | Raise baseline controls / quality |
| Modernize | Structural or platform change |
| Observe | Improve visibility before larger change |

<!-- TODO: Define priority model (impact × urgency × effort) without scoring live systems here. -->

## Non-goals

- Sprint tickets or staffing plans
- Vendor purchase recommendations as product endorsements

## Related

- [FINDINGS.md](FINDINGS.md)
- [MATURITY_MODEL.md](MATURITY_MODEL.md)

## Wave sequencing (migrated)

Waves are **dependency-driven**, not mere severity buckets.

| Wave | Intent |
| ---- | ------ |
| Wave 0 — Validate and Stabilize | Confirm critical findings; close severe exposures; establish inventory foundations |
| Wave 1 — Quick Wins and Risk Reduction | Supported upgrades; configuration corrections; straightforward fixes |
| Wave 2 — Foundation Modernization | Modularization; platform upgrades; test/deploy foundations |
| Wave 3 — Structural Modernization | Deeper structural change (decomposition, major platform shifts) |

Sequence concept: Finding → Recommendation → Initiative → Dependency analysis → Priority → Wave.

See also [ASSESSMENT_CONCEPTS.md](../ASSESSMENT_CONCEPTS.md).

