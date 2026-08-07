"""Models for Slice 13.3 installation verification reports."""

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
class VsCodeCliInstallationReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    installation_policy_status: str = "not_executed"
    approach_decision: str = "guidance_only"
    method_inventory: list[str] = field(default_factory=list)
    discovery_mapping_status: str = "not_executed"
    command_surface_status: str = "not_executed"
    first_run_status: str = "not_executed"
    guidance_status: str = "not_executed"
    clipboard_status: str = "not_executed"
    terminal_status: str = "not_executed"
    documentation_status: str = "not_executed"
    automatic_installation_status: str = "not_executed"
    network_boundary_status: str = "not_executed"
    persistence_boundary_status: str = "not_executed"
    telemetry_boundary_status: str = "not_executed"
    analytics_boundary_status: str = "not_executed"
    doctor_boundary_status: str = "not_executed"
    activation_boundary_status: str = "not_executed"
    privacy_status: str = "not_executed"
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
            "activation_boundary_status": self.activation_boundary_status,
            "analytics_boundary_status": self.analytics_boundary_status,
            "approach_decision": self.approach_decision,
            "automatic_installation_status": self.automatic_installation_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "clipboard_status": self.clipboard_status,
            "command_surface_status": self.command_surface_status,
            "deferred_clean_install_status": self.deferred_clean_install_status,
            "defects": [d.to_dict() for d in self.defects],
            "discovery_mapping_status": self.discovery_mapping_status,
            "doctor_boundary_status": self.doctor_boundary_status,
            "documentation_status": self.documentation_status,
            "failed_checks": self.failed_checks,
            "first_run_status": self.first_run_status,
            "guidance_status": self.guidance_status,
            "installation_policy_status": self.installation_policy_status,
            "limitations": sorted(self.limitations),
            "method_inventory": list(self.method_inventory),
            "network_boundary_status": self.network_boundary_status,
            "persistence_boundary_status": self.persistence_boundary_status,
            "privacy_status": self.privacy_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "telemetry_boundary_status": self.telemetry_boundary_status,
            "terminal_status": self.terminal_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
        }
