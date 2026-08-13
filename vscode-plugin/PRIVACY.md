# Privacy

CodeStrata VS Code Extension (Community Edition) is designed for local
Engineering Assessments.

## Product privacy authority

Canonical Community/Engine privacy documentation:

https://docs.codestrata.ai/security/privacy

This file summarizes extension-local behavior. If anything conflicts, the Docs
page above is authoritative.

## What this extension does

- Discovers a local **CodeStrata Engine** CLI (no automatic install)
- Runs `codestrata` CLI commands against your open workspace
- Reads Engine assessment artifacts under
  `.codestrata-artifacts/assessments/<repository-id>/current/`
- Shows findings, recommendations, and Problems diagnostics in VS Code
- Supports an **explicit** Publish/Share action for the current local report

## What this extension does not do

- Does **not** send source code to CodeStrata as Community telemetry
- Does **not** retain source code beyond temporary editor navigation
- Does **not** store AI provider credentials in extension settings
- Does **not** enable Community collection by default
- Does **not** override Engine-owned consent (CLI and VS Code share the same preference)
- Does **not** publish reports unless you explicitly choose Publish/Share

## Telemetry / assessment insights

Community collection is **disabled by default**. Eligible assessment commands
may prompt when consent is undecided. Choosing Allow persists **v2** consent
through the Engine (`CODESTRATA_HOME`) — the same preference the CLI uses —
covering anonymous usage metrics and privacy-safe assessment insights. Source
code and repository identity stay local. Consent does **not** publish reports.

Disable in CLI or VS Code applies to both surfaces.

See https://docs.codestrata.ai/reference/telemetry,
https://docs.codestrata.ai/security/privacy, and
https://docs.codestrata.ai/security/retention-and-deletion.

Telemetry opt-out does **not** revoke an already published public report.
Local reports under `.codestrata-artifacts/` remain user-controlled.
AI enrichment (if used) goes to the configured provider via the Engine — not
through the VS Code extension as a source-upload path.

Community Cloud production authority for ingest:

https://api.codestrata.ai

## Marketplace

Public distribution:
[CodeStrata for VS Code](https://marketplace.visualstudio.com/items?itemName=CodeStrataAI.codestrata-assessment)
(`CodeStrataAI.codestrata-assessment`, listing 0.2.1).
Extension source is private. Do not treat this repository as a public source listing.
