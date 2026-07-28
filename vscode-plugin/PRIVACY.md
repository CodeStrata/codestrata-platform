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
- Does **not** enable telemetry by default (none shipped in this Community release)
- Does **not** connect to Platform APIs

## Engine relationship

When you run an assessment, **CodeStrata Engine** reads your repository locally
according to Engine documentation and your configuration. Review Engine privacy
and security docs for CLI behavior.

## Credentials

Configure optional AI providers only in Engine (`codestrata.toml` / environment).  
Never confuse AI provider keys with CodeStrata Platform API keys.
