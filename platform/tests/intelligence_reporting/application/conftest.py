"""Fixtures for dataset ingestion tests — minimal sanitized reports only."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION

from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentDatasetInput,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    InclusionStatus,
    SourceType,
)


def full_engine_report(
    *,
    finding_id: str = "finding:1",
    evidence_id: str = "ev:alpha",
    recommendation_id: str = "rec:1",
    action_id: str = "pa:1",
    initiative_id: str = "init:1",
    extra_assessment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    assessment: dict[str, Any] = {
        "evidence": [
            {
                "evidence_id": evidence_id,
                "kind": "other",
                "production_mode": "direct",
                "location": {"path": "src/a.py", "line_start": 3, "line_end": 4},
                "limitations": [],
            }
        ],
        "findings": [
            {
                "id": finding_id,
                "rule_id": "rule.demo",
                "title": "Demo finding",
                "description": "Observed issue",
                "category": "security",
                "severity": "high",
                "confidence": 0.9,
                "evidence_refs": [{"evidence_id": evidence_id}],
                "primary_evidence_id": evidence_id,
                "synthesized_from_evidence_ids": [evidence_id],
                "evidence_completeness": "complete",
                "limitations": ["demo-limit"],
            }
        ],
        "deterministic_recommendations": [
            {
                "id": recommendation_id,
                "title": "Fix demo",
                "summary": "Address the finding",
                "priority": "high",
                "category": "security",
                "supporting_finding_ids": [finding_id],
                "related_finding_ids": [finding_id],
                "primary_finding_id": finding_id,
                "recommendation_type": "remediation",
                "evidence_completeness": "complete",
                "limitations": [],
            }
        ],
        "priority_actions": [
            {
                "action_id": action_id,
                "title": "Fix demo",
                "supporting_recommendation_ids": [recommendation_id],
                "primary_recommendation_id": recommendation_id,
                "supporting_finding_ids": [finding_id],
                "evidence_completeness": "complete",
                "limitations": [],
                "action_type": "remediation",
            }
        ],
        "roadmap": {
            "initiatives": [
                {
                    "initiative_id": initiative_id,
                    "title": "Secure baseline",
                    "supporting_priority_action_ids": [action_id],
                    "primary_priority_action_id": action_id,
                    "supporting_recommendation_ids": [recommendation_id],
                    "supporting_finding_ids": [finding_id],
                    "initiative_type": "priority_action_backed",
                    "evidence_completeness": "complete",
                    "limitations": [],
                    "depends_on_initiative_ids": [],
                }
            ]
        },
        "assessment_coverage": {
            "security_intelligence": {"status": "complete"},
            "dependency_intelligence": {"status": "disabled"},
            "cloud_readiness": {"status": "unavailable"},
        },
        "assessment_head_confidence": {
            "security_intelligence": {"level": "high"},
            "dependency_intelligence": {"level": "unavailable"},
        },
        "finding_correlations": [
            {
                "correlation_id": "corr:1",
                "correlation_type": "shared_evidence",
                "confidence": "high",
                "finding_ids": [finding_id],
            }
        ],
        "technologies": [
            {
                "technology_id": "tech:python",
                "name": "Python",
                "category": "language",
            }
        ],
        "summary": {
            "evidence_count": 1,
            "priority_action_count": 1,
            "roadmap_initiative_count": 1,
        },
    }
    if extra_assessment:
        assessment.update(extra_assessment)
    return {
        "schema_version": ASSESSMENT_JSON_SCHEMA_VERSION,
        "assessment": assessment,
    }


def legacy_flat_report() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "findings": [
            {
                "id": "finding:legacy",
                "rule_id": "rule.legacy",
                "title": "Legacy finding",
                "description": "Legacy",
                "category": "testing",
                "severity": "medium",
                "confidence": 0.5,
            }
        ],
        "recommendations": [
            {
                "id": "rec:legacy",
                "title": "Legacy rec",
                "summary": "Legacy",
                "priority": "medium",
                "category": "testing",
                "related_finding_ids": ["finding:legacy"],
            }
        ],
    }


def make_input(
    *,
    repository_id: str = "repo:one",
    assessment_id: str = "assessment:one",
    assessment_run_id: str = "run:one",
    report: dict[str, Any] | None = None,
    source_type: SourceType = SourceType.PUBLIC_OSS,
    visibility: DataVisibility = DataVisibility.ANONYMIZED,
    pinned_revision: str | None = "abc123def",
    source_reference: str | None = None,
    publication_permitted: bool = False,
    inclusion_status: InclusionStatus = InclusionStatus.INCLUDED,
    display_name: str | None = None,
) -> AssessmentDatasetInput:
    return AssessmentDatasetInput(
        repository_id=repository_id,
        assessment_id=assessment_id,
        assessment_run_id=assessment_run_id,
        report_document=deepcopy(report if report is not None else full_engine_report()),
        source_type=source_type,
        source_reference=source_reference,
        pinned_revision=pinned_revision,
        visibility=visibility,
        inclusion_status=inclusion_status,
        display_name=display_name,
        source_reference_publication_permitted=publication_permitted,
        report_reference=f"artifact:{assessment_id}:report_json",
    )
