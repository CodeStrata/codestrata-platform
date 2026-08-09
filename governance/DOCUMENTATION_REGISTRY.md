# Documentation Registry (Authoritative)

**Status:** Active  
**Scope:** Pre-Epic-17 repository documentation audit  
**Supersedes:** [`DOCUMENTATION_INVENTORY.md`](DOCUMENTATION_INVENTORY.md) (historical Phase 8.9.3 snapshot)  
**Version posture:** Community product **v0.2.0**  
**Does not start Epic 17.** No commit / tag / publish / deploy / remotes / cutover.

## Purpose

One authoritative classification of Markdown and documentation-like files so
historical, internal, verification, and public Community docs cannot compete as
current truth.

## Classification legend

| Class | Meaning |
| ----- | ------- |
| `PUBLIC_ACTIVE` | Community-facing / package-root docs suitable for public export |
| `INTERNAL_ACTIVE` | Maintainer / Platform / Infrastructure / Insights / Governance / Knowledge |
| `VERIFICATION_ACTIVE` | Active verification package READMEs and related docs |
| `HISTORICAL` | Retained evidence; must not compete with current authorities |
| `GENERATED` | Regenerable reports / machine output (prefer `reports/`) |
| `DUPLICATE` | Overlapping subject; non-authoritative copy (role-split OK) |
| `STALE` | Content claims outdated; update or mark historical |
| `ORPHAN` | Not referenced by docs, source, verification, or release tooling |
| `DELETE_CANDIDATE` | Clear temp / scratch / abandoned planning (removed when confirmed) |
| `OWNER_REVIEW_REQUIRED` | Keep until an explicit owner decision |

## Inventory counts (filtered)

Excludes `.git`, `.venv`, `node_modules`, `.terraform`, `__pycache__`, build
dists, `.vscode-test`, and vendored `validation/repos/**`.

| Metric | Count |
| ------ | ----: |
| Total documentation-like files (`.md`/`.txt`/`.rst`/`.adoc`) | 788 |
| PUBLIC_ACTIVE | 292 |
| INTERNAL_ACTIVE | 271 |
| VERIFICATION_ACTIVE | 97 |
| GENERATED (`reports/` etc.) | 66 |
| HISTORICAL | 22 |
| OWNER_REVIEW_REQUIRED (heuristic residual) | 40 |

Unfiltered noise (not counted above): vendored `validation/repos/**`,
`.vscode-test/**`, `.venv/**`.

## Authoritative documents (one per subject)

| Subject | Authority | Class |
| ------- | --------- | ----- |
| Monorepo README / Community entry | `README.md` | PUBLIC_ACTIVE |
| Installation (Community) | `docs/getting-started/install.md` | PUBLIC_ACTIVE |
| Release history | `CHANGELOG.md` (portal: `docs/reference/release-notes.md`) | PUBLIC_ACTIVE |
| Community docs portal | `docs/` (`docs/index.md`) | PUBLIC_ACTIVE |
| Monorepo / ecosystem architecture | `ARCHITECTURE.md` | PUBLIC_ACTIVE |
| Docs portal architecture | `docs/ARCHITECTURE.md` | PUBLIC_ACTIVE |
| Contributing (monorepo) | `CONTRIBUTING.md` | PUBLIC_ACTIVE |
| Privacy (Community portal) | `docs/security/privacy.md` | PUBLIC_ACTIVE |
| Telemetry (Community portal) | `docs/reference/telemetry.md` | PUBLIC_ACTIVE |
| Design System 1.0 | `design-system/` | PUBLIC_ACTIVE / shared |
| Amber historical brand archive | `governance/assets/` | HISTORICAL |
| VS Code Marketplace listing | `vscode-plugin/README.md` | PUBLIC_ACTIVE |
| Engine maintainer docs | `engine/docs/README.md` | PUBLIC_ACTIVE |
| Platform internal docs | `platform/docs/README.md` | INTERNAL_ACTIVE |
| Infrastructure docs | `infrastructure/docs/` | INTERNAL_ACTIVE |
| Insights docs | `insights/docs/`, `insights/README.md` | INTERNAL_ACTIVE |
| Governance (how we build) | `governance/` | INTERNAL_ACTIVE |
| Engineering knowledge | `knowledge/` | INTERNAL_ACTIVE |
| Documentation classification | **this file** | INTERNAL_ACTIVE |
| Epic 16 documentation cleanup guide | `platform/docs/repository-cleanup/community-documentation-cleanup.md` | INTERNAL_ACTIVE |
| Owner-review debt register | `platform/policies/repository_owner_review_register.json` | INTERNAL_ACTIVE |

## Public vs internal boundary

