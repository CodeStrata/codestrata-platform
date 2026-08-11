---
title: Engineering Intelligence Reports
description: Portfolio / multi-repository Engineering Intelligence Reports (EIR) versus single-repository Engineering Assessments.
---

# Engineering Intelligence Reports

**Engineering Intelligence** is the portfolio / multi-repository layer.

| Layer | Scope | Primary output |
| ---- | ----- | -------------- |
| **Engineering Assessment** | Single repository | Assessment Report (`assessment.html` / JSON) |
| **Engineering Intelligence** | Portfolio / multiple repositories | Engineering Intelligence Report (**EIR**) |

An Engineering Assessment does **not** automatically create an EIR. EIR generation
is a separate portfolio workflow that aggregates existing assessment outcomes —
it does not perform a hidden repository rescan.

## Community layout

```text
.codestrata-artifacts/
  assessments/<repository-id>/{current,previous}/   # Engineering Assessment
  intelligence/<portfolio-id>/{current,previous}/   # Engineering Intelligence (EIR)
```

Assessment HTML may include an **Assessment Overview** display head
(schema identity `engineering_intelligence` retained). That head summarizes
cross-head assessment signals and is **not** a portfolio EIR package. On-disk modular assessment
artifacts under `heads/*.json` are the eight completed module files defined by
the Engine artifact layout — do not conflate the HTML display vocabulary with
those eight filenames.

Commercial multi-repository Engineering Intelligence Report packages beyond the
Community artifact layout remain Platform-only and are not documented here as a
Community SaaS product.

## What this page is not

This documentation does **not** describe commercial portfolio dashboards,
organizational Knowledge Graph products, or Platform deployment. Those are outside
Community Edition documentation scope.

## Related

- [Assessment Reports](/reports/)
- [Findings & Recommendations](/reports/findings)
- [JSON Reports](/reference/json-reports)
- [Running Assessments](/assessments/)
- [Source Locality](/security/source-locality)
