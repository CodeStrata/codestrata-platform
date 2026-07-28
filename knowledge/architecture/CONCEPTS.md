# architecture — Concept IDs

**Status:** Canonical (Phase 8.9.4)
**Domain:** `architecture`

## Concepts

| Concept ID | Name | Description | Associated Catalog Rule IDs |
| ---------- | ---- | ----------- | --------------------------- |
| `ARCH-CON-001` | Dependency cycles | Directed cycles between architectural units | `AR-001` |
| `ARCH-CON-002` | Dependency direction | Invalid or inverted dependency direction | `AR-002` |
| `ARCH-CON-003` | Layer boundaries | Layer boundary integrity | `AR-003` |
| `ARCH-CON-004` | Cross-module coupling | Excessive coupling across modules | `AR-004` |
| `ARCH-CON-005` | Component concentration | Risk concentration in few components | `AR-005` |
| `ARCH-CON-006` | Framework leakage | Framework types leaking across boundaries | `AR-006` |
| `ARCH-CON-007` | Enterprise standard alignment | Mismatch with declared enterprise standards | `AR-007` |
| `ARCH-CON-010` | Language/runtime detection | Detected language or runtime platform | `LEG-006` |
| `ARCH-CON-011` | Framework detection | Detected application framework | `LEG-007` |
| `ARCH-CON-012` | Runtime engine declaration | Declared Node/runtime engine presence | `LEG-009` |

## Related

- [RULES.md](RULES.md)
- [FINDINGS.md](FINDINGS.md)
- [../RULE_CATALOG.md](../RULE_CATALOG.md)
- [../CONCEPTS.md](../CONCEPTS.md)
