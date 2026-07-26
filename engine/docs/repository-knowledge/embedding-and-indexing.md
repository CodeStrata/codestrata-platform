# Embedding and knowledge indexing

**Status:** Phase 5.3 complete (deterministic embeddings + in-memory indexing).

## Flow

```text
KnowledgeCorpus
      ↓
Embedding Provider
      ↓
Embedded Knowledge Chunks
      ↓
VectorRecord Mapping
      ↓
VectorStore (memory | pgvector)
      ↓
Knowledge Index Manifest
```

Phase 5.4 replaces only the storage provider. Projection, chunking, embeddings,
and indexing logic are unchanged.
## Embedding abstraction

`EmbeddingProvider` (`codestrata.application.knowledge.embedding`):

- `embed_text` / `embed_batch`
- `health` / `capabilities` / `model_identity`

Implemented provider: **`DeterministicEmbeddingProvider`** — hash-seeded, L2-normalized,
fixed-dimension vectors for tests/dogfood only (`is_production_semantic=false`).

Reserved (not implemented): `bedrock`, `openai`, `local_sentence_transformer`.

## Indexing

`KnowledgeIndexer` embeds eligible chunks, upserts `VectorRecord`s, and emits
`KnowledgeIndexManifest` (`knowledge-index-manifest` 1.0.0) without raw embedding
arrays.

Incremental statuses: `unchanged`, `added`, `updated`, `removed`, `skipped`, `failed`.
Compatibility requires matching provider/model/version/dimension and vector-record
schema. Stable identity for increments is `(document_id, sequence)`.

## Configuration

```toml
[knowledge.embedding]
enabled = false
provider = "deterministic"
model = "deterministic-test-embedding"
dimension = 384
batch_size = 32
max_input_characters = 12000

[knowledge.indexing]
enabled = false
delete_stale_records = true
write_manifest = false
manifest_filename = "repository-knowledge-index.json"
```

Independent of projection/chunking/vector_store settings.

## Out of scope

Production embeddings, Bedrock/OpenAI, retrieval, hybrid search, reranking,
RAG answering, MCP, semantic chunking. PostgreSQL + pgvector storage is Phase 5.4.
