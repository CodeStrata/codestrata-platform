"""Application models for portfolio retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from codestrata_platform.domain.portfolio_retrieval.index import PortfolioRetrievalIndex
from codestrata_platform.domain.portfolio_retrieval.lifecycle import PortfolioRetrievalIndexStatus
from codestrata_platform.domain.portfolio_retrieval.query import PortfolioRetrievalScore
from codestrata_platform.domain.portfolio_retrieval.ranking import RepositoryContribution
from codestrata_platform.domain.portfolio_retrieval.result import PortfolioRetrievalHit


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalIndexSummary:
    index_id: str
    portfolio_id: str
    portfolio_snapshot_id: str
    portfolio_snapshot_version: int
    index_version: int
    status: PortfolioRetrievalIndexStatus
    projection_key: str
    embedding_provider_id: str
    embedding_model_id: str
    embedding_dimension: int
    repository_count: int
    document_count: int
    chunk_count: int
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_aggregate(cls, index: PortfolioRetrievalIndex) -> PortfolioRetrievalIndexSummary:
        return cls(
            index_id=index.index_id.value,
            portfolio_id=index.portfolio_id.value,
            portfolio_snapshot_id=index.portfolio_snapshot_id.value,
            portfolio_snapshot_version=index.portfolio_snapshot_version,
            index_version=index.index_version.value,
            status=index.status,
            projection_key=index.projection_key.value,
            embedding_provider_id=index.embedding_provider_id.value,
            embedding_model_id=index.embedding_model_id.value,
            embedding_dimension=index.embedding_dimension.value,
            repository_count=len(index.repository_ids),
            document_count=len(index.documents),
            chunk_count=len(index.chunks),
            created_at=index.audit.created_at.value,
            completed_at=index.completed_at,
        )


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalIndexDetails(PortfolioRetrievalIndexSummary):
    organization_id: str
    workspace_id: str
    retrieval_schema_version: str
    chunking_policy_version: str
    ranking_policy_version: str
    repository_ids: tuple[str, ...]
    failure_reason: str | None
    superseded_at: datetime | None
    created: bool | None = None
    idempotent: bool | None = None

    @classmethod
    def from_aggregate(
        cls,
        index: PortfolioRetrievalIndex,
        *,
        created: bool | None = None,
        idempotent: bool | None = None,
    ) -> PortfolioRetrievalIndexDetails:
        summary = PortfolioRetrievalIndexSummary.from_aggregate(index)
        return cls(
            index_id=summary.index_id,
            portfolio_id=summary.portfolio_id,
            portfolio_snapshot_id=summary.portfolio_snapshot_id,
            portfolio_snapshot_version=summary.portfolio_snapshot_version,
            index_version=summary.index_version,
            status=summary.status,
            projection_key=summary.projection_key,
            embedding_provider_id=summary.embedding_provider_id,
            embedding_model_id=summary.embedding_model_id,
            embedding_dimension=summary.embedding_dimension,
            repository_count=summary.repository_count,
            document_count=summary.document_count,
            chunk_count=summary.chunk_count,
            created_at=summary.created_at,
            completed_at=summary.completed_at,
            organization_id=index.organization_id.value,
            workspace_id=index.workspace_id.value,
            retrieval_schema_version=index.retrieval_schema_version,
            chunking_policy_version=index.chunking_policy_version,
            ranking_policy_version=index.ranking_policy_version,
            repository_ids=tuple(item.value for item in index.repository_ids),
            failure_reason=index.failure_reason,
            superseded_at=index.superseded_at,
            created=created,
            idempotent=idempotent,
        )


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalDocumentSummary:
    document_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    title: str
    summary: str
    repository_ids: tuple[str, ...]
    primary_repository_id: str | None


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalDocumentDetails(PortfolioRetrievalDocumentSummary):
    structured_content: dict[str, str]
    metadata: dict[str, str]
    checksum: str


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalChunkSummary:
    chunk_id: str
    document_id: str
    ordinal: int
    token_estimate: int
    text: str
    repository_ids: tuple[str, ...]
    primary_repository_id: str | None
    has_embedding: bool


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalScoreBreakdown:
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

    @classmethod
    def from_score(cls, score: PortfolioRetrievalScore) -> PortfolioRetrievalScoreBreakdown:
        return cls(
            lexical_score=score.lexical_score,
            vector_score=score.vector_score,
            portfolio_score=score.portfolio_score,
            repository_score=score.repository_score,
            systemic_score=score.systemic_score,
            source_quality_score=score.source_quality_score,
            freshness_score=score.freshness_score,
            balance_adjustment=score.balance_adjustment,
            final_score=score.final_score,
            ranking_policy_version=score.ranking_policy_version,
        )


@dataclass(frozen=True, slots=True)
class RepositoryContributionModel:
    repository_id: str
    contribution_score: float
    finding_count: int
    is_primary: bool

    @classmethod
    def from_contribution(cls, item: RepositoryContribution) -> RepositoryContributionModel:
        return cls(
            repository_id=item.repository_id.value,
            contribution_score=item.contribution_score,
            finding_count=item.finding_count,
            is_primary=item.is_primary,
        )


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalSearchRequest:
    query_text: str
    mode: str = "hybrid"
    top_k: int = 10
    content_types: tuple[str, ...] = ()
    repository_balance_mode: str = "none"
    include_portfolio_aggregates: bool = True
    include_repository_context: bool = True
    include_score_breakdown: bool = True


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalSearchHitModel:
    result_id: str
    chunk_id: str
    document_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    title: str
    text: str
    score: PortfolioRetrievalScoreBreakdown
    repository_ids: tuple[str, ...]
    primary_repository_id: str | None
    repository_contributions: tuple[RepositoryContributionModel, ...]
    citations: tuple[str, ...]

    @classmethod
    def from_hit(cls, hit: PortfolioRetrievalHit) -> PortfolioRetrievalSearchHitModel:
        return cls(
            result_id=hit.result_id.value,
            chunk_id=hit.chunk_id.value,
            document_id=hit.document_id.value,
            content_type=hit.content_type.value,
            canonical_type=hit.canonical_type,
            canonical_id=hit.canonical_id,
            title=hit.title,
            text=hit.text,
            score=PortfolioRetrievalScoreBreakdown.from_score(hit.score),
            repository_ids=tuple(item.value for item in hit.repository_ids),
            primary_repository_id=(
                hit.primary_repository_id.value if hit.primary_repository_id else None
            ),
            repository_contributions=tuple(
                RepositoryContributionModel.from_contribution(item)
                for item in hit.repository_contributions
            ),
            citations=tuple(
                f"{item.source_kind}:{item.source_id}" for item in hit.citations
            ),
        )


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalSearchResultModel:
    hits: tuple[PortfolioRetrievalSearchHitModel, ...]
    mode: str
    top_k: int


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalIndexStatistics:
    index_id: str
    document_count: int
    chunk_count: int
    embedded_chunk_count: int
    repository_count: int
    content_type_counts: dict[str, int]


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalBuildResult:
    index: PortfolioRetrievalIndexDetails
    created: bool
    idempotent: bool


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalCitationLabel:
    label: str
    chunk_id: str
    document_id: str
    canonical_type: str
    canonical_id: str
    repository_ids: tuple[str, ...]
    references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalContextItem:
    label: str
    section: str
    content_type: str
    canonical_type: str
    canonical_id: str
    title: str
    text: str
    score: float
    repository_ids: tuple[str, ...]
    citation: PortfolioRetrievalCitationLabel


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalContextDiagnostic:
    kind: str
    detail: str
    repository_id: str | None = None


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalContext:
    items: tuple[PortfolioRetrievalContextItem, ...]
    sections: tuple[str, ...]
    token_estimate: int
    repository_count: int
    policy_version: str
    truncated: bool
    diagnostics: tuple[PortfolioRetrievalContextDiagnostic, ...]
