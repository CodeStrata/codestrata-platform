# CodeStrata Roadmap

> **ARCHIVE CANDIDATE (Phase 12.2.2)** — Retained for history. Do not treat as current public documentation. Prefer CHANGELOG / governance reports / public `docs/` for current guidance. File was **not deleted**.


**Audience:** Maintainers and core contributors.  
**Scope:** Current product direction only. Completed release history lives in
[CHANGELOG.md](CHANGELOG.md). Ecosystem architecture lives in
[ARCHITECTURE.md](ARCHITECTURE.md).

---

## Status

| Phase | Status |
| ----- | ------ |
| **1–4** Analysis foundation & Analysis Intelligence packs | Complete (see CHANGELOG) |
| **5** Repository Knowledge, packaging, monorepo, showcases, docs hygiene | **Complete** |
| **6.1** Modernization Advisor | **Complete** |
| **6.2** GitHub Repository Acquisition | **Complete** |
| **6.3** Customer Report Experience | **Complete** |
| **6.4** Developer Workflow / CI | **Complete** |
| **6.5** Extensibility & Integration | **Complete** |

---

## Phase 5 — Foundation (complete)

Phase 5 delivered the private monorepo foundation used going forward:

* Community Engine packaging and public export automation
* Platform-owned RAG + persistent Knowledge Graph
* Real-world showcase framework and internal `test-fixtures/`
* Security hardening, documentation ownership, maintainer handbook
* Operational `scripts/` surface (`verify_release`, export, security, showcase)

Detailed phase logs were retired from this file; see [CHANGELOG.md](CHANGELOG.md).

---

## Phase 6 — Engineering Workflow Intelligence

| Subphase | Intent |
| -------- | ------ |
| **6.1** | Modernization Advisor |
| **6.2** | GitHub Repository Acquisition (ephemeral public checkouts) |
| **6.3** | Customer Report Experience |
| **6.4** | Developer Workflow — `init` / `doctor` / quiet assess / sample GHA / Quick start |
| **6.5** | Extensibility & Integration — versioned contracts, assess AI registry, analyzer allowlist, `extensions list` |

**6.5 exit criteria (directional):**

* `EXTENSION_API_VERSION` published; CE needs no Platform
* Built-in assess AI providers unchanged via registry
* Empty analyzer allowlist ⇒ built-ins only
* `extensions list` + `doctor --extensions` diagnose load/version/duplicates

---

## Deferred (post-MVP)

* Broader language / build ecosystem expansion
* Hosted multi-tenancy, SSO, billing
* Diff-aware PR review / check annotations
* VS Code plugin implementation (Community); former Cursor extension removed in Epic 12

---

## How to use this file

* Update Phase 6 rows as subphases start or complete
* Record shipped work in [CHANGELOG.md](CHANGELOG.md)
* Operational how-to: [platform/README.md](platform/README.md)
