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
| **6.1** Modernization Advisor (BYO LLM narrative) | **In progress** |
| **6.2** GitHub Repository Acquisition (ephemeral public checkouts) | Next after 6.1 |
| Beyond 6.2 | Deferred pending engineering-leader feedback |

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

**Goal:** Bring CodeStrata intelligence into day-to-day engineering leadership
and workflows. Engine remains the deterministic source of truth; optional AI
and acquisition paths are fail-soft and bounded.

| Subphase | Intent |
| -------- | ------ |
| **6.1** | **Modernization Advisor** — unified `AiEnrichmentResult` narrative for CTOs/VPs over deterministic assessment; Bedrock + OpenAI providers; renderer-independent domain model; fail-soft |
| **6.2** | **GitHub Repository Acquisition** — secure ephemeral checkouts for public repositories |

**6.1 exit criteria (directional):**

* `--with-ai` produces Modernization Advisor output from one provider call
* Advisor never invents findings; citations stay within allowed IDs
* HTML and JSON consume the same enrichment domain model
* AI failure never blocks deterministic reports

**Out of 6.1:** RAG, Knowledge Graph chat, agents, Platform hosting, GitHub
acquisition (those belong elsewhere or in 6.2+).

---

## Deferred (post-MVP)

Explicitly **out of current Phase 6 MVP** until engineering-leader feedback
prioritizes them:

* Broader language / build ecosystem expansion beyond current JS, Java, Python,
  PHP, and C# / .NET coverage
* Modernization Intelligence pack (former Phase 4.10 direction)
* Hosted multi-tenancy, SSO, billing, commercial dashboards
* Additional AI providers, hybrid-retrieval productization beyond current
  Platform capabilities
* Cursor / VS Code plugin implementation (placeholders only today)
* Automated public-mirror publish/sync bots (export staging exists; publish is
  intentional and separate)
* Diff-aware PR review surfacing and CI check annotations (post-6.2)

---

## How to use this file

* Update Phase 6 rows as subphases start or complete
* Do **not** reintroduce long historical checklists here
* Record shipped work in [CHANGELOG.md](CHANGELOG.md)
* Operational how-to: [platform/README.md](platform/README.md)
