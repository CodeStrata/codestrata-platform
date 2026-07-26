# CodeStrata Engine (Community Edition)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Edition: Community](https://img.shields.io/badge/edition-Community-brightgreen.svg)](docs/community-edition.md)

> **Public mirror of `codestrata-platform/engine`.** Do not edit this repository
> directly — changes must land in the private monorepo and be re-exported.
> See the monorepo doc `docs/public-export.md`.

## What is CodeStrata?

CodeStrata is a Python CLI that:

1. Scans a local or GitHub repository
2. Detects technologies and extracts structural facts
3. Builds knowledge graphs (repository, engineering knowledge, assessment)
4. Runs deterministic rules → findings → recommendations
5. Optionally calls Amazon Bedrock **once** for narrative enrichment
6. Writes self-contained HTML Report v2 plus machine-readable JSON artifacts

Use it for modernization discovery, demos, and engineering due diligence.

**Community Edition** is the open-source product in this repository. Enterprise /
Platform services (SSO, billing, multi-tenancy) are out of scope — see
[docs/community-edition.md](docs/community-edition.md).

---

## Community vs future Enterprise / Platform

| Capability | Community Edition | Future Enterprise / Platform |
| ---------- | ----------------- | ---------------------------- |
| Local / GitHub repository assess | Yes | Yes |
| Deterministic findings & recommendations | Yes | Yes |
| HTML Report v2 + JSON artifacts | Yes | Yes |
| Local knowledge store & MCP | Yes (optional extras) | Yes |
| Optional Bedrock AI enrichment | Yes | Yes |
| Execution profiles | Yes | Yes |
| Enterprise Knowledge Graph (local YAML) | Not in public engine export (Platform/monorepo) | Expanded |
| Portfolio / multi-repo governance | Placeholder | Planned |
| SSO / RBAC / audit control plane | Not included | Planned |
| Billing / hosted multi-tenancy | Not included | Planned |

---

## Features (Community Edition)

* Local path and public/private GitHub repository assessment
* Technology detection for **Java**, **JavaScript/TypeScript**, **Python**,
  **PHP**, and **C# / .NET**
* Dependency evidence (Maven / npm / Composer / NuGet)
* Deterministic Rule Engine and Recommendation Engine
* Self-contained **HTML Report v2** (no CDN) + JSON artifacts
* Deterministic mode (zero AI calls) and optional AI mode (exactly one Bedrock call)
* Optional PMD static analysis for Java
* Execution profiles (`community` / `local` / `bedrock` / `openai`; `enterprise` profile is monorepo/Platform)
* Local knowledge store, FastMCP server, and Agent Framework
* Incremental assessment (opt-in)
* Extension hook for future Platform Enterprise KG (not shipped in public export)

---

## Architecture

```text
                    codestrata.toml / CLI
                           │
                           ▼
              Local path or GitHub clone
                           │
                           ▼
              Phase 1 analysis (detect + analyzers)
                           │
                           ▼
         Repository Inventory → Repository Graph
                           │
                           ▼
         Knowledge Pipeline ← Engineering Knowledge Graph
                           │
                           ▼
                   Assessment Graph
                           │
                           ▼
              Rule Engine → findings.json
                           │
                           ▼
         Recommendation Engine → recommendations.json
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
     Deterministic HTML/JSON    optional AI enrichment
        (report.html v2)         (one Bedrock call)
                                        │
                                        ▼
                                 ai-enrichment.json
```

Deeper design notes: [ARCHITECTURE.md](../ARCHITECTURE.md),
[docs/architecture-guide.md](docs/architecture-guide.md), and [docs/](docs/).

---

## Installation

Requires **Python 3.12+**. Full guide: [docs/installation.md](docs/installation.md).

Cloning the repository does **not** install the `codestrata` command. If you see
`ModuleNotFoundError: No module named 'codestrata'`, create a venv and install the
package editable from the repo root:

```bash
git clone https://github.com/sknampally/codestrata.git
cd codestrata

python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
# optional Bedrock + MCP + tests:
python -m pip install -e ".[dev,bedrock,openai,mcp]"
```

