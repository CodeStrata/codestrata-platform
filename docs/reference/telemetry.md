---
title: Telemetry
description: Community Edition telemetry and analytics posture for Engine and VS Code.
---

# Telemetry

Community Edition telemetry is **privacy-first** and **off by default** for product
transmission.

## Consent lifecycle

| State | Meaning |
| --- | --- |
| `disabled_by_default` | Fresh/default posture; no transmission |
| `allowed_for_session` | Explicit allow for this process/command |
| `denied_for_session` | Explicit deny for this process/command |
| `non_interactive_disabled` | CI/headless/TTY-absent suppression |

Consent is process/command-local and is **not** persisted for the privacy-first
runtime. Non-interactive runs never hang on a prompt.

Engine assess flags:

- `--telemetry-allow`
- `--telemetry-deny`

## Community Cloud

When Community Cloud product transmission is explicitly wired, production
requests use:

`https://api.codestrata.ai`

Telemetry ingest path:

`POST /api/v1/telemetry`

Related consent-gated streams (authenticated; client consent required):

- `/api/v1/assessment-metadata`
- `/api/v1/cli-events`
- `/api/v1/extension-events`
- `/api/v1/ai-usage`

See [Community Cloud API](/reference/community-api/).

Consent does **not** automatically publish Assessment or Engineering Intelligence
reports. Publish eligibility uses an explicit opt-in marker for the publish
command and still requires `--confirm-public-publish`.

## Principles

- No silent enable because Community Cloud, report publishing, or credentials exist
- VS Code consent is command-local, default Deny, and not persisted
- No machine identity or installation identity for Community telemetry
- Telemetry failures must not fail assessment or remove local reports
- Default / denied / non-interactive sessions keep HTTP transport unavailable
- After explicit opt-in with `CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL`, product
  transport targets `https://api.codestrata.ai` (no anonymous ingestion)

## VS Code extension

Eligible assessment commands may prompt for optional, privacy-safe anonymous product
telemetry for that command only. Dismissal or Deny is safe. Discovery, installation
guidance, initialization, report open, doctor, and recovery do not prompt.

There is no separate hidden VS Code telemetry consent setting that overrides the
CLI/privacy-first contract.

See the extension repository privacy materials packaged with the VS Code extension.

## Engine

Engine telemetry follows Engine public contracts: disabled by default, documented
event catalogs where applicable, and no requirement to enable telemetry to assess.

## Related

- [Privacy](/security/privacy)
- [Security](/security/)
- [FAQ](/faq/)
