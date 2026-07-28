# Engineering Intelligence Traceability

**Status:** Canonical (Phase 8.9.4)  
**Authority:** Knowledge (logical mapping)

## Purpose

Document the end-to-end logical relationship between Engineering Knowledge and
Engine runtime artifacts. This mapping does **not** change runtime execution.

## Chain

```text
Engineering Concept          (Knowledge Concept ID)
        ↓
Runtime Rule                 (Engine Runtime Rule ID + Catalog Rule ID)
        ↓
Evidence                     (normalized repository / portfolio evidence)
        ↓
Finding                      (deterministic observed condition)
        ↓
Assessment                   (assessment section / Engineering Snapshot)
        ↓
Customer Report              (HTML / JSON / Platform presentation)
```

## Identifier ownership

| Layer | Identifier | Source of truth |
| ----- | ---------- | --------------- |
| Concept | `ARCH-CON-001` | `knowledge/**/CONCEPTS.md` |
| Catalog rule | `AR-001` | `knowledge/RULE_CATALOG.md` |
| Runtime rule | `architecture.dependency-cycle` | Engine `domain/**/ids.py` |
| Finding | Finding ID (Engine) | Engine finding identity |
| Assessment | Assessment / snapshot IDs | Engine / Platform records |
| Report | Report artifact paths | Reporting pipeline |

## Responsibilities

| Concern | Owner |
| ------- | ----- |
| What the concept means | Knowledge |
| How the rule detects | Engine (runtime) |
| Permanent crosswalk | Rule Catalog + this document |
| How CodeStrata is built | Governance |

## Future AI reasoning

AI narratives and answering must cite Findings / Evidence and may reference
Concept IDs and Catalog Rule IDs for grounding. AI must not invent Concept IDs
or Rules. See Governance AI philosophy.

## Related

- [RULE_CATALOG.md](RULE_CATALOG.md)
- [CONCEPTS.md](CONCEPTS.md)
- [ASSESSMENT_CONCEPTS.md](ASSESSMENT_CONCEPTS.md)
- [governance/constitution/007_AI_PHILOSOPHY.md](../governance/constitution/007_AI_PHILOSOPHY.md)
