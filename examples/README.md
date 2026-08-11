# CodeStrata Examples

[![Related: Engine](https://img.shields.io/badge/requires-codestrata--engine-blue.svg)](https://github.com/CodeStrata/codestrata-engine)

Pinned **real-world open-source showcases** for demonstrating CodeStrata on
recognized applications — without vendoring third-party source into this
repository.

**Audience:** engineers and engineering leaders who want realistic assessment
demos; maintainers who refresh pinned revisions.

> **Public mirror** of `codestrata-platform/examples`. Prefer changes in the
> private monorepo.

---

## Why this repository?

| Need | This repo provides |
| ---- | ------------------ |
| Credible demos | Spring PetClinic, .NET eShop, Laravel RealWorld |
| Reproducible runs | Exact commit SHAs in manifests (never floating `main`) |
| Safe automation | Fetch scripts that refuse arbitrary URLs and skip installs |
| Bounded artifacts | Curated `expected-results/` summaries (not raw report trees) |
| Standalone config | Root `codestrata.toml` so assess works without a monorepo |

Language sample apps used in automated tests are **not** published here; they
remain Engine `test-fixtures/` (Community ships `sample-js-app` only).

---

## Relationship to other CodeStrata repos

| Repository | Role |
| ---------- | ---- |
| [codestrata-engine](https://github.com/CodeStrata/codestrata-engine) | Assessment CLI you must install first |
| **codestrata-examples** (this repo) | Showcase manifests, fetch scripts, attribution, curated summaries |
| Platform (private) | Portfolio / RAG — not required for baseline showcases |

Product statement: *The Engine produces structured engineering intelligence.
The Platform stores, connects, retrieves, and reasons over that intelligence.*

---

## Repository structure

```text
.
├── README.md
├── codestrata.toml         # Community config for showcase assess
├── real-world/
│   ├── manifests/          # one YAML per showcase (pinned SHA required)
│   ├── scripts/            # portable fetch + showcase runners
│   ├── MANIFEST_SCHEMA.md
│   ├── THIRD_PARTY.md      # attribution (no endorsement implied)
│   └── README.md
└── expected-results/       # curated summaries per showcase
```

---

## Showcases

| ID | Project | License | Typical runtime |
| -- | ------- | ------- | --------------- |
| `spring-petclinic` | Spring PetClinic | Apache-2.0 | moderate |
| `dotnet-eshop` | Microsoft .NET eShop | MIT | slow |
| `laravel-realworld` | Laravel RealWorld (layered) | MIT | fast |

Attribution: [real-world/THIRD_PARTY.md](real-world/THIRD_PARTY.md).  
Curated results: [expected-results/](expected-results/).

---

## Getting started

### Prerequisites

* Python 3.12+
* `git` on `PATH`
* [codestrata-engine](https://github.com/CodeStrata/codestrata-engine) installed
  (`codestrata` on `PATH`)
* Network access to GitHub for the fetch step
* Optional: [Install CodeStrata for VS Code](https://marketplace.visualstudio.com/items?itemName=CodeStrataAI.codestrata-assessment)
  (`CodeStrataAI.codestrata-assessment`) to run assessments from the editor.
  These showcases remain CLI-first.

Baseline showcases use `--profile community --no-ai` (no AI credentials).

### Install Engine (once)

```bash
git clone https://github.com/CodeStrata/codestrata-engine.git
cd codestrata-engine
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
codestrata version
```

### Fetch and assess (from this repository)

```bash
git clone https://github.com/CodeStrata/codestrata-examples.git
cd codestrata-examples

python real-world/scripts/fetch_example.py --list
python real-world/scripts/fetch_example.py spring-petclinic

codestrata assess \
  --repo .codestrata-examples/spring-petclinic \
  --output reports/showcases/spring-petclinic \
  --profile community \
  --no-ai
```

One-shot (fetch + assess + summary):

```bash
python real-world/scripts/run_showcase.py spring-petclinic
```

Fetched trees land under `.codestrata-examples/` (gitignored). Assessment
output lands under `reports/showcases/` (gitignored). Never commit upstream
source or raw report directories.

This repository ships a root `codestrata.toml` so those commands work without
any parent monorepo configuration.

More detail: [real-world/README.md](real-world/README.md).

---

## What is not included

* CodeStrata-owned `sample-*-app` language fixtures (except Engine's bundled JS sample)
* Golden mini-app `sample-reports/`
* Fetched third-party source trees
* Local assess report directories, caches, or credentials

---

## Maintainers: refreshing pins

Bump `commit_sha` + `pinned_on` in the manifest, re-run the showcase, update
`expected-results/` and `THIRD_PARTY.md`. Never pin floating branches or tags.
Schema: [real-world/MANIFEST_SCHEMA.md](real-world/MANIFEST_SCHEMA.md).
