# Cursor / AI Assistant Instructions

**Status:** Foundation  
**Authority:** AI guidance

## Objective

Tell AI coding assistants how to work in the CodeStrata monorepo without
violating Governance or architecture.

## Scope

Cursor Agent and similar assistants operating on this repository.

## 1. Read order (before changing code)

1. [governance/README.md](../README.md)
2. Relevant constitution docs (especially Architecture, Engineering, Security, AI)
3. [ARCHITECTURE.md](../../ARCHITECTURE.md)
4. Local module README / nearest engineering doc
5. Existing tests for the area

## 2. Hard rules

1. Do not redesign Platform or Engine architecture unprompted.
2. Do not add product capabilities during cleanup / governance / PE-foundation
   phases unless the phase explicitly requires it.
3. Engine must not import Platform.
4. Do not commit secrets; sanitize diagnostics.
5. Do not create git commits unless the user explicitly asks.
6. Prefer existing patterns over new frameworks.

## 3. Phase discipline

Follow the user’s phase objective and deliverable format exactly.
If the phase says “structure only”, do not implement product experience or
feature work.

## 4. Validation

Run the validation steps listed in the phase (often Ruff, targeted pytest,
`verify_release`).

## 5. References

- [PROMPT_TEMPLATE.md](PROMPT_TEMPLATE.md)
- [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md)
- [007_AI_PHILOSOPHY.md](../constitution/007_AI_PHILOSOPHY.md)
- [002_ENGINEERING_CONSTITUTION.md](../constitution/002_ENGINEERING_CONSTITUTION.md)
