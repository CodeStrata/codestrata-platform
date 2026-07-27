"""EngineeringPortfolio / PortfolioSnapshot ↔ persistence mappers."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.enums import EngineeringCategory, EngineeringSeverity
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.coverage import (
    AssessmentFreshnessSummary,
    EvidenceCoverageSummary,
    GraphCoverageSummary,
    PortfolioCoverageSummary,
    RecommendationCoverageSummary,
    RepositoryCoverageStatus,
)
from codestrata_platform.domain.portfolio.finding import (
    FindingConcentration,
    PortfolioFindingCluster,
    PortfolioFindingDistribution,
    PortfolioFindingSummary,
    RecurringFindingPattern,
)
from codestrata_platform.domain.portfolio.identifiers import (
    PortfolioDescription,
    PortfolioId,
    PortfolioMembershipId,
    PortfolioName,
    PortfolioPolicyVersion,
    PortfolioProjectionKey,
    PortfolioSnapshotId,
    PortfolioSnapshotVersion,
    PortfolioTechnologyId,
)
from codestrata_platform.domain.portfolio.lifecycle import (
    AssessmentFreshnessStatus,
    DependencySignalType,
    ModernizationTheme,
    ModernizationWave,
    PortfolioSnapshotStatus,
    PortfolioStatus,
    PriorityBand,
    RepositoryAvailabilityStatus,
    RepositoryCriticality,
    TechnologyLifecycleSignal,
    TechnologyStandardizationStatus,
)
from codestrata_platform.domain.portfolio.membership import PortfolioMembership
from codestrata_platform.domain.portfolio.modernization import (
    ModernizationCandidate,
    ModernizationConstraint,
    ModernizationDependency,
    ModernizationPriorityScore,
    PortfolioModernizationSummary,
)
from codestrata_platform.domain.portfolio.portfolio import EngineeringPortfolio
from codestrata_platform.domain.portfolio.recommendation import (
    PortfolioRecommendationPriority,
    PortfolioRecommendationSummary,
    RecommendationConcentration,
    RecommendationCoverageGap,
    RecurringRecommendationPattern,
)
from codestrata_platform.domain.portfolio.risk import (
    PortfolioRiskConcentration,
    PortfolioRiskDistribution,
    PortfolioRiskHotspot,
    PortfolioRiskSummary,
    RepositoryRiskProfile,
    SystemicRisk,
    TechnologyRiskProfile,
)
from codestrata_platform.domain.portfolio.snapshot import (
    PortfolioRepositorySnapshotSelection,
    PortfolioSnapshot,
)
from codestrata_platform.domain.portfolio.taxonomy import (
    CrossRepositoryDependencySignal,
    SharedDependencySummary,
)
from codestrata_platform.domain.portfolio.technology import (
    PortfolioTechnology,
    PortfolioTechnologyUsage,
    TechnologyConcentration,
)
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import (
    audit_from_record,
    ensure_utc,
)
from codestrata_platform.infrastructure.persistence.models.portfolio_records import (
    EngineeringPortfolioAnalysisRunRecord,
    EngineeringPortfolioFindingRecord,
    EngineeringPortfolioMembershipRecord,
    EngineeringPortfolioModernizationCandidateRecord,
    EngineeringPortfolioRecommendationRecord,
    EngineeringPortfolioRecord,
    EngineeringPortfolioRepositorySnapshotRecord,
    EngineeringPortfolioRiskRecord,
    EngineeringPortfolioSnapshotRecord,
    EngineeringPortfolioTechnologyRecord,
)

_SUMMARY_ONLY_KEY = "_portfolio_summary"
_DIAG_COVERAGE = "coverage_summary"
_DIAG_DEPENDENCIES = "dependency_summary"
_DIAG_MODERNIZATION = "modernization_meta"


def _repo_ids(values: list[Any] | tuple[Any, ...] | None) -> tuple[RepositoryId, ...]:
    return tuple(RepositoryId(str(item)) for item in (values or ()))


class PortfolioMapper:
    # ------------------------------------------------------------------
    # Portfolio aggregate
    # ------------------------------------------------------------------

    @staticmethod
    def to_portfolio_record(
        portfolio: EngineeringPortfolio,
    ) -> tuple[EngineeringPortfolioRecord, list[EngineeringPortfolioMembershipRecord]]:
        record = EngineeringPortfolioRecord(
            portfolio_id=portfolio.portfolio_id.value,
            organization_id=portfolio.organization_id.value,
            workspace_id=portfolio.workspace_id.value,
            name=portfolio.name.value,
            description=portfolio.description.value,
            status=portfolio.status.value,
            max_repositories=portfolio.max_repositories,
            created_at=portfolio.audit.created_at.value,
            updated_at=portfolio.audit.updated_at.value,
            archived_at=portfolio.archived_at,
            optimistic_version=portfolio._version,
        )
        memberships = [
            EngineeringPortfolioMembershipRecord(
                membership_id=item.membership_id.value,
                portfolio_id=portfolio.portfolio_id.value,
                repository_id=item.repository_id.value,
                criticality=item.criticality.value,
                business_capability=item.business_capability,
                owner_reference=item.owner_reference,
                lifecycle_status=item.lifecycle_status,
                tags=list(item.tags),
                added_at=item.added_at,
                removed_at=item.removed_at,
            )
            for item in portfolio.memberships
        ]
        return record, memberships

    @staticmethod
    def apply_portfolio_to_record(
        portfolio: EngineeringPortfolio,
        record: EngineeringPortfolioRecord,
    ) -> None:
        fresh, _ = PortfolioMapper.to_portfolio_record(portfolio)
        for column in EngineeringPortfolioRecord.__table__.columns:
            if column.name == "portfolio_id":
                continue
            setattr(record, column.name, getattr(fresh, column.name))

    @staticmethod
    def from_portfolio_record(
        record: EngineeringPortfolioRecord,
        memberships: list[EngineeringPortfolioMembershipRecord],
    ) -> EngineeringPortfolio:
        org = OrganizationId(record.organization_id)
        workspace = WorkspaceId(record.workspace_id)
        portfolio_id = PortfolioId(record.portfolio_id)
        domain_memberships = tuple(
            PortfolioMembership(
                membership_id=PortfolioMembershipId(item.membership_id),
                portfolio_id=portfolio_id,
                organization_id=org,
                workspace_id=workspace,
                repository_id=RepositoryId(item.repository_id),
                criticality=RepositoryCriticality(item.criticality),
                business_capability=item.business_capability,
                owner_reference=item.owner_reference,
                lifecycle_status=item.lifecycle_status,
                tags=tuple(str(tag) for tag in (item.tags or [])),
                added_at=ensure_utc(item.added_at),
                removed_at=ensure_utc(item.removed_at) if item.removed_at else None,
            )
            for item in memberships
        )
        return EngineeringPortfolio(
            portfolio_id=portfolio_id,
            organization_id=org,
            workspace_id=workspace,
            name=PortfolioName(record.name),
            description=PortfolioDescription(record.description),
            status=PortfolioStatus(record.status),
            memberships=domain_memberships,
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            archived_at=ensure_utc(record.archived_at) if record.archived_at else None,
            max_repositories=record.max_repositories,
            _version=record.optimistic_version,
        )

    # ------------------------------------------------------------------
    # Snapshot aggregate
    # ------------------------------------------------------------------

    @staticmethod
    def to_snapshot_records(
        snapshot: PortfolioSnapshot,
    ) -> tuple[
        EngineeringPortfolioSnapshotRecord,
        list[EngineeringPortfolioRepositorySnapshotRecord],
        list[EngineeringPortfolioTechnologyRecord],
        list[EngineeringPortfolioFindingRecord],
        list[EngineeringPortfolioRecommendationRecord],
        EngineeringPortfolioRiskRecord | None,
        list[EngineeringPortfolioModernizationCandidateRecord],
        EngineeringPortfolioAnalysisRunRecord | None,
    ]:
        snap_id = snapshot.portfolio_snapshot_id.value
        snapshot_record = EngineeringPortfolioSnapshotRecord(
            portfolio_snapshot_id=snap_id,
            portfolio_id=snapshot.portfolio_id.value,
            organization_id=snapshot.organization_id.value,
            workspace_id=snapshot.workspace_id.value,
            snapshot_version=snapshot.version.value,
            status=snapshot.status.value,
            projection_key=snapshot.projection_key.value,
            portfolio_schema_version=snapshot.portfolio_schema_version,
            aggregation_policy_version=snapshot.aggregation_policy_version.value,
            repository_count=snapshot.repository_count,
            available_repository_count=snapshot.available_repository_count,
            unavailable_repository_count=snapshot.unavailable_repository_count,
            created_at=snapshot.audit.created_at.value,
            updated_at=snapshot.audit.updated_at.value,
            completed_at=snapshot.completed_at,
            superseded_at=snapshot.superseded_at,
            failure_reason=snapshot.failure_reason,
            optimistic_version=snapshot._version,
        )

        repo_records = [
            EngineeringPortfolioRepositorySnapshotRecord(
                id=f"{snap_id}:repo:{item.repository_id.value}",
                portfolio_snapshot_id=snap_id,
                repository_id=item.repository_id.value,
                assessment_id=item.assessment_id.value if item.assessment_id else None,
                engineering_snapshot_id=item.engineering_snapshot_id,
                engineering_snapshot_version=item.engineering_snapshot_version,
                knowledge_graph_id=item.knowledge_graph_id,
                knowledge_graph_version=item.knowledge_graph_version,
                availability_status=item.availability_status.value,
                criticality=item.criticality.value,
                selected_at=item.selected_at,
                graph_intelligence_policy_version=item.graph_intelligence_policy_version,
            )
            for item in snapshot.repository_selections
        ]

        tech_records = [
            PortfolioMapper._technology_to_record(snap_id, item)
            for item in snapshot.technology_inventory
            if isinstance(item, PortfolioTechnology)
        ]

        finding_records = PortfolioMapper._finding_records(snap_id, snapshot.finding_inventory)
        recommendation_records = PortfolioMapper._recommendation_records(
            snap_id, snapshot.recommendation_inventory
        )

        risk_record = None
        if isinstance(snapshot.risk_summary, PortfolioRiskSummary):
            risk_record = PortfolioMapper._risk_to_record(snap_id, snapshot.risk_summary)

        modernization_records: list[EngineeringPortfolioModernizationCandidateRecord] = []
        modernization_meta: dict[str, Any] = {}
        if isinstance(snapshot.modernization_summary, PortfolioModernizationSummary):
            modernization_meta = PortfolioMapper._modernization_meta(
                snapshot.modernization_summary
            )
            modernization_records = [
                PortfolioMapper._modernization_candidate_to_record(
                    snap_id, candidate, modernization_meta
                )
                for candidate in snapshot.modernization_summary.candidates
            ]

        analysis_run = PortfolioMapper._analysis_run_for_snapshot(
            snapshot,
            coverage=snapshot.coverage_summary
            if isinstance(snapshot.coverage_summary, PortfolioCoverageSummary)
            else None,
            dependencies=PortfolioMapper._dependency_summary(snapshot.dependency_signals),
            modernization_meta=modernization_meta or None,
        )

        return (
            snapshot_record,
            repo_records,
            tech_records,
            finding_records,
            recommendation_records,
            risk_record,
            modernization_records,
            analysis_run,
        )

    @staticmethod
    def apply_snapshot_to_record(
        snapshot: PortfolioSnapshot,
        record: EngineeringPortfolioSnapshotRecord,
    ) -> None:
        fresh, *_ = PortfolioMapper.to_snapshot_records(snapshot)
        for column in EngineeringPortfolioSnapshotRecord.__table__.columns:
            if column.name == "portfolio_snapshot_id":
                continue
            setattr(record, column.name, getattr(fresh, column.name))

    @staticmethod
    def from_snapshot_records(
        record: EngineeringPortfolioSnapshotRecord,
        *,
        repository_records: list[EngineeringPortfolioRepositorySnapshotRecord],
        technology_records: list[EngineeringPortfolioTechnologyRecord],
        finding_records: list[EngineeringPortfolioFindingRecord],
        recommendation_records: list[EngineeringPortfolioRecommendationRecord],
        risk_record: EngineeringPortfolioRiskRecord | None,
        modernization_records: list[EngineeringPortfolioModernizationCandidateRecord],
        analysis_run: EngineeringPortfolioAnalysisRunRecord | None,
    ) -> PortfolioSnapshot:
        diagnostics = dict(analysis_run.diagnostics or {}) if analysis_run is not None else {}
        coverage = None
        if _DIAG_COVERAGE in diagnostics:
            coverage = PortfolioMapper.coverage_from_json(diagnostics[_DIAG_COVERAGE])
        dependencies: tuple[object, ...] = ()
        if _DIAG_DEPENDENCIES in diagnostics:
            dependencies = (
                PortfolioMapper.dependency_summary_from_json(diagnostics[_DIAG_DEPENDENCIES]),
            )

        finding_inventory = PortfolioMapper._findings_from_records(finding_records)
        recommendation_inventory = PortfolioMapper._recommendations_from_records(
            recommendation_records
        )
        risk_summary = (
            PortfolioMapper._risk_from_record(risk_record) if risk_record is not None else None
        )
        modernization_summary = PortfolioMapper._modernization_from_records(
            modernization_records,
            diagnostics.get(_DIAG_MODERNIZATION),
        )

        return PortfolioSnapshot(
            portfolio_snapshot_id=PortfolioSnapshotId(record.portfolio_snapshot_id),
            portfolio_id=PortfolioId(record.portfolio_id),
            organization_id=OrganizationId(record.organization_id),
            workspace_id=WorkspaceId(record.workspace_id),
            version=PortfolioSnapshotVersion(record.snapshot_version),
            status=PortfolioSnapshotStatus(record.status),
            projection_key=PortfolioProjectionKey(record.projection_key),
            portfolio_schema_version=record.portfolio_schema_version,
            aggregation_policy_version=PortfolioPolicyVersion(record.aggregation_policy_version),
            repository_selections=tuple(
                PortfolioRepositorySnapshotSelection(
                    repository_id=RepositoryId(item.repository_id),
                    availability_status=RepositoryAvailabilityStatus(item.availability_status),
                    selected_at=ensure_utc(item.selected_at),
                    criticality=RepositoryCriticality(item.criticality),
                    assessment_id=(
                        AssessmentId(item.assessment_id) if item.assessment_id else None
                    ),
                    engineering_snapshot_id=item.engineering_snapshot_id,
                    engineering_snapshot_version=item.engineering_snapshot_version,
                    knowledge_graph_id=item.knowledge_graph_id,
                    knowledge_graph_version=item.knowledge_graph_version,
                    graph_intelligence_policy_version=item.graph_intelligence_policy_version,
                )
                for item in repository_records
            ),
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            completed_at=ensure_utc(record.completed_at) if record.completed_at else None,
            superseded_at=ensure_utc(record.superseded_at) if record.superseded_at else None,
            failure_reason=record.failure_reason,
            technology_inventory=tuple(
                PortfolioMapper._technology_from_record(item) for item in technology_records
            ),
            finding_inventory=finding_inventory,
            recommendation_inventory=recommendation_inventory,
            risk_summary=risk_summary,
            modernization_summary=modernization_summary,
            coverage_summary=coverage,
            dependency_signals=dependencies,
            _version=record.optimistic_version,
        )

    # ------------------------------------------------------------------
    # Technology
    # ------------------------------------------------------------------

    @staticmethod
    def _technology_to_record(
        snap_id: str,
        item: PortfolioTechnology,
    ) -> EngineeringPortfolioTechnologyRecord:
        return EngineeringPortfolioTechnologyRecord(
            technology_id=item.technology_id.value,
            portfolio_snapshot_id=snap_id,
            canonical_key=item.canonical_key,
            normalized_name=item.normalized_name,
            framework=item.framework,
            categories=list(item.categories),
            repository_count=item.repository_count,
            repository_references=[ref.value for ref in item.repository_references],
            component_count=item.component_count,
            finding_count=item.finding_count,
            high_critical_finding_count=item.high_critical_finding_count,
            recommendation_count=item.recommendation_count,
            usage_percentage=item.usage_percentage,
            production_usage_count=item.production_usage_count,
            lifecycle_signal=item.lifecycle_signal.value,
            standardization_status=item.standardization_status.value,
            source_snapshot_references=list(item.source_snapshot_references),
            usages=[PortfolioMapper.technology_usage_to_json(usage) for usage in item.usages],
        )

    @staticmethod
    def _technology_from_record(
        record: EngineeringPortfolioTechnologyRecord,
    ) -> PortfolioTechnology:
        return PortfolioTechnology(
            technology_id=PortfolioTechnologyId(record.technology_id),
            canonical_key=record.canonical_key,
            normalized_name=record.normalized_name,
            framework=record.framework,
            categories=tuple(str(item) for item in (record.categories or [])),
            repository_count=record.repository_count,
            repository_references=_repo_ids(record.repository_references),
            component_count=record.component_count,
            finding_count=record.finding_count,
            high_critical_finding_count=record.high_critical_finding_count,
            recommendation_count=record.recommendation_count,
            usage_percentage=float(record.usage_percentage),
            production_usage_count=record.production_usage_count,
            lifecycle_signal=TechnologyLifecycleSignal(record.lifecycle_signal),
            standardization_status=TechnologyStandardizationStatus(record.standardization_status),
            concentration=TechnologyConcentration(
                repository_count=record.repository_count,
                usage_percentage=float(record.usage_percentage),
                production_usage_count=record.production_usage_count,
            ),
            source_snapshot_references=tuple(
                str(item) for item in (record.source_snapshot_references or [])
            ),
            usages=tuple(
                PortfolioMapper.technology_usage_from_json(item)
                for item in (record.usages or [])
            ),
        )

    @staticmethod
    def technology_usage_to_json(usage: PortfolioTechnologyUsage) -> dict[str, Any]:
        return {
            "repository_id": usage.repository_id.value,
            "engineering_snapshot_id": usage.engineering_snapshot_id,
            "component_count": usage.component_count,
            "finding_count": usage.finding_count,
            "high_critical_finding_count": usage.high_critical_finding_count,
            "recommendation_count": usage.recommendation_count,
            "production_scope": usage.production_scope,
        }

    @staticmethod
    def technology_usage_from_json(payload: dict[str, Any]) -> PortfolioTechnologyUsage:
        return PortfolioTechnologyUsage(
            repository_id=RepositoryId(str(payload["repository_id"])),
            engineering_snapshot_id=str(payload["engineering_snapshot_id"]),
            component_count=int(payload["component_count"]),
            finding_count=int(payload["finding_count"]),
            high_critical_finding_count=int(payload["high_critical_finding_count"]),
            recommendation_count=int(payload["recommendation_count"]),
            production_scope=bool(payload.get("production_scope", False)),
        )

    # ------------------------------------------------------------------
    # Findings
    # ------------------------------------------------------------------

    @staticmethod
    def _finding_records(
        snap_id: str,
        inventory: tuple[object, ...],
    ) -> list[EngineeringPortfolioFindingRecord]:
        summary = next(
            (item for item in inventory if isinstance(item, PortfolioFindingSummary)),
            None,
        )
        if summary is None:
            return []
        totals = PortfolioMapper._finding_summary_totals(summary)
        patterns = list(summary.recurring_patterns)
        if not patterns:
            return [
                EngineeringPortfolioFindingRecord(
                    id=f"{snap_id}:finding:{_SUMMARY_ONLY_KEY}",
                    portfolio_snapshot_id=snap_id,
                    recurrence_key=_SUMMARY_ONLY_KEY,
                    rule_id=_SUMMARY_ONLY_KEY,
                    category=EngineeringCategory.OTHER.value,
                    normalized_title_id=_SUMMARY_ONLY_KEY,
                    technology_key=None,
                    repository_count=summary.repository_count,
                    finding_count=summary.total_findings,
                    affected_repositories=[],
                    severity_distribution=[],
                    production_count=0,
                    evidence_coverage=0.0,
                    recommendation_coverage=0.0,
                    source_references=[],
                    summary_totals=totals,
                )
            ]
        return [
            EngineeringPortfolioFindingRecord(
                id=f"{snap_id}:finding:{pattern.recurrence_key}",
                portfolio_snapshot_id=snap_id,
                recurrence_key=pattern.recurrence_key,
                rule_id=pattern.rule_id,
                category=pattern.category.value,
                normalized_title_id=pattern.normalized_title_id,
                technology_key=pattern.technology_key,
                repository_count=pattern.repository_count,
                finding_count=pattern.finding_count,
                affected_repositories=[ref.value for ref in pattern.affected_repositories],
                severity_distribution=[
                    PortfolioMapper.finding_distribution_to_json(item)
                    for item in pattern.severity_distribution
                ],
                production_count=pattern.production_count,
                evidence_coverage=pattern.evidence_coverage,
                recommendation_coverage=pattern.recommendation_coverage,
                source_references=list(pattern.source_references),
                summary_totals=totals,
            )
            for pattern in patterns
        ]

    @staticmethod
    def _finding_summary_totals(summary: PortfolioFindingSummary) -> dict[str, Any]:
        return {
            "total_findings": summary.total_findings,
            "repository_count": summary.repository_count,
            "high_critical_count": summary.high_critical_count,
            "severity_distribution": [
                PortfolioMapper.finding_distribution_to_json(item)
                for item in summary.severity_distribution
            ],
            "clusters": [
                {
                    "cluster_key": cluster.cluster_key,
                    "pattern_keys": [pattern.recurrence_key for pattern in cluster.patterns],
                }
                for cluster in summary.clusters
            ],
        }

    @staticmethod
    def _findings_from_records(
        records: list[EngineeringPortfolioFindingRecord],
    ) -> tuple[object, ...]:
        if not records:
            return ()
        totals = dict(records[0].summary_totals or {})
        patterns: list[RecurringFindingPattern] = []
        for record in records:
            if record.recurrence_key == _SUMMARY_ONLY_KEY:
                continue
            patterns.append(
                RecurringFindingPattern(
                    recurrence_key=record.recurrence_key,
                    rule_id=record.rule_id,
                    category=EngineeringCategory(record.category),
                    normalized_title_id=record.normalized_title_id,
                    technology_key=record.technology_key,
                    repository_count=record.repository_count,
                    finding_count=record.finding_count,
                    affected_repositories=_repo_ids(record.affected_repositories),
                    severity_distribution=tuple(
                        PortfolioMapper.finding_distribution_from_json(item)
                        for item in (record.severity_distribution or [])
                    ),
                    production_count=record.production_count,
                    evidence_coverage=float(record.evidence_coverage),
                    recommendation_coverage=float(record.recommendation_coverage),
                    concentration=FindingConcentration(
                        repository_count=record.repository_count,
                        finding_count=record.finding_count,
                        production_count=record.production_count,
                    ),
                    source_references=tuple(str(item) for item in (record.source_references or [])),
                )
            )
        by_key = {pattern.recurrence_key: pattern for pattern in patterns}
        clusters = tuple(
            PortfolioFindingCluster(
                cluster_key=str(item["cluster_key"]),
                patterns=tuple(
                    by_key[key]
                    for key in item.get("pattern_keys", [])
                    if key in by_key
                ),
            )
            for item in totals.get("clusters", [])
            if isinstance(item, dict)
        )
        return (
            PortfolioFindingSummary(
                total_findings=int(totals.get("total_findings", 0)),
                repository_count=int(totals.get("repository_count", 0)),
                high_critical_count=int(totals.get("high_critical_count", 0)),
                recurring_patterns=tuple(patterns),
                clusters=clusters,
                severity_distribution=tuple(
                    PortfolioMapper.finding_distribution_from_json(item)
                    for item in totals.get("severity_distribution", [])
                ),
            ),
        )

    @staticmethod
    def finding_distribution_to_json(item: PortfolioFindingDistribution) -> dict[str, Any]:
        return {"severity": item.severity.value, "count": item.count}

    @staticmethod
    def finding_distribution_from_json(payload: dict[str, Any]) -> PortfolioFindingDistribution:
        return PortfolioFindingDistribution(
            severity=EngineeringSeverity(str(payload["severity"])),
            count=int(payload["count"]),
        )

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    @staticmethod
    def _recommendation_records(
        snap_id: str,
        inventory: tuple[object, ...],
    ) -> list[EngineeringPortfolioRecommendationRecord]:
        summary = next(
            (item for item in inventory if isinstance(item, PortfolioRecommendationSummary)),
            None,
        )
        if summary is None:
            return []
        totals = PortfolioMapper._recommendation_summary_totals(summary)
        gaps = [
            PortfolioMapper.coverage_gap_to_json(item) for item in summary.coverage_gaps
        ]
        patterns = list(summary.recurring_patterns)
        if not patterns:
            return [
                EngineeringPortfolioRecommendationRecord(
                    id=f"{snap_id}:recommendation:{_SUMMARY_ONLY_KEY}",
                    portfolio_snapshot_id=snap_id,
                    recurrence_key=_SUMMARY_ONLY_KEY,
                    canonical_recommendation_id=None,
                    category=EngineeringCategory.OTHER.value,
                    priority="unspecified",
                    linked_finding_rule=None,
                    target_technology=None,
                    target_component=None,
                    roadmap_horizon=None,
                    repository_count=summary.repository_count,
                    recommendation_count=summary.total_recommendations,
                    affected_repositories=[],
                    priority_score=0,
                    priority_band=PriorityBand.LOW.value,
                    contributing_factors=[],
                    source_references=[],
                    coverage_gaps=gaps,
                    summary_totals=totals,
                )
            ]
        return [
            EngineeringPortfolioRecommendationRecord(
                id=f"{snap_id}:recommendation:{pattern.recurrence_key}",
                portfolio_snapshot_id=snap_id,
                recurrence_key=pattern.recurrence_key,
                canonical_recommendation_id=pattern.canonical_recommendation_id,
                category=pattern.category.value,
                priority=pattern.priority,
                linked_finding_rule=pattern.linked_finding_rule,
                target_technology=pattern.target_technology,
                target_component=pattern.target_component,
                roadmap_horizon=pattern.roadmap_horizon,
                repository_count=pattern.repository_count,
                recommendation_count=pattern.recommendation_count,
                affected_repositories=[ref.value for ref in pattern.affected_repositories],
                priority_score=pattern.priority_score.score,
                priority_band=pattern.priority_score.band.value,
                contributing_factors=list(pattern.priority_score.contributing_factors),
                source_references=list(pattern.source_references),
                coverage_gaps=gaps,
                summary_totals={
                    **totals,
                    "priority_policy_version": pattern.priority_score.policy_version,
                },
            )
            for pattern in patterns
        ]

    @staticmethod
    def _recommendation_summary_totals(
        summary: PortfolioRecommendationSummary,
    ) -> dict[str, Any]:
        return {
            "total_recommendations": summary.total_recommendations,
            "repository_count": summary.repository_count,
            "coverage_gaps": [
                PortfolioMapper.coverage_gap_to_json(item) for item in summary.coverage_gaps
            ],
        }

    @staticmethod
    def _recommendations_from_records(
        records: list[EngineeringPortfolioRecommendationRecord],
    ) -> tuple[object, ...]:
        if not records:
            return ()
        totals = dict(records[0].summary_totals or {})
        gaps_payload = totals.get("coverage_gaps") or records[0].coverage_gaps or []
        patterns: list[RecurringRecommendationPattern] = []
        for record in records:
            if record.recurrence_key == _SUMMARY_ONLY_KEY:
                continue
            policy_version = str(
                (record.summary_totals or {}).get("priority_policy_version", "unknown")
            )
            patterns.append(
                RecurringRecommendationPattern(
                    recurrence_key=record.recurrence_key,
                    canonical_recommendation_id=record.canonical_recommendation_id,
                    category=EngineeringCategory(record.category),
                    priority=record.priority,
                    linked_finding_rule=record.linked_finding_rule,
                    target_technology=record.target_technology,
                    target_component=record.target_component,
                    roadmap_horizon=record.roadmap_horizon,
                    repository_count=record.repository_count,
                    recommendation_count=record.recommendation_count,
                    affected_repositories=_repo_ids(record.affected_repositories),
                    priority_score=PortfolioRecommendationPriority(
                        score=record.priority_score,
                        band=PriorityBand(record.priority_band),
                        contributing_factors=tuple(
                            str(item) for item in (record.contributing_factors or [])
                        ),
                        policy_version=policy_version,
                    ),
                    concentration=RecommendationConcentration(
                        repository_count=record.repository_count,
                        recommendation_count=record.recommendation_count,
                    ),
                    source_references=tuple(
                        str(item) for item in (record.source_references or [])
                    ),
                )
            )
        return (
            PortfolioRecommendationSummary(
                total_recommendations=int(totals.get("total_recommendations", 0)),
                repository_count=int(totals.get("repository_count", 0)),
                recurring_patterns=tuple(patterns),
                coverage_gaps=tuple(
                    PortfolioMapper.coverage_gap_from_json(item)
                    for item in gaps_payload
                    if isinstance(item, dict)
                ),
            ),
        )

    @staticmethod
    def coverage_gap_to_json(item: RecommendationCoverageGap) -> dict[str, Any]:
        return {
            "gap_key": item.gap_key,
            "finding_rule_id": item.finding_rule_id,
            "category": item.category.value,
            "severity": item.severity,
            "repository_count": item.repository_count,
            "finding_count": item.finding_count,
            "affected_repositories": [ref.value for ref in item.affected_repositories],
            "reason": item.reason,
        }

    @staticmethod
    def coverage_gap_from_json(payload: dict[str, Any]) -> RecommendationCoverageGap:
        return RecommendationCoverageGap(
            gap_key=str(payload["gap_key"]),
            finding_rule_id=str(payload["finding_rule_id"]),
            category=EngineeringCategory(str(payload["category"])),
            severity=str(payload["severity"]),
            repository_count=int(payload["repository_count"]),
            finding_count=int(payload["finding_count"]),
            affected_repositories=_repo_ids(payload.get("affected_repositories")),
            reason=str(payload["reason"]),
        )

    # ------------------------------------------------------------------
    # Risk
    # ------------------------------------------------------------------

    @staticmethod
    def _risk_to_record(
        snap_id: str,
        summary: PortfolioRiskSummary,
    ) -> EngineeringPortfolioRiskRecord:
        return EngineeringPortfolioRiskRecord(
            id=f"{snap_id}:risk",
            portfolio_snapshot_id=snap_id,
            overall_score=summary.overall_score,
            overall_band=summary.overall_band.value,
            policy_version=summary.policy_version,
            severity_distribution=[
                {"severity": item.severity.value, "count": item.count}
                for item in summary.severity_distribution
            ],
            concentrations=[
                PortfolioMapper.risk_concentration_to_json(item)
                for item in summary.concentrations
            ],
            hotspots=[PortfolioMapper.risk_hotspot_to_json(item) for item in summary.hotspots],
            repository_profiles=[
                PortfolioMapper.repository_risk_to_json(item)
                for item in summary.repository_profiles
            ],
            technology_profiles=[
                PortfolioMapper.technology_risk_to_json(item)
                for item in summary.technology_profiles
            ],
            systemic_risks=[
                PortfolioMapper.systemic_risk_to_json(item) for item in summary.systemic_risks
            ],
        )

    @staticmethod
    def _risk_from_record(record: EngineeringPortfolioRiskRecord) -> PortfolioRiskSummary:
        return PortfolioRiskSummary(
            overall_score=record.overall_score,
            overall_band=PriorityBand(record.overall_band),
            severity_distribution=tuple(
                PortfolioRiskDistribution(
                    severity=EngineeringSeverity(str(item["severity"])),
                    count=int(item["count"]),
                )
                for item in (record.severity_distribution or [])
            ),
            concentrations=tuple(
                PortfolioMapper.risk_concentration_from_json(item)
                for item in (record.concentrations or [])
            ),
            hotspots=tuple(
                PortfolioMapper.risk_hotspot_from_json(item) for item in (record.hotspots or [])
            ),
            repository_profiles=tuple(
                PortfolioMapper.repository_risk_from_json(item)
                for item in (record.repository_profiles or [])
            ),
            technology_profiles=tuple(
                PortfolioMapper.technology_risk_from_json(item)
                for item in (record.technology_profiles or [])
            ),
            systemic_risks=tuple(
                PortfolioMapper.systemic_risk_from_json(item)
                for item in (record.systemic_risks or [])
            ),
            policy_version=record.policy_version,
        )

    @staticmethod
    def risk_concentration_to_json(item: PortfolioRiskConcentration) -> dict[str, Any]:
        return {
            "dimension": item.dimension,
            "key": item.key,
            "repository_count": item.repository_count,
            "finding_count": item.finding_count,
            "high_critical_count": item.high_critical_count,
            "score": item.score,
            "band": item.band.value,
            "factors": list(item.factors),
        }

    @staticmethod
    def risk_concentration_from_json(payload: dict[str, Any]) -> PortfolioRiskConcentration:
        return PortfolioRiskConcentration(
            dimension=str(payload["dimension"]),
            key=str(payload["key"]),
            repository_count=int(payload["repository_count"]),
            finding_count=int(payload["finding_count"]),
            high_critical_count=int(payload["high_critical_count"]),
            score=int(payload["score"]),
            band=PriorityBand(str(payload["band"])),
            factors=tuple(str(item) for item in payload.get("factors", [])),
        )

    @staticmethod
    def risk_hotspot_to_json(item: PortfolioRiskHotspot) -> dict[str, Any]:
        return {
            "hotspot_key": item.hotspot_key,
            "repository_id": item.repository_id.value if item.repository_id else None,
            "technology_key": item.technology_key,
            "category": item.category.value if item.category else None,
            "score": item.score,
            "band": item.band.value,
            "factors": list(item.factors),
            "source_references": list(item.source_references),
        }

    @staticmethod
    def risk_hotspot_from_json(payload: dict[str, Any]) -> PortfolioRiskHotspot:
        category = payload.get("category")
        repository_id = payload.get("repository_id")
        return PortfolioRiskHotspot(
            hotspot_key=str(payload["hotspot_key"]),
            repository_id=RepositoryId(str(repository_id)) if repository_id else None,
            technology_key=payload.get("technology_key"),
            category=EngineeringCategory(str(category)) if category else None,
            score=int(payload["score"]),
            band=PriorityBand(str(payload["band"])),
            factors=tuple(str(item) for item in payload.get("factors", [])),
            source_references=tuple(str(item) for item in payload.get("source_references", [])),
        )

    @staticmethod
    def repository_risk_to_json(item: RepositoryRiskProfile) -> dict[str, Any]:
        return {
            "repository_id": item.repository_id.value,
            "score": item.score,
            "band": item.band.value,
            "finding_count": item.finding_count,
            "high_critical_count": item.high_critical_count,
            "evidence_gap_count": item.evidence_gap_count,
            "recommendation_gap_count": item.recommendation_gap_count,
            "factors": list(item.factors),
        }

    @staticmethod
    def repository_risk_from_json(payload: dict[str, Any]) -> RepositoryRiskProfile:
        return RepositoryRiskProfile(
            repository_id=RepositoryId(str(payload["repository_id"])),
            score=int(payload["score"]),
            band=PriorityBand(str(payload["band"])),
            finding_count=int(payload["finding_count"]),
            high_critical_count=int(payload["high_critical_count"]),
            evidence_gap_count=int(payload["evidence_gap_count"]),
            recommendation_gap_count=int(payload["recommendation_gap_count"]),
            factors=tuple(str(item) for item in payload.get("factors", [])),
        )

    @staticmethod
    def technology_risk_to_json(item: TechnologyRiskProfile) -> dict[str, Any]:
        return {
            "technology_key": item.technology_key,
            "score": item.score,
            "band": item.band.value,
            "repository_count": item.repository_count,
            "high_critical_count": item.high_critical_count,
            "factors": list(item.factors),
        }

    @staticmethod
    def technology_risk_from_json(payload: dict[str, Any]) -> TechnologyRiskProfile:
        return TechnologyRiskProfile(
            technology_key=str(payload["technology_key"]),
            score=int(payload["score"]),
            band=PriorityBand(str(payload["band"])),
            repository_count=int(payload["repository_count"]),
            high_critical_count=int(payload["high_critical_count"]),
            factors=tuple(str(item) for item in payload.get("factors", [])),
        )

    @staticmethod
    def systemic_risk_to_json(item: SystemicRisk) -> dict[str, Any]:
        return {
            "systemic_key": item.systemic_key,
            "title": item.title,
            "score": item.score,
            "band": item.band.value,
            "repository_count": item.repository_count,
            "evidence": list(item.evidence),
            "factors": list(item.factors),
        }

    @staticmethod
    def systemic_risk_from_json(payload: dict[str, Any]) -> SystemicRisk:
        return SystemicRisk(
            systemic_key=str(payload["systemic_key"]),
            title=str(payload["title"]),
            score=int(payload["score"]),
            band=PriorityBand(str(payload["band"])),
            repository_count=int(payload["repository_count"]),
            evidence=tuple(str(item) for item in payload.get("evidence", [])),
            factors=tuple(str(item) for item in payload.get("factors", [])),
        )

    # ------------------------------------------------------------------
    # Modernization
    # ------------------------------------------------------------------

    @staticmethod
    def _modernization_meta(summary: PortfolioModernizationSummary) -> dict[str, Any]:
        return {
            "theme_counts": [
                [theme.value, count] for theme, count in summary.theme_counts
            ],
            "wave_counts": [[wave.value, count] for wave, count in summary.wave_counts],
            "policy_version": summary.policy_version,
        }

    @staticmethod
    def _modernization_candidate_to_record(
        snap_id: str,
        candidate: ModernizationCandidate,
        summary_meta: dict[str, Any],
    ) -> EngineeringPortfolioModernizationCandidateRecord:
        meta = {
            **summary_meta,
            "affected_components": list(candidate.affected_components),
            "dependency_constraints": [
                asdict(item) for item in candidate.dependency_constraints
            ],
            "constraints": [asdict(item) for item in candidate.constraints],
            "priority_policy_version": candidate.priority.policy_version,
        }
        return EngineeringPortfolioModernizationCandidateRecord(
            id=f"{snap_id}:modernization:{candidate.candidate_id}",
            portfolio_snapshot_id=snap_id,
            candidate_id=candidate.candidate_id,
            repository_id=candidate.repository_id.value,
            theme=candidate.theme.value,
            wave=candidate.wave.value,
            priority_score=candidate.priority.score,
            priority_band=candidate.priority.band.value,
            confidence=candidate.priority.confidence,
            affected_technologies=list(candidate.affected_technologies),
            related_findings=list(candidate.related_findings),
            related_recommendations=list(candidate.related_recommendations),
            contributing_factors=list(candidate.priority.contributing_factors),
            wave_factors=list(candidate.wave_factors),
            evidence_coverage=candidate.evidence_coverage,
            source_snapshot_references=list(candidate.source_snapshot_references),
            summary_meta=meta,
        )

    @staticmethod
    def _modernization_from_records(
        records: list[EngineeringPortfolioModernizationCandidateRecord],
        diagnostics_meta: Any,
    ) -> PortfolioModernizationSummary | None:
        meta: dict[str, Any] = {}
        if records:
            meta = dict(records[0].summary_meta or {})
        elif isinstance(diagnostics_meta, dict):
            meta = dict(diagnostics_meta)
        else:
            return None

        candidates = tuple(
            ModernizationCandidate(
                candidate_id=record.candidate_id,
                repository_id=RepositoryId(record.repository_id),
                theme=ModernizationTheme(record.theme),
                priority=ModernizationPriorityScore(
                    score=record.priority_score,
                    band=PriorityBand(record.priority_band),
                    confidence=float(record.confidence),
                    contributing_factors=tuple(
                        str(item) for item in (record.contributing_factors or [])
                    ),
                    policy_version=str(
                        (record.summary_meta or {}).get(
                            "priority_policy_version",
                            meta.get("policy_version", "unknown"),
                        )
                    ),
                ),
                wave=ModernizationWave(record.wave),
                affected_technologies=tuple(
                    str(item) for item in (record.affected_technologies or [])
                ),
                affected_components=tuple(
                    str(item)
                    for item in (record.summary_meta or {}).get("affected_components", [])
                ),
                related_findings=tuple(str(item) for item in (record.related_findings or [])),
                related_recommendations=tuple(
                    str(item) for item in (record.related_recommendations or [])
                ),
                dependency_constraints=tuple(
                    ModernizationDependency(
                        dependency_key=str(item["dependency_key"]),
                        description=str(item["description"]),
                        blocking=bool(item["blocking"]),
                    )
                    for item in (record.summary_meta or {}).get("dependency_constraints", [])
                    if isinstance(item, dict)
                ),
                constraints=tuple(
                    ModernizationConstraint(
                        constraint_key=str(item["constraint_key"]),
                        description=str(item["description"]),
                        unresolved=bool(item["unresolved"]),
                    )
                    for item in (record.summary_meta or {}).get("constraints", [])
                    if isinstance(item, dict)
                ),
                evidence_coverage=float(record.evidence_coverage),
                source_snapshot_references=tuple(
                    str(item) for item in (record.source_snapshot_references or [])
                ),
                wave_factors=tuple(str(item) for item in (record.wave_factors or [])),
            )
            for record in records
        )
        return PortfolioModernizationSummary(
            candidates=candidates,
            theme_counts=tuple(
                (ModernizationTheme(str(theme)), int(count))
                for theme, count in meta.get("theme_counts", [])
            ),
            wave_counts=tuple(
                (ModernizationWave(str(wave)), int(count))
                for wave, count in meta.get("wave_counts", [])
            ),
            policy_version=str(meta.get("policy_version", "unknown")),
        )

    # ------------------------------------------------------------------
    # Coverage / dependencies via analysis-run diagnostics
    # ------------------------------------------------------------------

    @staticmethod
    def _dependency_summary(signals: tuple[object, ...]) -> SharedDependencySummary | None:
        for item in signals:
            if isinstance(item, SharedDependencySummary):
                return item
        return None

    @staticmethod
    def _analysis_run_for_snapshot(
        snapshot: PortfolioSnapshot,
        *,
        coverage: PortfolioCoverageSummary | None,
        dependencies: SharedDependencySummary | None,
        modernization_meta: dict[str, Any] | None,
    ) -> EngineeringPortfolioAnalysisRunRecord | None:
        if coverage is None and dependencies is None and not modernization_meta:
            return None
        diagnostics: dict[str, Any] = {}
        if coverage is not None:
            diagnostics[_DIAG_COVERAGE] = PortfolioMapper.coverage_to_json(coverage)
        if dependencies is not None:
            diagnostics[_DIAG_DEPENDENCIES] = PortfolioMapper.dependency_summary_to_json(
                dependencies
            )
        if modernization_meta:
            diagnostics[_DIAG_MODERNIZATION] = modernization_meta
        completed = snapshot.status is PortfolioSnapshotStatus.COMPLETED
        return EngineeringPortfolioAnalysisRunRecord(
            id=f"{snapshot.portfolio_snapshot_id.value}:analysis",
            portfolio_id=snapshot.portfolio_id.value,
            portfolio_snapshot_id=snapshot.portfolio_snapshot_id.value,
            status="completed" if completed else snapshot.status.value,
            aggregation_policy_version=snapshot.aggregation_policy_version.value,
            started_at=snapshot.audit.created_at.value,
            completed_at=snapshot.completed_at if completed else None,
            failure_reason=snapshot.failure_reason,
            diagnostics=diagnostics,
        )

    @staticmethod
    def coverage_to_json(summary: PortfolioCoverageSummary) -> dict[str, Any]:
        return {
            "repositories_total": summary.repositories_total,
            "repositories_with_published_snapshots": summary.repositories_with_published_snapshots,
            "repositories_without_assessments": summary.repositories_without_assessments,
            "repositories_unavailable": summary.repositories_unavailable,
            "repository_participation_percentage": summary.repository_participation_percentage,
            "repository_statuses": [
                {
                    "repository_id": item.repository_id.value,
                    "availability_status": item.availability_status.value,
                    "has_published_snapshot": item.has_published_snapshot,
                    "has_completed_graph": item.has_completed_graph,
                    "has_retrieval_index": item.has_retrieval_index,
                    "freshness_status": item.freshness_status.value,
                    "assessment_age_days": item.assessment_age_days,
                    "engineering_snapshot_id": item.engineering_snapshot_id,
                    "selected_at": item.selected_at.isoformat() if item.selected_at else None,
                }
                for item in summary.repository_statuses
            ],
            "freshness": {
                "current_count": summary.freshness.current_count,
                "aging_count": summary.freshness.aging_count,
                "stale_count": summary.freshness.stale_count,
                "unknown_count": summary.freshness.unknown_count,
                "evaluated_at": summary.freshness.evaluated_at.isoformat(),
                "policy_version": summary.freshness.policy_version,
                "current_threshold_days": summary.freshness.current_threshold_days,
                "aging_threshold_days": summary.freshness.aging_threshold_days,
            },
            "evidence": {
                "findings_total": summary.evidence.findings_total,
                "findings_with_evidence": summary.evidence.findings_with_evidence,
                "coverage_ratio": summary.evidence.coverage_ratio,
            },
            "recommendations": {
                "high_critical_findings": summary.recommendations.high_critical_findings,
                "high_critical_with_recommendations": (
                    summary.recommendations.high_critical_with_recommendations
                ),
                "coverage_ratio": summary.recommendations.coverage_ratio,
            },
            "graphs": {
                "repositories_with_graphs": summary.graphs.repositories_with_graphs,
                "repositories_total": summary.graphs.repositories_total,
                "coverage_ratio": summary.graphs.coverage_ratio,
            },
            "technology_coverage_count": summary.technology_coverage_count,
        }

    @staticmethod
    def coverage_from_json(payload: dict[str, Any]) -> PortfolioCoverageSummary:
        freshness = payload["freshness"]
        evidence = payload["evidence"]
        recommendations = payload["recommendations"]
        graphs = payload["graphs"]
        return PortfolioCoverageSummary(
            repositories_total=int(payload["repositories_total"]),
            repositories_with_published_snapshots=int(
                payload["repositories_with_published_snapshots"]
            ),
            repositories_without_assessments=int(payload["repositories_without_assessments"]),
            repositories_unavailable=int(payload["repositories_unavailable"]),
            repository_participation_percentage=float(
                payload["repository_participation_percentage"]
            ),
            repository_statuses=tuple(
                RepositoryCoverageStatus(
                    repository_id=RepositoryId(str(item["repository_id"])),
                    availability_status=RepositoryAvailabilityStatus(
                        str(item["availability_status"])
                    ),
                    has_published_snapshot=bool(item["has_published_snapshot"]),
                    has_completed_graph=bool(item["has_completed_graph"]),
                    has_retrieval_index=bool(item["has_retrieval_index"]),
                    freshness_status=AssessmentFreshnessStatus(str(item["freshness_status"])),
                    assessment_age_days=item.get("assessment_age_days"),
                    engineering_snapshot_id=item.get("engineering_snapshot_id"),
                    selected_at=(
                        ensure_utc(datetime.fromisoformat(item["selected_at"]))
                        if item.get("selected_at")
                        else None
                    ),
                )
                for item in payload.get("repository_statuses", [])
            ),
            freshness=AssessmentFreshnessSummary(
                current_count=int(freshness["current_count"]),
                aging_count=int(freshness["aging_count"]),
                stale_count=int(freshness["stale_count"]),
                unknown_count=int(freshness["unknown_count"]),
                evaluated_at=ensure_utc(datetime.fromisoformat(str(freshness["evaluated_at"]))),
                policy_version=str(freshness["policy_version"]),
                current_threshold_days=int(freshness["current_threshold_days"]),
                aging_threshold_days=int(freshness["aging_threshold_days"]),
            ),
            evidence=EvidenceCoverageSummary(
                findings_total=int(evidence["findings_total"]),
                findings_with_evidence=int(evidence["findings_with_evidence"]),
                coverage_ratio=float(evidence["coverage_ratio"]),
            ),
            recommendations=RecommendationCoverageSummary(
                high_critical_findings=int(recommendations["high_critical_findings"]),
                high_critical_with_recommendations=int(
                    recommendations["high_critical_with_recommendations"]
                ),
                coverage_ratio=float(recommendations["coverage_ratio"]),
            ),
            graphs=GraphCoverageSummary(
                repositories_with_graphs=int(graphs["repositories_with_graphs"]),
                repositories_total=int(graphs["repositories_total"]),
                coverage_ratio=float(graphs["coverage_ratio"]),
            ),
            technology_coverage_count=int(payload["technology_coverage_count"]),
        )

    @staticmethod
    def dependency_summary_to_json(summary: SharedDependencySummary) -> dict[str, Any]:
        return {
            "explicit_dependency_count": summary.explicit_dependency_count,
            "shared_exposure_count": summary.shared_exposure_count,
            "signals": [
                {
                    "signal_key": item.signal_key,
                    "signal_type": item.signal_type.value,
                    "is_explicit_dependency": item.is_explicit_dependency,
                    "is_shared_exposure": item.is_shared_exposure,
                    "repository_ids": [ref.value for ref in item.repository_ids],
                    "shared_key": item.shared_key,
                    "description": item.description,
                    "source_references": list(item.source_references),
                }
                for item in summary.signals
            ],
        }

    @staticmethod
    def dependency_summary_from_json(payload: dict[str, Any]) -> SharedDependencySummary:
        return SharedDependencySummary(
            signals=tuple(
                CrossRepositoryDependencySignal(
                    signal_key=str(item["signal_key"]),
                    signal_type=DependencySignalType(str(item["signal_type"])),
                    is_explicit_dependency=bool(item["is_explicit_dependency"]),
                    is_shared_exposure=bool(item["is_shared_exposure"]),
                    repository_ids=_repo_ids(item.get("repository_ids")),
                    shared_key=str(item["shared_key"]),
                    description=str(item["description"]),
                    source_references=tuple(
                        str(ref) for ref in item.get("source_references", [])
                    ),
                )
                for item in payload.get("signals", [])
            ),
            explicit_dependency_count=int(payload["explicit_dependency_count"]),
            shared_exposure_count=int(payload["shared_exposure_count"]),
        )
