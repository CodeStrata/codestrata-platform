# ADR: Vector store provider selection

**Status:** Accepted — Phase 5.4 implements PostgreSQL + pgvector  
**Date:** 2026-07-21 (updated 2026-07-25)

## Context

CodeStrata needs a provider-neutral vector abstraction so Repository Knowledge
indexing can evolve without coupling domain contracts to a single vendor.

## Decision

1. **PostgreSQL + pgvector** is the MVP persistence backend (`PgVectorStore`,
   Phase 5.4).
2. **In-memory provider** (`provider = "memory"`) remains the default for local
   runs and deterministic tests.
3. **Qdrant, OpenSearch, and Pinecone** remain future adapters behind the same
   `VectorStore` protocol.

## Consequences

- Domain models and the `VectorStore` port must not import PostgreSQL, pgvector,
  or vendor SDKs (optional dependency group `codestrata[pgvector]`).
- Factory creates `PgVectorStore` when provider resolves to `pgvector` and
  `CODESTRATA_DATABASE_URL` (or a deprecated alias) is available.
- Search uses cosine similarity with metadata filters and stable
  score/`record_id` ordering; hybrid search and reranking stay out of scope.
- Credentials stay in the environment / secret manager — not in committed TOML.