Verify the install points at this checkout:

```bash
python -c "import codestrata; print(codestrata.__file__)"
codestrata --version
codestrata version
codestrata about
codestrata assess --help
```

---

## Quick Start (local repo)

Short path: [docs/quick-start.md](docs/quick-start.md) · full tutorial:
[docs/tutorial.md](docs/tutorial.md).

```bash
# Bundled sample apps (JS / Python / Java / PHP / C#)
codestrata assess --repo examples/sample-js-app --output reports --no-ai
codestrata assess --repo examples/sample-python-app --output reports --no-ai
codestrata assess --repo examples/sample-java-app --output reports --no-ai
codestrata assess --repo examples/sample-php-app --output reports --no-ai
codestrata assess --repo examples/sample-csharp-app --output reports --no-ai

# Or your checkout
codestrata assess --repo /path/to/your-app --output reports
```

Open the newest `reports/<repo-name>/<timestamp>/report.html`.
How to read it: [docs/report-interpretation.md](docs/report-interpretation.md).

Config-driven equivalent (default `codestrata.toml` points at the JS sample):

```bash
codestrata config validate --config codestrata.toml
codestrata assess --config codestrata.toml --output reports --no-ai
```

---

## Quick Start (GitHub repo)

```toml
# codestrata.toml
[repository]
url = "https://github.com/YOUR_ORG/YOUR_REPO"
branch = "main"
```

```bash
codestrata assess --config codestrata.toml --output reports
```

### Execution profiles

Select secure defaults with an execution profile (`community` by default):

```bash
codestrata config profile --config codestrata.toml
codestrata config validate --config codestrata.toml
codestrata config effective --config codestrata.toml
codestrata assess --config codestrata.toml --profile local --output reports
```

See [docs/configuration-profiles.md](docs/configuration-profiles.md) for
precedence (`CLI > env > TOML > profile defaults`) and provider-specific
settings.

Private HTTPS repos: set a token in `.env` (never commit secrets) and reference
it from config—see [examples/README.md](../examples/README.md).

---

## AI mode

Deterministic mode is the default (`--no-ai`). AI mode requires AWS credentials
that can call Bedrock, plus a model ID:

```bash
aws sso login --profile <profile-name>
codestrata assess --config codestrata.toml --output reports --with-ai
```

Configure profile/region/model in `codestrata.toml`:

```toml
[aws]
profile = "<profile-name>"
region = "us-east-1"

[ai]
provider = "bedrock"

[ai.bedrock]
model_id = "amazon.nova-lite-v1:0"
```

| Mode | Provider calls | Enrichment artifact |
| ---- | -------------- | ------------------- |
| Deterministic | 0 | none |
| `--with-ai` | exactly 1 | `ai-enrichment.json` on success |

If AI fails, deterministic reports and graphs are kept; the CLI completes with a
warning (exit 0). AI never modifies `findings.json` or `recommendations.json`.

---

## Output artifacts

```text
reports/<repository-name>/<YYYYMMDD-HHMMSS>/
├── report.html              # HTML Report v2
├── report.json              # machine-readable assessment
├── findings.json            # deterministic rule findings
├── recommendations.json     # deterministic recommendations
├── ai-enrichment.json       # optional (--with-ai success)
├── ai-execution.json        # optional AI observability
└── graphs/
    ├── repository-manifest.json
    ├── repository-graph.json
    ├── engineering-knowledge-graph.json
    ├── knowledge-bindings.json
    ├── assessment-graph.json
    └── graph-summary.json
```

CodeStrata retains the latest **three** completed runs per repository.

---

## HTML report

HTML Report v2 is self-contained (embedded CSS, no external assets):

1. Executive Overview
2. Repository Profile
3. Technology and Version Summary
4. Assessment Summary
5. Findings (deterministic)
6. Recommendations (deterministic)
7. AI Enrichment (only when available; labeled AI-generated)
8. Graph and Artifact References
9. Assessment Metadata

Deterministic sections are authoritative. AI content is interpretive and kept
separate.

### Example screenshots

