---
title: Install CodeStrata Engine
description: Install and verify CodeStrata Engine using supported Community mechanisms.
---

# Install CodeStrata Engine

Choose one supported path. After install, verify with `codestrata version`.

## Option A — GitHub Release wheel (v0.2.0)

```bash
python3.12 -m pip install --user \
  https://github.com/CodeStrata/codestrata-engine/releases/download/v0.2.0/codestrata-0.2.0-py3-none-any.whl
codestrata version
```

PyPI `pip install codestrata` is not the published v0.2.0 channel until
`codestrata==0.2.0` is on the Python Package Index.

## Option B — virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install \
  https://github.com/CodeStrata/codestrata-engine/releases/download/v0.2.0/codestrata-0.2.0-py3-none-any.whl
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

## VS Code

After the Engine CLI is installed, you can also
[Install CodeStrata for VS Code](https://marketplace.visualstudio.com/items?itemName=CodeStrataAI.codestrata-assessment)
(`CodeStrataAI.codestrata-assessment`) from Visual Studio Marketplace.
The extension is a thin client of the CLI; it does not replace Engine install.
Extension source is private.

Next: [First Assessment](./first-assessment).
