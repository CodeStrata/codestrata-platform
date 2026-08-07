---
title: First Assessment
description: Run a deterministic Engineering Assessment and open the HTML report.
---

# First Assessment

Deterministic assessment is the default. It does not call AI providers.

## Assess a repository

From a repository you want to assess:

```bash
codestrata assess --repo . --output reports --no-ai
```

Useful flags:

| Flag | Purpose |
| ---- | ------- |
| `--no-ai` | Deterministic only (recommended default) |
| `--quiet` | Suppress stage progress |
| `--json-summary` | Machine-readable completion JSON on stdout |

```bash
codestrata assess --repo . --output reports --no-ai --quiet --json-summary
```

## Locate artifacts

Reports land under:

```text
reports/<repository-name>/<timestamp>/
```

Typical files:

- `report.html` — interactive Engineering Assessment
- JSON summary and related public artifacts used by IDE extensions

Example (macOS):

```bash
open "$(ls -dt reports/*/* | head -1)/report.html"
```

## Understand findings

Open `report.html` and review:

- Executive summary
- Findings with evidence and severity
- Recommendations

See [Understanding Reports](/reports/) and
[Findings & Recommendations](/reports/findings).

## Optional AI enhancement

AI is optional. It uses **your** Engine provider credentials (for example Bedrock
or OpenAI) — not Platform API keys.

```bash
codestrata ai
codestrata ai doctor
codestrata assess --repo . --output reports --with-ai
```

Details: [AI Providers](/ai-providers/) (Bedrock and OpenAI setup, troubleshooting).

## IDE extension

After your first CLI assessment, install the Community IDE client:

- [VS Code Extension](/extensions/vscode)

Continue: [Next Steps](./next-steps).
