# Repository Knowledge Retrieval (Phase 5.5 / 5.9)

**Status:** Complete — vector, lexical, and hybrid (RRF) retrieval modes.

## Flow

```text
RetrievalRequest
      ↓
Query Preparation (normalize + fingerprint)
      ↓
mode = vector | lexical | hybrid
      ├─ vector  → EmbeddingProvider → VectorStore.search
      ├─ lexical → fetch_filtered + BM25-lite scoring
      └─ hybrid  → both + Reciprocal Rank Fusion
      ↓
Deduplication + Diversity
      ↓
Context Assembly + Citations
      ↓
RetrievalResult
```

Default `mode = "vector"` preserves Phase 5.5 dense-only behavior.

## Contracts

- `RepositoryRetriever`
- `RetrievalRequest` / `RetrievalResult` (`repository-retrieval-*` 1.0.0)
- `RetrievalHit` / `RetrievalContext` (1.0.0)
- Status: `SUCCESS` | `EMPTY` | `PARTIAL` | `FAILED` | `DISABLED`

## Behavior

- Required scope: `tenant_id` + `repository_id` (optional `scan_id` / branch / commit)
- Deterministic query prep (no rewriting / LLM expansion)
- Vector: cosine search via existing `VectorStore` (memory or pgvector)
- Lexical: BM25-lite over indexed chunk text (works without production embeddings)
- Hybrid: weighted Reciprocal Rank Fusion (`rrf_k`, `vector_weight`, `lexical_weight`)
- No silent fallback between modes
- Deduplicate by chunk_id / content_hash / document+sequence
- Diversity caps per document / file / source_type
- Context budget: whole-chunk only (never mid-chunk truncate)
- Citations: `SRC-001`, `SRC-002`, …

## Configuration

```toml
[knowledge.retrieval]
enabled = false
mode = "vector"  # vector | lexical | hybrid
vector_weight = 1.0
lexical_weight = 1.0
top_k = 10
# result_limit = 10  # optional alias for top_k
candidate_limit = 30
minimum_score = 0.0
rrf_k = 60
```

Diagnostics include retrieval mode, vector/lexical/fused candidate counts,
final result count, latency, and score components.

## Out of scope

Graph expansion, learned reranking, conversational memory. MCP exposure is
Phase 5.7. Production embeddings/answers are Phase 5.8 — see
[ai-providers.md](ai-providers.md) and [grounded-answering.md](grounded-answering.md).
