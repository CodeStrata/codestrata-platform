# codestrata-platform

Private **source of truth** monorepo for **CodeStrata** development.

Current shipping Community product: **CodeStrata Engine 0.2.0** and
**CodeStrata VS Code Extension 0.2.0**. Public Community documentation lives in
[`docs/`](docs/). This monorepo also contains private Platform, Infrastructure,
and Insights work that is **not** part of the Community Edition surface.

> The Engine produces single-repository **Engineering Assessments**.  
> Portfolio **Engineering Intelligence Reports (EIR)** aggregate completed assessments.  
> The Platform (private) stores, connects, retrieves, and reasons over that
> intelligence for organizational products — it is not required for Community
> local assessment.

Official Community product names: CodeStrata · CodeStrata Engine ·
CodeStrata VS Code Extension.  
AI is a capability, not part of the product name.  
Visual branding: [`design-system/`](design-system/) (authoritative).  
Historical design notes: [`governance/assets/DESIGN-SYSTEM.md`](governance/assets/DESIGN-SYSTEM.md).

| | |
| --- | --- |
| Edition | Community Engine is MIT-licensed under `engine/` |
| Python | 3.12+ |
| Version | **0.2.0** |

---

## Start here (Community developer journey)

| Step | Doc |
| ---- | --- |
| What is CodeStrata? | [docs/getting-started/](docs/getting-started/) |
| Install | [docs/getting-started/install.md](docs/getting-started/install.md) |
| First assessment | [docs/getting-started/first-assessment.md](docs/getting-started/first-assessment.md) |
| Public docs portal | [docs/README.md](docs/README.md) · [docs/index.md](docs/index.md) |
| Engine maintainer docs | [engine/docs/README.md](engine/docs/README.md) |

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e "./engine[dev,mcp]"
codestrata init
codestrata doctor
codestrata assess --repo test-fixtures/sample-js-app --no-ai
# open .codestrata-artifacts/assessments/<repository-id>/current/assessment.html
```

---

## Engine vs Platform (boundary)

| Capability | CodeStrata Engine (Community) | CodeStrata Platform (private) |
| ---------- | ----------------------------- | ----------------------------- |
| Local / GitHub assess, Engineering Assessment reports | Shipped | Consumes Engine |
| Deterministic Engineering Assessment (no-AI default) | Shipped | Consumes / stores |
| Optional customer-configured AI | Shipped (`--with-ai`) | Provider utilities |
| Local MCP / local knowledge | Shipped | Adds Platform MCP surfaces |
| Engineering Knowledge Graph | Not included | Platform-only |
| Repository Retrieval / Answering | Not included | Platform-only |
| Portfolio Engineering Intelligence (EIR) | Community local EIR layout | Platform-only commercial |
| CodeStrata VS Code Extension | `vscode-plugin/` | — |

**Dependency rule:** Platform → Engine only. Engine must never import Platform.

Community docs do **not** present Platform capabilities as available in Community.
Maintainer boundary detail: [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Maintainer onboarding

1. Follow the Community journey above for Engine smoke.
2. [CONTRIBUTING.md](CONTRIBUTING.md) for setup and quality gates.
3. **[platform/README.md](platform/README.md)** for export, release, and private Platform ownership.
4. [ARCHITECTURE.md](ARCHITECTURE.md) · [CHANGELOG.md](CHANGELOG.md) ·
   [ROADMAP.md](ROADMAP.md) (**archive candidate** — not current public guidance).

Platform install (contributors only):

```bash
pip install -e "./platform[dev,mcp,pgvector]"
```

Security: [SECURITY.md](SECURITY.md) · [engine/SECURITY.md](engine/SECURITY.md) ·
[engine/docs/security/threat-model.md](engine/docs/security/threat-model.md).  
Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).  
License (Community Engine): [engine/LICENSE](engine/LICENSE).

Documentation cleanup authority (Epic 16):
[platform/docs/repository-cleanup/community-documentation-cleanup.md](platform/docs/repository-cleanup/community-documentation-cleanup.md).

---

## Generated repository mirrors

Destination repositories are **generated mirrors**. Develop only here, then
export and publish intentionally. Handbook: [platform/README.md](platform/README.md).

| Monorepo path | Destination | Visibility |
| ------------- | ----------- | ---------- |
| `engine/` | `CodeStrata/codestrata-engine` | **public** |
| `examples/` | `CodeStrata/codestrata-examples` | **public** |
| `docs/` | `CodeStrata/codestrata-docs` | **private** (publishable Community portal) |
| `vscode-plugin/` | `CodeStrata/codestrata-vscode` | **private** → Marketplace |

```bash
python scripts/verify_release.py --skip-lint --skip-tests
python scripts/export-public-repos.py --clean
python scripts/publish-repository-mirrors.py --repo codestrata-engine   # dry-run
```

Related products outside this monorepo: `codestrata-ui`, `codestrata-site`.
