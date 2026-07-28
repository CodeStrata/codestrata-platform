# Prompt Template

**Status:** Foundation  
**Authority:** AI guidance

## Objective

Provide a reusable prompt skeleton for AI-assisted CodeStrata work.

## Scope

Human → assistant task prompts. Not product LLM prompts for Modernization Advisor.

## Template

```text
Phase: <id and title>
Objective: <one paragraph>
Constraints:
- Do not modify product functionality unless required by this phase
- Do not redesign architecture
- Follow governance/ constitution and standards
- No commit unless explicitly requested

In scope: <bullets>
Out of scope: <bullets>

References:
- governance/...
- ARCHITECTURE.md / relevant engineering docs

Validation: <commands>
Deliverable format: <exactly as specified>
```

## Usage notes

1. Attach the smallest relevant file set; prefer paths over pasting large files.
2. Require PASS/FAIL deliverables when the phase defines them.
3. For Governance-only phases, forbid Product Experience and feature work.

<!-- TODO: Add specialized templates for bugfix, security review, and dogfood. -->

## References

- [CURSOR_INSTRUCTIONS.md](CURSOR_INSTRUCTIONS.md)
- [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md)
