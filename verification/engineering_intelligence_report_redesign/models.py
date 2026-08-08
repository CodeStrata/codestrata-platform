"""Models for Slice 14.4 verification."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]


@dataclass(frozen=True, slots=True)
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


@dataclass(frozen=True, slots=True)
class Defect:
    classification: str
    surface: str
    expected: str
    observed: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EirReportRedesignReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "14"
    slice: str = "14.4"
    design_policy: str = "codestrata-engineering-intelligence-report-design-policy:1.0"
    design_policy_status: str = "not_executed"
    design_system_consumption_status: str = "not_executed"
    domain_boundary_status: str = "not_executed"
    renderer_status: str = "not_executed"
    shell_status: str = "not_executed"
    executive_summary_status: str = "not_executed"
    intelligence_section_status: str = "not_executed"
    modernization_status: str = "not_executed"
    finding_status: str = "not_executed"
    evidence_status: str = "not_executed"
    recommendation_status: str = "not_executed"
    traceability_status: str = "not_executed"
    score_status: str = "not_executed"
    risk_status: str = "not_executed"
    chart_status: str = "not_executed"
    table_status: str = "not_executed"
    navigation_status: str = "not_executed"
    responsive_status: str = "not_executed"
    print_status: str = "not_executed"
    accessibility_status: str = "not_executed"
    offline_status: str = "not_executed"
    assessment_report_boundary_status: str = "not_executed"
    legacy_style_status: str = "not_executed"
    determinism_status: str = "not_executed"
    release_posture: dict[str, Any] = field(default_factory=dict)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_status": self.accessibility_status,
            "assessment_report_boundary_status": self.assessment_report_boundary_status,
            "blockers": list(self.blockers),
            "chart_status": self.chart_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "defects": [d.to_dict() for d in self.defects],
            "design_policy": self.design_policy,
            "design_policy_status": self.design_policy_status,
            "design_system_consumption_status": self.design_system_consumption_status,
            "determinism_status": self.determinism_status,
            "domain_boundary_status": self.domain_boundary_status,
            "epic": self.epic,
            "evidence_status": self.evidence_status,
            "executive_summary_status": self.executive_summary_status,
            "failed_checks": self.failed_checks,
            "finding_status": self.finding_status,
            "intelligence_section_status": self.intelligence_section_status,
            "legacy_style_status": self.legacy_style_status,
            "limitations": sorted(self.limitations),
            "modernization_status": self.modernization_status,
            "navigation_status": self.navigation_status,
            "offline_status": self.offline_status,
            "print_status": self.print_status,
            "recommendation_status": self.recommendation_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "renderer_status": self.renderer_status,
            "responsive_status": self.responsive_status,
            "risk_status": self.risk_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "score_status": self.score_status,
            "shell_status": self.shell_status,
            "slice": self.slice,
            "table_status": self.table_status,
            "total_checks": self.total_checks,
            "traceability_status": self.traceability_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
        }
