---
title: Engineering Assessments
description: How CodeStrata Engineering Assessments work — deterministic by default.
---

# Engineering Assessments

An **Engineering Assessment** analyzes a repository with CodeStrata Engine and
produces findings, recommendations, and reports grounded in evidence.

## Default path

Deterministic Engineering Intelligence:

```bash
codestrata assess --repo . --output reports --no-ai
```

Rules and evidence run locally. No AI provider is required.

## Optional AI

```bash
codestrata assess --repo . --output reports --with-ai
```

Requires Engine-configured provider credentials. See
[Deterministic vs AI](./deterministic-vs-ai) and [AI Providers](/ai-providers/).

## Outputs

- HTML Engineering Assessment report
- Public JSON artifacts for IDE extensions and automation

Continue: [Understanding Reports](/reports/).
