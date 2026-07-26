# Dependency Intelligence

Phase 4.4 of CodeStrata Analysis Intelligence.

| Sub-milestone | Status |
| ------------- | ------ |
| 4.4.1 Domain Foundation | Complete |
| 4.4.2 Dependency Evidence | Complete |
| 4.4.3 Rules & Findings | Complete |
| 4.4.3A Unresolved-version precision | Complete |
| 4.4.4 Dependency Inventory / Assessment Usability | Complete |
| 4.4.5 Assessment Synthesis | Complete |
| 4.4.6 Report Integration | Complete |

Design authority:
[PHASE_4_4_DEPENDENCY_INTELLIGENCE.md](../../design/PHASE_4_4_DEPENDENCY_INTELLIGENCE.md).

## Evidence ownership

- **Dependency Evidence** owns manifest discovery/parsing and normalized
  declaration facts (`dependency-evidence.json`).
- **Dependency Intelligence** consumes that evidence for hygiene rules and
  assessment-section projection. It must not reparse manifests.
- **Security Intelligence** (future) may consume the same evidence for
  vulnerability interpretation.

No CVE, license, version-freshness, or external registry data exists yet.

## 4.4.3 Hygiene rules

Five SharedRules under `dependency.core` (disabled by default):

- `dependency.unresolved-version`
- `dependency.mutable-version`
- `dependency.unbounded-requirement`
- `dependency.conflicting-exact-versions`
- `dependency.duplicate-declaration`

See [hygiene-rules.md](hygiene-rules.md).

```toml
[rules]
enabled = true

[rules.dependency]
enabled = true

[evidence.dependency]
enabled = true

[assessment.sections.dependency]
enabled = true

[report.sections.dependency]
enabled = true
```

See also:

- [taxonomy.md](taxonomy.md)
- [configuration.md](configuration.md)
- [evidence-ownership.md](evidence-ownership.md)
- [evidence.md](evidence.md)
- [report.md](report.md)
- [hygiene-rules.md](hygiene-rules.md)
- [assessment-inventory.md](assessment-inventory.md)
- [synthesis.md](synthesis.md)
