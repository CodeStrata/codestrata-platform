# HTML report opening (Slice 13.7)

Policy: `community-vscode-report-opening-policy:1.0`

## Purpose

Open the Engine-generated local HTML Engineering Assessment report safely.

The extension never generates or rewrites HTML. Engine assessment writes
`report.html` under:

```text
<output>/<repository-name>/<YYYYMMDD-HHMMSS>/report.html
```

Default `<output>` is the workspace-relative `reports` directory
(`codestrata.assessment.outputDirectory`).

## Approach B — prompt-driven open

After a successful assessment the extension notifies the user and offers
**Open HTML Report**. It does **not** auto-open.

- Failed assessment → no auto-open
- Cancelled assessment → no auto-open
- Missing report → postcondition; assessment success preserved
- Open failure → assessment success preserved (`report_open_failed`)

## Explicit command

`codestrata.openHtmlReport`:

- Opens an existing local report only
- Does not run assessment, init, CLI discovery, telemetry, or analytics
- Uses session artifacts when available, otherwise bounded discovery

## Boundaries

- Repository + output containment required
- Traversal / absolute escape / symlink escape rejected
- Remote / non-file URIs rejected
- Regular `report.html` file required
- Discovery depth limited to `<output>/<repo>/<run>/` (no filesystem crawl)
- `vscode.env.openExternal(Uri.file(...))` — no shell `open`/`xdg-open`
- Report contents are not parsed or transmitted

## Stale reports

When assessment returns a JSON `run_directory`, that Engine path is preferred
(fresh for that run). Fallback “latest HTML under output” is best-effort for the
explicit open command and does not claim absolute freshness.

## Deferred

~~Full recovery UX — Slice **13.8**~~ — see [failure-recovery.md](./failure-recovery.md).

~~Source-local verification — Slice **13.10**~~ — [source-locality.md](./source-locality.md). ~~CLI compatibility — Slice **13.11**~~ — [cli-compatibility.md](./cli-compatibility.md). ~~Marketplace branding — Slice **13.12**~~ — [marketplace-branding.md](./marketplace-branding.md). ~~Marketplace documentation — Slice **13.13**~~ — [marketplace-documentation.md](./marketplace-documentation.md). Clean install validation — Slice **13.14**.

## Related

- [assessment-execution.md](./assessment-execution.md)
- [assessment-progress.md](./assessment-progress.md)
- [community-workflow.md](./community-workflow.md)
