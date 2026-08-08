"""Models for Slice 14.9."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]


@dataclass(slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str
    category: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "detail": self.detail,
            "name": self.name,
            "ok": self.ok,
        }


@dataclass(slots=True)
class Defect:
    classification: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {"classification": self.classification, "summary": self.summary}


@dataclass(slots=True)
class ReportNavigationIaReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    ia_policy_status: str = "not_executed"
    hierarchy_status: str = "not_executed"
    heading_structure_status: str = "not_executed"
    section_header_status: str = "not_executed"
    anchor_status: str = "not_executed"
    deep_link_status: str = "not_executed"
    toc_status: str = "not_executed"
    assessment_mapping_status: str = "not_executed"
    eir_mapping_status: str = "not_executed"
    executive_summary_status: str = "not_executed"
    metadata_status: str = "not_executed"
    findings_evidence_status: str = "not_executed"
    recommendation_status: str = "not_executed"
    supporting_detail_status: str = "not_executed"
    empty_section_status: str = "not_executed"
    section_order_status: str = "not_executed"
    responsive_navigation_status: str = "not_executed"
    print_navigation_status: str = "not_executed"
    commercial_boundary_status: str = "not_executed"
    visualization_boundary_status: str = "not_executed"
    asset_boundary_status: str = "not_executed"
    accessibility_boundary_status: str = "not_executed"
    deployment_boundary_status: str = "not_executed"
    schema_boundary_status: str = "not_executed"
    determinism_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    release_posture: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_boundary_status": self.accessibility_boundary_status,
            "anchor_status": self.anchor_status,
            "assessment_mapping_status": self.assessment_mapping_status,
            "asset_boundary_status": self.asset_boundary_status,
            "blockers": sorted(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "commercial_boundary_status": self.commercial_boundary_status,
            "deep_link_status": self.deep_link_status,
            "defects": [d.to_dict() for d in self.defects],
            "deployment_boundary_status": self.deployment_boundary_status,
            "determinism_status": self.determinism_status,
            "eir_mapping_status": self.eir_mapping_status,
            "empty_section_status": self.empty_section_status,
            "executive_summary_status": self.executive_summary_status,
            "failed_checks": self.failed_checks,
            "findings_evidence_status": self.findings_evidence_status,
            "heading_structure_status": self.heading_structure_status,
            "hierarchy_status": self.hierarchy_status,
            "ia_policy_status": self.ia_policy_status,
            "limitations": sorted(self.limitations),
            "metadata_status": self.metadata_status,
            "print_navigation_status": self.print_navigation_status,
            "recommendation_status": self.recommendation_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "responsive_navigation_status": self.responsive_navigation_status,
            "schema_boundary_status": self.schema_boundary_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "section_header_status": self.section_header_status,
            "section_order_status": self.section_order_status,
            "supporting_detail_status": self.supporting_detail_status,
            "toc_status": self.toc_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "visualization_boundary_status": self.visualization_boundary_status,
        }
