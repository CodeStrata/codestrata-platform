"""Models for Slice 13.15 Epic 13 completion verification."""

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
    source_present: bool
    tests_present: bool
    docs_present: bool
    verification_status: str
    completion_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VsCodeEpic13CompletionReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str = "13"
    epic_version: str = "0.2.0"
    completion_contract: str = "vscode-epic13-completion-verification:1.0.0"
    slice_matrix: list[dict[str, Any]] = field(default_factory=list)
    policy_registry: list[dict[str, str]] = field(default_factory=list)
    schema_registry: list[dict[str, str]] = field(default_factory=list)
    extension_version: str = "0.2.0"
    active_editor_inventory: list[str] = field(default_factory=lambda: ["vscode"])
    retired_editor_inventory: list[str] = field(
        default_factory=lambda: ["cursor_extension"]
    )
    workflow_status: str = "not_executed"
    cli_status: str = "not_executed"
    initialization_status: str = "not_executed"
    assessment_status: str = "not_executed"
    progress_status: str = "not_executed"
    report_status: str = "not_executed"
    recovery_status: str = "not_executed"
    telemetry_status: str = "not_executed"
    locality_status: str = "not_executed"
    compatibility_status: str = "not_executed"
    marketplace_branding_status: str = "not_executed"
    marketplace_documentation_status: str = "not_executed"
    clean_install_status: str = "not_executed"
    package_boundary_status: str = "not_executed"
    privacy_status: str = "not_executed"
    security_status: str = "not_executed"
    engine_authority_status: str = "not_executed"
    platform_boundary_status: str = "not_executed"
    cloud_boundary_status: str = "not_executed"
    data_lake_boundary_status: str = "not_executed"
    documentation_status: str = "not_executed"
    release_posture: dict[str, Any] = field(default_factory=dict)
    epic14_absence_status: str = "not_executed"
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    completed_slices: int = 0
    total_slices: int = 15

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_editor_inventory": sorted(self.active_editor_inventory),
            "assessment_status": self.assessment_status,
            "blockers": list(self.blockers),
            "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
            "clean_install_status": self.clean_install_status,
            "cli_status": self.cli_status,
            "cloud_boundary_status": self.cloud_boundary_status,
            "compatibility_status": self.compatibility_status,
            "completed_slices": self.completed_slices,
            "completion_contract": self.completion_contract,
            "data_lake_boundary_status": self.data_lake_boundary_status,
            "defects": [d.to_dict() for d in self.defects],
            "documentation_status": self.documentation_status,
            "engine_authority_status": self.engine_authority_status,
            "epic": self.epic,
            "epic14_absence_status": self.epic14_absence_status,
            "epic_version": self.epic_version,
            "extension_version": self.extension_version,
            "failed_checks": self.failed_checks,
            "initialization_status": self.initialization_status,
            "limitations": sorted(self.limitations),
            "locality_status": self.locality_status,
            "marketplace_branding_status": self.marketplace_branding_status,
            "marketplace_documentation_status": self.marketplace_documentation_status,
            "package_boundary_status": self.package_boundary_status,
            "platform_boundary_status": self.platform_boundary_status,
            "policy_registry": sorted(
                self.policy_registry, key=lambda r: r.get("policy_id", "")
            ),
            "privacy_status": self.privacy_status,
            "progress_status": self.progress_status,
            "recovery_status": self.recovery_status,
            "release_posture": dict(sorted(self.release_posture.items())),
            "report_status": self.report_status,
            "retired_editor_inventory": sorted(self.retired_editor_inventory),
            "schema_name": self.schema_name,
            "schema_registry": sorted(
                self.schema_registry, key=lambda r: r.get("schema_name", "")
            ),
            "schema_version": self.schema_version,
            "security_status": self.security_status,
            "slice_matrix": sorted(
                self.slice_matrix, key=lambda r: r.get("slice", "")
            ),
            "telemetry_status": self.telemetry_status,
            "total_checks": self.total_checks,
            "total_slices": self.total_slices,
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "workflow_status": self.workflow_status,
        }
