# Branding Guidelines

**Status:** Foundation  
**Authority:** Standards (naming only)

## Objective

Standardize product naming and direct all visual branding to the Design System.

## Scope

Official product names and technical package/CLI names.  
**Visual design, tokens, typography, and brand artwork are not defined here.**

## 1. Official names

| Name | Use |
| ---- | --- |
| **CodeStrata** | Product name |
| **CodeStrata Engine** | Community Engine |
| **CodeStrata Platform** | Commercial Platform |

**Do not** treat “AI” as part of the product name. AI is a capability.

## 2. Package / CLI names (technical)

| Technical | Notes |
| --------- | ----- |
| `codestrata` | Python package / CLI (not renamed casually) |
| `codestrata-platform` | Platform package (private) |

## 3. Surfaces to keep naming-consistent

- CLI version / about output
- HTML report headers / footers
- OpenAPI `info.title` / descriptions
- MCP server display name
- Package `description` fields

Keep aligned with Product Experience Phase 9.3 branding sweep and
[`../assets/DESIGN-SYSTEM.md`](../assets/DESIGN-SYSTEM.md).

## 4. Design System & assets (authoritative)

**Single Design System authority:**

[`governance/assets/DESIGN-SYSTEM.md`](../assets/DESIGN-SYSTEM.md)

**Asset package** (preserve as uploaded):

[`governance/assets/README.md`](../assets/README.md)

Do not duplicate Design System rules in this file or elsewhere under
`governance/standards/`.

## 5. References

- [001_PRODUCT_VISION.md](../constitution/001_PRODUCT_VISION.md)
- [DESIGN-SYSTEM.md](../assets/DESIGN-SYSTEM.md)
- [`../assets/DESIGN-SYSTEM.md`](../assets/DESIGN-SYSTEM.md) (authority)
- [engine/src/codestrata/reporting/branding.py](../../engine/src/codestrata/reporting/branding.py)
