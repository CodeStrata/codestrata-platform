# 002 — Engineering Constitution

**Status:** Foundation  
**Authority:** Constitution

## Objective

Establish non-negotiable engineering rules for building and evolving CodeStrata.

## Scope

Applies to CodeStrata Engine, CodeStrata Platform, shared scripts, and exported
Community repositories. Does not replace language-specific coding standards
(see [CODING_STANDARDS.md](../standards/CODING_STANDARDS.md)).

## 1. Core tenets

1. **Deterministic analysis first; AI reasoning second.**
2. **Evidence over assertion** — findings and recommendations must be traceable.
3. **Layered architecture** — respect Domain → Application → Infrastructure /
   Interfaces boundaries.
4. **Engine must not depend on Platform.**
5. **Security and tenancy are defaults**, not opt-in features.
6. **Tests and `verify_release` are release gates**, not optional hygiene.

## 2. Change discipline

| Rule | Guidance |
| ---- | -------- |
| Small, reviewable changes | Prefer phased delivery over large rewrites |
| No silent architecture redesign | Architecture changes require explicit decision + doc updates |
| No capability creep in cleanup phases | Cleanup phases must not add product features |
| Prefer fixing root causes | Avoid compatibility shims unless intentional and documented |

<!-- TODO: Add RFC / ADR process for material architecture changes. -->

## 3. Quality gates

Canonical verifier: [scripts/verify_release.py](../../scripts/verify_release.py).

Expected local gates (see [CONTRIBUTING.md](../../CONTRIBUTING.md)):

- Ruff
- mypy (`engine/src` per release script)
- Non-network pytest
- `security_check`

## 4. Ownership

<!-- TODO: Define ownership matrix (Engine vs Platform vs Governance docs). -->

## 5. References

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [003_ARCHITECTURE_PRINCIPLES.md](003_ARCHITECTURE_PRINCIPLES.md)
- [005_SECURITY_PRIVACY_PRINCIPLES.md](005_SECURITY_PRIVACY_PRINCIPLES.md)
- [engine/docs/security/threat-model.md](../../engine/docs/security/threat-model.md)
