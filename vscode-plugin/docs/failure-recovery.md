# Failure and recovery (Slice 13.8)

Policy: `community-vscode-recovery-policy:1.0`

## Purpose

Communicate clearly when a Community VS Code operation fails:

1. **What** failed
2. **Why** it failed
3. **What to do next**

without exposing stack traces, filesystem paths, CLI stdout/stderr, provider
details, credentials, or internal implementation details.

## Rules

- Recovery actions **never** execute automatically
- No automatic retry, install, assessment rerun, or report reopen
- User may choose a recommended action button
- Primary assessment/init/discovery results stay authoritative
- Report / telemetry / analytics / progress failures remain secondary
- Telemetry and analytics schemas are unchanged; recovery emits neither

## Recommended actions

| Label | Command (user-triggered only) |
| --- | --- |
| Initialize Repository | `codestrata.init` |
| Install CLI | `codestrata.installEngine` |
| Correct CLI Setting | `codestrata.openDocumentation` |
| Run Assessment Again | `codestrata.assess` |
| Open Report | `codestrata.openHtmlReport` |
| Select Workspace | _(no auto command — open a folder)_ |
| Read Documentation | `codestrata.openDocumentation` |

## Failure domains

`workspace`, `initialization`, `cli_discovery`, `cli_installation`,
`assessment`, `report`, `progress`, `cancellation`, `user_declined`,
`internal`, `secondary_failure`

## Examples

| Category | Ownership | Recovery |
| --- | --- | --- |
| `repository_not_initialized` | primary | Initialize Repository |
| `cli_unavailable` | primary | Install CLI (install guidance UX retained) |
| `assessment_failed` | primary | Run Assessment Again |
| `assessment_cancelled` | primary | none |
| `report_not_found` | secondary | Run Assessment Again (primary success preserved) |
| `report_open_failed` | secondary | Open Report (primary success preserved) |

## Deferred

Telemetry consent integration — [telemetry-consent-integration.md](./telemetry-consent-integration.md) (Slice 13.9).

~~Source-local verification — Slice **13.10**~~ — [source-locality.md](./source-locality.md).

~~CLI compatibility — Slice **13.11**~~ — [cli-compatibility.md](./cli-compatibility.md). ~~Marketplace branding — Slice **13.12**~~ — [marketplace-branding.md](./marketplace-branding.md). ~~Marketplace documentation — Slice **13.13**~~ — [marketplace-documentation.md](./marketplace-documentation.md). Clean install validation — Slice **13.14**.

## Related

- [community-workflow.md](./community-workflow.md)
- [assessment-execution.md](./assessment-execution.md)
- [html-report-opening.md](./html-report-opening.md)
