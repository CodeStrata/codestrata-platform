"""Models for Slice 12.10 Epic 12 completion verification."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL", "BLOCKED"]

_ABS_PATH_RE = re.compile(r"(?<![\w.-])/Users/[\w./-]+")
_HOME_PATH_RE = re.compile(r"(?<![\w.-])/home/[\w./-]+")
_FORBIDDEN = (
    "/Users/",
    "/home/",
    "file://",
    "-----BEGIN",
    "sk-",
    "AKIA",
    "AWS_SECRET",
    "amazonaws.com",
)


def sanitize_text(value: str) -> str:
    text = _ABS_PATH_RE.sub("[REDACTED_PATH]", value)
    return _HOME_PATH_RE.sub("[REDACTED_PATH]", text)


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [sanitize_value(v) for v in value]
    return value


def report_contains_forbidden_leak(blob: str) -> list[str]:
    return [t for t in _FORBIDDEN if t in blob]


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    category: str = "general"

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "detail": sanitize_text(self.detail),
            "name": self.name,
            "ok": self.ok,
        }


@dataclass(frozen=True, slots=True)
class Defect:
    classification: str
    component: str
    expected: str
    actual: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "actual": sanitize_text(self.actual),
            "classification": self.classification,
            "component": self.component,
            "expected": sanitize_text(self.expected),
        }


@dataclass(frozen=True, slots=True)
class SliceEvidence:
    slice_id: str
    title: str
    package: str
    schema: str
    report_relative: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "package": self.package,
            "report_relative": self.report_relative,
            "schema": self.schema,
            "slice_id": self.slice_id,
            "status": self.status,
            "title": self.title,
        }


@dataclass
class Epic12CompletionReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: int = 12
    release: str = "0.2.0"
    completed_slices: int = 0
    total_slices: int = 10
    slice_matrix: list[SliceEvidence] = field(default_factory=list)
    cursor_product_status: str = "not_executed"
    cursor_release_status: str = "not_executed"
    cursor_documentation_status: str = "not_executed"
    retired_client_status: str = "not_executed"
    vscode_status: str = "not_executed"
    infrastructure_contract_status: str = "not_executed"
    infrastructure_exporter_status: str = "not_executed"
    infrastructure_export_status: str = "not_executed"
    export_target_status: str = "not_executed"
    ci_release_boundary_status: str = "not_executed"
    active_editor_extensions: list[str] = field(default_factory=list)
    active_clients: list[str] = field(default_factory=list)
    retired_clients: list[str] = field(default_factory=list)
    export_targets: list[str] = field(default_factory=list)
    target_visibility: dict[str, str] = field(default_factory=dict)
    manifest_registry: dict[str, str] = field(default_factory=dict)
    policy_registry: dict[str, str] = field(default_factory=dict)
    schema_registry: dict[str, str] = field(default_factory=dict)
    public_private_boundary_status: str = "not_executed"
    packaging_status: str = "not_executed"
    documentation_status: str = "not_executed"
    epic13_absent_status: str = "not_executed"
    start_epic_13: bool = False
    release_posture: dict[str, bool] = field(default_factory=dict)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    checks: list[CheckResult] = field(default_factory=list)
    prior_verifier_statuses: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return sanitize_value(
            {
                "active_clients": sorted(self.active_clients),
                "active_editor_extensions": sorted(self.active_editor_extensions),
                "blockers": sorted(self.blockers),
                "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
                "ci_release_boundary_status": self.ci_release_boundary_status,
                "completed_slices": self.completed_slices,
                "cursor_documentation_status": self.cursor_documentation_status,
                "cursor_product_status": self.cursor_product_status,
                "cursor_release_status": self.cursor_release_status,
                "defects": [d.to_dict() for d in self.defects],
                "documentation_status": self.documentation_status,
                "epic": self.epic,
                "epic13_absent_status": self.epic13_absent_status,
                "export_target_status": self.export_target_status,
                "export_targets": sorted(self.export_targets),
                "failed_checks": self.failed_checks,
                "infrastructure_contract_status": self.infrastructure_contract_status,
                "infrastructure_export_status": self.infrastructure_export_status,
                "infrastructure_exporter_status": self.infrastructure_exporter_status,
                "limitations": sorted(self.limitations),
                "manifest_registry": dict(sorted(self.manifest_registry.items())),
                "packaging_status": self.packaging_status,
                "policy_registry": dict(sorted(self.policy_registry.items())),
                "prior_verifier_statuses": dict(
                    sorted(self.prior_verifier_statuses.items())
                ),
                "public_private_boundary_status": self.public_private_boundary_status,
                "release": self.release,
                "release_posture": dict(sorted(self.release_posture.items())),
                "retired_client_status": self.retired_client_status,
                "retired_clients": sorted(self.retired_clients),
                "schema_name": self.schema_name,
                "schema_registry": dict(sorted(self.schema_registry.items())),
                "schema_version": self.schema_version,
                "slice_matrix": [s.to_dict() for s in self.slice_matrix],
                "start_epic_13": self.start_epic_13,
                "target_visibility": dict(sorted(self.target_visibility.items())),
                "total_checks": self.total_checks,
                "total_slices": self.total_slices,
                "verdict": self.verdict,
                "verification_id": self.verification_id,
                "vscode_status": self.vscode_status,
            }
        )

    def write_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
