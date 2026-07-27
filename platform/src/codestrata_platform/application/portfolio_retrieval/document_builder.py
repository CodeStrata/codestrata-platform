"""Build portfolio retrieval documents/chunks from a completed PortfolioSnapshot."""

from __future__ import annotations

from codestrata_platform.application.portfolio_retrieval.policies import (
    PORTFOLIO_CHUNKING_POLICY_VERSION,
    DefaultPortfolioChunkingPolicy,
)
from codestrata_platform.domain.portfolio.coverage import PortfolioCoverageSummary
from codestrata_platform.domain.portfolio.finding import PortfolioFindingSummary
from codestrata_platform.domain.portfolio.lifecycle import TechnologyStandardizationStatus
from codestrata_platform.domain.portfolio.modernization import PortfolioModernizationSummary
from codestrata_platform.domain.portfolio.recommendation import PortfolioRecommendationSummary
from codestrata_platform.domain.portfolio.risk import PortfolioRiskSummary, RepositoryRiskProfile
from codestrata_platform.domain.portfolio.snapshot import PortfolioSnapshot
from codestrata_platform.domain.portfolio.taxonomy import SharedDependencySummary
from codestrata_platform.domain.portfolio.technology import PortfolioTechnology
from codestrata_platform.domain.portfolio_retrieval.chunk import PortfolioRetrievalChunk
from codestrata_platform.domain.portfolio_retrieval.citation import PortfolioRetrievalCitation
from codestrata_platform.domain.portfolio_retrieval.document import PortfolioRetrievalDocument
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    ChunkChecksum,
    PortfolioRetrievalIndexId,
    deterministic_portfolio_chunk_id,
    deterministic_portfolio_document_id,
)
from codestrata_platform.domain.portfolio_retrieval.ranking import (
    HARD_MAX_CONTRIBUTING_REPOSITORIES,
)
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.chunk import estimate_tokens

_STANDARDIZED_STATUSES = frozenset(
    {
        TechnologyStandardizationStatus.STANDARD,
        TechnologyStandardizationStatus.PREFERRED,
        TechnologyStandardizationStatus.COMMON,
    }
)
_FRAGMENTED_STATUSES = frozenset(
    {
        TechnologyStandardizationStatus.FRAGMENTED,
        TechnologyStandardizationStatus.ISOLATED,
    }
)


def _bounded_repository_ids(
    repository_ids: tuple[RepositoryId, ...],
) -> tuple[tuple[RepositoryId, ...], int]:
    unique = sorted({item.value for item in repository_ids})
    total = len(unique)
    bounded = unique[:HARD_MAX_CONTRIBUTING_REPOSITORIES]
    return tuple(RepositoryId(value) for value in bounded), total


