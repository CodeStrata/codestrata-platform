# Branding and Terminology Audit

> **ARCHIVE CANDIDATE (Phase 12.2.2)** — Retained for history. Do not treat as current public documentation. Prefer CHANGELOG / governance reports / public `docs/` for current guidance. File was **not deleted**.


**Phase:** 9.1 audit · **Status update:** Phase 9.3 applied (working tree)

**Governance authority:** [`BRANDING_GUIDELINES.md`](../../../governance/standards/BRANDING_GUIDELINES.md), [`DESIGN-SYSTEM.md`](../../../governance/assets/DESIGN-SYSTEM.md)

## Canonical names (target)

| Name | Use |
| ---- | --- |
| **CodeStrata** | Product |
| **CodeStrata Platform** | Commercial Platform |
| **CodeStrata Engine** | Community Engine |
| **CodeStrata VS Code Extension** | Future / placeholder |
| **CodeStrata Cursor Extension** | Future / placeholder |

AI is a **capability**, not part of the product name.

## Phase 9.3 resolution (customer-visible)

| Surface | Before (9.1) | After (9.3) |
| ------- | ------------ | ----------- |
| HTML brand / footer | “CodeStrata AI …” | **CodeStrata** / Community Edition |
| OpenAPI title | “CodeStrata Commercial Platform API” | **CodeStrata Platform API** |
| CLI `enterprise` help | “Enterprise Knowledge Graph” | **Platform Engineering Knowledge Graph** |
| Assess / report title | “Modernization Assessment” | **Engineering Assessment** |
| MCP instructions | modernization knowledge server | Engineering Assessment + optional AI messaging |
| Package descriptions | mixed modernization wording | Engine / Platform Engineering Intelligence |

Historical AIMF / “AI Modernization Factory” references remain only in changelog /
archive context (tests continue to guard user docs).

## Remaining notes

- Technical identifiers (`enterprise` CLI group, module paths) are retained for
  compatibility; customer copy uses Engineering Knowledge Graph / Platform.
- Phase 9.1 audit rows below are preserved as evidence of the pre-9.3 state.

## Current inconsistencies observed in 9.1 (historical)

| Surface | Observed | Severity |
| ------- | -------- | -------- |
| `reporting/branding.py` | `BRAND_NAME = "CodeStrata AI"` | P1 (fixed) |
| HTML title/footer (golden path) | “CodeStrata AI …” | P1 (fixed) |
| CLI `version` / `about` | `CodeStrata` | OK |
| `package_metadata.PRODUCT_NAME` | `CodeStrata` | OK |
| OpenAPI title | “CodeStrata Commercial Platform API” | P2 (fixed in 9.3) |
| MCP name | `CodeStrata` | OK |
| CLI group `enterprise` | “Enterprise Knowledge Graph” | P1 (help relabeled) |
| Assess default `--report-title` | “Modernization Assessment” | P2 (fixed) |
| HTML report name | “Engineering Assessment” | Prefer this |
| Help / docs “Community Edition” | Mixed with Engine | P2 (aligned) |
| Phase numbers in CLI help | “Phase 4.2” etc. | P2 (reduced in 9.2) |
| AIMF / AI Modernization Factory | Historical; tests guard docs | Keep archived only |
| Internal CEIM | OK if customer sees “Engineering Snapshot” | P2 if leaked raw |
