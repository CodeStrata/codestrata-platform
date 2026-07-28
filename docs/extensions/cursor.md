---
title: CodeStrata Cursor Extension
description: Ground Cursor Chat and Agent with CodeStrata Engine assessments and generated rules.
---

# CodeStrata Cursor Extension

Bring deterministic **CodeStrata Engine** assessments into **Cursor** Chat / Agent.

## Purpose

Assess with Engine, then project public findings into a generated Cursor rule so
Chat and Agent conversations can stay grounded in Engineering Assessment evidence.

## Engine dependency

The extension is a thin client. Engine performs analysis. The extension consumes
public report artifacts.

## Assessment flow

1. Install extension → open a trusted repository.
2. Detect or install CodeStrata Engine.
3. Run **Engineering Assessment** (deterministic by default).
4. Confirm generated rule and open Chat / Agent.
5. Use suggested questions or copy a grounded conversation prompt.

## Generated rule

Path:

```text
.cursor/rules/codestrata-engineering.mdc
```

| Event | Behavior |
| ----- | -------- |
| Assessment success / Refresh | Create or atomically replace the CodeStrata-managed rule |
| Clear Assessment | Remove only the CodeStrata-managed file |
| User rules | Sibling `.cursor/rules/*` files are preserved |

Treat the file as a local generated artifact (often gitignored) unless your team
intentionally commits shared assessment context.

## Suggested questions

Use extension suggested questions or prompts such as:

*What are the highest-priority engineering risks in this repository?*

## Cursor Chat and Agent usage

- Prefer Copy Conversation Prompt when direct insertion is unavailable.
- Inspect source before applying model-suggested changes.

## Grounding limitations

Cursor answers may still include model inference. CodeStrata findings must not be
invented. Truncation and grounding limits are stated inside the generated rule.

## Optional AI

Engine `--with-ai` remains optional. Extension settings default to deterministic
assessment.

## Generated-rule governance

- Only the CodeStrata-managed rule file is replaced.
- Foreign rule files are not overwritten.
- Review before commit.

## Privacy and security

See [Security](/security/) and [Privacy](/security/privacy).

## Detailed reference

[codestrata-cursor](https://github.com/sknampally/codestrata-cursor)
(public mirror when published).
