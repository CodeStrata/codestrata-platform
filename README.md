# codestrata-platform

Private **source of truth** for CodeStrata Community and Commercial development.

> The Engine produces structured engineering intelligence. The Platform stores,
> connects, retrieves, and reasons over that intelligence.

Public GitHub repositories are **generated mirrors** — do not edit them directly.
See [docs/public-export.md](docs/public-export.md).

| Badge | |
| ----- | --- |
| Edition | Community Engine is MIT-licensed under `engine/` |
| Python | 3.12+ |
| Version | 0.1.0 |

---

## Repository map

```text
codestrata-platform/
├── engine/              Community Engine (CLI, MCP, packaging)  → codestrata-engine
├── examples/            Sample apps + golden reports           → codestrata-examples
├── cursor-plugin/       Placeholder only                       → codestrata-cursor
├── vscode-plugin/       Placeholder only                       → codestrata-vscode
├── platform/            Implemented commercial RAG + Knowledge Graph (not exported)
├── scripts/             Export, validate, dogfood harnesses
├── public-export-manifest.yaml
├── docs/                Monorepo sync + index
└── tests/architecture/  Engine ↔ Platform boundary tests
```

### What lives where

| Area | Path | Public? |
| ---- | ---- | ------- |
| **Engine** | `engine/` | Yes → `codestrata-engine` |
| **Examples** | `examples/` | Yes → `codestrata-examples` |
| **Plugins** | `cursor-plugin/`, `vscode-plugin/` | Placeholders only |
| **Platform** | `platform/` | No (private; RAG + Knowledge Graph) |

Related products outside this monorepo: `codestrata-ui`, `codestrata-site`.

---

## Community Engine (quick start)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e "./engine[dev,mcp]"
codestrata assess --repo examples/sample-js-app --output reports --no-ai
```

Engine docs: [engine/docs/quick-start.md](engine/docs/quick-start.md) ·
[engine/docs/community-edition.md](engine/docs/community-edition.md) ·
[engine/README.md](engine/README.md)

---

## Community vs Platform

| Capability | Community Engine | Platform (`platform/`) |
| ---------- | ---------------- | ---------------------- |
| Local / GitHub assess, HTML/JSON reports | Shipped | Consumes Engine |
| MCP assessment tools | Shipped | Adds RAG + KG tools via entry points |
| Repository RAG (index/retrieve/answer) | Not included | Implemented under `platform/rag/` |
| Persistent Knowledge Graph | Not included | Implemented under `platform/knowledge_graph/` |
| Hosted multi-tenancy / SSO / billing | Not included | Not implemented (do not treat as shipped) |
| Cursor / VS Code extensions | Placeholders | — |

Install Platform for private monorepo development:

```bash
pip install -e "./platform[dev,mcp,pgvector]"
```

---

## Public export (staging only)

```bash
python scripts/export-public-repos.py --dry-run
python scripts/export-public-repos.py
python scripts/validate-public-exports.py
```

No GitHub create/push/publish is performed by these scripts.

---

## Development

```bash
pip install -e "./engine[dev,mcp]"
pip install -e "./platform[dev,mcp,pgvector]"
ruff check .
mypy engine/src
pytest
python scripts/security_check.py
python scripts/validate-public-exports.py
```

Security: [engine/SECURITY.md](engine/SECURITY.md) ·
[engine/docs/security/threat-model.md](engine/docs/security/threat-model.md)
