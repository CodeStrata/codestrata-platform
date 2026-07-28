---
title: Configuration
description: CodeStrata Engine configuration overview for Community assessments.
---

# Configuration

```bash
codestrata init
```

Typical local configuration uses `codestrata.toml` and optional `.env` for
overrides. Shell environment variables take precedence.

## Profiles and providers

Engine configuration profiles select assessment and optional AI provider settings.
Platform credentials are not required for Community assessment.

## Secrets

- Never commit API keys
- Prefer environment variables for secrets
- Do not place Platform secrets in Community Engine config unless intentionally
  integrating with Platform publish flows (separate from local assess)
