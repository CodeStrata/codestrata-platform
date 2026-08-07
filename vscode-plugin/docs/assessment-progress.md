# Assessment progress (Slice 13.6)

Policy: `community-vscode-assessment-progress-policy:1.0`

## Purpose

Present a single, truthful, cancellation-aware progress lifecycle for
`codestrata.assess` and `codestrata.assessWithAi` without fabricating Engine
signals the CLI does not provide.

## Decision A — indeterminate progress

v0.2.0 Engine assessment has **no structured progress protocol**. The extension
invokes `assess` with `--quiet` / `--json-summary` and does **not** parse stdout
for percentages.

Therefore:

- progress is **indeterminate** by default
- `progress.report` may carry **message text only**
- fabricated increments, timers, finding counts, and file-count percentages are
  **forbidden**

## Lifecycle

Progress starts **only after** workspace validation, initialized-repository
check, compatible CLI discovery, optional AI confirmation, and telemetry consent.

Visible phases (observables only):

1. `running_assessment`
2. `finalizing`
3. `locating_report`
4. terminal: `completed` | `failed` | `cancelled`

One `window.withProgress` (Notification) + one `AssessmentProgressLifecycle`
per assessment. AI assessment does **not** create a second progress bar.

## Cancellation

- Progress is cancellable
- First cancellation request aborts the one product CLI process
- Duplicate cancellation does not kill twice
- No retry and no report open after authoritative cancellation

## Authority

Slice 13.5 `AssessmentExecutionResult` remains primary. Progress/UI failures are
isolated and cannot rewrite Engine exit outcomes. Report missing remains a
postcondition.

## Privacy

Progress text excludes repository/workspace/CLI/report paths, providers, models,
credentials, findings, and source snippets. Stable diagnostics omit stdout/stderr,
timings, and timestamps.

## Deferred

- ~~Report-opening UX — Slice **13.7**~~ —
  [html-report-opening.md](./html-report-opening.md)
- ~~Failure/recovery UX — Slice **13.8**~~ — [failure-recovery.md](./failure-recovery.md)

## Related

- [assessment-execution.md](./assessment-execution.md)
- [community-workflow.md](./community-workflow.md)
