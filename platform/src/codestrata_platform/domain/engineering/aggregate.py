"""EngineeringSnapshot aggregate — canonical engineering view of an assessment."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.enums import EngineeringSnapshotStatus
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.engineering.value_objects import (
    EngineeringComponent,
    EngineeringEvidence,
    EngineeringFinding,
    EngineeringMetric,
    EngineeringRecommendation,
    EngineeringRelationship,
    EngineeringSnapshotVersion,
    EngineeringTag,
    EngineeringTechnology,
)
from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvalidValueError,
    InvariantViolationError,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(slots=True)
class EngineeringSnapshot:
    """Normalized engineering representation derived from assessment intelligence."""

    snapshot_id: EngineeringSnapshotId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    assessment_id: AssessmentId
    assessment_intelligence_id: str
    assessment_revision: int
    version: EngineeringSnapshotVersion
    status: EngineeringSnapshotStatus
    source_artifact_ids: tuple[str, ...]
    technologies: tuple[EngineeringTechnology, ...]
    components: tuple[EngineeringComponent, ...]
    findings: tuple[EngineeringFinding, ...]
    recommendations: tuple[EngineeringRecommendation, ...]
    metrics: tuple[EngineeringMetric, ...]
    evidence: tuple[EngineeringEvidence, ...]
    relationships: tuple[EngineeringRelationship, ...]
    tags: tuple[EngineeringTag, ...]
    audit: AuditInfo
    published_at: datetime | None = None
    _version: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        if self.assessment_revision < 1:
            raise InvalidValueError(
                "assessment_revision must be >= 1",
                reason_code="invalid_assessment_revision",
            )
        compact = self.assessment_intelligence_id.strip()
        if not compact:
            raise InvalidValueError(
                "assessment_intelligence_id must be non-blank",
                reason_code="empty_assessment_intelligence_id",
            )
        object.__setattr__(self, "assessment_intelligence_id", compact)
        self._assert_unique_collections()

    @classmethod
    def create(
        cls,
        *,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        repository_id: RepositoryId,
        assessment_id: AssessmentId,
        assessment_intelligence_id: str,
        assessment_revision: int,
        version: int,
        source_artifact_ids: tuple[str, ...],
        snapshot_id: EngineeringSnapshotId | None = None,
    ) -> EngineeringSnapshot:
        sources = tuple(sorted({item.strip() for item in source_artifact_ids if item.strip()}))
        if not sources:
            raise InvalidValueError(
                "source_artifact_ids must be non-empty",
                reason_code="empty_source_artifacts",
            )
        return cls(
            snapshot_id=snapshot_id or EngineeringSnapshotId.generate(),
            organization_id=organization_id,
            workspace_id=workspace_id,
            repository_id=repository_id,
            assessment_id=assessment_id,
            assessment_intelligence_id=assessment_intelligence_id,
            assessment_revision=assessment_revision,
            version=EngineeringSnapshotVersion(version),
            status=EngineeringSnapshotStatus.DRAFT,
            source_artifact_ids=sources,
            technologies=(),
            components=(),
            findings=(),
            recommendations=(),
            metrics=(),
            evidence=(),
            relationships=(),
            tags=(),
            audit=AuditInfo.create(),
        )

    def build(
        self,
        *,
        technologies: tuple[EngineeringTechnology, ...] = (),
        components: tuple[EngineeringComponent, ...] = (),
        findings: tuple[EngineeringFinding, ...] = (),
        recommendations: tuple[EngineeringRecommendation, ...] = (),
        metrics: tuple[EngineeringMetric, ...] = (),
        evidence: tuple[EngineeringEvidence, ...] = (),
        relationships: tuple[EngineeringRelationship, ...] = (),
        tags: tuple[EngineeringTag, ...] = (),
    ) -> None:
        self._require_mutable()
        if self.status not in {
            EngineeringSnapshotStatus.DRAFT,
            EngineeringSnapshotStatus.BUILDING,
        }:
            raise InvalidStateTransitionError(
                f"Cannot build snapshot in status {self.status.value}",
                reason_code="invalid_build_transition",
            )
        self.technologies = technologies
        self.components = components
        self.findings = findings
        self.recommendations = recommendations
        self.metrics = metrics
        self.evidence = evidence
        self.relationships = relationships
        self.tags = tags
        self._assert_unique_collections()
        self._assert_recommendation_finding_links()
        self.status = EngineeringSnapshotStatus.BUILDING
        self.audit = self.audit.touch()
        self._version += 1

    def publish(self) -> None:
        self._require_mutable()
        if self.status is not EngineeringSnapshotStatus.BUILDING:
            raise InvalidStateTransitionError(
                f"Cannot publish snapshot in status {self.status.value}",
                reason_code="invalid_publish_transition",
            )
        self.status = EngineeringSnapshotStatus.PUBLISHED
        self.published_at = datetime.now(UTC)
        self.audit = self.audit.touch()
        self._version += 1

    def supersede(self) -> None:
        if self.status is not EngineeringSnapshotStatus.PUBLISHED:
            raise InvalidStateTransitionError(
                f"Cannot supersede snapshot in status {self.status.value}",
                reason_code="invalid_supersede_transition",
            )
        self.status = EngineeringSnapshotStatus.SUPERSEDED
        self.audit = self.audit.touch()
        self._version += 1

    def archive(self) -> None:
        if self.status not in {
            EngineeringSnapshotStatus.PUBLISHED,
            EngineeringSnapshotStatus.SUPERSEDED,
        }:
            raise InvalidStateTransitionError(
                f"Cannot archive snapshot in status {self.status.value}",
                reason_code="invalid_archive_transition",
            )
        self.status = EngineeringSnapshotStatus.ARCHIVED
        self.audit = self.audit.touch()
        self._version += 1

    def snapshot(self) -> EngineeringSnapshot:
        return replace(self)

    def _require_mutable(self) -> None:
        if self.status is EngineeringSnapshotStatus.PUBLISHED:
            raise InvalidStateTransitionError(
                "Published engineering snapshots are immutable",
                reason_code="snapshot_immutable",
            )
        if self.status in {
            EngineeringSnapshotStatus.SUPERSEDED,
            EngineeringSnapshotStatus.ARCHIVED,
        }:
            raise InvalidStateTransitionError(
                f"Snapshot in status {self.status.value} is immutable",
                reason_code="snapshot_immutable",
            )

    def _assert_unique_collections(self) -> None:
        finding_ids = [item.finding_id.value for item in self.findings]
        if len(finding_ids) != len(set(finding_ids)):
            raise InvariantViolationError(
                "Finding ids must be unique within a snapshot",
                reason_code="duplicate_finding_id",
            )
        source_finding_ids = [item.source_finding_id for item in self.findings]
        if len(source_finding_ids) != len(set(source_finding_ids)):
            raise InvariantViolationError(
                "Source finding ids must be unique within a snapshot",
                reason_code="duplicate_source_finding_id",
            )
        recommendation_ids = [item.recommendation_id.value for item in self.recommendations]
        if len(recommendation_ids) != len(set(recommendation_ids)):
            raise InvariantViolationError(
                "Recommendation ids must be unique within a snapshot",
                reason_code="duplicate_recommendation_id",
            )
        tech_keys = [item.canonical_key for item in self.technologies]
        if len(tech_keys) != len(set(tech_keys)):
            raise InvariantViolationError(
                "Technology keys must be unique within a snapshot",
                reason_code="duplicate_technology_key",
            )
        metric_names = [item.name for item in self.metrics]
        if len(metric_names) != len(set(metric_names)):
            raise InvariantViolationError(
                "Metric names must be unique within a snapshot",
                reason_code="duplicate_metric_name",
            )

    def _assert_recommendation_finding_links(self) -> None:
        known = {item.source_finding_id for item in self.findings} | {
            item.finding_id.value for item in self.findings
        }
        for recommendation in self.recommendations:
            for related in recommendation.related_finding_ids:
                if related not in known:
                    raise InvariantViolationError(
                        f"Recommendation references unknown finding {related}",
                        reason_code="unknown_related_finding",
                    )
