# Privacy

CodeStrata VS Code Extension (Community Edition) is designed for local
Engineering Assessments.

## Product privacy authority

Canonical Community/Engine privacy documentation:

https://docs.codestrata.ai/security/privacy

This file summarizes extension-local behavior. If anything conflicts, the Docs
page above is authoritative for Community product data behavior.

## What this extension does

- Discovers a local **CodeStrata Engine** CLI (no automatic install)
- Runs `codestrata` CLI commands against your open workspace
- Reads Engine assessment artifacts under
  `.codestrata-artifacts/assessments/<repository-id>/current/`
  (for example `assessment.html`, `assessment.json`, `heads/`)
- Shows findings, recommendations, and Problems diagnostics in VS Code
- Supports an **explicit** Publish/Share action for the current local report

## What this extension does not do

- Does **not** send source code to CodeStrata as Community telemetry
- Does **not** retain source code beyond temporary editor navigation
- Does **not** store AI provider credentials in extension settings
- Does **not** enable telemetry by default
- Does **not** persist telemetry consent for privacy-first flows
- Does **not** publish reports unless you explicitly choose Publish/Share

## Telemetry (privacy-first)

Anonymous product telemetry is **disabled by default**. Eligible assessment
commands may prompt once for **command-local** consent (default Deny; not
saved). Telemetry opt-in does **not** publish reports.

See https://docs.codestrata.ai/security/privacy,
https://docs.codestrata.ai/security/source-locality,
https://docs.codestrata.ai/architecture/community-cloud,
https://docs.codestrata.ai/ai-providers/,
https://docs.codestrata.ai/reference/telemetry,
https://docs.codestrata.ai/security/data-collection, and
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
