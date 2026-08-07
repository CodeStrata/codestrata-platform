# Assessment execution (Slice 13.5)

Policy: `community-vscode-assessment-execution-policy:1.0`

## Purpose

User-triggered **Run Assessment** (`codestrata.assess`) and
**Run Assessment with AI** (`codestrata.assessWithAi`) share one
safe orchestration path. The **Engine CLI** is the sole authority that analyzes
the repository and writes assessment artifacts.

## Readiness order

1. Validate eligible local workspace
2. Validate **initialized** repository (Slice 13.4 state detection)
3. Discover compatible CodeStrata CLI (Slice 13.2)
4. If CLI unavailable → Slice 13.3 guidance and **stop** (no auto-resume)
5. Optional AI confirmation (AI command only)
6. Command-local telemetry consent (eligible commands only)
7. Consent-gated analytics construction (unavailable sink)
8. One Engine `assess` product process (`shell: false`)
9. Capture primary CLI result
10. Finalize telemetry/analytics fail-silently
11. Evaluate report **postcondition**
12. Optional report-open adapter (Slice 13.7 owns UX)

Telemetry consent is **not** prompted for repositories that cannot be assessed.

Initialization does **not** automatically initialize before assessment.

## Commands

| Command | Operation | Engine flags |
| --- | --- | --- |
| `codestrata.assess` | `run_assessment` | `assess … --no-ai --quiet --json-summary` |
| `codestrata.assessWithAi` | `run_assessment_with_ai` | `assess … --with-ai --quiet --json-summary` |

The selected command determines AI mode. Settings alone do not silently flip
`codestrata.assess` into AI mode.

## Engine authority

- Exit code / cancellation determine primary success/failure
- Finding counts, grades, scores, and AI advisor status do **not** rewrite success
- AI fail-soft remains Engine-owned: provider failure may still yield core reports
- Extension does not retry without AI or switch providers

## Report postcondition

After CLI exit 0, local report discovery may succeed or fail:

- `report_available = true` → load findings/recommendations locally
- `report_available = false` → `report_missing` postcondition; **primary exit remains success**
- Report-open failure remains distinct (`report_open_failed`) and does not rewrite assessment success

## Boundaries

- No source upload by the extension
- Assessment does not mutate source, CodeStrata config, or `.git`
- Generated assessment artifacts under the Engine output directory are allowed
- Standard assessment: extension adds no network path
- AI assessment: only Engine may call configured providers; credentials stay Engine-owned
- Telemetry transport / analytics sink remain unavailable

## Deferred

- ~~Report-opening UX — Slice **13.7**~~ —
  [html-report-opening.md](./html-report-opening.md)
- ~~Failure/recovery UX — Slice **13.8**~~ — [failure-recovery.md](./failure-recovery.md)
- Precise AI source-local documentation — Slice **13.10**

## Related

- [community-workflow.md](./community-workflow.md)
- [assessment-progress.md](./assessment-progress.md)
- [html-report-opening.md](./html-report-opening.md)
- [failure-recovery.md](./failure-recovery.md)
- [telemetry-consent-integration.md](./telemetry-consent-integration.md)
- [source-locality.md](./source-locality.md)
- [repository-initialization.md](./repository-initialization.md)
- [cli-discovery.md](./cli-discovery.md)
- [cli-installation.md](./cli-installation.md)
- [telemetry.md](./telemetry.md)
- [analytics.md](./analytics.md)
