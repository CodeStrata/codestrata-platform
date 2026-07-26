# Phase 4.4.3 — Dependency Hygiene Dogfood Review

**Date:** 2026-07-24 (updated by **4.4.3A**)  
**Artifacts:** `reports/dogfood-phase-4-4-3/` (original); correction dogfood in
`reports/dogfood-phase-4-4-3a/` — see
[PHASE_4_4_3A_UNRESOLVED_VERSION_PRECISION_REVIEW.md](PHASE_4_4_3A_UNRESOLVED_VERSION_PRECISION_REVIEW.md).

## Recommendation

**Accept Phase 4.4.3** with the **4.4.3A precision correction** applied.
Gradle `${webjars*Version}` must not remain as findings solely because the
collector did not resolve them.

## CodeStrata (post-4.4.3A)

| Field | Value |
| ----- | ----- |
| Section status | `partially_succeeded` |
| Dependency findings | 2 |
| Source roles | test/fixture |

| Rule | Disposition |
| ---- | ----------- |
| `dependency.unresolved-version` on `${missing.version}` | **True positive** — proven under Maven local property contract |
| `dependency.duplicate-declaration` on `httpx` | **True positive** — fixture duplicate |

## Spring Petclinic (post-4.4.3A)

| Field | Value |
| ----- | ----- |
| Dependency findings | **0** |
| Diagnostics | Gradle interpolation unsupported-resolution retained |
| Prior 4.4.3 findings | 3 × `${webjars*Version}` — **withdrawn as findings**; retained as coverage diagnostics |

## Historical note (pre-4.4.3A)

Original 4.4.3 dogfood incorrectly accepted Petclinic Gradle interpolations as
findings. That disposition is superseded by 4.4.3A.
