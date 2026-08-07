"""Models for Slice 13.13 Marketplace documentation verification."""

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
class VsCodeMarketplaceDocsReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    documentation_policy_status: str = "not_executed"
    structure_status: str = "not_executed"
    claim_matrix_status: str = "not_executed"
    workflow_status: str = "not_executed"
    installation_status: str = "not_executed"
    initialization_status: str = "not_executed"
    assessment_status: str = "not_executed"
    ai_status: str = "not_executed"
    progress_status: str = "not_executed"
    report_status: str = "not_executed"
    recovery_status: str = "not_executed"
    compatibility_status: str = "not_executed"
    telemetry_status: str = "not_executed"
    locality_status: str = "not_executed"
    privacy_status: str = "not_executed"
    security_status: str = "not_executed"
    screenshot_status: str = "not_executed"
    link_status: str = "not_executed"
    cursor_absence_status: str = "not_executed"
    cloud_claim_status: str = "not_executed"
    internal_boundary_status: str = "not_executed"
    package_rendering_status: str = "not_executed"
    accessibility_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
    deferred_clean_install_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessibility_status": self.accessibility_status,
            "ai_status": self.ai_status,
            "assessment_status": self.assessment_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "claim_matrix_status": self.claim_matrix_status,
            "cloud_claim_status": self.cloud_claim_status,
            "compatibility_status": self.compatibility_status,
            "cursor_absence_status": self.cursor_absence_status,
            "deferred_clean_install_status": self.deferred_clean_install_status,
            "defects": [d.to_dict() for d in self.defects],
            "documentation_policy_status": self.documentation_policy_status,
            "failed_checks": self.failed_checks,
            "initialization_status": self.initialization_status,
            "installation_status": self.installation_status,
            "internal_boundary_status": self.internal_boundary_status,
            "limitations": sorted(self.limitations),
            "link_status": self.link_status,
            "locality_status": self.locality_status,
            "package_rendering_status": self.package_rendering_status,
            "privacy_status": self.privacy_status,
            "progress_status": self.progress_status,
            "recovery_status": self.recovery_status,
            "report_status": self.report_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "screenshot_status": self.screenshot_status,
            "security_status": self.security_status,
            "structure_status": self.structure_status,
            "telemetry_status": self.telemetry_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
            "workflow_status": self.workflow_status,
        }
