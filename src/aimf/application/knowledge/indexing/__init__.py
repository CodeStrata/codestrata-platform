"""Knowledge indexing application package (Phase 5.3)."""

from aimf.application.knowledge.indexing.indexer import (
    INDEX_ARTIFACT_FILENAME,
    KnowledgeIndexer,
    KnowledgeIndexRequest,
    create_knowledge_indexer,
    write_knowledge_index_artifact,
)
from aimf.application.knowledge.indexing.mapping import (
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
