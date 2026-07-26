# CodeStrata Platform (private)

The Engine produces structured engineering intelligence. The Platform stores,
connects, retrieves, and reasons over that intelligence.

This directory contains **implemented** commercial capabilities only:

```text
platform/
├── README.md
├── pyproject.toml
├── docs/
│   └── knowledge_graph/
├── src/codestrata_platform/
│   ├── rag/                 # retrieval, indexing, embeddings, vector stores, answering
│   ├── knowledge_graph/     # persistent Enterprise Knowledge Graph
│   └── extensions/          # CLI/MCP/AI entry points for the Engine
└── tests/
```

## Dependency direction

`Platform → Engine` only. Community Engine never imports this package.

Install for monorepo development:

```bash
pip install -e "./engine[dev,mcp]"
pip install -e "./platform[dev,mcp,pgvector]"
```

Platform surfaces register through Engine entry points
(`codestrata.cli_extensions`, `codestrata.mcp_extensions`,
`codestrata.ai_provider_extensions`, `codestrata.acceptance_extensions`).

Do not treat speculative folders (organizations, billing, tenancy, dashboards)
as implemented product surface.
