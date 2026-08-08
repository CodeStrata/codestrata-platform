"""Models for Slice 14.5 verification."""

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
class VsCodeVisualReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "14"
    slice: str = "14.5"
    visual_policy: str = "codestrata-vscode-visual-experience-policy:1.0"
    visual_policy_status: str = "not_executed"
    design_system_mapping_status: str = "not_executed"
    native_host_boundary_status: str = "not_executed"
    product_naming_status: str = "not_executed"
    command_title_status: str = "not_executed"
    activity_bar_status: str = "not_executed"
    first_run_status: str = "not_executed"
    messaging_status: str = "not_executed"
    progress_status: str = "not_executed"
    status_bar_status: str = "not_executed"
    recovery_status: str = "not_executed"
    report_ready_status: str = "not_executed"
    cli_guidance_status: str = "not_executed"
    doctor_status: str = "not_executed"
    settings_status: str = "not_executed"
    output_channel_status: str = "not_executed"
    icon_status: str = "not_executed"
    welcome_state_status: str = "not_executed"
    community_scope_status: str = "not_executed"
    privacy_wording_status: str = "not_executed"
    telemetry_wording_status: str = "not_executed"
    theme_compatibility_status: str = "not_executed"
    accessibility_status: str = "not_executed"
    marketplace_boundary_status: str = "not_executed"
    asset_boundary_status: str = "not_executed"
    legacy_branding_status: str = "not_executed"
    vscode_regression_status: str = "not_executed"
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
            "activity_bar_status": self.activity_bar_status,
            "asset_boundary_status": self.asset_boundary_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "cli_guidance_status": self.cli_guidance_status,
            "command_title_status": self.command_title_status,
            "community_scope_status": self.community_scope_status,
            "defects": [d.to_dict() for d in self.defects],
            "design_system_mapping_status": self.design_system_mapping_status,
            "determinism_status": self.determinism_status,
            "doctor_status": self.doctor_status,
            "epic": self.epic,
            "failed_checks": self.failed_checks,
            "first_run_status": self.first_run_status,
            "icon_status": self.icon_status,
            "legacy_branding_status": self.legacy_branding_status,
            "limitations": sorted(self.limitations),
            "marketplace_boundary_status": self.marketplace_boundary_status,
            "messaging_status": self.messaging_status,
            "native_host_boundary_status": self.native_host_boundary_status,
            "output_channel_status": self.output_channel_status,
            "privacy_wording_status": self.privacy_wording_status,
            "product_naming_status": self.product_naming_status,
            "progress_status": self.progress_status,
            "recovery_status": self.recovery_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "report_ready_status": self.report_ready_status,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "settings_status": self.settings_status,
            "slice": self.slice,
            "status_bar_status": self.status_bar_status,
            "telemetry_wording_status": self.telemetry_wording_status,
            "theme_compatibility_status": self.theme_compatibility_status,
            "total_checks": self.total_checks,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "visual_policy": self.visual_policy,
            "visual_policy_status": self.visual_policy_status,
            "vscode_regression_status": self.vscode_regression_status,
            "welcome_state_status": self.welcome_state_status,
        }
