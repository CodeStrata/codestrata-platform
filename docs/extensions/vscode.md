---
title: CodeStrata VS Code Extension
description: Run Engineering Assessments from VS Code with CodeStrata Engine discovery, findings, and reports.
---

# CodeStrata VS Code Extension

Run local **Engineering Assessments** without leaving VS Code.

## Purpose

Bring Engine CLI assessments into the editor: progress, findings explorer,
recommendations, diagnostics, and HTML report access.

## Installation

1. Install **CodeStrata** from the VS Code Marketplace (or Install from VSIX).
2. Open a repository folder.
3. On first run, the extension detects **CodeStrata Engine** or offers guided install.
4. Run your first Engineering Assessment.

Manual Engine install if needed:

```bash
python3.12 -m pip install --user 'codestrata[mcp]'
codestrata version
```

## Engine dependency

The extension requires CodeStrata Engine. It does not analyze source independently.

## Automatic Engine discovery

Resolution order typically:

1. Configured executable (`codestrata.engine.executable`)
2. Workspace `.venv`
3. Active Python environment
4. `PATH`

Guided install uses supported mechanisms (`uv tool`, `pipx`, or `pip --user`).

## First assessment

Use **Run Engineering Assessment** (deterministic / `--no-ai` by default).

## Findings, recommendations, diagnostics, reports

After a successful assessment the extension loads public artifacts into:

- Findings tree
- Recommendations view
- Editor diagnostics
- Open HTML report command

## Optional AI

**Run Engineering Assessment with AI** uses Engine provider configuration.
Credentials are **not** stored in the extension.

## Privacy and security

- Local Engine execution
- No Platform requirement for Community assessment
- See [Security](/security/) and [Privacy](/security/privacy)

## Detailed reference

Repository and packaging docs:
[codestrata-vscode](https://github.com/CodeStrata/codestrata-vscode)
(public mirror when published).
