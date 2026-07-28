# CodeStrata Engineering Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Audience:** Maintainers, rule authors, AI assistants, design partners

## Purpose

`knowledge/` is the canonical definition of **what CodeStrata knows** about
software engineering.

It separates engineering expertise from product implementation so that:

- assessment domains stay coherent
- findings and recommendations share a conceptual vocabulary
- maturity models remain comparable
- future rule packs can trace to documented knowledge

## Boundaries

| Concern | Location | Role |
| ------- | -------- | ---- |
| **Knowledge** (this tree) | `knowledge/` | What CodeStrata knows (engineering concepts) |
| **Governance** | `governance/` | How CodeStrata is designed, built, and evolved |
| **Implementation** | `engine/`, `platform/` | How CodeStrata executes assessments and APIs |
| **User documentation** | future docs portal / existing user guides | How users interact with CodeStrata |

**Rules**

1. Knowledge documents **concepts**, not Python/SQL/API/tests.
2. Implementation **consumes** and should eventually **trace back** to Knowledge.
3. Governance is not Knowledge; Knowledge is not product docs.
4. Do not migrate or enumerate implemented rules in this foundation phase.

## Domains

| Domain | Path | Focus |
| ------ | ---- | ----- |
| Architecture | [architecture/](architecture/) | Structure, coupling, fitness |
| Cloud | [cloud/](cloud/) | Cloud readiness and cloud-native posture |
| AI Readiness | [ai/](ai/) | Safe, useful AI augmentation readiness |
| Security | [security/](security/) | Application and repository security concepts |
| Dependency | [dependency/](dependency/) | Dependency health and supply chain |
| Technical Debt | [technical-debt/](technical-debt/) | Maintainability and debt |
| Performance | [performance/](performance/) | Efficiency and scalability |
| Cost | [cost/](cost/) | Engineering cost and efficiency |
| Compliance | [compliance/](compliance/) | Control and evidence concepts |
| Documentation | [documentation/](documentation/) | Engineering documentation quality |
| Modernization | [modernization/](modernization/) | Transformation patterns and sequencing |
| Portfolio | [portfolio/](portfolio/) | Multi-repository / estate knowledge |


## Traceability & Rule Catalog (Phase 8.9.4)

| Document | Role |
| -------- | ---- |
| [CONCEPTS.md](CONCEPTS.md) | Concept ID framework |
| [RULE_CATALOG.md](RULE_CATALOG.md) | Catalog Rule ID ↔ Runtime Rule ID ↔ Concept ID |
| [TRACEABILITY.md](TRACEABILITY.md) | End-to-end logical mapping |
| [catalog/rules.json](catalog/rules.json) | Machine-readable catalog mirror |
| Per-domain [CONCEPTS.md](architecture/CONCEPTS.md) | Domain concept tables |

## Per-domain documents

Each domain contains:

| File | Intent |
| ---- | ------ |
| `README.md` | Purpose, scope, relationships, evolution |
| `RULES.md` | Purpose of rules (no implemented rule catalog yet) |
| `FINDINGS.md` | Meaning of findings in the domain |
| `RECOMMENDATIONS.md` | Recommendation philosophy |
| `MATURITY_MODEL.md` | Intended maturity structure (unscored) |
| `REFERENCES.md` | External standards and references (TODO placeholders) |

## Relationship to existing engineering docs

Phase 8.9.3 consolidates assessment methodology and domain taxonomies into
Knowledge. Engine docs under `engine/docs/analysis-intelligence/` and
`engine/docs/assessment-framework/` retain **implementation** notes and
**pointer stubs** to this tree.

Cross-cutting assessment concepts:
[ASSESSMENT_CONCEPTS.md](ASSESSMENT_CONCEPTS.md)

## Future work

1. Author deeper domain content beyond foundation outlines.
2. Migrate rule packs to cite Knowledge domains.
3. Continue replacing remaining conceptual duplicates with references.
4. Wire implementation identifiers to Knowledge concept IDs.

## Related

- [governance/README.md](../governance/README.md)
- [ASSESSMENT_CONCEPTS.md](ASSESSMENT_CONCEPTS.md)
- [ARCHITECTURE.md](../ARCHITECTURE.md)
