# Phase 9 Implementation Plan

> **ARCHIVE CANDIDATE (Phase 12.2.2)** — Retained for history. Do not treat as current public documentation. Prefer CHANGELOG / governance reports / public `docs/` for current guidance. File was **not deleted**.


**Phase:** 9.1 planning output  
**Constraint:** Do not implement these phases in 9.1.

## Principles

1. Preserve canonical intelligence pipeline (CEIM → … → on-read Presentation/Roadmap).
2. No assessment/intelligence/retrieval/answering behavior changes unless a PE phase explicitly requires UX-safe fixes (e.g., P0 config abort).
3. Governance + Knowledge remain authorities; PE implements experience against them.
4. Small, independently testable slices.

## Recommended sequence

### Phase 9.2 — CLI, configuration, diagnostics, onboarding

**Goals:** Unblock first scan; clarify help; standardize errors/exit codes.

- Fix PE-P0-01 / PE-P0-02 (answer_model / validation UX)
- Tier CLI help (Primary / Advanced / Platform / Maintainer)
- Doctor improvements (MCP enablement, AI optional checks)
- Config validation messages aligned with `init`/`doctor`
- Exit-code contract documentation + tests

**Exit criteria:** Fresh Community path `init → doctor → assess --no-ai` succeeds on sample fixture with packaged or fixed defaults; P0 closed.

### Phase 9.3 — Branding, terminology, report identity

**Goals:** Align names with Governance; unify assessment titles.

- Replace user-visible “CodeStrata AI” with **CodeStrata**
- Align report title defaults to Engineering Assessment
- Relabel Enterprise CLI toward Platform
- Disambiguate Engine roadmap vs Strategic Roadmap

**Exit criteria:** HTML/CLI/about/OpenAPI naming consistent with branding guidelines; golden HTML grep clean.

### Phase 9.4 — Report experience & Design System integration

**Goals:** Improve HTML/JSON usability without redesigning intelligence content.

- Consume Design System tokens/assets from `governance/assets/`
- Navigation, confidence/coverage callouts, Community/Platform footer clarity
- Print/a11y pass against Design System

**Exit criteria:** Report rendering tests + visual checklist vs Design System; no pipeline changes.

### Phase 9.5 — API & MCP experience

**Goals:** Integrator clarity.

- Complete OpenAPI tags/summaries/examples
- Document Community MCP vs Platform tools
- Auth/error envelope consistency messaging
- Feature-flag operator reference

**Exit criteria:** OpenAPI inventory test extended; MCP discovery docs accurate.

**Status (9.5):** Complete — see [API_MCP_EXPERIENCE.md](API_MCP_EXPERIENCE.md) and
[SDK_READINESS.md](SDK_READINESS.md).

### Phase 9.6 — Documentation portal readiness (not full portal)

**Goals:** Prep IA and Community-facing guides; no full portal build unless scoped elsewhere.

- Source-retention & privacy statements per edition
- Quick-start paths that match CLI
- Cross-links to Governance/Knowledge (no duplication)

**Exit criteria:** Doc inventory links valid; Community quick-start dogfood passes.

**Status (9.6):** Complete — developer portal index at
[engine/docs/README.md](../../../engine/docs/README.md) with journey navigation,
Getting Started / Quick Start / Community vs Platform / APIs / Examples, and
updated troubleshooting.

### Phase 9.7 — Public SDK / API readiness (gate)

**Goals:** Freeze customer contracts for external consumers.

- Versioning policy, changelog discipline, example clients
- Only after 9.2–9.5 stabilizations

**Exit criteria:** Explicit “ready for public SDK” checklist signed off in Governance playbooks.

**Status (9.7):** Complete —
[PUBLIC_CONTRACT_COMPATIBILITY.md](../../../governance/playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md),
[SDK_READINESS.md](SDK_READINESS.md),
[EXTENSION_READINESS.md](EXTENSION_READINESS.md),
[INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md).

## Mapping gaps → phases

| Gap IDs | Phase |
| ------- | ----- |
| PE-P0-01, PE-P0-02, PE-P1-04, PE-P1-07, PE-P2-02/03/06/07/08 | 9.2 |
| PE-P1-01, PE-P1-02, PE-P1-06, PE-P2-01/04 | 9.3 |
| PE-P2-05 + report UX | 9.4 |
| PE-P1-03 + API/MCP | 9.5 |
| PE-P1-05 + docs | 9.6 |
| PE-P3-03 | 9.7 |

## Explicit non-goals for Phase 9 PE track

- New intelligence domains or rules
- Architecture redesign
- Community repository extraction
- Full documentation portal (Phase 12+)
- Changing CEIM / on-read purity rules
