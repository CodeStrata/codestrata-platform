---
title: Install CodeStrata Engine
description: Install and verify CodeStrata Engine using supported Community mechanisms.
---

# Install CodeStrata Engine

Choose one supported path. After install, verify with `codestrata version`.

## Option A — pip (user)

```bash
python3.12 -m pip install --user 'codestrata[mcp]'
codestrata version
```

## Option B — virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install 'codestrata[mcp]'
codestrata version
```

## Option C — from Engine source

Public `codestrata-engine` checkout (or monorepo `engine/` for contributors):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[mcp]'
codestrata version
```

## Verify and diagnose

```bash
codestrata version
codestrata about
codestrata doctor
```

`doctor` checks that the CLI and environment are usable for assessment.
Fix any reported issues before continuing.

## Initialize configuration (when needed)

```bash
codestrata init
```

Creates local Engine configuration (for example `codestrata.toml`) for profiles
and optional providers. You can assess with defaults in many cases; run `init`
when you need project-local configuration.

Next: [First Assessment](./first-assessment).
