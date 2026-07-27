"""SQLAlchemy ORM persistence records (Infrastructure only)."""

from __future__ import annotations

from codestrata_platform.infrastructure.persistence.models.answer_records import (
    EngineeringAnswerCitationRecord,
    EngineeringAnswerFeedbackRecord,
    EngineeringAnswerRunRecord,
)
from codestrata_platform.infrastructure.persistence.models.assessment_artifact_record import (
    AssessmentArtifactRecord,
)
from codestrata_platform.infrastructure.persistence.models.assessment_intelligence_record import (
    AssessmentIntelligenceRecord,
)
from codestrata_platform.infrastructure.persistence.models.assessment_record import (
    AssessmentRecord,
)
from codestrata_platform.infrastructure.persistence.models.base import Base
from codestrata_platform.infrastructure.persistence.models.engineering_records import (
    EngineeringComponentRecord,
    EngineeringEvidenceRecord,
    EngineeringFindingRecord,
    EngineeringMetricRecord,
    EngineeringRecommendationRecord,
    EngineeringRelationshipRecord,
    EngineeringSnapshotRecord,
    EngineeringTagRecord,
    EngineeringTaxonomyRecord,
    EngineeringTechnologyRecord,
)
from codestrata_platform.infrastructure.persistence.models.evidence_reference_record import (
    EvidenceReferenceRecord,
)
from codestrata_platform.infrastructure.persistence.models.executive_intelligence_records import (
    EngineeringExecutiveFindingRecord,
    EngineeringExecutiveIntelligenceSnapshotRecord,
    EngineeringExecutiveMetricRecord,
    EngineeringExecutiveObservationRecord,
    EngineeringExecutiveRecommendationRecord,
)
from codestrata_platform.infrastructure.persistence.models.finding_record import FindingRecord
from codestrata_platform.infrastructure.persistence.models.graph_intelligence_records import (
    GraphIntegrityResultRecord,
    GraphIntelligenceRunRecord,
)
from codestrata_platform.infrastructure.persistence.models.intelligence_source_artifact_record import (  # noqa: E501
    IntelligenceSourceArtifactRecord,
)
from codestrata_platform.infrastructure.persistence.models.knowledge_graph_records import (
    EngineeringGraphEdgeRecord,
    EngineeringGraphNodeRecord,
    EngineeringGraphProjectionRecord,
    EngineeringKnowledgeGraphRecord,
)
from codestrata_platform.infrastructure.persistence.models.metric_record import MetricRecord
from codestrata_platform.infrastructure.persistence.models.organization_record import (
    OrganizationRecord,
)
from codestrata_platform.infrastructure.persistence.models.portfolio_answer_records import (
    EngineeringPortfolioAnswerCitationRecord,
    EngineeringPortfolioAnswerFeedbackRecord,
    EngineeringPortfolioAnswerRunRecord,
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
from codestrata_platform.infrastructure.persistence.models.portfolio_retrieval_records import (
    EngineeringPortfolioRetrievalChunkRecord,
    EngineeringPortfolioRetrievalDocumentRecord,
    EngineeringPortfolioRetrievalIndexRecord,
    EngineeringPortfolioRetrievalIndexRunRecord,
)
from codestrata_platform.infrastructure.persistence.models.recommendation_finding_link_record import (  # noqa: E501
    RecommendationFindingLinkRecord,
)
from codestrata_platform.infrastructure.persistence.models.recommendation_record import (
    RecommendationRecord,
)
from codestrata_platform.infrastructure.persistence.models.repository_record import (
    RepositoryRecord,
)
from codestrata_platform.infrastructure.persistence.models.retrieval_records import (
    EngineeringRetrievalChunkRecord,
    EngineeringRetrievalDocumentRecord,
    EngineeringRetrievalIndexRecord,
    EngineeringRetrievalIndexRunRecord,
)
from codestrata_platform.infrastructure.persistence.models.workspace_record import (
    WorkspaceRecord,
)

__all__ = [
    "AssessmentArtifactRecord",
    "AssessmentIntelligenceRecord",
    "AssessmentRecord",
    "Base",
    "EngineeringAnswerCitationRecord",
    "EngineeringAnswerFeedbackRecord",
    "EngineeringAnswerRunRecord",
    "EngineeringComponentRecord",
    "EngineeringEvidenceRecord",
    "EngineeringExecutiveFindingRecord",
    "EngineeringExecutiveIntelligenceSnapshotRecord",
    "EngineeringExecutiveMetricRecord",
    "EngineeringExecutiveObservationRecord",
    "EngineeringExecutiveRecommendationRecord",
    "EngineeringFindingRecord",
    "EngineeringGraphEdgeRecord",
    "EngineeringGraphNodeRecord",
    "EngineeringGraphProjectionRecord",
    "EngineeringKnowledgeGraphRecord",
    "EngineeringMetricRecord",
    "EngineeringPortfolioAnalysisRunRecord",
    "EngineeringPortfolioAnswerCitationRecord",
    "EngineeringPortfolioAnswerFeedbackRecord",
    "EngineeringPortfolioAnswerRunRecord",
    "EngineeringPortfolioFindingRecord",
    "EngineeringPortfolioMembershipRecord",
    "EngineeringPortfolioModernizationCandidateRecord",
    "EngineeringPortfolioRecommendationRecord",
    "EngineeringPortfolioRecord",
    "EngineeringPortfolioRepositorySnapshotRecord",
    "EngineeringPortfolioRetrievalChunkRecord",
    "EngineeringPortfolioRetrievalDocumentRecord",
    "EngineeringPortfolioRetrievalIndexRecord",
    "EngineeringPortfolioRetrievalIndexRunRecord",
    "EngineeringPortfolioRiskRecord",
    "EngineeringPortfolioSnapshotRecord",
    "EngineeringPortfolioTechnologyRecord",
    "EngineeringRecommendationRecord",
    "EngineeringRelationshipRecord",
    "EngineeringRetrievalChunkRecord",
    "EngineeringRetrievalDocumentRecord",
    "EngineeringRetrievalIndexRecord",
    "EngineeringRetrievalIndexRunRecord",
    "EngineeringSnapshotRecord",
    "EngineeringTagRecord",
    "EngineeringTaxonomyRecord",
    "EngineeringTechnologyRecord",
    "EvidenceReferenceRecord",
    "FindingRecord",
    "GraphIntegrityResultRecord",
    "GraphIntelligenceRunRecord",
    "IntelligenceSourceArtifactRecord",
    "MetricRecord",
    "OrganizationRecord",
    "RecommendationFindingLinkRecord",
    "RecommendationRecord",
    "RepositoryRecord",
    "WorkspaceRecord",
]
