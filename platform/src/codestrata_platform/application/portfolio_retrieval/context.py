"""Bounded deterministic portfolio retrieval context assembly."""

from __future__ import annotations

from codestrata_platform.application.portfolio_retrieval.models import (
    PortfolioRetrievalCitationLabel,
    PortfolioRetrievalContext,
    PortfolioRetrievalContextDiagnostic,
    PortfolioRetrievalContextItem,
)
from codestrata_platform.application.portfolio_retrieval.policies import (
    DefaultPortfolioContextPolicy,
)
from codestrata_platform.domain.portfolio_retrieval.errors import PortfolioRetrievalLimitError
from codestrata_platform.domain.portfolio_retrieval.result import PortfolioRetrievalHit
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
from codestrata_platform.domain.retrieval.chunk import estimate_tokens

_MAX_REPEATS_PER_CANONICAL = 3

_SECTION_BY_CONTENT_TYPE: dict[PortfolioRetrievalContentType, str] = {
    PortfolioRetrievalContentType.PORTFOLIO_SUMMARY: "Portfolio Overview",
    PortfolioRetrievalContentType.PORTFOLIO_RISK: "Systemic Risks",
    PortfolioRetrievalContentType.SYSTEMIC_RISK: "Systemic Risks",
    PortfolioRetrievalContentType.PORTFOLIO_TECHNOLOGY: "Technology Landscape",
    PortfolioRetrievalContentType.TECHNOLOGY_STANDARDIZATION: "Technology Landscape",
    PortfolioRetrievalContentType.TECHNOLOGY_FRAGMENTATION: "Technology Landscape",
    PortfolioRetrievalContentType.PORTFOLIO_FINDING: "Recurring Findings",
    PortfolioRetrievalContentType.RECURRING_FINDING: "Recurring Findings",
    PortfolioRetrievalContentType.PORTFOLIO_RECOMMENDATION: "Recurring Recommendations",
    PortfolioRetrievalContentType.RECURRING_RECOMMENDATION: "Recurring Recommendations",
    PortfolioRetrievalContentType.MODERNIZATION_THEME: "Modernization Candidates",
    PortfolioRetrievalContentType.MODERNIZATION_CANDIDATE: "Modernization Candidates",
    PortfolioRetrievalContentType.MODERNIZATION_WAVE: "Modernization Candidates",
    PortfolioRetrievalContentType.PORTFOLIO_COVERAGE: "Portfolio Coverage",
    PortfolioRetrievalContentType.REPOSITORY_PROFILE: "Repository Profiles",
    PortfolioRetrievalContentType.REPOSITORY_RISK_PROFILE: "Repository Profiles",
    PortfolioRetrievalContentType.REPOSITORY_TECHNOLOGY_PROFILE: "Repository Profiles",
    PortfolioRetrievalContentType.REPOSITORY_SUPPORTING_CONTEXT: "Repository Profiles",
    PortfolioRetrievalContentType.CROSS_REPOSITORY_SIGNAL: "Cross-Repository Signals",
    PortfolioRetrievalContentType.SHARED_EXPOSURE: "Cross-Repository Signals",
}

_SECTION_ORDER = (
    "Portfolio Overview",
    "Systemic Risks",
    "Technology Landscape",
    "Recurring Findings",
    "Recurring Recommendations",
    "Modernization Candidates",
    "Portfolio Coverage",
    "Repository Profiles",
    "Cross-Repository Signals",
    "Supporting Context",
)


