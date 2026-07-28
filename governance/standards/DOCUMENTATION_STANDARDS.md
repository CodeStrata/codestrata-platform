# Documentation Standards

**Status:** Canonical (updated Phase 8.9.3)  
**Authority:** Standards

## Objective

Keep documentation accurate, non-duplicative, and clearly layered.

## Scope

All markdown in this monorepo and future public docs.

## 1. Documentation layers

| Layer | Location | Rule |
| ----- | -------- | ---- |
| Governance | `governance/` | Normative — how we design & build |
| Engineering Knowledge | `knowledge/` | What CodeStrata knows — engineering concepts |
| User documentation | `engine/docs/` guides, future portal | How to use — reference Governance/Knowledge |
| Developer documentation | `engine/docs/architecture/`, `platform/docs/`, `ARCHITECTURE.md` | How implementation works today |
| Operational documentation | security checklists, release notes, playbooks | How to operate / release |
| Inventory | [DOCUMENTATION_INVENTORY.md](../DOCUMENTATION_INVENTORY.md) | Classification of source docs |

## 2. Rules

1. **Governance and Knowledge are single authorities** for their concerns.
2. **Do not duplicate** Governance or Knowledge content in Engine/Platform docs —
   link instead.
3. When implementation changes, update developer docs in the same change when
   they become technically incorrect.
4. Prefer short, linked docs over encyclopedias.
5. Mark unknowns as **TODO** or **Not confirmed**.

## 3. Migration stance

Phase 8.9.3 consolidates duplicated methodology and taxonomy into Knowledge and
normative boundaries into Governance. Remaining `engine/docs/assessment-framework/`
conceptual files are pointers. Implementation contracts stay in developer docs.

## 4. Community inheritance

Public Community repositories should inherit references to applicable
`governance/` and `knowledge/` documents rather than forked copies of
principles.

## 5. References

- [governance/README.md](../README.md)
- [knowledge/README.md](../../knowledge/README.md)
- [engine/docs/README.md](../../engine/docs/README.md)
- [platform/docs/README.md](../../platform/docs/README.md)
