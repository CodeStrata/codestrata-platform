---
title: CLI Reference
description: Common CodeStrata Engine CLI commands for Community Edition.
---

# CLI Reference

Common Community commands:

```bash
codestrata --version
codestrata version
codestrata about
codestrata doctor
codestrata init
codestrata ai
codestrata ai doctor
codestrata assess --repo . --no-ai
codestrata assess --repo . --with-ai
```

## Version semantics

| Surface | Meaning |
| --- | --- |
| `codestrata --version` / `codestrata version` | **Installed package/runtime** version (candidate may be `0.2.0`) |
| `GET /api/v1/community/status` → `engine_version` | Latest **published** GitHub Release for `CodeStrata/codestrata-engine`, with candidate fallback per Community Status contract |

These are different concepts. After the published GitHub Release `v0.2.0`,
Community Status `engine_version` is `0.2.0`. Do not hard-code Status.

Artifacts default under
`.codestrata-artifacts/assessments/<repository-id>/current/`
(`assessment.html`, `assessment.json`, `heads/`).

## Assess flags

| Flag | Purpose |
| ---- | ------- |
| `--repo` | Repository path or supported remote |
| `--output` | Optional override for the assessments output root (default: `.codestrata-artifacts/assessments`) |
| `--no-ai` | Deterministic only (**default**) — no AI provider invocation |
| `--with-ai` | Optional AI enrichment via configured provider (Bedrock / OpenAI / OpenRouter) |
| `--model-id` | Optional model override (requires `--with-ai`; required for OpenRouter when unset in config) |
| `--quiet` | Less progress output |
| `--json-summary` | Completion JSON on stdout |
| `--telemetry-allow` | Session/frontend bridge only — does **not** create consent or override Disabled |
| `--telemetry-deny` | Session deny for this assess (privacy-first) |

## AI commands

| Command | Purpose |
| ------- | ------- |
| `codestrata ai` | Optional AI onboarding (Bedrock / OpenAI / OpenRouter, current config, next steps) |
| `codestrata ai --provider bedrock\|openai\|openrouter` | Concise setup guide for that AI provider |
| `codestrata ai doctor` | Validate AI configuration without assessing (never prints secrets) |

See [AI Providers](/ai-providers/) and [Source Locality](/security/source-locality).
Provider selection for assess is configuration-driven (`[ai].provider`); credentials
stay in the AWS chain / environment — never in report artifacts or telemetry.

## Telemetry / assessment insights (opt-in)

Community collection is **disabled by default**. When preference is undecided
and the terminal is interactive, `assess` may ask once (v2 scope):

```text
Help improve CodeStrata?
Share anonymous usage metrics and privacy-safe assessment insights.
Source code and repository identity stay local. Reports are not published.
[y/N]:
```

Enter defaults to No. **Yes** persists **v2** (usage + assessment insights).
**Legacy v1** users keep lifecycle-only scope until they accept a broader
upgrade prompt — never silently expanded.

```bash
codestrata telemetry status
codestrata telemetry status --json
codestrata telemetry enable    # durable v2 Yes
codestrata telemetry disable   # future collection off
codestrata assess --repo . --no-ai --telemetry-allow   # bridge only; not consent
codestrata assess --repo . --no-ai --telemetry-deny
```

`--telemetry-allow` does **not** invent consent or override Disabled. Quiet /
CI runs never prompt; durable v2 may emit approved streams without prompting.

Telemetry / insights opt-in is **not** report-publish authorization. Publishing
is a separate explicit action. Voluntary public-report Yes/No feedback is also
separate from telemetry consent.

```bash
# Interactive (recommended) — one confirmation prompt
codestrata report publish

# Non-interactive / CI
codestrata report publish --confirm-public-publish
# Local/private repository ids (local-*):
codestrata report publish --confirm-public-publish --acknowledge-private-repository

# Successful publish returns: https://reports.codestrata.ai/r/<opaque-id>
```

No AWS account, Secrets Manager access, or hidden telemetry environment variable
is required for normal Community publishing. The Engine authenticates with a
packaged public Community client credential (overridable for operators).

### Telemetry examples

```bash
# Default / disabled (no Community transmission from these flags alone)
codestrata assess --repo . --no-ai

# Explicit process override allow (does not rewrite stored preference)
codestrata assess --repo . --no-ai --telemetry-allow

# Explicit process override deny
codestrata assess --repo . --no-ai --telemetry-deny

# Persist preference
codestrata telemetry enable
codestrata telemetry disable
codestrata telemetry status
```

### AI examples

```bash
# Deterministic default
codestrata assess --repo . --no-ai

# Optional AI enrichment (provider from [ai].provider / docs)
codestrata assess --repo . --with-ai
```

Provider setup: [AI Providers](/ai-providers/). Credentials stay in environment /
cloud chains — never in CLI args or report artifacts.

There is no Engine CLI `report revoke` command in the current surface; revoke
uses authenticated `DELETE /api/v1/reports/<public-id>` (see
[Community Cloud API](/reference/community-api/) and
[Retention and Deletion](/security/retention-and-deletion)).

Canonical docs:

- [Telemetry](/reference/telemetry)
- [Data Collection](/security/data-collection)
- [Privacy](/security/privacy)
- [Retention and Deletion](/security/retention-and-deletion)
- [Community Cloud API](/reference/community-api/)

Deep Engine CLI detail remains in Engine repository documentation. This portal
documents the supported public journey commands only.
