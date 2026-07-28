# dependency — Concept IDs

**Status:** Canonical (Phase 8.9.4)
**Domain:** `dependency`

## Concepts

| Concept ID | Name | Description | Associated Catalog Rule IDs |
| ---------- | ---- | ----------- | --------------------------- |
| `DEP-CON-001` | Unresolved versions | Dependency versions not resolved | `DEP-001` |
| `DEP-CON-002` | Mutable versions | Mutable / floating versions | `DEP-002` |
| `DEP-CON-003` | Unbounded requirements | Unbounded version ranges | `DEP-003` |
| `DEP-CON-004` | Version conflicts | Conflicting exact versions | `DEP-004` |
| `DEP-CON-005` | Duplicate declarations | Duplicate dependency declarations | `DEP-005` |
| `DEP-CON-010` | Build wrapper hygiene | Missing build wrappers | `LEG-005` |
| `DEP-CON-011` | Unsupported framework version | Unsupported framework/runtime version | `LEG-008` |
| `DEP-CON-012` | Missing engine constraint | Missing declared engine constraint | `LEG-010` |
| `DEP-CON-013` | Lockfile hygiene | Missing lockfiles | `LEG-011` |

## Related

- [RULES.md](RULES.md)
- [FINDINGS.md](FINDINGS.md)
- [../RULE_CATALOG.md](../RULE_CATALOG.md)
- [../CONCEPTS.md](../CONCEPTS.md)