| Surface | Classification | Export |
| ------- | -------------- | ------ |
| `docs/` Community portal (excl. `platform/**`, `internal/**`) | PUBLIC_ACTIVE | Community docs package |
| `docs/platform/**` | HISTORICAL / unpublished | Excluded (`srcExclude`) |
| `docs/internal/**` | HISTORICAL placeholder | Excluded (`srcExclude`) |
| `engine/docs/**`, Engine package roots | PUBLIC_ACTIVE | Community engine |
| `vscode-plugin/**` package docs | PUBLIC_ACTIVE | Community vscode |
| `examples/**` | PUBLIC_ACTIVE | Community examples |
| `platform/docs/**` | INTERNAL_ACTIVE | Not Community |
| `infrastructure/docs/**` | INTERNAL_ACTIVE | Private export only |
| `insights/docs/**` | INTERNAL_ACTIVE | Private export only |
| `governance/**`, `knowledge/**` | INTERNAL_ACTIVE | Not Community product docs |
| `verification/**` READMEs | VERIFICATION_ACTIVE | Not product docs |

**Result:** Public Community documentation remains Community-only. Platform,
Infrastructure, and Insights documentation remain private/internal. Unpublished
`docs/platform/` retains an ARCHIVE banner for verifier continuity but is not
published.

## Duplicate pairs (role-split; not deleted)

| Pair | Authoritative | Non-authoritative / scoped |
| ---- | ------------- | -------------------------- |
| `ARCHITECTURE.md` vs `docs/ARCHITECTURE.md` | Root = monorepo map | Docs portal architecture only |
| `design-system/` vs `governance/assets/DESIGN-SYSTEM.md` | Design System 1.0 | HISTORICAL amber |
| Root / docs / engine `SECURITY.md` | Package-scoped | Pointers must stay thin |
| `docs/PRIVACY.md` vs `docs/security/privacy.md` | Published portal page | Package-root extraction copy |

## Files deleted (this audit)

| Path | Reason |
| ---- | ------ |
| `docs/internal/security-high-production-vscode-20260730-061625.md` | Generated assessment dump under docs tree |
| `docs/internal/security-detector-precision-audit-vscode.md` | Generated audit report under docs tree |
| `docs/internal/security-context-classification-acceptance.md` | Companion scratch acceptance notes |
| `docs/internal/_audit_vscode_secret_findings.json` | Scratch audit artifact (261KB) |
| `docs/internal/_precision_vscode_security_context.py` | Underscore scratch helper in docs tree |
| `vscode-plugin/PLACEHOLDER.md` | Temporary extraction naming marker |
| `platform/docs/product-experience/PHASE_9_IMPLEMENTATION_PLAN.md` | Abandoned planning output |
| `platform/docs/product-experience/PRODUCT_EXPERIENCE_GAPS.md` | Stale Phase 9.1 backlog |

## Retained as historical (not deleted)

| Path / set | Note |
| ---------- | ---- |
| `governance/DOCUMENTATION_INVENTORY.md` | Superseded snapshot; bannered HISTORICAL |
| `docs/MIGRATION_PLAN.md` | Portal migration evidence; bannered HISTORICAL |
| `docs/platform/index.md` | ARCHIVE / unpublished commercial positioning |
| `docs/internal/README.md` | Placeholder after scratch purge |
| `platform/docs/product-experience/*_AUDIT.md` (+ related) | Phase 9 baseline; README bannered HISTORICAL |
| `governance/assets/` | Amber archive (OR-16.8-005) |
| `ROADMAP.md` | Archive candidate |
| Cursor/AIMF removal verification packages | Historical proof of retirement |

## Stale claims fixed (not deleted)

Epic 16 verification package READMEs no longer claim later slices “not started”
(16.1–16.10 are complete). `platform/docs/repository-cleanup/community-documentation-cleanup.md`
updated accordingly. Governance README Design System pointer corrected to
`design-system/` (amber archive remains historical).

## Orphans / residual owner-review

| Item | Class | Decision |
| ---- | ----- | -------- |
| Platform commercial docs under `platform/docs/{rag,knowledge_graph,...}/` | OWNER_REVIEW_REQUIRED | Keep INTERNAL; commercial prototype posture (OR-16.8-001) |
| Unmarked PE experience notes (non-audit) | HISTORICAL / OWNER_REVIEW | Retain under historical PE README |
| `docs/community/vs-platform.md` | PUBLIC boundary page (unpublished intent) | Keep; do not promote Platform as Community |
| `governance/assets/` mass prune | OWNER_REVIEW_REQUIRED | OR-16.8-005 |
| Governance standards still linking amber `DESIGN-SYSTEM.md` | STALE pointers | Prefer `design-system/`; amber links are historical (no runtime change this audit) |
| Engine validation result `latest_run_id.txt` / summary md | GENERATED-ish residual | Operational artifacts; not Community docs |

## Intentionally not deleted

- Active verification READMEs
- Internal architecture docs (`platform/docs/architecture/`, etc.)
- Useful historical PE audits (bannered)
- Knowledge / governance normative content
- Vendored third-party docs under `validation/repos/`

## Epic 17 boundary

This audit prepares documentation posture for Epic 17. It does **not**:

- start Epic 17
- deploy AWS
- create remotes
- perform repository cutover
- publish packages
- tag or commit
