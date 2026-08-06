# Privacy

CodeStrata VS Code Extension (Community Edition) is designed for local Engineering Assessments.

## What this extension does

- Discovers and/or installs **CodeStrata Engine** on your machine
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

See [docs/telemetry.md](docs/telemetry.md) and [docs/analytics.md](docs/analytics.md).
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
