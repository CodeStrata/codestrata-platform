# CodeStrata Engine (Community Edition)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Edition: Community](https://img.shields.io/badge/edition-Community-brightgreen.svg)](docs/community-edition.md)

> The Engine produces structured engineering intelligence.

Open-source CLI that assesses a software repository and produces deterministic
findings, recommendations, and a self-contained HTML/JSON modernization report.

**Audience:** engineers and engineering leaders evaluating a codebase for
modernization, due diligence, or portfolio discovery.

> **Public mirror.** Prefer changes in the private `codestrata-platform` monorepo;
> this repository is generated for Community distribution.

---

## Why CodeStrata Engine?

| You need | Community Engine delivers |
| -------- | ------------------------- |
| A fast read on stack, risks, and next steps | Local or GitHub `codestrata assess` |
| Evidence you can trust | Deterministic rules (AI optional, never invents findings) |
| Something you can share | Self-contained HTML Report v2 + JSON artifacts |
| Automation | CLI, optional MCP, optional Agent Framework |

**Not in Community Engine:** hosted SaaS, SSO/billing, multi-tenant control planes,
or commercial RAG / persistent Knowledge Graph (those live in the private
Platform package). Details: [docs/community-edition.md](docs/community-edition.md).

---

## How CodeStrata fits together

| Repository | Role | Public? |
| ---------- | ---- | ------- |
| **codestrata-engine** (this repo) | Assessment CLI, reports, Engine docs | Yes |
| **codestrata-examples** | Pinned real-world showcase manifests + fetch scripts | Yes |
| **Platform** (`platform/` in the monorepo) | RAG + persistent Knowledge Graph | Private |

Product statement: *The Engine produces structured engineering intelligence.
The Platform stores, connects, retrieves, and reasons over that intelligence.*

---

## Quick start

Requires **Python 3.12+**.

```bash
git clone https://github.com/sknampally/codestrata-engine.git
cd codestrata-engine

python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
# Cloning does not install the CLI — install the package from this checkout:
python -m pip install -e .
python -m pip install -e ".[dev,mcp]"

python -c "import codestrata; print(codestrata.__file__)"
codestrata version
codestrata assess --repo test-fixtures/sample-js-app --output reports --no-ai
```

If you see `ModuleNotFoundError: No module named 'codestrata'`, activate the
venv and re-run `python -m pip install -e .`.

Open the newest `reports/sample-js-app/<timestamp>/report.html`.

Assess your own tree:

```bash
codestrata assess --repo /path/to/your-app --output reports --no-ai
```

Guides: [docs/quick-start.md](docs/quick-start.md) ·
[docs/installation.md](docs/installation.md) ·
[docs/tutorial.md](docs/tutorial.md).

---

## What an assessment does

```text
codestrata.toml / CLI
        │
        ▼
Local path or GitHub clone
        │
        ▼
Detect technologies + extract facts
        │
        ▼
Repository graph → assessment graph
        │
        ▼
Deterministic rules → findings → recommendations
        │
        ├──────────────────┐
        ▼                  ▼
HTML + JSON reports   optional AI narrative (one Bedrock call)
```

Default mode is **deterministic** (`--no-ai`: zero provider calls). Optional
`--with-ai` adds narrative only; it never rewrites findings or recommendations.

---

## Example workflows

**Config-driven assess** (default `codestrata.toml` points at the bundled JS sample):

```bash
codestrata config validate --config codestrata.toml
codestrata assess --config codestrata.toml --output reports --no-ai
```

**GitHub repository:**

```toml
# codestrata.toml
[repository]
url = "https://github.com/YOUR_ORG/YOUR_REPO"
branch = "main"
```

```bash
codestrata assess --config codestrata.toml --output reports --no-ai
```

**Execution profile** (optional): `--profile local` — see
[docs/configuration-profiles.md](docs/configuration-profiles.md).

**Optional AI narrative** (Bedrock; never rewrites findings):

```bash
aws sso login --profile <profile-name>
codestrata assess --config codestrata.toml --output reports --with-ai
```

**Real-world showcases** (separate public repo): install Engine, then follow
[codestrata-examples](https://github.com/sknampally/codestrata-examples) for
pinned third-party applications assessed on demand.

---

## Output artifacts

```text
reports/<repository-name>/<YYYYMMDD-HHMMSS>/
├── report.html
├── report.json
├── findings.json
├── recommendations.json
├── ai-enrichment.json      # only with successful --with-ai
└── graphs/
```

How to read reports: [docs/report-interpretation.md](docs/report-interpretation.md).

Demo HTML snapshots: [docs/images/](docs/images/).

---

## Supported technologies

| Area | Support |
| ---- | ------- |
| Languages | Java, JavaScript/TypeScript, Python, PHP, C# / .NET |
| Build / deps | Maven, npm, Composer, NuGet / MSBuild |
| CI | GitHub Actions discovery |
| Static analysis | Optional PMD (Java) |
| AI enrichment | Optional Amazon Bedrock Converse |
| Sources | Local filesystem, GitHub HTTPS/SSH |

This public package ships `test-fixtures/sample-js-app` for offline smoke.
Additional language fixtures live in the private monorepo.

---

## Documentation

| Doc | Topic |
| --- | ----- |
| [docs/README.md](docs/README.md) | Docs index |
| [docs/community-edition.md](docs/community-edition.md) | Community scope |
| [docs/cli-reference.md](docs/cli-reference.md) | CLI reference |
| [docs/architecture-guide.md](docs/architecture-guide.md) | Architecture map |
| [docs/mcp/setup.md](docs/mcp/setup.md) | MCP setup |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Troubleshooting |
| [SUPPORT.md](SUPPORT.md) | How to get help |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and
[docs/contributor-guide.md](docs/contributor-guide.md).

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy src
```

---

## License

MIT — see [LICENSE](LICENSE).

## Author

Satish Nampally — https://github.com/sknampally
