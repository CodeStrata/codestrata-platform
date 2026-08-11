---
title: Getting Started
description: End-to-end journey from install to your first Engineering Assessment with CodeStrata Engine.
---

# Getting Started

This journey takes you from a clean machine to a local **Engineering Assessment**
with **CodeStrata Engine**. Deterministic assessment is the default; optional AI
enhancement is covered at the end.

## Journey

1. [Prerequisites](./prerequisites)
2. [Install CodeStrata Engine](./install)
3. Verify installation (`codestrata version`)
4. Run `codestrata doctor`
5. Initialize configuration (`codestrata init`) where needed
6. [Assess a repository](./first-assessment)
7. Locate generated artifacts
8. Open the HTML report
9. Understand findings and recommendations
10. Optional AI setup
11. Install an IDE extension — [Next steps](./next-steps)

```text
pip / uv / pipx  →  codestrata version
                 →  codestrata doctor
                 →  codestrata init   (optional first time)
                 →  codestrata assess --no-ai
                 →  open .codestrata-artifacts/assessments/<repository-id>/current/assessment.html
```

## Product model

| Name | Role |
| ---- | ---- |
| **CodeStrata** | Product family |
| **CodeStrata Engine** | Community assessment engine (this journey) |
| **CodeStrata Platform** | Commercial organizational product |
| **Engineering Assessment** | Single-repository analysis and Assessment Report |
| **Engineering Intelligence** | Portfolio / multi-repository layer; Engineering Intelligence Report (EIR) |
| **Community Edition** | Community distribution of Engine and clients |

Continue with [Prerequisites](./prerequisites).
