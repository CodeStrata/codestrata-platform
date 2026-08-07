# Privacy

CodeStrata VS Code Extension (Community Edition) is designed for local Engineering Assessments.

## What this extension does

- Discovers a local **CodeStrata Engine** CLI (no automatic install)
- Runs `codestrata` CLI commands against your open workspace
- Reads public Engine report artifacts (`report.json`, findings, HTML report)
- Shows findings, recommendations, and Problems diagnostics in VS Code

## What this extension does not do

- Does **not** send source code to CodeStrata Platform
- Does **not** retain source code beyond temporary editor navigation
- Does **not** store AI provider credentials in extension settings
- Does **not** enable telemetry by default
- Does **not** persist telemetry consent or generate installation IDs
- Does **not** connect to Platform APIs

## Telemetry (privacy-first, Slice 9.13+)

Anonymous product telemetry is **disabled by default**. Eligible commands
(`codestrata.assess`, `codestrata.assessWithAi`) may prompt once for
**command-local** consent (default Deny; not saved). Transport is unavailable
in this Community release (no HTTP, no queue, no endpoint settings). Cross-client
principle parity with the Engine CLI is verified in Slice 9.14
(`verification/privacy_first_telemetry/`). Epic 9 completion is verified in
Slice 9.15 (`verification/privacy_first_telemetry_completion/`). Production
collection is **not operational**.

See [docs/telemetry.md](docs/telemetry.md), [docs/analytics.md](docs/analytics.md),
and [docs/community-workflow.md](docs/community-workflow.md) (Slice 13.1
orchestration; consent remains command-local). CLI discovery is local-only and
does not log executable paths or raw probe output in stable diagnostics
([docs/cli-discovery.md](docs/cli-discovery.md)). Installation guidance is
user-triggered and does not run package managers or persist install state
([docs/cli-installation.md](docs/cli-installation.md)).
Repository initialization is explicit (`codestrata.init`), Engine-authored, and
does not trigger telemetry, analytics, assessment, or AI
([docs/repository-initialization.md](docs/repository-initialization.md)).
Assessment requires an initialized repository and compatible CLI before
command-local telemetry consent
([docs/assessment-execution.md](docs/assessment-execution.md)).
Assessment progress is indeterminate Notification UI after consent
([docs/assessment-progress.md](docs/assessment-progress.md)).
HTML reports open locally only after user action
([docs/html-report-opening.md](docs/html-report-opening.md)).
Failure messages use privacy-safe what/why/next recovery guidance
([docs/failure-recovery.md](docs/failure-recovery.md)) without paths,
CLI output, stack traces, or credentials.
Epic 10 privacy verification:
[`../../verification/anonymous_analytics_privacy/`](../../verification/anonymous_analytics_privacy/).
Epic 10 completion (Slice 10.9):
[`../../verification/anonymous_analytics_completion/`](../../verification/anonymous_analytics_completion/).
Anonymous analytics remain contracts-only; production collection is **not operational**.

## Engine relationship

When you run an assessment, **CodeStrata Engine** reads your repository locally
according to Engine documentation and your configuration. Review Engine privacy
and security docs for CLI behavior.

## Credentials

Configure optional AI providers only in Engine (`codestrata.toml` / environment).  
Never confuse AI provider keys with CodeStrata Platform API keys.

Consent is requested only after assessment readiness (Slice 13.9); see [docs/telemetry-consent-integration.md](docs/telemetry-consent-integration.md).

Authoritative source-locality contract: [docs/source-locality.md](docs/source-locality.md). CLI–extension compatibility diagnostics never include paths, stdout/stderr, environment, or credentials ([docs/cli-compatibility.md](docs/cli-compatibility.md)). When AI enrichment is enabled, the local Engine may send provider request content to the configured AI provider.
