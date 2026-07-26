# codestrata-platform

Private **source of truth** monorepo for CodeStrata Community and Commercial
development. Do not treat this repository as a public product surface.

> The Engine produces structured engineering intelligence.  
> The Platform stores, connects, retrieves, and reasons over that intelligence.

| | |
| --- | --- |
| Edition | Community Engine is MIT-licensed under `engine/` |
| Python | 3.12+ |
| Version | 0.1.0 |

---

## Repository layout

```text
codestrata-platform/
├── engine/              Community Engine (CLI, MCP, packaging)  → codestrata-engine
├── examples/            Real-world showcase manifests          → codestrata-examples
├── test-fixtures/       Internal language samples (not exported as examples)
├── cursor-plugin/       Placeholder only                       → codestrata-cursor
├── vscode-plugin/       Placeholder only                       → codestrata-vscode
├── platform/            Implemented commercial RAG + Knowledge Graph (not exported)
├── scripts/             Operational: verify_release, export, security, showcase wrappers
├── public-export-manifest.yaml
└── tests/architecture/  Engine ↔ Platform boundary tests
```

| Area | Path | Public mirror? |
| ---- | ---- | -------------- |
| **Engine** | `engine/` | Yes → `codestrata-engine` |
| **Examples** | `examples/` | Yes → `codestrata-examples` |
| **Test fixtures** | `test-fixtures/` | No (Engine smoke may vendor `sample-js-app`) |
| **Plugins** | `cursor-plugin/`, `vscode-plugin/` | Placeholders only |
| **Platform** | `platform/` | No |

Related products outside this monorepo: `codestrata-ui`, `codestrata-site`.

---

## Engine vs Platform

| Capability | Community Engine | Platform (`platform/`) |
| ---------- | ---------------- | ---------------------- |
| Local / GitHub assess, HTML/JSON reports | Shipped | Consumes Engine |
| MCP assessment tools | Shipped | Adds RAG + KG tools via entry points |
| Repository RAG (index/retrieve/answer) | Not included | Implemented under `platform/rag/` |
| Persistent Knowledge Graph | Not included | Implemented under `platform/knowledge_graph/` |
| Hosted multi-tenancy / SSO / billing | Not included | Not implemented |
| Cursor / VS Code extensions | Placeholders | — |

**Dependency rule:** Platform → Engine only. Engine must never import Platform.

---

## Generated public repositories

Public GitHub repositories are **generated mirrors**. Develop only in this
monorepo, then export and publish intentionally.

| Monorepo path | Public repository |
| ------------- | ----------------- |
| `engine/` | `codestrata-engine` |
| `examples/` | `codestrata-examples` |
| `cursor-plugin/` | `codestrata-cursor` |
| `vscode-plugin/` | `codestrata-vscode` |

Staging export (no remotes, push, or publish):

```bash
python scripts/verify_release.py --skip-lint --skip-tests
# or step-by-step:
python scripts/export-public-repos.py --dry-run
python scripts/export-public-repos.py
python scripts/validate-public-exports.py
```

Full export, validation, release, and ownership rules:
**[platform/README.md](platform/README.md)** (maintainer handbook).

---

## Maintainer onboarding

1. Read this file for orientation.
2. Follow [CONTRIBUTING.md](CONTRIBUTING.md) for setup and quality gates.
3. Use **[platform/README.md](platform/README.md)** for export, release, and
   documentation ownership (do not duplicate that handbook here).
4. Check [ROADMAP.md](ROADMAP.md) for current direction and
   [ARCHITECTURE.md](ARCHITECTURE.md) for ecosystem architecture.

Quick local smoke:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e "./engine[dev,mcp]"
pip install -e "./platform[dev,mcp,pgvector]"
codestrata assess --repo test-fixtures/sample-js-app --output reports --no-ai
```

Engine docs: [engine/docs/quick-start.md](engine/docs/quick-start.md) ·
[engine/README.md](engine/README.md)

Security: [engine/SECURITY.md](engine/SECURITY.md) ·
[engine/docs/security/threat-model.md](engine/docs/security/threat-model.md)
