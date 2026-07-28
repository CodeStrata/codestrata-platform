# Engine → Public Docs Migration Plan

This plan classifies existing `engine/docs/` content for eventual adaptation into
the public portal (`docs/`). **No source documents are deleted in this phase.**

## Ownership after migration

| Class | Ownership |
| ----- | --------- |
| A — Engine-specific | Remain in Engine `docs/` (and public `codestrata-engine`) |
| B — Public journey | Adapt into `docs/` (codestrata-docs); Engine may keep a short pointer |
| Link | Public portal links to Engine GitHub docs for depth |
| Merge | Combine overlapping journey pages into one portal section |
| Retire | Only after portal replacement is complete and linked (future phase) |

## Classification (representative)

| Source (`engine/docs/`) | Destination public section | Recommendation | Duplication risk | Ownership after |
| ----------------------- | -------------------------- | -------------- | ---------------- | --------------- |
| `README.md` | Home / nav model | **Adapt** journey index; do not copy monorepo governance links | High if both stay as portals | Portal owns public nav; Engine README becomes Engine-focused |
| `getting-started.md` | `/getting-started/` | **Adapt / merge** | Medium | Portal |
| `quick-start.md` | `/getting-started/` | **Merge** into install + first assessment | High with portal journey | Portal |
| `installation.md` | `/getting-started/install`, `/engine/installation` | **Adapt** | Medium | Portal (journey) + Engine (extras detail) |
| `tutorial.md` | `/getting-started/first-assessment` | **Adapt** | Medium | Portal |
| `report-interpretation.md` | `/reports/` | **Adapt** | Medium | Portal |
| `ai-enrichment.md` | `/ai-providers/` | **Adapt** overview; **retain** provider deep dive in Engine | Medium | Split |
| `community-vs-platform.md` | `/community/vs-platform` | **Adapt** (no governance path links) | High | Portal public; Engine keep technical checklist pointers |
| `community-edition.md` | `/community/` | **Link / adapt** selectively | Low | Engine retains checklist depth |
| `cli-reference.md` | `/reference/cli` | **Adapt** journey commands; **retain** full reference in Engine | Medium | Split |
| `configuration-profiles.md` | `/reference/configuration` | **Adapt** overview; **retain** profiles in Engine | Medium | Split |
| `public-contracts.md` | `/reference/public-contracts` | **Link**; **retain** authoritative contracts in Engine | Low | Engine |
| `report-contract.md` | `/reference/json-reports` | **Link / retain** | Low | Engine |
| `apis.md` | `/reference/api` | **Adapt** positioning; strip Platform-only deep links | Medium | Portal + Engine |
| `mcp/**`, `mcp-server.md` | `/reference/mcp` | **Adapt** overview; **retain** tool catalogs in Engine | Medium | Split |
| `examples.md` | `/community/examples` | **Adapt** | Low | Portal |
| `troubleshooting.md` | `/troubleshooting/` | **Adapt** common issues; **retain** Engine-specific in Engine | Medium | Split |
| `contributor-guide.md` | Engine CONTRIBUTING | **Retain** | Low | Engine |
| `architecture-guide.md`, `architecture/**` | — | **Retain** (A) | — | Engine |
| `analysis-intelligence/**` | — | **Retain** (A) | — | Engine |
| `assessment-framework/**` | — | **Retain** (A); selective public concepts later | — | Engine |
| `security/**` (Engine threat model) | `/security/` only at high level | **Retain** depth in Engine; portal keeps public baseline | Low | Split |
| `extension-architecture.md` | `/extensions/` | **Link**; extensions own READMEs | Low | Extensions + Engine |
| `roadmap.md`, `mvp-*`, `release-readiness.md` | — | **Retain** internal / Engine; **do not** put on public nav | — | Engine |
| `RELEASE_NOTES-*.md` | `/reference/release-notes` | **Link** | Low | Engine releases |

## Principles

1. Public portal = developer journeys and product model.
2. Engine docs = contracts, architecture, contributor and domain depth.
3. No private Platform implementation docs in the public portal.
4. Prefer one canonical public page per journey topic to avoid duplicate SEO URLs.
5. Cleanup and retire steps are **out of scope** for Phase 12.1.
