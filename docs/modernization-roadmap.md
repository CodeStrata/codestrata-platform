# Modernization Roadmap Engine

Phase 5.10 converts existing assessment findings and recommendations into a
deterministic phased modernization plan. It does **not** re-run assessments,
invent findings, or call AI models.

## Configuration

Disabled by default:

```toml
[report.sections.roadmap]
enabled = false
include_assumptions = true
include_limitations = true
include_evidence = true
```

When enabled, `aimf assess` adds `assessment.roadmap` to `report.json` and a
**Phased Modernization Plan** section to the HTML report (`#modernization-roadmap-assessment`).
Schema version remains `1.2` (additive key only).

## Phases

| Phase | Typical categories |
| --- | --- |
| Stabilize | testing, build, documentation, governance, configuration, CI/CD, reliability |
| Secure | security |
| Modernize | architecture, dependency, maintainability, modernization, technical debt, cloud, AI readiness, unknown |
| Optimize | performance |

## Mapping rules

- **Group** recommendations by `(phase, category)`; duplicate recommendation IDs collapse.
- **Priority** is the highest priority among grouped recommendations (`immediate`/`critical` → critical).
- **Effort** uses explicit effort when present; otherwise action-count buckets (`xs`…`xl`).
- **Risk** uses explicit risk when present, otherwise priority, then escalates from finding severity.
- **Dependencies** are cross-phase only: Secure→Stabilize; Modernize→Secure+Stabilize; Optimize→prior phases.
- **Identifiers** are stable digests of phase, category, and sorted recommendation IDs.

## CLI

```bash
aimf roadmap inspect --report path/to/report.json
aimf roadmap phases --report path/to/report.json
aimf roadmap initiatives --report path/to/report.json
aimf roadmap generate --recommendations recommendations.json [--findings findings.json]
```

`generate` reads existing artifacts only; it does not mutate repositories.
