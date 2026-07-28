# Product Experience Baseline & Audit

**Phase:** 9.1  
**Status:** Audit complete (evidence-based; no product changes)  
**Audience:** Maintainers planning Phase 9 implementation

## Purpose

Document the **current** CodeStrata product experience before PE changes.
Findings are grounded in CLI behavior, configuration, implementation paths,
tests, and representative golden-path runs performed in this phase.

## Canonical authorities (do not duplicate)

| Concern | Location |
| ------- | -------- |
| How CodeStrata is built | [`governance/`](../../../governance/) |
| What CodeStrata knows | [`knowledge/`](../../../knowledge/) |
| Design System | [`governance/assets/DESIGN-SYSTEM.md`](../../../governance/assets/DESIGN-SYSTEM.md) |
| Rule Catalog | [`knowledge/RULE_CATALOG.md`](../../../knowledge/RULE_CATALOG.md) |
| Traceability | [`knowledge/TRACEABILITY.md`](../../../knowledge/TRACEABILITY.md) |
| Branding naming (Governance) | [`governance/standards/BRANDING_GUIDELINES.md`](../../../governance/standards/BRANDING_GUIDELINES.md) |

## Document index

| Document | Contents |
| -------- | -------- |
| [CURRENT_USER_JOURNEYS.md](CURRENT_USER_JOURNEYS.md) | Journeys by persona |
| [CLI_AUDIT.md](CLI_AUDIT.md) | Public CLI inventory |
| [CONFIGURATION_AUDIT.md](CONFIGURATION_AUDIT.md) | Config / env / gates |
| [AI_EXPERIENCE_AUDIT.md](AI_EXPERIENCE_AUDIT.md) | AI entry points & behavior |
| [REPORT_EXPERIENCE_AUDIT.md](REPORT_EXPERIENCE_AUDIT.md) | Reports & outputs |
| [API_MCP_AUDIT.md](API_MCP_AUDIT.md) | REST + MCP (9.1 baseline) |
| [API_MCP_EXPERIENCE.md](API_MCP_EXPERIENCE.md) | Phase 9.5 integrator experience |
| [SDK_READINESS.md](SDK_READINESS.md) | Phase 9.7 public SDK readiness (signed) |
| [EXTENSION_READINESS.md](EXTENSION_READINESS.md) | VS Code / Cursor API needs |
| [INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md) | REST / MCP / CLI / report examples |
| Engine documentation portal | [engine/docs/README.md](../../../engine/docs/README.md) (Phase 9.6) |
| Public contract policy | [PUBLIC_CONTRACT_COMPATIBILITY.md](../../../governance/playbooks/PUBLIC_CONTRACT_COMPATIBILITY.md) |
| [BRANDING_TERMINOLOGY_AUDIT.md](BRANDING_TERMINOLOGY_AUDIT.md) | Naming drift |
| [COMMUNITY_PLATFORM_EXPERIENCE.md](COMMUNITY_PLATFORM_EXPERIENCE.md) | Boundaries |
| [PRODUCT_EXPERIENCE_GAPS.md](PRODUCT_EXPERIENCE_GAPS.md) | P0–P3 backlog |
| [PHASE_9_IMPLEMENTATION_PLAN.md](PHASE_9_IMPLEMENTATION_PLAN.md) | Recommended sequence |

## Canonical architecture (preserved)

```text
Assessment → Assessment Intelligence → Published CEIM → Engineering Knowledge Graph
→ Repository Retrieval → Repository Answering → Portfolio Intelligence
→ Portfolio Retrieval → Portfolio Answering → Executive Intelligence
→ On-read Presentation → On-read Strategic Roadmap
```

This audit does **not** change that flow.

## Golden-path status (this audit)

| Path | Result | Notes |
| ---- | ------ | ----- |
| Doctor with repo `codestrata.toml` | Pass | Checks OK |
| Assess `--no-ai` with repo `codestrata.toml` | **Fail mid-run** | `ai.bedrock.answer_model` empty→None validation (P0) |
| Assess `--no-ai` with packaged defaults.toml | Pass | HTML+JSON written |
| Assess `--with-ai` without AWS creds | Pass with fallback | Reports written; `AI status: fallback` |
| Missing config file | Exit 1 | Clear message |
| MCP tools (default config) | Blocked | `[mcp].enabled=false` |
| Platform OpenAPI | Not live-hit | Documented from code/tests |
| Remote GitHub scan | Not run | Needs network/token |

## Related

- Engine user docs: [`engine/docs/README.md`](../../../engine/docs/README.md)
- Platform maintainer docs: [`../README.md`](../README.md)
