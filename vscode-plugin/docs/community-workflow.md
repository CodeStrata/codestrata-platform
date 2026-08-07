# CodeStrata Community VS Code workflow (Slice 13.1)

Policy: `community-vscode-workflow-policy:1.0`

## Authoritative user journey

1. **Open a folder/workspace** — extension activates (`onStartupFinished`). No
   assessment, no telemetry prompt, no CLI construction for assessment.
2. **Initialize Repository** (`codestrata.init`) — user-triggered; see
   [repository-initialization.md](./repository-initialization.md). Compatible
   CLI required; Engine writes `codestrata.toml`; already-initialized skips CLI;
   no assessment / telemetry / analytics.
3. **Run Assessment** (`codestrata.assess`) — see
   [assessment-execution.md](./assessment-execution.md). Readiness:
   workspace → initialized repository → CLI discovery → command-local
   telemetry consent → one Engine assess CLI process → progress lifecycle
   ([assessment-progress.md](./assessment-progress.md)). Report availability is a
   postcondition; report-opening UX deferred to Slice 13.7.
4. **Run Assessment with AI** (`codestrata.assessWithAi`) — same orchestration
   with `--with-ai`; AI fail-soft remains Engine-owned.
5. **Open Report** (`codestrata.openHtmlReport`) — local HTML only; see
   [html-report-opening.md](./html-report-opening.md). Open failure is distinct
   from assessment failure; see [failure-recovery.md](./failure-recovery.md).

## Operations

| Command | Operation |
| --- | --- |
| `codestrata.init` | `initialize_repository` |
| `codestrata.assess` | `run_assessment` |
| `codestrata.assessWithAi` | `run_assessment_with_ai` |
| `codestrata.openHtmlReport` | `open_report` |

Compatibility alias: `codestrata.doctor` → `codestrata.checkEnvironment`
(environment check; not a workflow operation).

## States

`idle` → `validating_workspace` → (`initializing` | `awaiting_consent` |
`opening_report`) → `running_assessment` → `locating_report` →
`opening_report` → (`completed` | `failed` | `cancelled`).

Invalid transitions raise a bounded `WorkflowTransitionError`.

## Boundaries

- Engine CLI is authoritative for assessment/init exit status.
- Telemetry/analytics failures are isolated and cannot change primary outcomes.
- Progress starts/closes once per assessment.
- Diagnostics omit workspace/CLI/report paths, stdout/stderr, credentials.
- Source code remains local; no transmission.

## Deferred

- ~~13.2 CLI detection~~ — [cli-discovery.md](./cli-discovery.md)
- ~~13.3 CLI installation~~ — **guidance-only**
  ([cli-installation.md](./cli-installation.md)); no automatic package install
- ~~13.4 repository initialization~~ —
  [repository-initialization.md](./repository-initialization.md)
- ~~13.5 assessment execution~~ —
  [assessment-execution.md](./assessment-execution.md)
- ~~13.6 assessment progress~~ —
  [assessment-progress.md](./assessment-progress.md)
- ~~13.7 HTML report opening~~ —
  [html-report-opening.md](./html-report-opening.md)
- ~~13.8 recovery-step UX~~ — [failure-recovery.md](./failure-recovery.md)
- ~~13.9 telemetry consent integration~~ — [telemetry-consent-integration.md](./telemetry-consent-integration.md)
- ~~13.10 source locality~~ — [source-locality.md](./source-locality.md)
- ~~13.11 version compatibility~~ — [cli-compatibility.md](./cli-compatibility.md)
- 13.14 clean-install package validation
- ~~Marketplace branding~~ — [marketplace-branding.md](./marketplace-branding.md)
- ~~Marketplace documentation~~ — [marketplace-documentation.md](./marketplace-documentation.md)
- Clean install validation (13.14)

## CLI discovery (Slice 13.2)

Assessment ordering: workspace → **CLI discovery** → consent → progress → one
product CLI invocation. Discovery uses a side-effect-free `version` probe that
does not count as the product invocation. See [cli-discovery.md](./cli-discovery.md).

When discovery fails, [installation guidance](./cli-installation.md) may be
offered; the product command does not continue automatically.

## Implementation

Typed contract: `src/communityWorkflow/`.  
Orchestration session is wired from `extension.ts` for init/assess/report.