class PortfolioRetrievalContextAssembler:
    """Assemble a bounded, citable portfolio retrieval context from ranked hits."""

    def __init__(self, *, policy: DefaultPortfolioContextPolicy | None = None) -> None:
        self._policy = policy or DefaultPortfolioContextPolicy()

    def assemble(
        self,
        hits: tuple[PortfolioRetrievalHit, ...],
        *,
        max_tokens: int | None = None,
        max_repositories: int | None = None,
        unavailable_repos: tuple[str, ...] = (),
        stale_repos: tuple[str, ...] = (),
    ) -> PortfolioRetrievalContext:
        token_budget = (
            max_tokens if max_tokens is not None else self._policy.default_max_tokens
        )
        repo_budget = (
            max_repositories
            if max_repositories is not None
            else self._policy.default_max_repositories
        )
        if token_budget < 1 or token_budget > self._policy.hard_max_tokens:
            raise PortfolioRetrievalLimitError(
                f"max_tokens must be between 1 and {self._policy.hard_max_tokens}",
                reason_code="portfolio_context_token_limit_exceeded",
            )
        if repo_budget < 1 or repo_budget > self._policy.hard_max_repositories:
            raise PortfolioRetrievalLimitError(
                "max_repositories must be between 1 and "
                f"{self._policy.hard_max_repositories}",
                reason_code="portfolio_context_repository_limit_exceeded",
            )

        seen_chunks: set[str] = set()
        seen_canonical: set[tuple[str, str]] = set()
        type_counts: dict[str, int] = {}
        included_repositories: dict[str, None] = {}
        excluded_repositories: dict[str, None] = {}
        items: list[PortfolioRetrievalContextItem] = []
        tokens = 0
        truncated = False

        for hit in hits:
            chunk_key = hit.chunk_id.value
            if chunk_key in seen_chunks:
                continue
            canonical_key = (hit.canonical_type, hit.canonical_id)
            if (
                canonical_key in seen_canonical
                and type_counts.get(hit.content_type.value, 0) >= _MAX_REPEATS_PER_CANONICAL
            ):
                continue

            hit_repository_ids = tuple(
                sorted({item.value for item in hit.repository_ids})
            )
            new_repositories = tuple(
                repo for repo in hit_repository_ids if repo not in included_repositories
            )
            projected_repo_count = len(included_repositories) + len(new_repositories)
            if new_repositories and projected_repo_count > repo_budget:
                for repo in new_repositories:
                    excluded_repositories[repo] = None
                continue

            piece_tokens = estimate_tokens(hit.text)
            if tokens + piece_tokens > token_budget:
                truncated = True
                break

            seen_chunks.add(chunk_key)
            seen_canonical.add(canonical_key)
            type_counts[hit.content_type.value] = type_counts.get(hit.content_type.value, 0) + 1
            for repo in new_repositories:
                included_repositories[repo] = None
            tokens += piece_tokens

            label = f"P{len(items) + 1}"
            citation = PortfolioRetrievalCitationLabel(
                label=label,
                chunk_id=hit.chunk_id.value,
                document_id=hit.document_id.value,
                canonical_type=hit.canonical_type,
                canonical_id=hit.canonical_id,
                repository_ids=hit_repository_ids,
                references=tuple(
                    f"{item.source_kind}:{item.source_id}" for item in hit.citations
                ),
            )
            section = _SECTION_BY_CONTENT_TYPE.get(hit.content_type, "Supporting Context")
            items.append(
                PortfolioRetrievalContextItem(
                    label=label,
                    section=section,
                    content_type=hit.content_type.value,
                    canonical_type=hit.canonical_type,
                    canonical_id=hit.canonical_id,
                    title=hit.title,
                    text=hit.text,
                    score=hit.score.final_score,
                    repository_ids=hit_repository_ids,
                    citation=citation,
                )
            )

        diagnostics: list[PortfolioRetrievalContextDiagnostic] = []
        for repo in unavailable_repos:
            diagnostics.append(
                PortfolioRetrievalContextDiagnostic(
                    kind="unavailable_repository",
                    detail=(
                        f"Repository {repo} has no available intelligence and was "
                        "excluded from this context."
                    ),
                    repository_id=repo,
                )
            )
        for repo in stale_repos:
            diagnostics.append(
                PortfolioRetrievalContextDiagnostic(
                    kind="stale_repository",
                    detail=(
                        f"Repository {repo} intelligence is stale and may not reflect "
                        "the current state."
                    ),
                    repository_id=repo,
                )
            )
        for repo in excluded_repositories:
            diagnostics.append(
                PortfolioRetrievalContextDiagnostic(
                    kind="excluded_repository",
                    detail=(
                        f"Repository {repo} was excluded because the context reached "
                        f"its repository limit of {repo_budget}."
                    ),
                    repository_id=repo,
                )
            )
        if truncated:
            diagnostics.append(
                PortfolioRetrievalContextDiagnostic(
                    kind="truncated",
                    detail=f"Context truncated at the {token_budget}-token budget.",
                )
            )

        present_sections = {item.section for item in items}
        sections = tuple(
            section for section in _SECTION_ORDER if section in present_sections
        )

        return PortfolioRetrievalContext(
            items=tuple(items),
            sections=sections,
            token_estimate=tokens,
            repository_count=len(included_repositories),
            policy_version=self._policy.version,
            truncated=truncated,
            diagnostics=tuple(diagnostics),
        )


__all__ = ["PortfolioRetrievalContextAssembler"]
