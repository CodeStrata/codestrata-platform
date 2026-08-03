# Public OSS Engineering Intelligence Demonstration

Slice **6.11** demonstration artifacts for the commercial Engineering Intelligence
pipeline. This is **not** a SaaS product, website, or customer reporting service.

## Artifacts

| File | Description |
| --- | --- |
| `catalog.json` | Curated public OSS repository catalog (pins + fixture paths) |
| `fixtures/*/report.json` | Canonical Engine assessment reports (schema **1.2**) |
| `engineering-intelligence-report.json` | Website-safe export JSON |
| `engineering-intelligence-report.html` | Self-contained static HTML |
| `export-manifest.json` | Artifact digests and export identity |

## Dataset

Five validated public OSS repositories from the Community qualification suite:

- spring-petclinic (Java)
- full-stack-fastapi-template (Python)
- angular-realworld-example-app (TypeScript)
- BookStack (PHP)
- eShop (C#)

Fixtures are copied assessment `report.json` files. Generation does **not**
rescans repositories, use the network, or invent new intelligence logic.

## Regenerate

From the repository root:

```bash
PYTHONPATH=platform:platform/src:engine/src \
  python -m codestrata_platform.intelligence_reporting.application.oss_demonstration
```

Repeated runs with the same fixtures must produce identical report ID, export ID,
JSON, HTML, and manifest digests.

## Interpretation

This demonstration uses a curated validation dataset. It is not a random sample
and must not be presented as an industry benchmark.
