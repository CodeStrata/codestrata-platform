# 007 — AI Philosophy

**Status:** Foundation  
**Authority:** Constitution

## Objective

Define how AI is used inside CodeStrata products and how AI assistants may help
build CodeStrata.

## Scope

Product AI capabilities (Modernization Advisor, answering, embeddings) and
development-time AI (Cursor, coding agents). Naming: AI is a **capability**, not
part of the product name.

## 1. Product AI principles

1. **AI never invents repository facts.**
2. **Deterministic assessment remains valid without AI.**
3. **AI output is labeled** as interpretation / advisor content.
4. **Provider neutrality** — Bedrock, OpenAI, and deterministic providers must
   not change the meaning of findings.
5. **Budget and failure modes** — timeouts, throttling, and auth failures degrade
   safely with sanitized diagnostics.

## 2. Where AI is allowed

| Area | Allowed role |
| ---- | ------------ |
| Modernization Advisor | Narrative over deterministic evidence |
| Repository / Portfolio answering | Grounded answers with citations |
| Embeddings / retrieval | Similarity search only |
| Rule evaluation / finding IDs | **Not allowed** — remain deterministic |

<!-- TODO: Expand grounding / citation requirements for answering surfaces. -->

## 3. Development-time AI principles

1. AI assistants must follow `governance/` and existing architecture docs.
2. Prefer small, validated diffs; do not redesign architecture unprompted.
3. Do not introduce secrets into commits, logs, or examples.
4. Use [CURSOR_INSTRUCTIONS.md](../ai/CURSOR_INSTRUCTIONS.md) and
   [REVIEW_CHECKLIST.md](../ai/REVIEW_CHECKLIST.md).

## 4. Anti-patterns

- Using AI to “fill in” missing evidence
- Treating model output as a Finding without deterministic backing
- Embedding provider credentials in docs or fixtures
- Renaming the product to include “AI” in customer-facing brand

## 5. References

- [ARCHITECTURE.md](../../ARCHITECTURE.md) — Engineering philosophy
- [004_PRODUCT_PRINCIPLES.md](004_PRODUCT_PRINCIPLES.md)
- [PROMPT_TEMPLATE.md](../ai/PROMPT_TEMPLATE.md)
