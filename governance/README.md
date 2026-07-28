# CodeStrata Engineering Governance

**Status:** Foundation (Phase 8.9.1; cleanup 8.9.1A)  
**Audience:** Maintainers, contributors, AI assistants, design partners

## Purpose

`governance/` is the long-term **source of truth** for how CodeStrata is designed,
built, maintained, and evolved.

It separates:

| Concern | Location |
| ------- | -------- |
| Source code | `engine/`, `platform/`, plugins, scripts |
| Governance (this tree) | `governance/` |
| Engineering knowledge | [`knowledge/`](../knowledge/) — concepts; existing `engine/docs/` remain until migration |
| User documentation | Future public docs portal (Phase 12+) — must reference Governance, not duplicate it |
| Operational playbooks | `governance/playbooks/` |

## Product naming

| Name | Meaning |
| ---- | ------- |
| **CodeStrata** | Product |
| **CodeStrata Engine** | Community Engine (`engine/`) |
| **CodeStrata Platform** | Commercial Platform (`platform/`) — use product name **CodeStrata Platform** in customer copy |
| **CodeStrata VS Code Extension** | Placeholder / future |
| **CodeStrata Cursor Extension** | Placeholder / future |

AI is a **capability**, not part of the product name.

## Layout

```text
governance/
├── README.md                 # This file
├── constitution/             # Normative product & engineering principles
├── standards/                # Day-to-day engineering & product standards
├── playbooks/                # Operational checklists (release, dogfood, public contracts)
├── ai/                       # Instructions for AI-assisted development
└── assets/                   # Uploaded brand package + DESIGN-SYSTEM.md (single design authority)
```

Public API / SDK / CLI / report compatibility:
[`playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md`](playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md).

**Design System authority:** [`assets/DESIGN-SYSTEM.md`](assets/DESIGN-SYSTEM.md)  
(`standards/DESIGN_SYSTEM.md` is a pointer only.)

## How to use

1. **Normative decisions** → start in `constitution/`.
2. **Implementation standards** → `standards/`.
3. **Visual branding / Design System** → `assets/DESIGN-SYSTEM.md`.
4. **AI-assisted work** → `ai/` (especially `CURSOR_INSTRUCTIONS.md`).
5. **Release / RC / dogfood / demos** → `playbooks/`.
6. **Implementation detail** → keep in existing engineering docs; link here rather than copy.

## Authority & conflict resolution

1. **Constitution** outranks standards and playbooks.
2. **Standards** outrank local style preferences.
3. **Implementation** remains authoritative for *what the code does today*
   (see [ARCHITECTURE.md](../ARCHITECTURE.md) and
   [platform/docs/architecture/PLATFORM_ARCHITECTURE.md](../platform/docs/architecture/PLATFORM_ARCHITECTURE.md)).
4. When implementation and Governance disagree, open a change that updates either
   the code or Governance — do not silently diverge.

## Community inheritance

Public Community repositories (Engine, examples, plugins) should inherit applicable
standards from this tree. Export/publish pipelines must not strip required
governance references without an explicit decision.

## Document status legend

| Marker | Meaning |
| ------ | ------- |
| **Foundation** | Structure established; content outlined |
| **TODO** | Content to be authored in a later phase |
| **Reference** | Points at existing authoritative docs |

## Related existing docs (not replaced)

- [DOCUMENTATION_INVENTORY.md](DOCUMENTATION_INVENTORY.md) — source doc classification
- [ARCHITECTURE.md](../ARCHITECTURE.md) — implementation architecture map
- [ROADMAP.md](../ROADMAP.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [knowledge/README.md](../knowledge/README.md)
- [engine/docs/security/](../engine/docs/security/)
- [platform/docs/architecture/](../platform/docs/architecture/)
- [scripts/verify_release.py](../scripts/verify_release.py)
