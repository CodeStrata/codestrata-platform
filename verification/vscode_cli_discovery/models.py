"""Models for Slice 13.2 CLI discovery verification reports."""

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
class VsCodeCliDiscoveryReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    discovery_policy_status: str = "not_executed"
    candidate_source_inventory: list[str] = field(default_factory=list)
    precedence_status: str = "not_executed"
    explicit_configuration_status: str = "not_executed"
    path_discovery_status: str = "not_executed"
    executable_validation_status: str = "not_executed"
    probe_status: str = "not_executed"
    identity_validation_status: str = "not_executed"
    version_parsing_status: str = "not_executed"
    compatibility_status: str = "not_executed"
    activation_boundary_status: str = "not_executed"
    workflow_integration_status: str = "not_executed"
    doctor_boundary_status: str = "not_executed"
    privacy_status: str = "not_executed"
    telemetry_boundary_status: str = "not_executed"
    analytics_boundary_status: str = "not_executed"
    subprocess_boundary_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
    deferred_installation_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "activation_boundary_status": self.activation_boundary_status,
            "analytics_boundary_status": self.analytics_boundary_status,
            "blockers": list(self.blockers),
            "candidate_source_inventory": list(self.candidate_source_inventory),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "compatibility_status": self.compatibility_status,
            "deferred_installation_status": self.deferred_installation_status,
            "defects": [d.to_dict() for d in self.defects],
            "discovery_policy_status": self.discovery_policy_status,
            "doctor_boundary_status": self.doctor_boundary_status,
            "executable_validation_status": self.executable_validation_status,
            "explicit_configuration_status": self.explicit_configuration_status,
            "failed_checks": self.failed_checks,
            "identity_validation_status": self.identity_validation_status,
            "limitations": sorted(self.limitations),
            "path_discovery_status": self.path_discovery_status,
            "precedence_status": self.precedence_status,
            "privacy_status": self.privacy_status,
            "probe_status": self.probe_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "subprocess_boundary_status": self.subprocess_boundary_status,
            "telemetry_boundary_status": self.telemetry_boundary_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "version_parsing_status": self.version_parsing_status,
            "vscode_regression_status": self.vscode_regression_status,
            "workflow_integration_status": self.workflow_integration_status,
        }


FORBIDDEN_LEAK_MARKERS = (
    "/Users/",
    "/home/",
    "C:\\\\Users",
    "PATH=",
    "stdout",
    "stderr",
    "timestamp",
)


def report_contains_forbidden_leak(payload: dict[str, Any]) -> list[str]:
    text = str(payload)
    return [marker for marker in FORBIDDEN_LEAK_MARKERS if marker in text and marker != "stdout"]
