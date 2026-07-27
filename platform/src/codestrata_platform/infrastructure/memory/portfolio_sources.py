"""Bounded portfolio source intelligence adapter."""

from __future__ import annotations

from codestrata_platform.domain.assessment.ports import AssessmentRepository
from codestrata_platform.domain.engineering.enums import (
    EngineeringRelationshipType,
    EngineeringSnapshotStatus,
)
from codestrata_platform.domain.engineering.ports import EngineeringSnapshotRepository
from codestrata_platform.domain.knowledge_graph.ports import KnowledgeGraphRepository
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.ports import PublishedRepositoryIntelligence
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.ports import RetrievalIndexRepository
from codestrata_platform.domain.workspace.ids import WorkspaceId


class DefaultPortfolioSourceIntelligenceRepository:
    """Load latest published repository Platform intelligence for portfolio aggregation."""

    def __init__(
        self,
        *,
        assessments: AssessmentRepository,
        snapshots: EngineeringSnapshotRepository,
        graphs: KnowledgeGraphRepository,
        retrieval_indexes: RetrievalIndexRepository | None = None,
    ) -> None:
        self._assessments = assessments
        self._snapshots = snapshots
        self._graphs = graphs
        self._retrieval = retrieval_indexes

    def load_latest_published(
        self,
        *,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        repository_id: RepositoryId,
    ) -> PublishedRepositoryIntelligence | None:
        assessments = self._assessments.list_by_repository(repository_id)
        if not assessments:
            return None
        # Prefer most recently created assessment with a published snapshot.
        ordered = sorted(
            assessments,
            key=lambda item: item.audit.created_at.value,
            reverse=True,
        )
        for assessment in ordered:
            # Assessment has no organization_id; tenant scope is enforced via
            # workspace/repository on the assessment and organization on the snapshot.
            if (
                assessment.workspace_id != workspace_id
                or assessment.repository_id != repository_id
            ):
                continue
            snapshot = self._snapshots.get_latest_published(assessment.assessment_id)
            if snapshot is None or snapshot.status is not EngineeringSnapshotStatus.PUBLISHED:
                continue
            if (
                snapshot.organization_id != organization_id
                or snapshot.workspace_id != workspace_id
                or snapshot.repository_id != repository_id
            ):
                continue
            graph = self._graphs.get_latest_completed(repository_id)
            has_retrieval = False
            if self._retrieval is not None:
                index = self._retrieval.get_latest_completed(repository_id)
                has_retrieval = index is not None
            explicit_deps = tuple(
                sorted(
                    {
                        rel.target_id
                        for rel in snapshot.relationships
                        if rel.relationship_type is EngineeringRelationshipType.DEPENDS_ON
                        and rel.target_type == "repository"
                    }
                )
            )
            return PublishedRepositoryIntelligence(
                repository_id=repository_id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                assessment_id=assessment.assessment_id.value,
                engineering_snapshot=snapshot,
                knowledge_graph_id=graph.graph_id.value if graph else None,
                knowledge_graph_version=graph.graph_version.value if graph else None,
                graph_intelligence_policy_version=(
                    graph.projector_version if graph is not None else None
                ),
                has_retrieval_index=has_retrieval,
                published_at=snapshot.published_at,
                explicit_repository_dependencies=explicit_deps,
            )
        return None
