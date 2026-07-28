# AI Readiness Knowledge

**Status:** Foundation (Phase 8.9.2)  
**Domain:** `ai`

## Purpose

Define what makes a codebase and operating model ready for safe, useful AI augmentation.

## Why this domain exists

AI capabilities amplify existing engineering quality and risk; readiness must be explicit.

## Scope

**In scope**

- AI readiness concepts for repositories and teams
- Grounding, citation, and hallucination risk concepts
- Data/privacy boundaries for AI use
- Evaluation and human-in-the-loop expectations

**Out of scope**

- Product AI philosophy for building CodeStrata (see governance)
- Provider SDK implementation details
- Model training recipes

## Relationship to other domains

| Domain | Relationship |
| ------ | ------------ |
| [security](../security/README.md) | Secrets, data leakage, and prompt-injection adjacent risks |
| [documentation](../documentation/README.md) | Docs quality affects AI grounding |
| [architecture](../architecture/README.md) | Clear boundaries improve AI-assisted change |
| [compliance](../compliance/README.md) | AI usage constraints and records |

## Domain documents

| Document | Role |
| -------- | ---- |
| [CONCEPTS.md](CONCEPTS.md) | Stable Concept IDs for this domain |
| [RULES.md](RULES.md) | Purpose of engineering rules in this domain |
| [FINDINGS.md](FINDINGS.md) | What findings mean here |
| [RECOMMENDATIONS.md](RECOMMENDATIONS.md) | Recommendation philosophy |
| [MATURITY_MODEL.md](MATURITY_MODEL.md) | Intended maturity structure |
| [REFERENCES.md](REFERENCES.md) | External standards and references |

## Future evolution

Keep provider-neutral; separate readiness knowledge from CodeStrata product AI features.

## Boundaries

- This folder is **engineering knowledge**, not implementation.
- Do not place Python, SQL, APIs, tests, or product code here.
- Implementation under `engine/` / `platform/` should eventually trace to these concepts.
