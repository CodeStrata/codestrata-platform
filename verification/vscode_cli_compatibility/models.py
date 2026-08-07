"""Models for Slice 13.11 CLI compatibility verification."""

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
class VsCodeCliCompatibilityReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    compatibility_policy_status: str = "not_executed"
    matrix_status: str = "not_executed"
    ordering_status: str = "not_executed"
    workflow_integration_status: str = "not_executed"
    doctor_integration_status: str = "not_executed"
    installation_guidance_status: str = "not_executed"
    privacy_status: str = "not_executed"
    determinism_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "compatibility_policy_status": self.compatibility_policy_status,
            "defects": [d.to_dict() for d in self.defects],
            "determinism_status": self.determinism_status,
            "doctor_integration_status": self.doctor_integration_status,
            "failed_checks": self.failed_checks,
            "installation_guidance_status": self.installation_guidance_status,
            "limitations": sorted(self.limitations),
            "matrix_status": self.matrix_status,
            "ordering_status": self.ordering_status,
            "privacy_status": self.privacy_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
            "workflow_integration_status": self.workflow_integration_status,
        }
