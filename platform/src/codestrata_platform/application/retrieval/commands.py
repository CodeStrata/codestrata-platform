"""Retrieval application commands."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.retrieval.identifiers import RetrievalIndexId


@dataclass(frozen=True, slots=True)
class BuildRetrievalIndexCommand:
    snapshot_id: EngineeringSnapshotId
    graph_id: KnowledgeGraphId | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    embedding_dimension: int | None = None


@dataclass(frozen=True, slots=True)
class RebuildRetrievalIndexCommand:
    index_id: RetrievalIndexId
    embedding_provider: str | None = None
    embedding_model: str | None = None
    embedding_dimension: int | None = None


@dataclass(frozen=True, slots=True)
class FailRetrievalIndexCommand:
    index_id: RetrievalIndexId
    reason: str


@dataclass(frozen=True, slots=True)
class SupersedeRetrievalIndexCommand:
    index_id: RetrievalIndexId


@dataclass(frozen=True, slots=True)
class ArchiveRetrievalIndexCommand:
    index_id: RetrievalIndexId
