"""Knowledge indexing application package (Phase 5.3)."""

from codestrata_platform.rag.application.indexing.indexer import (
    INDEX_ARTIFACT_FILENAME,
    KnowledgeIndexer,
    KnowledgeIndexRequest,
    create_knowledge_indexer,
    write_knowledge_index_artifact,
)
from codestrata_platform.rag.application.indexing.mapping import (
    build_vector_record_for_chunk,
    chunk_matches_scope,
    chunk_vector_metadata,
)

__all__ = [
    "INDEX_ARTIFACT_FILENAME",
    "KnowledgeIndexRequest",
    "KnowledgeIndexer",
    "build_vector_record_for_chunk",
    "chunk_matches_scope",
    "chunk_vector_metadata",
    "create_knowledge_indexer",
    "write_knowledge_index_artifact",
]
