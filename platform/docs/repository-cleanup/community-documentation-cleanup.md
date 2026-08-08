# Community Documentation Cleanup (Slice 16.2)

**Policy:** `repository-documentation-policy:1.0`  
**Verification:** `repository-documentation-verification:1.0.0`  
**Report:** `reports/verification/sv16-2/repository-documentation-verification.json`  
**Scope:** Documentation-only. No runtime / API / schema changes. Slice 16.3 not started.

## Purpose

Make the monorepo comfortable to become public from a **documentation** perspective
for the current **v0.2.0 Community** product, while keeping Platform and historical
knowledge correctly classified (not deleted).

## Authoritative document registry

| Subject | Authority |
| ------- | --------- |
| Monorepo README | `README.md` |
| Installation (Community) | `docs/getting-started/install.md` |
| Release history | `CHANGELOG.md` (portal summary: `docs/reference/release-notes.md`) |
| Community docs hierarchy | `docs/` (`docs/index.md` entry) |
| Monorepo architecture | `ARCHITECTURE.md` |
| Docs portal architecture | `docs/ARCHITECTURE.md` |
| Contributing (monorepo) | `CONTRIBUTING.md` |
| Privacy (Community) | `docs/security/privacy.md` |
| Telemetry (Community portal) | `docs/reference/telemetry.md` |
| Design System | `design-system/` (`design-system/README.md`, tokens under `design-system/tokens/`) |
| VS Code Marketplace listing | `vscode-plugin/README.md` |
| Engine maintainer docs | `engine/docs/README.md` |
| Platform internal docs | `platform/docs/README.md` (INTERNAL) |
| Community Engine license | `engine/LICENSE` |
| Community code of conduct | `engine/CODE_OF_CONDUCT.md` |

Pointers (non-authoritative duplicates) must link to the authority above rather than
restate full procedures.

## Classification legend

| Class | Meaning |
| ----- | ------- |
| ACTIVE | Current Community or clearly scoped maintainer docs |
| GENERATED | Build/export output — do not edit by hand |
| HISTORICAL | Kept for history; not current product guidance |
| EXPORT_ONLY | Staging/export mirrors |
| OWNER_REVIEW_REQUIRED | Needs human decision before public emphasis |
| DELETE_CANDIDATE | Safe to remove in a later cleanup slice (not deleted in 16.2) |
| ARCHIVE_CANDIDATE | Prefer archive marking over deletion |
| STALE | Out-of-date relative to v0.2.0; must not remain ACTIVE without fix |

## Hierarchy rules

1. **Public Community** content lives under `docs/` and is published via VitePress
   (Platform / internal paths excluded from publish).
2. **Engine maintainer** contracts stay under `engine/docs/`.
3. **Platform** docs stay under `platform/docs/` and are INTERNAL — never presented
   as Community capabilities.
4. **Design System** authority is `design-system/`; `governance/assets/DESIGN-SYSTEM.md`
   is historical / non-authoritative for product colour.
5. **Generated** trees (`docs/.vitepress/dist`, `insights/dist`, `.export-staging`)
   are not manually edited.
6. **Historical knowledge** (including AIMF rename history in changelogs) is retained
   and classified — not deleted.

## Cleanup actions in Slice 16.2

- Align root README to **v0.2.0** Community truth and registry links
- Remove active Cursor-extension identity from published Community docs
- Mark unpublished `docs/platform/` and `docs/internal/` clearly
- Strengthen INTERNAL banners on Platform docs index
- Keep ROADMAP as ARCHIVE CANDIDATE
- Establish root SECURITY / CODE_OF_CONDUCT pointers for public readiness
- Verify one authority each for README, installation, release, and docs hierarchy

## Forbidden in this slice

- Runtime / API / schema / unrelated policy edits
- Deleting historical knowledge
- Starting Slice 16.3
- Commit / tag / publish / deploy
