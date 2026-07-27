"""Retrieval API DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BuildRetrievalIndexRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str = Field(min_length=1, max_length=160)
    graph_id: str | None = Field(default=None, min_length=1, max_length=160)
    embedding_provider: str | None = Field(default=None, min_length=1, max_length=64)
    embedding_model: str | None = Field(default=None, min_length=1, max_length=128)
    embedding_dimension: int | None = Field(default=None, ge=1, le=8192)


class RebuildRetrievalIndexRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    embedding_provider: str | None = Field(default=None, min_length=1, max_length=64)
    embedding_model: str | None = Field(default=None, min_length=1, max_length=128)
    embedding_dimension: int | None = Field(default=None, ge=1, le=8192)


class RetrievalIndexSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index_id: str
    repository_id: str
    assessment_id: str
    engineering_snapshot_id: str
    knowledge_graph_id: str
    index_version: int
    status: str
    projection_key: str
    embedding_provider_id: str
    embedding_model_id: str
    embedding_dimension: int
    document_count: int
    chunk_count: int
    created_at: datetime
    completed_at: datetime | None


class RetrievalIndexDetailsResponse(RetrievalIndexSummaryResponse):
    organization_id: str
    workspace_id: str
    engineering_snapshot_version: int
    knowledge_graph_version: int
    retrieval_schema_version: str
    chunking_policy_version: str
    failure_reason: str | None = None
    created: bool | None = None
    idempotent: bool | None = None


class RetrievalDocumentSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    title: str
    summary: str


class RetrievalChunkSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    ordinal: int
    token_estimate: int
    text: str
    has_embedding: bool


class RetrievalSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_text: str = Field(min_length=1, max_length=4000)
    mode: str = Field(default="hybrid", min_length=1, max_length=32)
    top_k: int = Field(default=10, ge=1, le=100)
    content_types: list[str] | None = None
    canonical_types: list[str] | None = None
    canonical_ids: list[str] | None = None
    graph_node_ids: list[str] | None = None
    minimum_score: float | None = Field(default=None, ge=0.0, le=1.0)
    include_source_references: bool = True
    include_score_breakdown: bool = True


class RetrievalScoreBreakdownResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lexical_score: float
    vector_score: float
    graph_score: float
    source_quality_score: float
    final_score: float
    policy_version: str


class RetrievalSearchHitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    chunk_id: str
    document_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    title: str
    text: str
    score: RetrievalScoreBreakdownResponse
    source_references: list[str]
    graph_node_ids: list[str]


class RetrievalSearchResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hits: list[RetrievalSearchHitResponse]
    mode: str
    top_k: int


class RetrievalContextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_text: str = Field(min_length=1, max_length=4000)
    mode: str = Field(default="hybrid", min_length=1, max_length=32)
    top_k: int = Field(default=10, ge=1, le=100)
    max_tokens: int = Field(default=6000, ge=1, le=12000)
    content_types: list[str] | None = None


class RetrievalCitationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    canonical_type: str
    canonical_id: str
    source_references: list[str]
    graph_node_ids: list[str]


class RetrievalContextItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    text: str
    score: float
    citation: RetrievalCitationResponse


class RetrievalContextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RetrievalContextItemResponse]
    token_estimate: int
    policy_version: str
    truncated: bool


class RetrievalIndexStatisticsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index_id: str
    document_count: int
    chunk_count: int
    embedded_chunk_count: int
    content_type_counts: dict[str, int]