Self-contained demo HTML snapshots live under `docs/images/`:

* [docs/images/report-deterministic-demo.html](docs/images/report-deterministic-demo.html)
* [docs/images/report-ai-demo.html](docs/images/report-ai-demo.html)

Generate a local report with the Quick Start commands and open `report.html` in
a browser. Interpretation: [docs/report-interpretation.md](docs/report-interpretation.md).

---

## Supported technologies

| Area | Community Edition support |
| ---- | ------------------------- |
| Languages | Java, JavaScript/TypeScript, Python, PHP, C# / .NET |
| Frameworks (detected) | Spring Boot, Express/Node, Flask, Laravel/Composer stacks, ASP.NET / .NET |
| Build / deps | Maven, npm, Composer, NuGet / MSBuild |
| CI | GitHub Actions discovery |
| Static analysis | Optional PMD (Java) |
| AI | Amazon Bedrock Converse (optional); OpenAI for knowledge providers |
| Sources | Local filesystem, GitHub HTTPS/SSH |
| Samples | `examples/sample-{js,python,java,php,csharp}-app` |
| Sample reports | [examples/sample-reports/](../examples/sample-reports/README.md) |

---

## Roadmap

**Phase 2** — Core platform foundation (assessment, knowledge graphs, agents,
incremental assessment).

**Phase 3** — Enterprise Knowledge Graph (Platform/monorepo; excluded from the
public Community engine export — see [docs/community-edition.md](docs/community-edition.md)).

**Phase 4.1** — Shared Rule Platform (infrastructure; see
[docs/analysis-intelligence/](docs/analysis-intelligence/)).

**Phase 4.1.2** — Assessment Framework methodology (see
[docs/assessment-framework/](docs/assessment-framework/)). Packs start at 4.2.

**Phase 4.2+ / 5+** — Analysis Intelligence packs, language expansion, workflow
intelligence, platform expansion. See [ROADMAP.md](../ROADMAP.md).

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and
[docs/contributor-guide.md](docs/contributor-guide.md). Please follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

```bash
python -m pip install -e ".[dev]"
pytest
pytest tests/docs -q
ruff check .
ruff format --check .
mypy src
```

Stuck? [docs/troubleshooting.md](docs/troubleshooting.md).

---

## Documentation index

| Doc | Topic |
| --- | ----- |
| [docs/community-edition.md](docs/community-edition.md) | Community Edition scope |
| [docs/COMMUNITY_EDITION_CHECKLIST.md](docs/COMMUNITY_EDITION_CHECKLIST.md) | Public release checklist |
| [docs/RELEASE_NOTES-0.1.0.md](docs/RELEASE_NOTES-0.1.0.md) | 0.1.0 release notes (draft) |
| [docs/quick-start.md](docs/quick-start.md) | Quick start |
| [docs/installation.md](docs/installation.md) | Installation |
| [docs/tutorial.md](docs/tutorial.md) | End-to-end tutorial |
| [docs/architecture-guide.md](docs/architecture-guide.md) | Architecture guide |
| [ARCHITECTURE.md](../ARCHITECTURE.md) | System design overview |
| [docs/cli-reference.md](docs/cli-reference.md) | CLI reference |
| [docs/configuration-profiles.md](docs/configuration-profiles.md) | Execution profiles |
| [docs/report-interpretation.md](docs/report-interpretation.md) | Reading reports |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Troubleshooting |
| [docs/contributor-guide.md](docs/contributor-guide.md) | Contributor guide |
| [docs/mcp/setup.md](docs/mcp/setup.md) | MCP setup |
| [SUPPORT.md](SUPPORT.md) | How to get help |
| [examples/README.md](../examples/README.md) | Language samples |
| [examples/sample-reports/README.md](../examples/sample-reports/README.md) | Example HTML/JSON reports |
| [CHANGELOG.md](../CHANGELOG.md) | Release notes history |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting |
| [docs/README.md](docs/README.md) | Full docs index |

---

## License

MIT License — see [LICENSE](LICENSE).

## Author

Satish Nampally — https://github.com/sknampally
