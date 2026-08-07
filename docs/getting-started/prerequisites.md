---
title: Prerequisites
description: What you need before installing CodeStrata Engine.
---

# Prerequisites

| Requirement | Notes |
| ----------- | ----- |
| Python **3.12+** | Required for CodeStrata Engine |
| Git | Required only when assessing a remote GitHub URL |
| Terminal access | Install and run the `codestrata` CLI |
| Optional IDE | VS Code for the Community extension workflow |

You do **not** need:

- CodeStrata Platform credentials
- Cloud database access
- AI provider keys (unless you later enable `--with-ai`)

When you do enable AI, validate first:

```bash
codestrata ai doctor
```

See [AI Providers](/ai-providers/) for Bedrock and OpenAI setup.

Next: [Install Engine](./install).
