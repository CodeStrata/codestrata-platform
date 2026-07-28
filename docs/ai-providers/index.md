---
title: AI Providers
description: Optional AI enhancement for CodeStrata Engine using your provider credentials.
---

# AI Providers

AI is an **optional capability** of CodeStrata Engine. Deterministic assessment
(`--no-ai`) is the default and does not require provider keys.

## When to use AI

Use `--with-ai` when you want optional enrichment such as modernization advisor
content on top of deterministic findings.

```bash
codestrata assess --repo . --output reports --with-ai
```

## Providers

Engine supports developer-configured providers (for example Bedrock and OpenAI)
via Engine configuration and environment variables. Install the matching extras
when needed (`bedrock`, `openai`).

## What AI is not

- Not the product name (“CodeStrata AI” is not used)
- Not a substitute for CodeStrata Platform
- Not required for Community Edition assessments

Never put Platform API keys in Engine AI configuration. See
[Community vs Platform](/community/vs-platform).
