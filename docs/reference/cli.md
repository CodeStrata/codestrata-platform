---
title: CLI Reference
description: Common CodeStrata Engine CLI commands for Community Edition.
---

# CLI Reference

Common Community commands:

```bash
codestrata version
codestrata about
codestrata doctor
codestrata init
codestrata ai
codestrata ai doctor
codestrata assess --repo . --no-ai
codestrata assess --repo . --with-ai
```

Artifacts default under
`.codestrata-artifacts/assessments/<repository-id>/current/`
(`assessment.html`, `assessment.json`, `heads/`).

## Assess flags

| Flag | Purpose |
| ---- | ------- |
| `--repo` | Repository path or supported remote |
| `--output` | Optional override for the assessments output root (default: `.codestrata-artifacts/assessments`) |
| `--no-ai` | Deterministic only |
| `--with-ai` | Optional AI enhancement (your Bedrock or OpenAI credentials) |
| `--quiet` | Less progress output |
| `--json-summary` | Completion JSON on stdout |
| `--telemetry-allow` | Process-local Community telemetry allow (privacy-first) |
| `--telemetry-deny` | Process-local Community telemetry deny (privacy-first) |

## AI commands

| Command | Purpose |
| ------- | ------- |
| `codestrata ai` | Optional AI onboarding (Bedrock / OpenAI, current config, next steps) |
| `codestrata ai --provider bedrock\|openai` | Concise setup guide for that AI provider |
| `codestrata ai doctor` | Validate AI configuration without assessing (never prints secrets) |

See [AI Providers](/ai-providers/) for Bedrock and OpenAI setup.

## Telemetry (opt-in)

Anonymous product telemetry is **disabled by default**. For `assess`, use
privacy-first process-local consent:

```bash
codestrata assess --repo . --no-ai --telemetry-allow
codestrata assess --repo . --no-ai --telemetry-deny
codestrata telemetry status
```

Legacy preference commands (`codestrata telemetry enable|disable|show|reset`)
remain for compatibility only and do **not** authorize the privacy-first assess
runtime.

See [Privacy](/security/privacy) and [Community Cloud API](/reference/community-api/).

Deep Engine CLI detail remains in Engine repository documentation. This portal
documents the supported public journey commands only.
