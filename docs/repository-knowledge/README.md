# Repository Knowledge Layer

**Status:** Phases 5.1–5.9 (foundation through hybrid retrieval).

CodeStrata’s Repository Knowledge Layer turns assessment outputs into canonical,
traceable knowledge suitable for indexing, retrieval, and citation-bound
answers. Projection, chunking, embeddings, vector storage, retrieval (vector /
lexical / hybrid), grounded answering, MCP, and optional Bedrock/OpenAI
providers are implemented. Graph expansion and learned reranking are **not**.

See [ai-providers.md](ai-providers.md) for production embedding/answer provider
configuration.
## Architecture

```text
Repository
   +
Assessment
   +
Findings
   +
Evidence
   +
Reports
      ↓
Canonical Knowledge Documents   (knowledge-document 1.0.0)
      ↓
Knowledge Chunks                (knowledge-chunk 1.0.0)
      ↓
Embeddings + KnowledgeIndexer
      ↓
VectorStore  →  memory | pgvector
      ↓
RepositoryRetriever             (Phase 5.5)
      ↓
GroundedAnswerEngine            (Phase 5.6+)
      ↓
AnswerProvider                  (deterministic | bedrock | openai)
```

## Relationship to the engineering knowledge store

| Concern | Package | Persistence |
| ------- | ------- | ----------- |
| Phase 2 engineering knowledge store | `application.knowledge` + SQLite | `.aimf/knowledge/` |
| Phase 5 Repository Knowledge Layer | `domain.knowledge` + `infrastructure.vector_store` | memory or PostgreSQL + pgvector |

`[knowledge].directory` continues to configure the Phase 2 store.
`[knowledge].enabled` and related gates default **off**; vector store defaults to
**memory**.

## Domain models

- `KnowledgeDocument` — canonical unit of knowledge with stable `document_id`,
  fingerprint, metadata, and traceability
- `KnowledgeChunk` — bounded slice of a document
- `KnowledgeSource` — provenance pointers (repo, scan, finding, evidence, …)
- `KnowledgeMetadata` — filterable facets (tenant, language, severity, …)
- `KnowledgeTraceability` — audit lineage binding an artifact to its source

Stable source types: `repository_file`, `architecture`, `technical_debt`,
`dependency`, `security`, `test`, `cloud`, `ai_readiness`, `performance`,
`finding`, `evidence`, `recommendation`, `report_section`.

## Configuration

```toml
[knowledge]
directory = ".aimf/knowledge"
enabled = false

[knowledge.vector_store]
provider = "memory"   # or "pgvector" via CODESTRATA_VECTOR_STORE_PROVIDER
connection_string_env = "CODESTRATA_DATABASE_URL"
schema = "codestrata"
hnsw = true
```

Prefer `CODESTRATA_DATABASE_URL` for PostgreSQL credentials. See
[vector-store-setup.md](vector-store-setup.md).

Grounded answering (Phase 5.6+) is documented in
[grounded-answering.md](grounded-answering.md). Production Bedrock/OpenAI
providers (Phase 5.8) are documented in [ai-providers.md](ai-providers.md).
`[knowledge.answering]` / `[knowledge.embedding]` default **off**; select
providers via `[ai].embedding_provider` and `[ai].answer_provider`.

## Out of scope (through Phase 5.9)

- Anthropic / Azure OpenAI / Gemini / Ollama / vLLM
- Graph expansion / learned reranking
- Conversational memory
- Semantic / LLM-based chunking
- Silent provider or retrieval-mode fallback
- AWS infrastructure provisioning

Hybrid retrieval (vector + lexical RRF) is Phase 5.9 — see
[retrieval.md](retrieval.md). MCP exposure is Phase 5.7 — see
[../mcp/overview.md](../mcp/overview.md).

See [projection-and-chunking.md](projection-and-chunking.md),
[embedding-and-indexing.md](embedding-and-indexing.md),
[ai-providers.md](ai-providers.md),
[vector-store.md](vector-store.md),
[vector-store-setup.md](vector-store-setup.md),
[retrieval.md](retrieval.md), and
[grounded-answering.md](grounded-answering.md).
