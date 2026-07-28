# Technical Debt — Recommendations

**Status:** Foundation  
**Domain:** `technical-debt`

## Objective

Explain recommendation philosophy for **Technical Debt**.

## Definition

A recommendation is a prioritized engineering action that addresses one or more
findings (or a coherent finding theme) in this domain.

## Philosophy in this domain

Pay-down actions sized to impact, not cosmetic cleanup.

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
