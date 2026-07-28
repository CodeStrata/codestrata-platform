# Engineering Concept IDs

**Status:** Canonical (Phase 8.9.4)  
**Authority:** Engineering Knowledge

## Purpose

Stable **Concept IDs** identify engineering concepts in Knowledge. They are the
permanent conceptual keys that runtime rules, findings, reports, tests, and
future AI reasoning should reference.

## Format

```text
<DOMAIN>-CON-<NNN>
```

| Prefix | Domain |
| ------ | ------ |
| `ARCH-CON` | architecture |
| `SEC-CON` | security |
| `TD-CON` | technical-debt |
| `DEP-CON` | dependency |
| `CLOUD-CON` | cloud |
| `AI-CON` | ai |
| `PERF-CON` | performance |
| `COST-CON` | cost |
| `COMP-CON` | compliance |
| `DOC-CON` | documentation |
| `MOD-CON` | modernization |
| `PORT-CON` | portfolio |

Concept IDs belong **only** in Knowledge. They are not Engine package names and
must not be relocated into runtime code as the source of truth.

## Relationship to runtime

```text
Concept ID  →  Catalog Rule ID  →  Runtime Rule ID (Engine)
```

See [TRACEABILITY.md](TRACEABILITY.md) and [RULE_CATALOG.md](RULE_CATALOG.md).

## Per-domain concept lists

Each domain maintains [CONCEPTS.md](architecture/CONCEPTS.md) (and siblings)
with the authoritative concept table for that domain.
