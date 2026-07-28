# Community & GitHub Metrics

**Phase:** 14.3  
**Audience:** Maintainers

## GitHub readiness checklist (per public Community repo)

Validate on each mirror (`codestrata-engine`, `codestrata-docs`,
`codestrata-examples`, `codestrata-vscode`, `codestrata-cursor`):

- [ ] README.md
- [ ] LICENSE
- [ ] SECURITY.md
- [ ] CONTRIBUTING.md
- [ ] CODE_OF_CONDUCT.md (where applicable)
- [ ] PRIVACY.md (Engine / docs / extensions)
- [ ] Issue templates
- [ ] Pull request template
- [ ] Discussions enabled (org/repo setting)
- [ ] Repository topics set
- [ ] Repository description set
- [ ] Website / docs URL set
- [ ] Release notes template available

Engine ships GitHub templates under `engine/.github/` for export.

## Metrics to monitor

| Metric | Why |
| --- | --- |
| Stars | Awareness / social proof |
| Forks | Downstream interest |
| Watchers | Engaged followers |
| Visitors (Traffic) | Discovery |
| Clones | Serious evaluation |
| Release downloads | Adoption of artifacts |
| Issues opened/closed | Support load + product gaps |
| Discussions | Community Q&A health |
| Pull requests | Contribution velocity |
| Contributors | Breadth of participation |

## Product metrics (opt-in telemetry)

| Metric | Event / derivation |
| --- | --- |
| Installations | `installation_created` |
| Telemetry opt-in % | enabled installations / known installations |
| First assessments | first `assessment_completed` per id |
| Successful assessments | `assessment_completed` |
| Failed assessments | `assessment_failed` |
| Reports opened | `report_opened` |
| AI usage % | `ai_used` / completed assessments |
| Monthly active installations | distinct ids with events in 28d |
| Repeat usage | ids with ≥2 completed assessments in window |
| Version adoption | `codestrata_version` distribution |

Local counters also appear in `codestrata telemetry status` → `local_counters`.

## Related

- Engine `PRIVACY.md` / `docs/telemetry.md`
- Activation / funnel definitions for Community product metrics live in this file
  (install → opt-in → assess → report → repeat / AI usage). Founder/company
  operational dashboards are out of scope for this repository.
