"""Models for Slice 14.14 Epic 14 completion verification."""

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


@dataclass(frozen=True, slots=True)
class SliceRow:
    slice: str
    title: str
    policy: str
    verification_schema: str
    status: str
    checks: int
    failed_checks: int
    blockers: list[str]
    limitations: list[str]
    completion_state: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "blockers": list(self.blockers),
            "checks": self.checks,
            "completion_state": self.completion_state,
            "failed_checks": self.failed_checks,
            "limitations": list(self.limitations),
            "policy": self.policy,
            "slice": self.slice,
            "status": self.status,
            "title": self.title,
            "verification_schema": self.verification_schema,
        }


@dataclass
class UnifiedProductExperienceCompletionReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "14"
    epic_complete: bool = False
    slice_matrix: list[dict[str, Any]] = field(default_factory=list)
    policy_registry: list[dict[str, str]] = field(default_factory=list)
    schema_registry: list[dict[str, str]] = field(default_factory=list)
    surface_registry: list[dict[str, Any]] = field(default_factory=list)
    slice_matrix_status: str = "not_executed"
    policy_registry_status: str = "not_executed"
    schema_registry_status: str = "not_executed"
    surface_registry_status: str = "not_executed"
    design_system_status: str = "not_executed"
    documentation_status: str = "not_executed"
    assessment_report_status: str = "not_executed"
    eir_report_status: str = "not_executed"
    vscode_status: str = "not_executed"
    marketplace_status: str = "not_executed"
    presentation_status: str = "not_executed"
    visualization_status: str = "not_executed"
    report_ia_status: str = "not_executed"
    brand_asset_status: str = "not_executed"
    accessibility_responsive_status: str = "not_executed"
    documentation_deployment_status: str = "not_executed"
    cross_surface_consistency_status: str = "not_executed"
    assessment_parity_status: str = "not_executed"
    community_boundary_status: str = "not_executed"
    privacy_boundary_status: str = "not_executed"
    current_regression_status: str = "not_executed"
    historical_verification_boundary_status: str = "not_executed"
    release_posture_status: str = "not_executed"
    slice_15_7_boundary_status: str = "not_executed"
    determinism_status: str = "not_executed"
    release_posture: dict[str, Any] = field(default_factory=dict)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    completed_slices: int = 0
    total_slices: int = 14

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_responsive_status": self.accessibility_responsive_status,
            "assessment_parity_status": self.assessment_parity_status,
            "assessment_report_status": self.assessment_report_status,
            "blockers": list(self.blockers),
            "brand_asset_status": self.brand_asset_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "community_boundary_status": self.community_boundary_status,
            "completed_slices": self.completed_slices,
            "cross_surface_consistency_status": self.cross_surface_consistency_status,
            "current_regression_status": self.current_regression_status,
            "defects": [d.to_dict() for d in self.defects],
            "design_system_status": self.design_system_status,
            "determinism_status": self.determinism_status,
            "documentation_deployment_status": self.documentation_deployment_status,
            "documentation_status": self.documentation_status,
            "eir_report_status": self.eir_report_status,
            "epic": self.epic,
            "slice_15_7_boundary_status": self.slice_15_7_boundary_status,
            "epic_complete": self.epic_complete,
            "failed_checks": self.failed_checks,
            "historical_verification_boundary_status": (
                self.historical_verification_boundary_status
            ),
            "limitations": sorted(self.limitations),
            "marketplace_status": self.marketplace_status,
            "policy_registry": self.policy_registry,
            "policy_registry_status": self.policy_registry_status,
            "presentation_status": self.presentation_status,
            "privacy_boundary_status": self.privacy_boundary_status,
            "release_posture": self.release_posture,
            "release_posture_status": self.release_posture_status,
            "report_ia_status": self.report_ia_status,
            "schema_name": self.schema_name,
            "schema_registry": self.schema_registry,
            "schema_registry_status": self.schema_registry_status,
            "schema_version": self.schema_version,
            "slice_matrix": self.slice_matrix,
            "slice_matrix_status": self.slice_matrix_status,
            "surface_registry": self.surface_registry,
            "surface_registry_status": self.surface_registry_status,
            "total_checks": self.total_checks,
            "total_slices": self.total_slices,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "visualization_status": self.visualization_status,
            "vscode_status": self.vscode_status,
        }
