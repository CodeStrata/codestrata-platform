"""Portfolio retrieval query and score value objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.portfolio_retrieval.errors import PortfolioRetrievalLimitError
from codestrata_platform.domain.portfolio_retrieval.lifecycle import RepositoryBalanceMode
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode

DEFAULT_TOP_K = 10
HARD_MAX_TOP_K = 100
_MAX_FILTERS = 40
HARD_MAX_QUERY_REPOSITORIES = 200


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalQuery:
    query_text: str
    mode: RetrievalMode = RetrievalMode.HYBRID
    top_k: int = DEFAULT_TOP_K
    content_types: tuple[PortfolioRetrievalContentType, ...] = ()
    filters: Mapping[str, str] = field(default_factory=dict)
    repository_ids: tuple[RepositoryId, ...] = ()
    exclude_repository_ids: tuple[RepositoryId, ...] = ()
    repository_balance_mode: RepositoryBalanceMode = RepositoryBalanceMode.NONE
    include_portfolio_aggregates: bool = True
    include_repository_context: bool = True
    include_score_breakdown: bool = True

    def __post_init__(self) -> None:
        compact = self.query_text.strip()
        if not compact:
            raise InvalidValueError(
                "query_text must be non-blank",
                reason_code="empty_portfolio_retrieval_query",
            )
        object.__setattr__(self, "query_text", compact)
        if self.top_k < 1 or self.top_k > HARD_MAX_TOP_K:
            raise PortfolioRetrievalLimitError(
                f"top_k must be between 1 and {HARD_MAX_TOP_K}",
                reason_code="portfolio_retrieval_top_k_exceeded",
            )
        if len(self.repository_ids) > HARD_MAX_QUERY_REPOSITORIES:
            raise PortfolioRetrievalLimitError(
                f"repository_ids may contain at most {HARD_MAX_QUERY_REPOSITORIES} entries",
                reason_code="portfolio_retrieval_repository_filter_too_large",
            )
        if len(self.exclude_repository_ids) > HARD_MAX_QUERY_REPOSITORIES:
            raise PortfolioRetrievalLimitError(
                "exclude_repository_ids may contain at most "
                f"{HARD_MAX_QUERY_REPOSITORIES} entries",
                reason_code="portfolio_retrieval_exclude_repository_filter_too_large",
            )
        included = set(self.repository_ids)
        excluded = set(self.exclude_repository_ids)
        if included & excluded:
            raise InvalidValueError(
                "repository_ids and exclude_repository_ids must not overlap",
                reason_code="portfolio_retrieval_conflicting_repository_filters",
            )
        filters = {
            str(key).strip(): str(value).strip()[:256]
            for key, value in dict(self.filters).items()
            if str(key).strip() and str(value).strip()
        }
        if len(filters) > _MAX_FILTERS:
            raise InvalidValueError(
                "filters exceeds maximum keys",
                reason_code="portfolio_retrieval_filters_too_large",
            )
        object.__setattr__(self, "filters", dict(sorted(filters.items())))


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalScore:
    lexical_score: float = 0.0
    vector_score: float = 0.0
    portfolio_score: float = 0.0
    repository_score: float = 0.0
    systemic_score: float = 0.0
    source_quality_score: float = 0.0
    freshness_score: float = 0.0
    balance_adjustment: float = 0.0
    final_score: float = 0.0
    ranking_policy_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name in (
            "lexical_score",
            "vector_score",
            "portfolio_score",
            "repository_score",
            "systemic_score",
            "source_quality_score",
            "freshness_score",
            "final_score",
        ):
            value = float(getattr(self, name))
            if value < 0:
                raise InvalidValueError(
                    f"{name} must be >= 0",
                    reason_code="invalid_portfolio_retrieval_score",
                )
        adjustment = float(self.balance_adjustment)
        if adjustment != adjustment or adjustment in {float("inf"), float("-inf")}:
            raise InvalidValueError(
                "balance_adjustment must be finite",
                reason_code="invalid_portfolio_retrieval_balance_adjustment",
            )
        compact_version = self.ranking_policy_version.strip()
        if not compact_version:
            raise InvalidValueError(
                "ranking_policy_version must be non-blank",
                reason_code="empty_ranking_policy_version",
            )
        object.__setattr__(self, "ranking_policy_version", compact_version)