class PortfolioRetrievalDocumentBuilder:
    """Build deterministic portfolio-scoped retrieval documents and chunks."""

    def __init__(self, *, policy: DefaultPortfolioChunkingPolicy | None = None) -> None:
        self._policy = policy or DefaultPortfolioChunkingPolicy()

    @property
    def policy_version(self) -> str:
        return self._policy.version or PORTFOLIO_CHUNKING_POLICY_VERSION

    def build(
        self,
        *,
        index_id: PortfolioRetrievalIndexId,
        portfolio_snapshot: PortfolioSnapshot,
    ) -> tuple[tuple[PortfolioRetrievalDocument, ...], tuple[PortfolioRetrievalChunk, ...]]:
        docs_and_texts: list[tuple[PortfolioRetrievalDocument, str]] = []
        docs_and_texts.append(self._portfolio_summary(index_id, portfolio_snapshot))
        docs_and_texts.extend(self._technologies(index_id, portfolio_snapshot))
        docs_and_texts.extend(self._findings(index_id, portfolio_snapshot))
        docs_and_texts.extend(self._recommendations(index_id, portfolio_snapshot))
        docs_and_texts.extend(self._risk(index_id, portfolio_snapshot))
        docs_and_texts.extend(self._modernization(index_id, portfolio_snapshot))
        coverage_doc = self._coverage(index_id, portfolio_snapshot)
        if coverage_doc is not None:
            docs_and_texts.append(coverage_doc)
        docs_and_texts.extend(self._repository_profiles(index_id, portfolio_snapshot))
        docs_and_texts.extend(self._repository_supporting_context(index_id, portfolio_snapshot))
        docs_and_texts.extend(self._dependency_signals(index_id, portfolio_snapshot))

        documents: list[PortfolioRetrievalDocument] = []
        chunks: list[PortfolioRetrievalChunk] = []
        for document, text in docs_and_texts:
            documents.append(document)
            chunks.extend(self._chunk_document(document, text))
        return tuple(documents), tuple(chunks)

    def _frozen_engineering_snapshot_id(
        self,
        snapshot: PortfolioSnapshot,
        repository_id: RepositoryId | None,
    ) -> str | None:
        if repository_id is None:
            return None
        for item in snapshot.repository_selections:
            if item.repository_id == repository_id and item.engineering_snapshot_id:
                return item.engineering_snapshot_id
        return None

    def _document(
        self,
        *,
        index_id: PortfolioRetrievalIndexId,
        snapshot: PortfolioSnapshot,
        content_type: PortfolioRetrievalContentType,
        canonical_type: str,
        canonical_id: str,
        title: str,
        text: str,
        citation_source_kind: str,
        citation_source_id: str,
        structured_content: dict[str, str] | None = None,
        metadata: dict[str, str] | None = None,
        repository_ids: tuple[RepositoryId, ...] = (),
        primary_repository_id: RepositoryId | None = None,
    ) -> tuple[PortfolioRetrievalDocument, str]:
        bounded_repos, total_repos = _bounded_repository_ids(repository_ids)
        meta = dict(metadata or {})
        if total_repos > len(bounded_repos):
            meta["contributing_repository_count"] = str(total_repos)
            meta["contributing_repositories_truncated"] = "true"
        citation_repository = primary_repository_id or (
            bounded_repos[0] if len(bounded_repos) == 1 else None
        )
        document = PortfolioRetrievalDocument(
            document_id=deterministic_portfolio_document_id(
                index_id=index_id.value,
                content_type=content_type.value,
                canonical_id=canonical_id,
            ),
            index_id=index_id,
            portfolio_id=snapshot.portfolio_id,
            portfolio_snapshot_id=snapshot.portfolio_snapshot_id,
            content_type=content_type,
            canonical_type=canonical_type,
            canonical_id=canonical_id,
            title=title,
            summary=text,
            repository_ids=bounded_repos,
            primary_repository_id=primary_repository_id,
            structured_content=structured_content or {},
            citations=(
                PortfolioRetrievalCitation(
                    source_kind=citation_source_kind,
                    source_id=citation_source_id,
                    repository_id=(
                        citation_repository.value if citation_repository is not None else None
                    ),
                    engineering_snapshot_id=self._frozen_engineering_snapshot_id(
                        snapshot,
                        citation_repository,
                    ),
                    portfolio_snapshot_id=snapshot.portfolio_snapshot_id.value,
                ),
            ),
            metadata=meta,
        )
        return document, text

    def _portfolio_summary(
        self,
        index_id: PortfolioRetrievalIndexId,
        snapshot: PortfolioSnapshot,
    ) -> tuple[PortfolioRetrievalDocument, str]:
        risk = (
            snapshot.risk_summary
            if isinstance(snapshot.risk_summary, PortfolioRiskSummary)
            else None
        )
        modernization = (
            snapshot.modernization_summary
            if isinstance(snapshot.modernization_summary, PortfolioModernizationSummary)
            else None
        )
        coverage = (
            snapshot.coverage_summary
            if isinstance(snapshot.coverage_summary, PortfolioCoverageSummary)
            else None
        )
        technology_count = sum(
            1 for item in snapshot.technology_inventory if isinstance(item, PortfolioTechnology)
        )
        wave_counts = ", ".join(
            f"{wave.value}: {count}"
            for wave, count in (modernization.wave_counts if modernization else ())
        ) or "none"
        text = (
            f"Portfolio overview for snapshot {snapshot.portfolio_snapshot_id.value} "
            f"(version {snapshot.version.value}). "
            f"Repositories: {snapshot.repository_count} total, "
            f"{snapshot.available_repository_count} available, "
            f"{snapshot.unavailable_repository_count} unavailable. "
            f"Technologies tracked: {technology_count}. "
            + (
                f"Overall risk score {risk.overall_score} (band {risk.overall_band.value}) "
                f"with {len(risk.systemic_risks)} systemic risk(s). "
                if risk
                else "Risk summary unavailable. "
            )
            + (
                f"Modernization candidates: {len(modernization.candidates)}; "
                f"by wave: {wave_counts}. "
                if modernization
                else "Modernization summary unavailable. "
            )
            + (
                f"Coverage participation {coverage.repository_participation_percentage:.1f}% "
                f"across {coverage.repositories_total} repositories."
                if coverage
                else "Coverage summary unavailable."
            )
        )
        return self._document(
            index_id=index_id,
            snapshot=snapshot,
            content_type=PortfolioRetrievalContentType.PORTFOLIO_SUMMARY,
            canonical_type="portfolio_snapshot",
            canonical_id=snapshot.portfolio_snapshot_id.value,
            title="Portfolio overview",
            text=text,
            citation_source_kind="portfolio_snapshot",
            citation_source_id=snapshot.portfolio_snapshot_id.value,
            structured_content={
                "repository_count": str(snapshot.repository_count),
                "technology_count": str(technology_count),
            },
        )

    def _technologies(
        self,
        index_id: PortfolioRetrievalIndexId,
        snapshot: PortfolioSnapshot,
    ) -> list[tuple[PortfolioRetrievalDocument, str]]:
        results: list[tuple[PortfolioRetrievalDocument, str]] = []
        for tech in snapshot.technology_inventory:
            if not isinstance(tech, PortfolioTechnology):
                continue
            categories = ", ".join(tech.categories) or "uncategorized"
            text = (
                f"Technology {tech.normalized_name} ({tech.canonical_key}). "
                f"Framework: {tech.framework or 'none'}. Categories: {categories}. "
                f"Used in {tech.repository_count} repositories "
                f"({tech.usage_percentage:.1f}% of the portfolio), "
                f"{tech.production_usage_count} in production. "
                f"Findings: {tech.finding_count} total, "
                f"{tech.high_critical_finding_count} high/critical. "
                f"Recommendations: {tech.recommendation_count}. "
                f"Lifecycle signal: {tech.lifecycle_signal.value}. "
                f"Standardization status: {tech.standardization_status.value}."
            )
            results.append(
                self._document(
                    index_id=index_id,
                    snapshot=snapshot,
                    content_type=PortfolioRetrievalContentType.PORTFOLIO_TECHNOLOGY,
                    canonical_type="technology",
                    canonical_id=tech.canonical_key,
                    title=tech.normalized_name,
                    text=text,
                    citation_source_kind="portfolio_technology",
                    citation_source_id=tech.technology_id.value,
                    structured_content={
                        "standardization_status": tech.standardization_status.value,
                        "lifecycle_signal": tech.lifecycle_signal.value,
                    },
                    repository_ids=tech.repository_references,
                )
            )

            if tech.standardization_status in _STANDARDIZED_STATUSES:
                std_text = (
                    f"{tech.normalized_name} is standardized across the portfolio "
                    f"(status: {tech.standardization_status.value}), used by "
                    f"{tech.repository_count} of the portfolio's repositories "
                    f"({tech.usage_percentage:.1f}%). This concentration supports "
                    "consistent tooling, shared expertise, and lower integration risk."
                )
                results.append(
                    self._document(
                        index_id=index_id,
                        snapshot=snapshot,
                        content_type=PortfolioRetrievalContentType.TECHNOLOGY_STANDARDIZATION,
                        canonical_type="technology_standardization",
                        canonical_id=tech.canonical_key,
                        title=f"{tech.normalized_name} standardization",
                        text=std_text,
                        citation_source_kind="portfolio_technology",
                        citation_source_id=tech.technology_id.value,
                        repository_ids=tech.repository_references,
                    )
                )
            elif tech.standardization_status in _FRAGMENTED_STATUSES:
                frag_text = (
                    f"{tech.normalized_name} usage is fragmented across the portfolio "
                    f"(status: {tech.standardization_status.value}), appearing in only "
                    f"{tech.repository_count} repositories "
                    f"({tech.usage_percentage:.1f}%). Fragmented adoption increases "
                    "maintenance overhead and may indicate a modernization or "
                    "standardization opportunity."
                )
                results.append(
                    self._document(
                        index_id=index_id,
                        snapshot=snapshot,
                        content_type=PortfolioRetrievalContentType.TECHNOLOGY_FRAGMENTATION,
                        canonical_type="technology_fragmentation",
                        canonical_id=tech.canonical_key,
                        title=f"{tech.normalized_name} fragmentation",
                        text=frag_text,
                        citation_source_kind="portfolio_technology",
                        citation_source_id=tech.technology_id.value,
                        repository_ids=tech.repository_references,
                    )
                )
        return results

    def _findings(
        self,
        index_id: PortfolioRetrievalIndexId,
        snapshot: PortfolioSnapshot,
    ) -> list[tuple[PortfolioRetrievalDocument, str]]:
        summary = snapshot.finding_inventory[0] if snapshot.finding_inventory else None
        if not isinstance(summary, PortfolioFindingSummary):
            return []
        results: list[tuple[PortfolioRetrievalDocument, str]] = []
        distribution = ", ".join(
            f"{item.severity.value}: {item.count}" for item in summary.severity_distribution
        ) or "none"
        overview_text = (
            f"Portfolio finding summary: {summary.total_findings} findings across "
            f"{summary.repository_count} repositories, {summary.high_critical_count} "
            f"high/critical. Severity distribution: {distribution}. "
            f"Recurring patterns identified: {len(summary.recurring_patterns)}."
        )
        results.append(
            self._document(
                index_id=index_id,
                snapshot=snapshot,
                content_type=PortfolioRetrievalContentType.PORTFOLIO_FINDING,
                canonical_type="portfolio_finding_summary",
                canonical_id=f"{snapshot.portfolio_snapshot_id.value}-findings",
                title="Portfolio finding summary",
                text=overview_text,
                citation_source_kind="portfolio_finding_summary",
                citation_source_id=snapshot.portfolio_snapshot_id.value,
                structured_content={
                    "total_findings": str(summary.total_findings),
                    "high_critical_count": str(summary.high_critical_count),
                },
            )
        )
        for pattern in summary.recurring_patterns:
            severity_text = ", ".join(
                f"{item.severity.value}: {item.count}" for item in pattern.severity_distribution
            ) or "none"
            text = (
                f"Recurring finding pattern for rule {pattern.rule_id} "
                f"({pattern.category.value}). Affects {pattern.repository_count} "
                f"repositories with {pattern.finding_count} findings "
                f"({pattern.production_count} in production). "
                f"Severity distribution: {severity_text}. "
                f"Evidence coverage {pattern.evidence_coverage:.0%}, "
                f"recommendation coverage {pattern.recommendation_coverage:.0%}."
            )
            results.append(
                self._document(
                    index_id=index_id,
                    snapshot=snapshot,
                    content_type=PortfolioRetrievalContentType.RECURRING_FINDING,
                    canonical_type="recurring_finding",
                    canonical_id=pattern.recurrence_key,
                    title=f"Recurring finding: {pattern.rule_id}",
                    text=text,
                    citation_source_kind="recurring_finding_pattern",
                    citation_source_id=pattern.recurrence_key,
                    structured_content={
                        "rule_id": pattern.rule_id,
                        "category": pattern.category.value,
                    },
                    repository_ids=pattern.affected_repositories,
                )
            )
        return results

    def _recommendations(
        self,
        index_id: PortfolioRetrievalIndexId,
        snapshot: PortfolioSnapshot,
    ) -> list[tuple[PortfolioRetrievalDocument, str]]:
        summary = (
            snapshot.recommendation_inventory[0] if snapshot.recommendation_inventory else None
        )
        if not isinstance(summary, PortfolioRecommendationSummary):
            return []
        results: list[tuple[PortfolioRetrievalDocument, str]] = []
        overview_text = (
            f"Portfolio recommendation summary: {summary.total_recommendations} "
            f"recommendations across {summary.repository_count} repositories. "
            f"Recurring patterns: {len(summary.recurring_patterns)}. "
            f"Coverage gaps: {len(summary.coverage_gaps)}."
        )
        results.append(
            self._document(
                index_id=index_id,
                snapshot=snapshot,
                content_type=PortfolioRetrievalContentType.PORTFOLIO_RECOMMENDATION,
                canonical_type="portfolio_recommendation_summary",
                canonical_id=f"{snapshot.portfolio_snapshot_id.value}-recommendations",
                title="Portfolio recommendation summary",
                text=overview_text,
                citation_source_kind="portfolio_recommendation_summary",
                citation_source_id=snapshot.portfolio_snapshot_id.value,
                structured_content={
                    "total_recommendations": str(summary.total_recommendations),
                },
            )
        )
        for pattern in summary.recurring_patterns:
            text = (
                f"Recurring recommendation ({pattern.category.value}, priority "
                f"{pattern.priority}) affecting {pattern.repository_count} repositories "
                f"with {pattern.recommendation_count} recommendations. "
                f"Target technology: {pattern.target_technology or 'none'}. "
                f"Target component: {pattern.target_component or 'none'}. "
                f"Roadmap horizon: {pattern.roadmap_horizon or 'unspecified'}. "
                f"Priority score {pattern.priority_score.score} "
                f"(band {pattern.priority_score.band.value})."
            )
            results.append(
                self._document(
                    index_id=index_id,
                    snapshot=snapshot,
                    content_type=PortfolioRetrievalContentType.RECURRING_RECOMMENDATION,
                    canonical_type="recurring_recommendation",
                    canonical_id=pattern.recurrence_key,
                    title=f"Recurring recommendation: {pattern.recurrence_key}",
                    text=text,
                    citation_source_kind="recurring_recommendation_pattern",
                    citation_source_id=pattern.recurrence_key,
                    structured_content={"category": pattern.category.value},
                    repository_ids=pattern.affected_repositories,
                )
            )
        return results

    def _risk(
        self,
        index_id: PortfolioRetrievalIndexId,
        snapshot: PortfolioSnapshot,
    ) -> list[tuple[PortfolioRetrievalDocument, str]]:
        risk = snapshot.risk_summary
        if not isinstance(risk, PortfolioRiskSummary):
            return []
        results: list[tuple[PortfolioRetrievalDocument, str]] = []
        severity_text = ", ".join(
            f"{item.severity.value}: {item.count}" for item in risk.severity_distribution
        ) or "none"
        overview_text = (
            f"Portfolio risk summary: overall score {risk.overall_score} "
            f"(band {risk.overall_band.value}). Severity distribution: {severity_text}. "
            f"Concentrations: {len(risk.concentrations)}. Hotspots: {len(risk.hotspots)}. "
            f"Systemic risks: {len(risk.systemic_risks)}."
        )
        results.append(
            self._document(
                index_id=index_id,
                snapshot=snapshot,
                content_type=PortfolioRetrievalContentType.PORTFOLIO_RISK,
                canonical_type="portfolio_risk_summary",
                canonical_id=f"{snapshot.portfolio_snapshot_id.value}-risk",
                title="Portfolio risk summary",
                text=overview_text,
                citation_source_kind="portfolio_risk_summary",
                citation_source_id=snapshot.portfolio_snapshot_id.value,
                structured_content={
                    "overall_score": str(risk.overall_score),
                    "overall_band": risk.overall_band.value,
                },
            )
        )
        for systemic in risk.systemic_risks:
            factors = ", ".join(systemic.factors) or "none"
            text = (
                f"Systemic risk: {systemic.title}. Score {systemic.score} "
                f"(band {systemic.band.value}), affecting {systemic.repository_count} "
                f"repositories. Contributing factors: {factors}."
            )
            results.append(
                self._document(
                    index_id=index_id,
                    snapshot=snapshot,
                    content_type=PortfolioRetrievalContentType.SYSTEMIC_RISK,
                    canonical_type="systemic_risk",
                    canonical_id=systemic.systemic_key,
                    title=systemic.title,
                    text=text,
                    citation_source_kind="systemic_risk",
                    citation_source_id=systemic.systemic_key,
                    structured_content={
                        "score": str(systemic.score),
                        "band": systemic.band.value,
                    },
                )
            )
        return results

    def _modernization(
        self,
        index_id: PortfolioRetrievalIndexId,
        snapshot: PortfolioSnapshot,
    ) -> list[tuple[PortfolioRetrievalDocument, str]]:
        modernization = snapshot.modernization_summary
        if not isinstance(modernization, PortfolioModernizationSummary):
            return []
        results: list[tuple[PortfolioRetrievalDocument, str]] = []
        theme_text = ", ".join(
            f"{theme.value}: {count}" for theme, count in modernization.theme_counts
        ) or "none"
        wave_text = ", ".join(
            f"{wave.value}: {count}" for wave, count in modernization.wave_counts
        ) or "none"
        results.append(
            self._document(
                index_id=index_id,
                snapshot=snapshot,
                content_type=PortfolioRetrievalContentType.MODERNIZATION_THEME,
                canonical_type="modernization_theme_distribution",
                canonical_id=f"{snapshot.portfolio_snapshot_id.value}-themes",
                title="Modernization themes",
                text=(
                    f"Portfolio modernization candidates by theme: {theme_text}. "
                    f"Total candidates: {len(modernization.candidates)}."
                ),
                citation_source_kind="portfolio_modernization_summary",
                citation_source_id=snapshot.portfolio_snapshot_id.value,
            )
        )
        results.append(
            self._document(
                index_id=index_id,
                snapshot=snapshot,
                content_type=PortfolioRetrievalContentType.MODERNIZATION_WAVE,
                canonical_type="modernization_wave_distribution",
                canonical_id=f"{snapshot.portfolio_snapshot_id.value}-waves",
                title="Modernization waves",
                text=(
                    f"Portfolio modernization candidates by wave: {wave_text}. "
                    f"Total candidates: {len(modernization.candidates)}."
                ),
                citation_source_kind="portfolio_modernization_summary",
                citation_source_id=snapshot.portfolio_snapshot_id.value,
            )
        )
        for candidate in modernization.candidates:
            technologies = ", ".join(candidate.affected_technologies) or "none"
            text = (
                f"Modernization candidate ({candidate.theme.value}) for repository "
                f"{candidate.repository_id.value}, assigned to {candidate.wave.value}. "
                f"Priority score {candidate.priority.score} "
                f"(band {candidate.priority.band.value}, confidence "
                f"{candidate.priority.confidence:.0%}). "
                f"Affected technologies: {technologies}. "
                f"Related findings: {len(candidate.related_findings)}; "
                f"related recommendations: {len(candidate.related_recommendations)}. "
                f"Evidence coverage {candidate.evidence_coverage:.0%}."
            )
            results.append(
                self._document(
                    index_id=index_id,
                    snapshot=snapshot,
                    content_type=PortfolioRetrievalContentType.MODERNIZATION_CANDIDATE,
                    canonical_type="modernization_candidate",
                    canonical_id=candidate.candidate_id,
                    title=f"Modernization candidate: {candidate.theme.value}",
                    text=text,
                    citation_source_kind="modernization_candidate",
                    citation_source_id=candidate.candidate_id,
                    structured_content={
                        "theme": candidate.theme.value,
                        "wave": candidate.wave.value,
                    },
                    repository_ids=(candidate.repository_id,),
                    primary_repository_id=candidate.repository_id,
                )
            )
        return results

    def _coverage(
        self,
        index_id: PortfolioRetrievalIndexId,
        snapshot: PortfolioSnapshot,
    ) -> tuple[PortfolioRetrievalDocument, str] | None:
        coverage = snapshot.coverage_summary
        if not isinstance(coverage, PortfolioCoverageSummary):
            return None
        text = (
            f"Portfolio coverage summary: {coverage.repositories_total} repositories "
            f"total, {coverage.repositories_with_published_snapshots} with published "
            f"snapshots, {coverage.repositories_without_assessments} without "
            f"assessments, {coverage.repositories_unavailable} unavailable. "
            f"Participation rate {coverage.repository_participation_percentage:.1f}%. "
            f"Freshness: {coverage.freshness.current_count} current, "
            f"{coverage.freshness.aging_count} aging, {coverage.freshness.stale_count} "
            f"stale, {coverage.freshness.unknown_count} unknown. "
            f"Evidence coverage ratio {coverage.evidence.coverage_ratio:.0%}. "
            f"Recommendation coverage ratio {coverage.recommendations.coverage_ratio:.0%}. "
            f"Knowledge graph coverage ratio {coverage.graphs.coverage_ratio:.0%}. "
            f"Technologies covered: {coverage.technology_coverage_count}."
        )
        return self._document(
            index_id=index_id,
            snapshot=snapshot,
            content_type=PortfolioRetrievalContentType.PORTFOLIO_COVERAGE,
            canonical_type="portfolio_coverage_summary",
            canonical_id=f"{snapshot.portfolio_snapshot_id.value}-coverage",
            title="Portfolio coverage summary",
            text=text,
            citation_source_kind="portfolio_coverage_summary",
            citation_source_id=snapshot.portfolio_snapshot_id.value,
            structured_content={
                "repositories_total": str(coverage.repositories_total),
                "participation_percentage": f"{coverage.repository_participation_percentage:.1f}",
            },
        )

    def _repository_profiles(
        self,
        index_id: PortfolioRetrievalIndexId,
        snapshot: PortfolioSnapshot,
    ) -> list[tuple[PortfolioRetrievalDocument, str]]:
        coverage = snapshot.coverage_summary
        risk = snapshot.risk_summary
        coverage_statuses = (
            coverage.repository_statuses if isinstance(coverage, PortfolioCoverageSummary) else ()
        )
        coverage_by_repo = {item.repository_id.value: item for item in coverage_statuses}
        risk_by_repo: dict[str, RepositoryRiskProfile] = {
            item.repository_id.value: item
            for item in (risk.repository_profiles if isinstance(risk, PortfolioRiskSummary) else ())
        }
        repository_keys = sorted(set(coverage_by_repo) | set(risk_by_repo))
        results: list[tuple[PortfolioRetrievalDocument, str]] = []
        for repository_key in repository_keys:
            repository_id = RepositoryId(repository_key)
            cov = coverage_by_repo.get(repository_key)
            risk_profile = risk_by_repo.get(repository_key)
            parts = [f"Repository profile for {repository_key}."]
            if cov is not None:
                parts.append(
                    f"Availability: {cov.availability_status.value}. "
                    f"Published snapshot: {cov.has_published_snapshot}. "
                    f"Completed knowledge graph: {cov.has_completed_graph}. "
                    f"Retrieval index: {cov.has_retrieval_index}. "
                    f"Freshness: {cov.freshness_status.value}"
                    + (
                        f" ({cov.assessment_age_days} days old)."
                        if cov.assessment_age_days is not None
                        else "."
                    )
                )
            if risk_profile is not None:
                factors = ", ".join(risk_profile.factors) or "none"
                parts.append(
                    f"Risk score {risk_profile.score} (band {risk_profile.band.value}). "
                    f"Findings: {risk_profile.finding_count} total, "
                    f"{risk_profile.high_critical_count} high/critical. "
                    f"Evidence gaps: {risk_profile.evidence_gap_count}; "
                    f"recommendation gaps: {risk_profile.recommendation_gap_count}. "
                    f"Factors: {factors}."
                )
            text = " ".join(parts)
            results.append(
                self._document(
                    index_id=index_id,
                    snapshot=snapshot,
                    content_type=PortfolioRetrievalContentType.REPOSITORY_PROFILE,
                    canonical_type="repository",
                    canonical_id=repository_key,
                    title=f"Repository profile: {repository_key}",
                    text=text,
                    citation_source_kind="repository_profile",
                    citation_source_id=repository_key,
                    repository_ids=(repository_id,),
                    primary_repository_id=repository_id,
                )
            )
        return results

    def _repository_supporting_context(
        self,
        index_id: PortfolioRetrievalIndexId,
        snapshot: PortfolioSnapshot,
    ) -> list[tuple[PortfolioRetrievalDocument, str]]:
        results: list[tuple[PortfolioRetrievalDocument, str]] = []
        for selection in sorted(
            snapshot.repository_selections,
            key=lambda item: item.repository_id.value,
        ):
            text = (
                f"Frozen repository supporting context for {selection.repository_id.value}. "
                f"Availability: {selection.availability_status.value}. "
                f"Criticality: {selection.criticality.value}. "
                f"Engineering snapshot: {selection.engineering_snapshot_id or 'none'} "
                f"(version {selection.engineering_snapshot_version or 0}). "
                f"Knowledge graph: {selection.knowledge_graph_id or 'none'} "
                f"(version {selection.knowledge_graph_version or 0})."
            )
            results.append(
                self._document(
                    index_id=index_id,
                    snapshot=snapshot,
                    content_type=PortfolioRetrievalContentType.REPOSITORY_SUPPORTING_CONTEXT,
                    canonical_type="repository_supporting_context",
                    canonical_id=selection.repository_id.value,
                    title=f"Supporting context: {selection.repository_id.value}",
                    text=text,
                    citation_source_kind="repository_selection",
                    citation_source_id=selection.repository_id.value,
                    structured_content={
                        "engineering_snapshot_id": selection.engineering_snapshot_id or "",
                        "engineering_snapshot_version": str(
                            selection.engineering_snapshot_version or 0
                        ),
                        "knowledge_graph_id": selection.knowledge_graph_id or "",
                        "knowledge_graph_version": str(selection.knowledge_graph_version or 0),
                        "availability_status": selection.availability_status.value,
                        "criticality": selection.criticality.value,
                    },
                    repository_ids=(selection.repository_id,),
                    primary_repository_id=selection.repository_id,
                )
            )
        return results

    def _dependency_signals(
        self,
        index_id: PortfolioRetrievalIndexId,
        snapshot: PortfolioSnapshot,
    ) -> list[tuple[PortfolioRetrievalDocument, str]]:
        dependencies = snapshot.dependency_signals[0] if snapshot.dependency_signals else None
        if not isinstance(dependencies, SharedDependencySummary):
            return []
        results: list[tuple[PortfolioRetrievalDocument, str]] = []
        for signal in dependencies.signals:
            content_type = (
                PortfolioRetrievalContentType.SHARED_EXPOSURE
                if signal.is_shared_exposure
                else PortfolioRetrievalContentType.CROSS_REPOSITORY_SIGNAL
            )
            text = (
                f"{'Shared exposure' if signal.is_shared_exposure else 'Cross-repository signal'} "
                f"({signal.signal_type.value}): {signal.description}. "
                f"Shared key: {signal.shared_key}. "
                f"Affects {len(signal.repository_ids)} repositories."
            )
            results.append(
                self._document(
                    index_id=index_id,
                    snapshot=snapshot,
                    content_type=content_type,
                    canonical_type=(
                        "shared_exposure"
                        if signal.is_shared_exposure
                        else "cross_repository_signal"
                    ),
                    canonical_id=signal.signal_key,
                    title=signal.signal_type.value.replace("_", " ").title(),
                    text=text,
                    citation_source_kind="cross_repository_dependency_signal",
                    citation_source_id=signal.signal_key,
                    structured_content={"signal_type": signal.signal_type.value},
                    repository_ids=signal.repository_ids,
                )
            )
        return results

    def _chunk_document(
        self,
        document: PortfolioRetrievalDocument,
        text: str,
    ) -> tuple[PortfolioRetrievalChunk, ...]:
        max_chars = self._policy.hard_max_tokens * 4
        parts: list[str] = []
        remaining = text.strip()
        while remaining:
            piece = remaining[:max_chars].rstrip()
            if estimate_tokens(piece) > self._policy.hard_max_tokens:
                piece = remaining[: self._policy.hard_max_tokens * 4].rstrip()
            parts.append(piece)
            remaining = remaining[len(piece) :].lstrip()
        if not parts:
            parts = [document.summary]
        chunks: list[PortfolioRetrievalChunk] = []
        for ordinal, part in enumerate(parts):
            chunk_text = part if ordinal == 0 else f"{document.title}. {part}"
            if estimate_tokens(chunk_text) > self._policy.hard_max_tokens:
                overflow = self._policy.hard_max_tokens * 4
                chunk_text = chunk_text[:overflow].rstrip()
            checksum = ChunkChecksum.from_text(chunk_text)
            chunks.append(
                PortfolioRetrievalChunk(
                    chunk_id=deterministic_portfolio_chunk_id(
                        document_id=document.document_id.value,
                        ordinal=ordinal,
                        checksum=checksum.value,
                    ),
                    document_id=document.document_id,
                    index_id=document.index_id,
                    portfolio_id=document.portfolio_id,
                    portfolio_snapshot_id=document.portfolio_snapshot_id,
                    ordinal=ordinal,
                    text=chunk_text,
                    token_estimate=estimate_tokens(chunk_text),
                    checksum=checksum,
                    repository_ids=document.repository_ids,
                    primary_repository_id=document.primary_repository_id,
                    citations=document.citations,
                    metadata=dict(document.metadata),
                )
            )
        return tuple(chunks)


__all__ = ["PortfolioRetrievalDocumentBuilder"]
