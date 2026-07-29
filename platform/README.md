# CodeStrata Maintainer Handbook

**Audience:** CodeStrata maintainers and core contributors only.  
**Not** a public marketing, customer, or Community Edition document.

This file lives under `platform/` because the Platform package is private and
never exported. It is the **ecosystem maintainer handbook** for the private
monorepo `codestrata-platform`.

> CodeStrata Engine produces structured Engineering Intelligence.  
> CodeStrata Platform stores, connects, retrieves, and reasons over that intelligence.

---

## 1. Purpose of the private monorepo

`codestrata-platform` is the **single source of truth** for:

* Community Engine development (`engine/`)
* Implemented commercial Platform capabilities (`platform/`)
* Public showcase manifests (`examples/`)
* Internal test fixtures (`test-fixtures/`)
* Plugin placeholders and export automation

Public GitHub repositories are **generated mirrors**. Do not develop in the
mirrors. Land every change here, then export and publish intentionally.

### Actively developed repositories

| Repository | Visibility | Role |
| ---------- | ---------- | ---- |
| `codestrata-platform` | Private | Source of truth (this monorepo) |
| `codestrata-ui` | Private | Commercial UI (separate) |
| `codestrata-site` | Public | Marketing site (separate) |

### Generated public mirrors

| Monorepo path | Public repository |
| ------------- | ----------------- |
| `engine/` | `codestrata-engine` |
| `examples/` | `codestrata-examples` |
| `cursor-plugin/` | `codestrata-cursor` |
| `vscode-plugin/` | `codestrata-vscode` |

Mapping, includes, excludes, and validation commands:
[public-export-manifest.yaml](../public-export-manifest.yaml).

Supporting docs:

* [../ARCHITECTURE.md](../ARCHITECTURE.md) — system architecture
* [../ROADMAP.md](../ROADMAP.md) — current product direction
* [../CONTRIBUTING.md](../CONTRIBUTING.md) — contribution entry points

---

## 2. Repository layout and responsibilities

```text
codestrata-platform/
├── engine/                 # Community Engine (public → codestrata-engine)
├── platform/               # Private RAG + Knowledge Graph (NOT exported)
├── examples/               # Real-world showcase manifests (→ codestrata-examples)
├── test-fixtures/          # Internal language samples + golden mini-reports
├── cursor-plugin/          # Placeholder (→ codestrata-cursor)
├── vscode-plugin/          # Placeholder (→ codestrata-vscode)
├── scripts/                # verify_release, export, security, showcase wrappers
├── tests/architecture/     # Engine ↔ Platform boundary tests
├── public-export-manifest.yaml
├── ARCHITECTURE.md
├── ROADMAP.md
├── CHANGELOG.md
└── CONTRIBUTING.md
```

| Path | Responsibility |
| ---- | -------------- |
| `engine/` | MIT Community CLI, assessment, reports, Engine docs/tests |
| `platform/` | Implemented RAG + persistent KG + extension entry points |
| `examples/` | Showcase manifests, fetch/run scripts, attribution, curated results |
| `test-fixtures/` | Deterministic language fixtures for tests and Engine smoke |
| `cursor-plugin/` | Public placeholder only |
| `vscode-plugin/` | Public placeholder only |
| `scripts/` | Release verification, export, security, packaging smoke, showcase wrappers |
| **This handbook** | Ecosystem operations (export, release, ownership) |

Package-local Platform install and smoke workflows:
[docs/getting-started.md](docs/getting-started.md).

---

## 3. Engine vs Platform ownership

| Rule | Detail |
| ---- | ------ |
| Dependency direction | **Platform → Engine only** |
| Engine imports | Engine must never import `codestrata_platform` |
| Discovery | Platform registers via Engine entry points (`codestrata.cli_extensions`, `codestrata.mcp_extensions`, `codestrata.ai_provider_extensions`, `codestrata.acceptance_extensions`) |
| Community focus | Engine docs and public export stay free of private Platform implementation detail |
| Commercial ownership | RAG and persistent Knowledge Graph live under `platform/` |

Boundary tests: [tests/architecture/test_engine_platform_boundary.py](../tests/architecture/test_engine_platform_boundary.py).

Do not treat speculative surfaces (SSO, billing, hosted multi-tenancy, dashboards)
as implemented product.

---

## 4. Public export workflow

Manifest: [public-export-manifest.yaml](../public-export-manifest.yaml).

Staging output: `.export-staging/<mirror-name>/` (gitignored).

```bash
# Preview
python scripts/export-public-repos.py --dry-run

# Export all mirrors
python scripts/export-public-repos.py

# Export one mirror
python scripts/export-public-repos.py --repo codestrata-engine
python scripts/export-public-repos.py --repo codestrata-examples
python scripts/export-public-repos.py --repo codestrata-cursor
python scripts/export-public-repos.py --repo codestrata-vscode
```

| Mirror | Source | Visibility | Must include | Must exclude |
| ------ | ------ | ---------- | ------------ | ------------ |
| `codestrata-engine` | `engine/` (+ smoke fixture) | public | CE package, docs, `test-fixtures/sample-js-app` | `platform/`, secrets, reports |
| `codestrata-examples` | `examples/` | public | real-world manifests/scripts, attribution, curated expected-results | `sample-*-app`, sample-reports, fetched trees |
| `codestrata-cursor` | `cursor-plugin/` | private | Extension package + docs | `node_modules`, `*.vsix`, `out/` |
| `codestrata-vscode` | `vscode-plugin/` | private | Extension package + docs | `node_modules`, `*.vsix`, `out/` |
| `codestrata-docs` | `docs/` | private | VitePress site source | `node_modules`, `.vitepress/dist` |

Export scripts **do not** create remotes, push, or publish.

### How to review diffs

