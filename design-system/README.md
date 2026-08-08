# CodeStrata Visual Design System

**Slice:** 14.1 — Define CodeStrata Visual Design System  
**Version:** 1.0.0  
**Authority:** Live https://codestrata.ai (captured 2026-08-07)  
**Status:** Definition complete. **No product surface redesign in this slice.**

## Purpose

Authoritative visual language for later Epic 14 slices (14.2–14.12). This package
defines tokens, components, themes, accessibility, responsive rules, and
**surface language contracts**. It does **not** redesign:

- documentation site
- HTML assessment reports
- Engineering Intelligence reports
- VS Code extension UI
- Marketplace assets

## Policies

| Policy | Version |
| ------ | ------- |
| `codestrata-design-system-policy` | 1.0 |
| `codestrata-visual-language-policy` | 1.0 |
| `codestrata-cross-surface-presentation-policy` | 1.0 |
| `codestrata-visualization-policy` | 1.0 |
| `codestrata-report-information-architecture-policy` | 1.0 |
| `codestrata-brand-asset-policy` | 1.0 |
| `codestrata-accessibility-responsive-policy` | 1.0 |

## Package map

| Path | Contents |
| ---- | -------- |
| `tokens/` | Canonical machine-readable token catalog |
| `assets/` | Master brand mark, wordmark, and approved variants (14.10) |
| `contracts/` | Cross-surface presentation / component / consumer / visualization / IA / asset / accessibility / responsive mappings (14.7–14.11) |
| `colors/` | Palette + semantic color docs |
| `typography/` | Type stack and scale |
| `spacing/` | Spacing rhythm |
| `elevation/` | Shadow / elevation |
| `icons/` | Icon style rules |
| `components/` | Reusable component contracts (spec only) |
| `layouts/` | Layout / navigation / grid rules |
| `themes/` | Light (default) + dark (night) themes |
| `accessibility/` | Contrast, focus, keyboard, motion |
| `responsive/` | Breakpoints and behavior |
| `surfaces/` | Visual rules per product surface (define only) |
| `documentation/` | Human-readable design system docs |
| `policies/` | Versioned design policies |
| `source/` | Website capture provenance |

## Token CSS entry

Canonical CSS variables: [`tokens/tokens.css`](tokens/tokens.css)

## Verification

`verification/visual_design_system/`  
Schema: `codestrata-visual-design-system-verification:1.0.0`  
Report: `reports/verification/sv14-1/`

## Explicit non-goals (Slice 14.1)

- No commit / tag / publish / deploy
- Slice **14.2** not started
- No application of tokens to product surfaces in this slice
