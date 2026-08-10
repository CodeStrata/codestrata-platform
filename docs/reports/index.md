---
title: Understanding Reports
description: How to read CodeStrata Engineering Assessment HTML and JSON reports.
---

# Understanding Reports

After `codestrata assess`, open:

```text
.codestrata-artifacts/assessments/<repository-id>/current/assessment.html
```

A prior successful run may remain under `previous/`.

## What you will see

- Product header and executive overview of engineering posture
- Assessment heads with status, findings, evidence, and limitations
- Findings with severity labels (not color-only), evidence, and rule identity
- Recommendations prioritized for modernization
- Optional AI sections only when `--with-ai` was used

The HTML report uses the CodeStrata visual design system (light-first teal language)
and remains fully local/offline — no remote fonts, scripts, or stylesheets.

## JSON artifacts

Machine-readable outputs support IDE extensions and CI. See
[JSON Reports](/reference/json-reports) and [Findings](/reference/findings).

## Interpretation tips

1. Start with highest-severity findings.
2. Follow evidence links to file paths and rules.
3. Treat recommendations as engineering guidance grounded in the assessment —
   validate against your codebase before applying changes.

More detail: [Findings & Recommendations](./findings).
