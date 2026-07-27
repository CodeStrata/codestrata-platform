"""Portfolio retrieval document value objects."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio_retrieval.citation import PortfolioRetrievalCitation
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    PortfolioRetrievalDocumentId,
    PortfolioRetrievalIndexId,
)
from codestrata_platform.domain.portfolio_retrieval.ranking import (
    HARD_MAX_CONTRIBUTING_REPOSITORIES,
)
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.document import sanitize_retrieval_text

_MAX_TITLE = 256
_MAX_SUMMARY = 4000
_MAX_METADATA = 40


def _bounded(value: str, *, field_name: str, max_length: int) -> str:
    compact = value.strip()
    if not compact:
        raise InvalidValueError(
            f"{field_name} must be non-blank",
            reason_code=f"empty_{field_name}",
        )
    if len(compact) > max_length:
        raise InvalidValueError(
            f"{field_name} exceeds maximum length",
            reason_code=f"{field_name}_too_long",
        )
    return compact


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalDocument:
    """Portfolio-scoped retrieval document with portfolio/repository provenance."""

    document_id: PortfolioRetrievalDocumentId
    index_id: PortfolioRetrievalIndexId
    portfolio_id: PortfolioId
    portfolio_snapshot_id: PortfolioSnapshotId
    content_type: PortfolioRetrievalContentType
    canonical_type: str
    canonical_id: str
    title: str
    summary: str
    repository_ids: tuple[RepositoryId, ...] = ()
    primary_repository_id: RepositoryId | None = None
    structured_content: Mapping[str, str] = field(default_factory=dict)
    citations: tuple[PortfolioRetrievalCitation, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)
    checksum: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_type",
            _bounded(self.canonical_type, field_name="canonical_type", max_length=64),
        )
        object.__setattr__(
            self,
            "canonical_id",
            _bounded(self.canonical_id, field_name="canonical_id", max_length=160),
        )
        object.__setattr__(
            self,
            "title",
            _bounded(self.title, field_name="title", max_length=_MAX_TITLE),
        )
        object.__setattr__(
            self,
            "summary",
            sanitize_retrieval_text(self.summary, max_length=_MAX_SUMMARY),
        )
        if len(self.repository_ids) > HARD_MAX_CONTRIBUTING_REPOSITORIES:
            raise InvalidValueError(
                "repository_ids exceeds maximum contributing repositories of "
                f"{HARD_MAX_CONTRIBUTING_REPOSITORIES}",
                reason_code="portfolio_retrieval_document_repositories_too_large",
            )
        if self.primary_repository_id is not None and self.repository_ids:
            if self.primary_repository_id not in self.repository_ids:
                raise InvalidValueError(
                    "primary_repository_id must be included in repository_ids",
                    reason_code="portfolio_retrieval_document_primary_repository_missing",
                )
        if not self.citations:
            raise InvalidValueError(
                "Portfolio retrieval documents require citations",
                reason_code="missing_portfolio_retrieval_citations",
            )
        structured = {
            str(key).strip(): sanitize_retrieval_text(str(value), max_length=2000)
            for key, value in dict(self.structured_content).items()
            if str(key).strip() and str(value).strip()
        }
        if len(structured) > _MAX_METADATA:
            raise InvalidValueError(
                "structured_content exceeds maximum keys",
                reason_code="portfolio_retrieval_structured_content_too_large",
            )
        metadata = {
            str(key).strip(): str(value).strip()[:256]
            for key, value in dict(self.metadata).items()
            if str(key).strip() and str(value).strip()
        }
        if len(metadata) > _MAX_METADATA:
            raise InvalidValueError(
                "metadata exceeds maximum keys",
                reason_code="portfolio_retrieval_metadata_too_large",
            )
        object.__setattr__(self, "structured_content", dict(sorted(structured.items())))
        object.__setattr__(self, "metadata", dict(sorted(metadata.items())))
        digest = self.checksum.strip().lower() or self.compute_checksum()
        object.__setattr__(self, "checksum", digest)

    def compute_checksum(self) -> str:
        payload = "|".join(
            [
                self.content_type.value,
                self.canonical_type,
                self.canonical_id,
                self.title,
                self.summary,
                repr(sorted(self.structured_content.items())),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
