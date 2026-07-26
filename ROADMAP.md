# CodeStrata Roadmap

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
| **6.1–6.5** Engineering Workflow Intelligence (MVP) | **Next** |
| Beyond 6.5 | Deferred pending engineering-leader feedback |

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

## Phase 6 — Engineering Workflow Intelligence (MVP)

**Goal:** Bring CodeStrata intelligence into day-to-day engineering workflows,
starting with GitHub pull-request review. Scope below is the **MVP target**;
detailed design may be refined with engineering-leader feedback before each
subphase starts.

| Subphase | Intent |
| -------- | ------ |
| **6.1** | PR / workflow foundations — GitHub context model, auth/config boundaries, safe repository + PR identification |
| **6.2** | Diff-aware assessment — reuse incremental / impact analysis on PR changes; produce PR-scoped findings |
| **6.3** | PR review surfacing — publish review comments or check annotations grounded in existing findings/evidence |
| **6.4** | CI integration — GitHub Actions (or equivalent) entry points; non-interactive assess/report for PRs |
| **6.5** | MVP hardening — acceptance harness, failure modes, docs, and export-safe Community surfaces for the PR workflow |

**MVP exit criteria (directional):**

* A maintainer can run CodeStrata against a pull request and get grounded,
  evidence-backed feedback without inventing facts
* Community Engine remains usable offline / without hosted Platform secrets
* Platform may extend workflow surfaces via existing entry points only
  (Platform → Engine)

---

## Deferred (post-MVP)

Explicitly **out of MVP** until engineering-leader feedback prioritizes them:

* Broader language / build ecosystem expansion beyond current JS, Java, Python,
  PHP, and C# / .NET coverage
* Modernization Intelligence pack (former Phase 4.10 direction)
* Hosted multi-tenancy, SSO, billing, commercial dashboards
* Additional AI providers, hybrid-retrieval productization beyond current
  Platform capabilities
* Cursor / VS Code plugin implementation (placeholders only today)
* Automated public-mirror publish/sync bots (export staging exists; publish is
  intentional and separate)

---

## How to use this file

* Update **Phase 6** rows as subphases start or complete
* Do **not** reintroduce long historical checklists here
* Record shipped work in [CHANGELOG.md](CHANGELOG.md)
* Operational how-to: [platform/README.md](platform/README.md)
