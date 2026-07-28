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
codestrata assess --repo . --output reports --no-ai
codestrata assess --repo . --output reports --with-ai
```

## Assess flags

| Flag | Purpose |
| ---- | ------- |
| `--repo` | Repository path or supported remote |
| `--output` | Output directory for reports |
| `--no-ai` | Deterministic only |
| `--with-ai` | Optional AI enhancement (your Bedrock or OpenAI credentials) |
| `--quiet` | Less progress output |
| `--json-summary` | Completion JSON on stdout |

## AI commands

| Command | Purpose |
| ------- | ------- |
| `codestrata ai` | Optional AI onboarding (Bedrock / OpenAI, current config, next steps) |
| `codestrata ai --provider bedrock\|openai` | Concise setup guide for that AI provider |
| `codestrata ai doctor` | Validate AI configuration without assessing (never prints secrets) |

See [AI Providers](/ai-providers/) for Bedrock and OpenAI setup.

## Telemetry (opt-in)

Anonymous telemetry is **disabled by default**.

```bash
codestrata telemetry status
codestrata telemetry enable
codestrata telemetry disable
codestrata telemetry reset
codestrata telemetry show
```

See [Privacy](/security/privacy).

Deep Engine CLI detail remains in Engine repository documentation. This portal
documents the supported public journey commands only.
