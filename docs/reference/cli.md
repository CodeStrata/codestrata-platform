---
title: CLI Reference
description: Common CodeStrata Engine CLI commands for Community Edition.
---

# CLI Reference

Common Community commands:

```bash
codestrata version
codestrata about
codestrata doctor
codestrata init
codestrata assess --repo . --output reports --no-ai
codestrata assess --repo . --output reports --with-ai
```

## Assess flags

| Flag | Purpose |
| ---- | ------- |
| `--repo` | Repository path or supported remote |
| `--output` | Output directory for reports |
| `--no-ai` | Deterministic only |
| `--with-ai` | Optional AI enhancement |
| `--quiet` | Less progress output |
| `--json-summary` | Completion JSON on stdout |

Deep Engine CLI detail remains in Engine repository documentation. This portal
documents the supported public journey commands only.
