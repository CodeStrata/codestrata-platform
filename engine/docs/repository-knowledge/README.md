# Repository Knowledge Layer (Platform)

RAG projection, embeddings, vector storage, retrieval, and grounded answering
are **Platform** capabilities. They are not required for Community Edition
`codestrata assess`.

In the monorepo, documentation lives at:

`platform/docs/rag/`

Install Platform for local development:

```bash
pip install -e "./platform[dev,mcp,pgvector]"
```

Community assessment, local knowledge store, MCP assessment tools, and reports
remain documented under `engine/docs/`.
