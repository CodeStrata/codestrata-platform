"""Models for Slice 14.8."""

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
class VisualizationSystemReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    visualization_policy_status: str = "not_executed"
    domain_semantics_status: str = "not_executed"
    semantic_role_status: str = "not_executed"
    risk_status: str = "not_executed"
    severity_status: str = "not_executed"
    status_visualization_status: str = "not_executed"
    confidence_status: str = "not_executed"
    score_status: str = "not_executed"
    score_component_status: str = "not_executed"
    palette_status: str = "not_executed"
    chart_contract_status: str = "not_executed"
    chart_inventory_status: str = "not_executed"
    legend_status: str = "not_executed"
    empty_state_status: str = "not_executed"
    assessment_mapping_status: str = "not_executed"
    eir_mapping_status: str = "not_executed"
    docs_boundary_status: str = "not_executed"
    marketplace_boundary_status: str = "not_executed"
    vscode_boundary_status: str = "not_executed"
    dark_theme_status: str = "not_executed"
    print_status: str = "not_executed"
    accessibility_baseline_status: str = "not_executed"
    schema_boundary_status: str = "not_executed"
    navigation_boundary_status: str = "not_executed"
    asset_boundary_status: str = "not_executed"
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
            "accessibility_baseline_status": self.accessibility_baseline_status,
            "assessment_mapping_status": self.assessment_mapping_status,
            "asset_boundary_status": self.asset_boundary_status,
            "blockers": sorted(self.blockers),
            "chart_contract_status": self.chart_contract_status,
            "chart_inventory_status": self.chart_inventory_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "confidence_status": self.confidence_status,
            "dark_theme_status": self.dark_theme_status,
            "defects": [d.to_dict() for d in self.defects],
            "determinism_status": self.determinism_status,
            "docs_boundary_status": self.docs_boundary_status,
            "domain_semantics_status": self.domain_semantics_status,
            "eir_mapping_status": self.eir_mapping_status,
            "empty_state_status": self.empty_state_status,
            "failed_checks": self.failed_checks,
            "legend_status": self.legend_status,
            "limitations": sorted(self.limitations),
            "marketplace_boundary_status": self.marketplace_boundary_status,
            "navigation_boundary_status": self.navigation_boundary_status,
            "palette_status": self.palette_status,
            "print_status": self.print_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "risk_status": self.risk_status,
            "schema_boundary_status": self.schema_boundary_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "score_component_status": self.score_component_status,
            "score_status": self.score_status,
            "semantic_role_status": self.semantic_role_status,
            "severity_status": self.severity_status,
            "status_visualization_status": self.status_visualization_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "visualization_policy_status": self.visualization_policy_status,
            "vscode_boundary_status": self.vscode_boundary_status,
        }
