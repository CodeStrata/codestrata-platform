"""Domain tests for Canonical Engineering Intelligence Model."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering import (
    EngineeringCategory,
    EngineeringFinding,
    EngineeringFindingId,
    EngineeringRecommendation,
    EngineeringRecommendationId,
    EngineeringSeverity,
    EngineeringSnapshot,
    EngineeringSnapshotStatus,
    EngineeringTechnology,
    EngineeringTechnologyId,
    normalize_technology_name,
)
from codestrata_platform.domain.engineering.services import map_category, map_severity
from codestrata_platform.domain.errors import (
    InvalidStateTransitionError,
    InvariantViolationError,
)
from codestrata_platform.domain.intelligence.enums import FindingCategory, FindingSeverity
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _snapshot(**overrides) -> EngineeringSnapshot:
    values = {
        "organization_id": OrganizationId("org:1"),
        "workspace_id": WorkspaceId("workspace:1"),
        "repository_id": RepositoryId("repo:1"),
        "assessment_id": AssessmentId("assessment:1"),
        "assessment_intelligence_id": "intelligence:1",
        "assessment_revision": 1,
        "version": 1,
        "source_artifact_ids": ("artifact:1",),
    }
    values.update(overrides)
    return EngineeringSnapshot.create(**values)


def test_technology_normalization() -> None:
    assert normalize_technology_name("Spring Boot") == ("spring-boot", "Spring Boot")
    assert normalize_technology_name("k8s") == ("kubernetes", "Kubernetes")
    assert normalize_technology_name("unknown-tech") is None


def test_severity_and_category_mapping() -> None:
    assert map_severity(FindingSeverity.CRITICAL) is EngineeringSeverity.CRITICAL
    assert map_category(FindingCategory.SECURITY) is EngineeringCategory.SECURITY
    assert map_category("technical_debt") is EngineeringCategory.TECHNICAL_DEBT


def test_snapshot_lifecycle() -> None:
    snapshot = _snapshot()
    assert snapshot.status is EngineeringSnapshotStatus.DRAFT
    finding = EngineeringFinding(
        finding_id=EngineeringFindingId.generate(),
        source_finding_id="finding:1",
        category=EngineeringCategory.SECURITY,
        severity=EngineeringSeverity.HIGH,
        title="Issue",
        summary="Summary",
        rule_id="rule.security.x",
        confidence=0.9,
    )
    tech = EngineeringTechnology(
        technology_id=EngineeringTechnologyId.generate(),
        canonical_key="spring-boot",
        display_name="Spring Boot",
        category=EngineeringCategory.ARCHITECTURE,
    )
    snapshot.build(findings=(finding,), technologies=(tech,))
    assert snapshot.status is EngineeringSnapshotStatus.BUILDING
    snapshot.publish()
    assert snapshot.status is EngineeringSnapshotStatus.PUBLISHED
    with pytest.raises(InvalidStateTransitionError):
        snapshot.build()
    snapshot.supersede()
    assert snapshot.status is EngineeringSnapshotStatus.SUPERSEDED


def test_recommendation_must_reference_known_findings() -> None:
    snapshot = _snapshot()
    recommendation = EngineeringRecommendation(
        recommendation_id=EngineeringRecommendationId.generate(),
        source_recommendation_id="rec:1",
        category=EngineeringCategory.SECURITY,
        severity=EngineeringSeverity.HIGH,
        title="Fix",
        rationale="Because",
        priority="high",
        related_finding_ids=("finding:missing",),
    )
    with pytest.raises(InvariantViolationError):
        snapshot.build(recommendations=(recommendation,))
