# security — Concept IDs

**Status:** Canonical (Phase 8.9.4)
**Domain:** `security`

## Concepts

| Concept ID | Name | Description | Associated Catalog Rule IDs |
| ---------- | ---- | ----------- | --------------------------- |
| `SEC-CON-001` | Private key material | Private keys present in repository evidence | `SE-001` |
| `SEC-CON-002` | Credential hygiene | Credential literals and placeholders in config | `SE-002`, `SE-003` |
| `SEC-CON-003` | TLS verification | TLS/hostname verification controls | `SE-004`, `SE-005` |
| `SEC-CON-004` | Authentication enablement | Authentication disabled signals | `SE-006` |
| `SEC-CON-005` | CORS permissiveness | Overly permissive CORS origins | `SE-007` |
| `SEC-CON-006` | Debug exposure | Debug mode enabled in configuration | `SE-008` |

## Related

- [RULES.md](RULES.md)
- [FINDINGS.md](FINDINGS.md)
- [../RULE_CATALOG.md](../RULE_CATALOG.md)
- [../CONCEPTS.md](../CONCEPTS.md)
