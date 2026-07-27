"""Portfolio Retrieval API DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BuildPortfolioRetrievalIndexRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_id: str = Field(min_length=1, max_length=160)
    workspace_id: str = Field(min_length=1, max_length=160)
    portfolio_id: str = Field(min_length=1, max_length=160)
    portfolio_snapshot_id: str | None = Field(default=None, min_length=1, max_length=160)
    embedding_provider: str | None = Field(default=None, min_length=1, max_length=64)
    embedding_model: str | None = Field(default=None, min_length=1, max_length=128)
    embedding_dimension: int | None = Field(default=None, ge=1, le=8192)


class RebuildPortfolioRetrievalIndexRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    embedding_provider: str | None = Field(default=None, min_length=1, max_length=64)
    embedding_model: str | None = Field(default=None, min_length=1, max_length=128)
    embedding_dimension: int | None = Field(default=None, ge=1, le=8192)
    force: bool = False


class PortfolioRetrievalIndexSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index_id: str
    portfolio_id: str
    portfolio_snapshot_id: str
    portfolio_snapshot_version: int
    index_version: int
    status: str
    projection_key: str
    embedding_provider_id: str
    embedding_model_id: str
    embedding_dimension: int
    repository_count: int
    document_count: int
    chunk_count: int
    created_at: datetime
    completed_at: datetime | None


class PortfolioRetrievalIndexDetailsResponse(PortfolioRetrievalIndexSummaryResponse):
    organization_id: str
    workspace_id: str
    retrieval_schema_version: str
    chunking_policy_version: str
    ranking_policy_version: str
    repository_ids: list[str]
    failure_reason: str | None = None
    superseded_at: datetime | None = None
    created: bool | None = None
    idempotent: bool | None = None


class PortfolioRetrievalDocumentSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    title: str
    summary: str
    repository_ids: list[str]
    primary_repository_id: str | None = None


class PortfolioRetrievalChunkSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    document_id: str
    ordinal: int
    token_estimate: int
    text: str
    repository_ids: list[str]
    primary_repository_id: str | None = None
    has_embedding: bool


class PortfolioRetrievalSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_text: str = Field(min_length=1, max_length=4000)
    mode: str = Field(default="hybrid", min_length=1, max_length=32)
    top_k: int = Field(default=10, ge=1, le=100)
    content_types: list[str] | None = None
    repository_ids: list[str] | None = None
    exclude_repository_ids: list[str] | None = None
    repository_balance_mode: str = Field(default="none", min_length=1, max_length=64)
    include_portfolio_aggregates: bool = True
    include_repository_context: bool = True
    include_score_breakdown: bool = True


class PortfolioRetrievalScoreBreakdownResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lexical_score: float
    vector_score: float
    portfolio_score: float
    repository_score: float
    systemic_score: float
    source_quality_score: float
    freshness_score: float
    balance_adjustment: float
    final_score: float
    ranking_policy_version: str


class RepositoryContributionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository_id: str
    contribution_score: float
    finding_count: int
    is_primary: bool


class PortfolioRetrievalSearchHitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_id: str
    chunk_id: str
    document_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    title: str
    text: str
    score: PortfolioRetrievalScoreBreakdownResponse
    repository_ids: list[str]
    primary_repository_id: str | None = None
    repository_contributions: list[RepositoryContributionResponse]
    citations: list[str]


class PortfolioRetrievalSearchResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hits: list[PortfolioRetrievalSearchHitResponse]
    mode: str
    top_k: int


class PortfolioRetrievalContextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_text: str = Field(min_length=1, max_length=4000)
    mode: str = Field(default="hybrid", min_length=1, max_length=32)
    top_k: int = Field(default=10, ge=1, le=100)
    max_tokens: int = Field(default=10_000, ge=1, le=20_000)
    max_repositories: int = Field(default=20, ge=1, le=100)
    content_types: list[str] | None = None
    repository_balance_mode: str = Field(default="none", min_length=1, max_length=64)


class PortfolioRetrievalCitationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    chunk_id: str
    document_id: str
    canonical_type: str
    canonical_id: str
    repository_ids: list[str]
    references: list[str]


class PortfolioRetrievalContextItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    section: str
    content_type: str
    canonical_type: str
    canonical_id: str
    title: str
    text: str
    score: float
    repository_ids: list[str]
    citation: PortfolioRetrievalCitationResponse


class PortfolioRetrievalContextDiagnosticResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    detail: str
    repository_id: str | None = None


class PortfolioRetrievalContextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PortfolioRetrievalContextItemResponse]
    sections: list[str]
    token_estimate: int
    repository_count: int
    policy_version: str
    truncated: bool
    diagnostics: list[PortfolioRetrievalContextDiagnosticResponse]


class PortfolioRetrievalIndexStatisticsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index_id: str
    document_count: int
    chunk_count: int
    embedded_chunk_count: int
    repository_count: int
    content_type_counts: dict[str, int]
