---
title: First Assessment
description: Run a deterministic Engineering Assessment and open the HTML report.
---

# First Assessment

Deterministic assessment is the default. It does not call AI providers.

## Assess a repository

From a repository you want to assess:

```bash
codestrata assess --repo . --no-ai
```

Useful flags:

| Flag | Purpose |
| ---- | ------- |
| `--no-ai` | Deterministic only (recommended default) |
| `--quiet` | Suppress stage progress |
| `--json-summary` | Machine-readable completion JSON on stdout |
| `--telemetry-allow` / `--telemetry-deny` | Session bridge / deny only — `--telemetry-allow` does **not** create consent (optional; off by default) |

```bash
codestrata assess --repo . --no-ai --quiet --json-summary
```

## Locate artifacts

Reports land under:

```text
.codestrata-artifacts/assessments/<repository-id>/current/
```

A prior successful run may remain under `previous/`. Typical files:

- `assessment.html` — interactive Engineering Assessment
- `assessment.json` — machine-readable assessment artifact
- `heads/` — per-head assessment artifacts

Example (macOS):

```bash
open .codestrata-artifacts/assessments/*/current/assessment.html
```

## Understand findings

Open `assessment.html` and review:

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
codestrata assess --repo . --with-ai
```

Details: [AI Providers](/ai-providers/) (Bedrock and OpenAI setup, troubleshooting).

## IDE extension

After your first CLI assessment, install the Community IDE client:

- [Install CodeStrata for VS Code](https://marketplace.visualstudio.com/items?itemName=CodeStrataAI.codestrata-assessment)
  (`CodeStrataAI.codestrata-assessment`)
- Docs: [VS Code Extension](/extensions/vscode)

Continue: [Next Steps](./next-steps).
