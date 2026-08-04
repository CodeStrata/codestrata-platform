"""Synthetic fixtures for offline SV.6 scenario tests (no network)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION

from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentDatasetInput,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    SourceType,
)


def synthetic_report(
    *,
    finding_id: str = "finding:1",
    evidence_id: str = "ev:alpha",
    recommendation_id: str = "rec:1",
    action_id: str = "pa:1",
    initiative_id: str = "init:1",
    rule_id: str = "rule.demo",
    technologies: list[dict[str, Any]] | None = None,
    extra_assessment: dict[str, Any] | None = None,
    include_finding: bool = True,
) -> dict[str, Any]:
    findings = []
    recommendations = []
    priority_actions = []
    initiatives = []
    evidence = [
        {
            "evidence_id": evidence_id,
            "kind": "other",
            "production_mode": "direct",
            "location": {"path": "src/a.py", "line_start": 3, "line_end": 4},
            "limitations": [],
        }
    ]
    if include_finding:
        findings.append(
            {
                "id": finding_id,
                "rule_id": rule_id,
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
        )
        recommendations.append(
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
        )
        priority_actions.append(
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
        )
        initiatives.append(
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
        )
    assessment: dict[str, Any] = {
        "evidence": evidence,
        "findings": findings,
        "deterministic_recommendations": recommendations,
        "priority_actions": priority_actions,
        "roadmap": {"initiatives": initiatives},
        "assessment_coverage": {
            "security_intelligence": {"status": "complete"},
            "dependency_intelligence": {"status": "disabled"},
            "cloud_readiness": {"status": "unavailable"},
        },
        "assessment_head_confidence": {
            "security_intelligence": {"level": "high"},
            "dependency_intelligence": {"level": "unavailable"},
        },
        "finding_correlations": (
            [
                {
                    "correlation_id": "corr:1",
                    "correlation_type": "shared_evidence",
                    "confidence": "high",
                    "finding_ids": [finding_id],
                }
            ]
            if include_finding
            else []
        ),
        "technologies": technologies
        if technologies is not None
        else [{"technology_id": "tech:python", "name": "Python", "category": "language"}],
        "summary": {
            "evidence_count": len(evidence),
            "priority_action_count": len(priority_actions),
            "roadmap_initiative_count": len(initiatives),
        },
    }
    if extra_assessment:
        assessment.update(extra_assessment)
    return {
        "schema_version": ASSESSMENT_JSON_SCHEMA_VERSION,
        "assessment": assessment,
    }


def make_public_input(
    *,
    repository_id: str,
    assessment_id: str,
    assessment_run_id: str,
    report: dict[str, Any] | None = None,
    pinned_revision: str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    visibility: DataVisibility = DataVisibility.PUBLIC,
    source_type: SourceType = SourceType.PUBLIC_OSS,
) -> AssessmentDatasetInput:
    slug = repository_id.split(":", 1)[-1]
    return AssessmentDatasetInput(
        repository_id=repository_id,
        assessment_id=assessment_id,
        assessment_run_id=assessment_run_id,
        report_document=deepcopy(report if report is not None else synthetic_report()),
        report_reference=f"artifact:{assessment_id}:report_json",
        source_type=source_type,
        visibility=visibility,
        pinned_revision=pinned_revision,
        source_reference=f"https://github.com/example/{slug}",
        source_reference_publication_permitted=visibility is DataVisibility.PUBLIC,
        display_name=slug,
        explicitly_selected=True,
    )
