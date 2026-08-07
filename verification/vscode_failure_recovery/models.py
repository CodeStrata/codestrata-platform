"""Models for Slice 13.8 failure recovery verification reports."""

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
class VsCodeFailureRecoveryReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    recovery_policy_status: str = "not_executed"
    catalog_status: str = "not_executed"
    presentation_status: str = "not_executed"
    primary_authority_status: str = "not_executed"
    secondary_isolation_status: str = "not_executed"
    auto_execute_forbidden_status: str = "not_executed"
    privacy_status: str = "not_executed"
    telemetry_boundary_status: str = "not_executed"
    analytics_boundary_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "analytics_boundary_status": self.analytics_boundary_status,
            "auto_execute_forbidden_status": self.auto_execute_forbidden_status,
            "blockers": list(self.blockers),
            "catalog_status": self.catalog_status,
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "defects": [d.to_dict() for d in self.defects],
            "failed_checks": self.failed_checks,
            "limitations": sorted(self.limitations),
            "presentation_status": self.presentation_status,
            "primary_authority_status": self.primary_authority_status,
            "privacy_status": self.privacy_status,
            "recovery_policy_status": self.recovery_policy_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "secondary_isolation_status": self.secondary_isolation_status,
            "telemetry_boundary_status": self.telemetry_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
        }
