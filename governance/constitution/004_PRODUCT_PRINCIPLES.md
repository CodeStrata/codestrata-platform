# 004 — Product Principles

**Status:** Foundation  
**Authority:** Constitution

## Objective

Define product-facing principles that keep CodeStrata trustworthy, usable, and
consistent across CLI, APIs, and reports.

## Scope

Product behavior and customer experience principles. Visual detail lives in
[`governance/assets/DESIGN-SYSTEM.md`](../assets/DESIGN-SYSTEM.md).
Product naming lives in
[BRANDING_GUIDELINES.md](../standards/BRANDING_GUIDELINES.md).

## 1. Trust principles

1. **Deterministic facts are the source of truth**; AI narratives are interpretation.
2. **Show evidence, confidence, coverage, and limitations** where applicable.
3. **Never invent repository facts** in AI or report copy.
4. **Fail safely** — degrade to deterministic output rather than fabricate.

## 2. Consistency principles

| Area | Expectation |
| ---- | ----------- |
| Terminology | Use canonical terms (Repository, Assessment, Engineering Snapshot, …) |
| Naming | Follow [NAMING_CONVENTIONS.md](../standards/NAMING_CONVENTIONS.md) |
| Errors | Actionable messages; no secret leakage |
| Versioning | Consistent version reporting across CLI / API / reports |

<!-- TODO: Publish the canonical terminology glossary in standards. -->

## 3. Usability principles

1. Prefer a clear primary workflow (`assess`) over legacy paths.
2. First-run should work without cloud credentials in deterministic mode.
3. Progress and completion summaries should be predictable across commands.

## 4. Commercial vs Community product principles

- Community Engine delivers valuable standalone assessment.
- Platform adds multi-tenant persistence, RAG, portfolio, and executive
  capabilities without breaking Engine independence.

## 5. References

- [001_PRODUCT_VISION.md](001_PRODUCT_VISION.md)
- [007_AI_PHILOSOPHY.md](007_AI_PHILOSOPHY.md)
- [REPORT_STANDARDS.md](../standards/REPORT_STANDARDS.md)
- [engine/docs/report-generation.md](../../engine/docs/report-generation.md)
