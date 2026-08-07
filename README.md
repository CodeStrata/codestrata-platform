# codestrata-platform

Private **source of truth** monorepo for **CodeStrata Engine** (Community) and
**CodeStrata Platform** development. Do not treat this repository as a public
product surface.

> The Engine produces structured Engineering Intelligence.  
> The Platform stores, connects, retrieves, and reasons over that intelligence.

Official product names: CodeStrata · CodeStrata Engine · CodeStrata Platform ·
CodeStrata VS Code Extension.  
AI is a capability, not part of the product name.  
Visual branding: [`governance/assets/DESIGN-SYSTEM.md`](governance/assets/DESIGN-SYSTEM.md).

| | |
| --- | --- |
| Edition | Community Engine is MIT-licensed under `engine/` |
| Python | 3.12+ |
| Version | 0.1.0 |

---

## Start here (developer journey)

Public product documentation lives in [`docs/`](docs/) (future **codestrata-docs** /
[docs.codestrata.ai](https://docs.codestrata.ai)). Engine `engine/docs/` is for
maintainer contracts and architecture.

| Step | Doc |
| ---- | --- |
| What is CodeStrata? | [docs/getting-started/](docs/getting-started/) |
| Install | [docs/getting-started/install.md](docs/getting-started/install.md) |
| First assessment | [docs/getting-started/first-assessment.md](docs/getting-started/first-assessment.md) |
| Community vs Platform | [docs/community/vs-platform.md](docs/community/vs-platform.md) |
| Public docs portal | [docs/README.md](docs/README.md) |
| Engine maintainer docs | [engine/docs/README.md](engine/docs/README.md) |

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e "./engine[dev,mcp]"
codestrata init
codestrata doctor
codestrata assess --repo test-fixtures/sample-js-app --output reports --no-ai
# open reports/sample-js-app/<timestamp>/report.html
```

---

## Engine vs Platform

| Capability | CodeStrata Engine (Community) | CodeStrata Platform |
| ---------- | ----------------------------- | ------------------- |
| Local / GitHub assess, Engineering Assessment reports | Shipped | Consumes Engine |
| Deterministic Engineering Intelligence | Shipped | Consumes / stores |
| Optional customer-configured AI | Shipped (`--with-ai`) | Provider utilities |
| Local MCP / local knowledge | Shipped | Adds Platform MCP surfaces |
| Engineering Knowledge Graph | Not included | Implemented |
| Repository Retrieval / Answering | Not included | Implemented |
| Portfolio Intelligence | Not included | Implemented |
| Executive Intelligence / Strategic Roadmap | Not included | Implemented |
| Hosted multi-tenancy / SSO / billing | Not included | Not fully productized |
| CodeStrata VS Code Extension | `vscode-plugin/` | — |

**Dependency rule:** Platform → Engine only. Engine must never import Platform.

Details: [docs/community/vs-platform.md](docs/community/vs-platform.md).

---

## Maintainer onboarding

1. Follow the developer journey above for Engine smoke.
2. [CONTRIBUTING.md](CONTRIBUTING.md) for setup and quality gates.
3. **[platform/README.md](platform/README.md)** for export, release, and doc ownership.
4. [ARCHITECTURE.md](ARCHITECTURE.md) · [CHANGELOG.md](CHANGELOG.md) · [ROADMAP.md](ROADMAP.md) (archive candidate).

Platform install (contributors only):

```bash
pip install -e "./platform[dev,mcp,pgvector]"
```

Security: [engine/SECURITY.md](engine/SECURITY.md) ·
[engine/docs/security/threat-model.md](engine/docs/security/threat-model.md).

---

## Generated repository mirrors

Destination repositories are **generated mirrors**. Develop only here, then
export and publish intentionally. Handbook: [platform/README.md](platform/README.md).

| Monorepo path | Destination | Visibility |
| ------------- | ----------- | ---------- |
| `engine/` | `CodeStrata/codestrata-engine` | **public** |
| `examples/` | `CodeStrata/codestrata-examples` | **public** |
| `docs/` | `CodeStrata/codestrata-docs` | **private** |
| `vscode-plugin/` | `CodeStrata/codestrata-vscode` | **private** |

```bash
python scripts/verify_release.py --skip-lint --skip-tests
python scripts/export-public-repos.py --clean
python scripts/publish-repository-mirrors.py --repo codestrata-engine   # dry-run
```

Related products outside this monorepo: `codestrata-ui`, `codestrata-site`.
