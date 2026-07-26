# Vector-store abstraction

Provider-neutral contracts live in:

- Domain models: `codestrata.domain.knowledge.vector`
- Application port: `codestrata.application.knowledge.vector_store.VectorStore`
- In-memory adapter: `codestrata.infrastructure.vector_store.memory.InMemoryVectorStore`
- PostgreSQL + pgvector adapter: `codestrata.infrastructure.vector_store.pgvector.PgVectorStore`

Operational setup (Docker, env vars, secrets): see
[vector-store-setup.md](vector-store-setup.md).

## Protocol

```text
VectorStore
  upsert(records)
  search(query)
  delete_scope(scope)
  delete_ids(record_ids)
  health()
  capabilities()
```

Supporting models: `VectorRecord`, `VectorQuery`, `VectorSearchResult`,
`VectorFilter`, `VectorStoreCapabilities`, `VectorStoreHealth`, `IndexScope`.

## Guarantees

- Dense vectors with cosine similarity
- Metadata filtering (`VectorFilter`)
- Tenant / repository / scan isolation via metadata + `IndexScope`
- Deterministic `record_id` values (`vr:…`) for idempotent upserts
- Stable search ordering: score descending, then `record_id` ascending
- No silent fallback from `pgvector` to `memory`

## Providers

| Provider | Status |
| -------- | ------ |
| `memory` | Default — zero setup, non-persistent |
| `pgvector` | Production storage (Docker or hosted PostgreSQL) |
| Qdrant / OpenSearch / Pinecone | Future adapters |

### Configuration (Phase 5.4.1)

```toml
[knowledge.vector_store]
provider = "memory"
connection_string_env = "CODESTRATA_DATABASE_URL"
schema = "codestrata"
hnsw = true
connect_timeout_seconds = 10
```

Canonical environment variables:

- `CODESTRATA_VECTOR_STORE_PROVIDER`
- `CODESTRATA_DATABASE_URL`
- `CODESTRATA_DATABASE_SCHEMA`

Deprecated compatibility: `CODESTRATA_PGVECTOR_URL`, TOML `connection_string`.

Never put real credentials in `codestrata.toml`. Search remains cosine-only (no hybrid,
keyword, or reranking).

See [provider-decision.md](provider-decision.md) and
[vector-store-setup.md](vector-store-setup.md).
