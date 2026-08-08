---
title: Repository Initialization
description: Initialize local CodeStrata Engine configuration for a repository (Community Edition).
---

# Repository Initialization

CodeStrata Engine owns repository configuration. Community workflows (CLI or VS Code)
initialize a local `codestrata.toml` (or equivalent Engine config) without rewriting
your application source.

## When to initialize

Initialize once per repository before the first assessment when no valid Engine
configuration exists.

## CLI

```bash
codestrata init
```

Engine behavior (Community):

- Creates or verifies local configuration
- Preserves a valid existing configuration (repeat-safe)
- Fails closed on invalid or partial configuration rather than forcing overwrite

Exact flags and paths follow the [CLI reference](/reference/cli) and
[Configuration](/reference/configuration).

## VS Code

Use **Initialize Repository** from the CodeStrata command palette. The extension
orchestrates a single Engine init invocation when needed — it does not write
configuration files itself.

## After initialization

Continue with [First Assessment](/getting-started/first-assessment) or
[Running Assessments](/assessments/).
