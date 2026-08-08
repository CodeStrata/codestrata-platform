"""Models for Slice 14.13 cross-surface visual consistency."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL"]
CellValue = Literal["canonical", "adapted", "not_applicable", "violation"]


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
class ConsistencyMatrixCell:
    row: str
    column: str
    value: CellValue
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "column": self.column,
            "detail": self.detail,
            "row": self.row,
            "value": self.value,
        }


@dataclass(slots=True)
class CrossSurfaceVisualConsistencyReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    policy_status: str = "not_executed"
    contract_status: str = "not_executed"
    matrix_status: str = "not_executed"
    adaptations_status: str = "not_executed"
    identity_status: str = "not_executed"
    colors_status: str = "not_executed"
    typography_status: str = "not_executed"
    spacing_status: str = "not_executed"
    radii_status: str = "not_executed"
    borders_status: str = "not_executed"
    shadows_status: str = "not_executed"
    components_status: str = "not_executed"
    evidence_status: str = "not_executed"
    visualization_status: str = "not_executed"
    report_shells_status: str = "not_executed"
    navigation_status: str = "not_executed"
    naming_status: str = "not_executed"
    community_scope_status: str = "not_executed"
    docs_consumer_status: str = "not_executed"
    assessment_consumer_status: str = "not_executed"
    eir_consumer_status: str = "not_executed"
    vscode_consumer_status: str = "not_executed"
    marketplace_consumer_status: str = "not_executed"
    api_portal_consumer_status: str = "not_executed"
    deployment_output_status: str = "not_executed"
    dark_theme_status: str = "not_executed"
    print_consistency_status: str = "not_executed"
    responsive_regression_status: str = "not_executed"
    accessibility_regression_status: str = "not_executed"
    legacy_branding_status: str = "not_executed"
    browser_validation_status: str = "not_executed"
    epic_completion_boundary_status: str = "not_executed"
    determinism_status: str = "not_executed"
    consistency_matrix: list[ConsistencyMatrixCell] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    release_posture: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        # Field names match Slice 14.13 report contract (semantic aliases).
        return {
            "accessibility_regression_status": self.accessibility_regression_status,
            "adaptation_registry_status": self.adaptations_status,
            "api_portal_status": self.api_portal_consumer_status,
            "assessment_status": self.assessment_consumer_status,
            "blockers": sorted(self.blockers),
            "border_status": self.borders_status,
            "browser_validation_status": self.browser_validation_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "color_status": self.colors_status,
            "community_scope_status": self.community_scope_status,
            "component_status": self.components_status,
            "consistency_matrix": [
                c.to_dict()
                for c in sorted(
                    self.consistency_matrix, key=lambda x: (x.row, x.column)
                )
            ],
            "consistency_matrix_status": self.matrix_status,
            "consistency_policy_status": self.policy_status,
            "dark_theme_status": self.dark_theme_status,
            "defects": [d.to_dict() for d in self.defects],
            "deployment_output_status": self.deployment_output_status,
            "determinism_status": self.determinism_status,
            "documentation_status": self.docs_consumer_status,
            "eir_status": self.eir_consumer_status,
            "epic_completion_boundary_status": self.epic_completion_boundary_status,
            "evidence_status": self.evidence_status,
            "failed_checks": self.failed_checks,
            "identity_status": self.identity_status,
            "legacy_branding_status": self.legacy_branding_status,
            "limitations": sorted(self.limitations),
            "marketplace_status": self.marketplace_consumer_status,
            "naming_status": self.naming_status,
            "navigation_status": self.navigation_status,
            "print_status": self.print_consistency_status,
            "radius_status": self.radii_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "report_shell_status": self.report_shells_status,
            "responsive_regression_status": self.responsive_regression_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "shadow_status": self.shadows_status,
            "spacing_status": self.spacing_status,
            "total_checks": self.total_checks,
            "typography_status": self.typography_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "visualization_status": self.visualization_status,
            "vscode_status": self.vscode_consumer_status,
        }