1. Run export into `.export-staging/`
2. Diff against a previous staging directory or a local clone of the public mirror
3. Review added / changed / deleted counts printed by the export script

---

## 5. Export validation (quality gates)

Run from the monorepo root before any release or mirror sync.

**Canonical entry point:**

```bash
python scripts/verify_release.py
# Full Engine fresh-venv export smoke (slower):
python scripts/verify_release.py --full-export-install
# Optional packaging / live acceptance:
python scripts/verify_release.py --with-clean-install
python scripts/verify_release.py --with-acceptance
```

`verify_release.py` runs security → ruff → mypy → pytest (`not network`) →
export → validate-public-exports (`--skip-install` by default).

Or run steps individually:

```bash
python scripts/security_check.py
python scripts/export-public-repos.py
python scripts/validate-public-exports.py
# Faster structural check without engine fresh-venv install:
python scripts/validate-public-exports.py --skip-install

ruff check .
mypy engine/src
pytest
```

### scripts/ inventory (long-term)

| Script | Role |
| ------ | ---- |
| `verify_release.py` | Canonical release / maintainer verification |
| `security_check.py` | Repository security hygiene |
| `export-public-repos.py` | Stage public mirrors |
| `validate-public-exports.py` | Validate staged mirrors |
| `clean_install_smoke.py` | Packaging wheel + fresh-venv smoke |
| `bench_runtime_performance.py` | Performance benchmark harness |
| `fetch_example.py` | Showcase: fetch pinned example (wrapper) |
| `run_showcase.py` | Showcase: fetch + assess (wrapper; network) |

Canonical showcase implementations live under
`examples/real-world/scripts/` (exported with `codestrata-examples`).

Typical expectations:

* `security_check.py` — no findings
* Export staging refreshes cleanly for all four mirrors
* `validate-public-exports.py` — required files present; forbidden globs clean
* `ruff` / `mypy engine/src` / `pytest` — green on the default offline suite

Validation also checks:

* no `platform/` or private artifacts in exports
* required packaging / governance files present
* engine fresh-venv install + CLI assess smoke (uses `test-fixtures/sample-js-app`)
* examples: real-world showcase manifests, fetch/run scripts, THIRD_PARTY
  attribution, and curated expected-results only (no `sample-*-app`, no
  sample-reports, never fetched upstream trees or local reports)
* plugin placeholders only contain allowed files

Network showcase fetches (`pytest -m network`, `scripts/run_showcase.py`) are
**opt-in** and must not gate normal CI.

---

## 6. Release and publish workflow

Maintainers follow this sequence. Do not skip validation.

1. **Develop** in `codestrata-platform` on a feature branch.
2. **Validate** locally (section 5).
3. **Export** mirrors into `.export-staging/`.
4. **Verify exported repositories**
   * Review export script added/changed/deleted summaries
   * Spot-check Engine README / Examples README in staging
   * Confirm no `platform/`, secrets, or `sample-*-app` leakage into examples
5. **Commit** monorepo changes (when explicitly requested).
6. **Push** the monorepo branch / merge per team process.
7. **Tag** only after the monorepo revision is accepted.
8. **Publish** public mirrors from staging in a **separate intentional step**
   (not part of the export scripts):
   1. Validate exports
   2. Sync staging trees into the public mirror clones (scripted in a later phase)
   3. Open PRs on the public mirrors from the sync bot/account
   4. Tag releases from mirror repos only after the platform commit is reviewed

### Emergency fixes without divergence

If a critical fix is needed in a public mirror:

1. **Still land the fix in `codestrata-platform` first**
2. Re-export and re-validate
3. Publish the mirror from staging

Do **not** commit directly to `codestrata-engine` / `examples` / plugin mirrors
except as a last-resort hotfix, and immediately backport to this monorepo in the
same incident window.

---

## 7. Documentation ownership

| Location | Owner / audience | Notes |
| -------- | ---------------- | ----- |
| Root (`README`, `ARCHITECTURE`, `ROADMAP`, `CHANGELOG`, `CONTRIBUTING`) | Ecosystem | Monorepo orientation |
| `engine/docs/` | Community Engine users & contributors | Exported with Engine |
| `platform/docs/` | Platform developers | Private; RAG, KG, getting-started |
| `examples/` | Showcase users & maintainers | Exported as codestrata-examples |
| `test-fixtures/` | Maintainers / tests | Not part of examples export |
| **This handbook** (`platform/README.md`) | Maintainers only | Export, release, ownership |

Prefer linking over copying. If content belongs in Engine CE docs, put it under
`engine/docs/` — not here.

---

## 8. Maintenance principles

1. **Engine stays community focused** — public docs and export must work for
   open-source users without private Platform secrets or implementation dumps.
2. **Platform owns commercial capabilities** — RAG and persistent KG stay under
   `platform/`.
3. **Never duplicate code or documentation** — one canonical home; link elsewhere.
4. **Keep exports clean** — no `platform/`, credentials, fetched showcase trees,
   or raw report directories in public mirrors.
5. **Preserve dependency direction** — Platform → Engine only; enforce with
   architecture tests.
6. **Fixtures ≠ showcases** — language samples in `test-fixtures/`; real-world
   pins in `examples/`.
7. **Pin showcases deliberately** — full commit SHAs only; never floating
   `main`/`master`.

---

## 9. Platform package pointer

For day-to-day Platform package work (install, RAG/KG smoke, tests):

* [docs/getting-started.md](docs/getting-started.md)
* [docs/README.md](docs/README.md)
* [docs/rag/README.md](docs/rag/README.md)
* [docs/knowledge_graph/README.md](docs/knowledge_graph/README.md)
* [docs/architecture/PLATFORM_ARCHITECTURE.md](docs/architecture/PLATFORM_ARCHITECTURE.md)
