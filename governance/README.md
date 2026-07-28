# CodeStrata Engineering Governance

**Status:** Active  
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
| User documentation | Public docs portal — must reference Governance, not duplicate it |
| Operational playbooks | `governance/playbooks/` |
| Generated validation output | `.generated/` (gitignored; never under `governance/`) |

## Product naming

| Name | Meaning |
| ---- | ------- |
| **CodeStrata** | Product |
| **CodeStrata Engine** | Community Engine (`engine/`) |
| **CodeStrata Platform** | Commercial Platform (`platform/`) — use product name **CodeStrata Platform** in customer copy |
| **CodeStrata VS Code Extension** | Editor extension (`vscode-plugin/`) |
| **CodeStrata Cursor Extension** | Editor extension (`cursor-plugin/`) |

AI is a **capability**, not part of the product name.

## Layout

```text
governance/
├── README.md                 # This file
├── DOCUMENTATION_INVENTORY.md
├── adr/                      # Architecture Decision Records
├── constitution/             # Normative product & engineering principles
├── standards/                # Day-to-day engineering & product standards
├── playbooks/                # Operational checklists (release, dogfood, contracts)
├── release/                  # Community release / extraction guidance
├── metrics/                  # Long-term Community/GitHub metric definitions
├── ai/                       # Instructions for AI-assisted development
└── assets/                   # Brand package + DESIGN-SYSTEM.md (design authority)
```

Public API / SDK / CLI / report compatibility:
[`playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md`](playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md).

**Design System authority:** [`assets/DESIGN-SYSTEM.md`](assets/DESIGN-SYSTEM.md)

## How to use

1. **Normative decisions** → start in `constitution/` (and `adr/` for accepted ADRs).
2. **Implementation standards** → `standards/`.
3. **Visual branding / Design System** → `assets/DESIGN-SYSTEM.md`.
4. **AI-assisted work** → `ai/` (especially `CURSOR_INSTRUCTIONS.md`).
5. **Internal RC / dogfood / demos** → `playbooks/`.
6. **Community public distribution** → `release/COMMUNITY_RELEASE_CHECKLIST.md`.
7. **Implementation detail** → keep in engineering docs; link here rather than copy.

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
| **Active** | Current living governance |
| **Foundation** | Structure established; content outlined |
| **TODO** | Content to be authored later |
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
- [scripts/validate_release.py](../scripts/validate_release.py)
