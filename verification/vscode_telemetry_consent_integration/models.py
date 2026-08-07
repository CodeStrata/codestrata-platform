"""Models for Slice 13.9 telemetry consent integration verification."""

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
class VsCodeTelemetryConsentIntegrationReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    integration_policy_status: str = "not_executed"
    runtime_relationship_status: str = "not_executed"
    eligibility_status: str = "not_executed"
    readiness_ordering_status: str = "not_executed"
    consent_prompt_status: str = "not_executed"
    consent_scope_status: str = "not_executed"
    non_interactive_status: str = "not_executed"
    allow_status: str = "not_executed"
    deny_status: str = "not_executed"
    analytics_integration_status: str = "not_executed"
    telemetry_lifecycle_status: str = "not_executed"
    primary_authority_status: str = "not_executed"
    report_boundary_status: str = "not_executed"
    recovery_boundary_status: str = "not_executed"
    init_install_discovery_status: str = "not_executed"
    activation_status: str = "not_executed"
    persistence_status: str = "not_executed"
    identity_status: str = "not_executed"
    transport_status: str = "not_executed"
    privacy_status: str = "not_executed"
    diagnostics_status: str = "not_executed"
    cross_client_relationship_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "activation_status": self.activation_status,
            "allow_status": self.allow_status,
            "analytics_integration_status": self.analytics_integration_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "consent_prompt_status": self.consent_prompt_status,
            "consent_scope_status": self.consent_scope_status,
            "cross_client_relationship_status": self.cross_client_relationship_status,
            "defects": [d.to_dict() for d in self.defects],
            "deny_status": self.deny_status,
            "diagnostics_status": self.diagnostics_status,
            "eligibility_status": self.eligibility_status,
            "failed_checks": self.failed_checks,
            "identity_status": self.identity_status,
            "init_install_discovery_status": self.init_install_discovery_status,
            "integration_policy_status": self.integration_policy_status,
            "limitations": sorted(self.limitations),
            "non_interactive_status": self.non_interactive_status,
            "persistence_status": self.persistence_status,
            "primary_authority_status": self.primary_authority_status,
            "privacy_status": self.privacy_status,
            "readiness_ordering_status": self.readiness_ordering_status,
            "recovery_boundary_status": self.recovery_boundary_status,
            "report_boundary_status": self.report_boundary_status,
            "runtime_relationship_status": self.runtime_relationship_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "telemetry_lifecycle_status": self.telemetry_lifecycle_status,
            "total_checks": self.total_checks,
            "transport_status": self.transport_status,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "vscode_regression_status": self.vscode_regression_status,
        }
