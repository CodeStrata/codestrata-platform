# Knowledge document projection and chunking

**Status:** Phase 5.2 complete (projection + deterministic chunking only).

## Flow

```text
Repository + Assessments + Findings + Evidence + Reports
                         ↓
               Knowledge Projectors
                         ↓
                KnowledgeDocuments
                         ↓
             Deterministic Chunker
                         ↓
                 KnowledgeChunks
                         ↓
             Phase 5.3 Embeddings and Indexing (not implemented)
```

## Projectors

| Source type | Input |
| ----------- | ----- |
| `repository_file` | Manifest + `RepositoryContentReader` |
| `finding` | Phase 3 `Finding` |
| `recommendation` | Phase 3 `Recommendation` |
| `evidence` | In-memory evidence aggregates |
| `architecture` … `performance` | Assessment sections |
| `report_section` | Report section view-models |

Empty/disabled sections are skipped with diagnostics. No report-file re-reads.

## Chunking

`DeterministicKnowledgeChunker` (`deterministic-chunker` 1.0.0):

1. Source-code structural (header/imports, classes, methods, config blocks, fallback windows)
2. Assessment-aware (`##` sections: posture, themes, conclusions, recommendations, inventories, limitations)
3. Finding / recommendation primary chunks
4. Report-section heading hierarchy

Configurable `max_characters`, `overlap_characters`, `preserve_logical_units`. No LLM or semantic splitting.

## Corpus

`KnowledgeCorpus` (`knowledge-corpus` 1.0.0) holds documents, chunks, coverage, diagnostics, limitations, fingerprint, and corpus ID.

Optional artifact: `repository-knowledge-corpus.json` when
`[knowledge.projection].write_corpus_artifact = true`.

## Configuration

```toml
[knowledge.projection]
enabled = false
include_repository_files = true
include_findings = true
include_recommendations = true
include_evidence = true
include_assessments = true
include_report_sections = true
write_corpus_artifact = false

[knowledge.chunking]
enabled = false
strategy = "deterministic"
max_characters = 4000
overlap_characters = 400
preserve_logical_units = true
```

Independent of `[knowledge.vector_store]` (Phase 5.2 does not write vectors).

## Out of scope

Embeddings, pgvector, vector-store writes, retrieval, RAG, MCP, AI/LLM, semantic chunking.
