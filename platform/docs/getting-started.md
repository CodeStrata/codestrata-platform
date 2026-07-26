# Platform getting started

Minimal local setup for implemented Platform capabilities: **RAG** (Repository
Knowledge Layer) and the **persistent Knowledge Graph**.

## Purpose

The Engine produces structured engineering intelligence. The Platform stores,
connects, retrieves, and reasons over that intelligence.

**Dependency direction:** Platform → Engine only. Install and use the Engine
first. Community Engine never imports the Platform package.

## Prerequisites

* Python 3.12+
* Monorepo checkout of `codestrata-platform`
* Working Engine install (`codestrata` on `PATH`)
* Optional for pgvector-backed RAG: Docker / PostgreSQL (memory vector store
  works without it)

## Local installation

From the monorepo root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e "./engine[dev,mcp]"
pip install -e "./platform[dev,mcp,pgvector]"
codestrata version
```

Platform CLI/MCP surfaces register through Engine entry points after the
Platform package is installed.

## RAG smoke workflow

Uses the local knowledge store and deterministic providers (no cloud AI
credentials required).

1. Point `codestrata.toml` at a small fixture (for example
   `test-fixtures/sample-js-app`).
2. Enable knowledge projection / indexing / retrieval / answering gates (see
   [rag/README.md](rag/README.md) for TOML keys). Default vector store:
   `memory`.
3. Index via onboarding (orchestrates assess + index):

```bash
codestrata onboard test-fixtures/sample-js-app \
  --config codestrata.toml \
  --output reports \
  --provider deterministic
```

4. Ask a grounded question:

```bash
codestrata repository answer <repository-id-or-path> \
  "What technologies were detected?" \
  --config codestrata.toml
```

Details: [rag/README.md](rag/README.md), [rag/grounded-answering.md](rag/grounded-answering.md).

## Knowledge Graph smoke workflow

```bash
codestrata enterprise init /tmp/cs-kg-smoke --force
codestrata enterprise validate /tmp/cs-kg-smoke
codestrata enterprise build /tmp/cs-kg-smoke
```

Details: [knowledge_graph/README.md](knowledge_graph/README.md),
[knowledge_graph/cli.md](knowledge_graph/cli.md).

## Tests

```bash
pytest platform/tests -q
```

Focused subsets:

```bash
pytest platform/tests/rag -q
pytest platform/tests/knowledge_graph -q
```

## Architecture docs

* [architecture/PLATFORM_ARCHITECTURE.md](architecture/PLATFORM_ARCHITECTURE.md)
* [architecture/PLATFORM_CAPABILITY_INVENTORY.md](architecture/PLATFORM_CAPABILITY_INVENTORY.md)
* [rag/README.md](rag/README.md)
* [knowledge_graph/README.md](knowledge_graph/README.md)

## Out of scope here

This guide does **not** cover deployment, SaaS hosting, authentication, billing,
tenancy, or unimplemented commercial surfaces.
