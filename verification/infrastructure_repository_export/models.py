"""Models for Slice 12.7 export verification."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Verdict = Literal["PASS", "PASS_WITH_LIMITATIONS", "FAIL", "BLOCKED"]

_ABS_PATH_RE = re.compile(r"(?<![\w.-])/Users/[\w./-]+")
_HOME_PATH_RE = re.compile(r"(?<![\w.-])/home/[\w./-]+")
_FORBIDDEN_REPORT_TOKENS = (
    "/Users/",
    "/home/",
    "file://",
    "-----BEGIN",
    "sk-",
    "AKIA",
    "VSCE_PAT=",
    "OVSX_TOKEN=",
    "amazonaws.com",
    "github.com/",
)


def sanitize_text(value: str) -> str:
    text = _ABS_PATH_RE.sub("[REDACTED_PATH]", value)
    text = _HOME_PATH_RE.sub("[REDACTED_PATH]", text)
    return text


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    return value


def report_contains_forbidden_leak(blob: str) -> list[str]:
    return [token for token in _FORBIDDEN_REPORT_TOKENS if token in blob]


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
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "actual": sanitize_text(self.actual),
            "classification": self.classification,
            "component": self.component,
            "detail": sanitize_text(self.detail),
            "expected": sanitize_text(self.expected),
        }


@dataclass
class InfrastructureRepositoryExportReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    exporter_status: str = "not_executed"
    dual_export_status: str = "not_executed"
    deterministic_tree_status: str = "not_executed"
    manifest_status: str = "not_executed"
    inventory_status: str = "not_executed"
    checksum_status: str = "not_executed"
    layout_status: str = "not_executed"
    required_content_status: str = "not_executed"
    prohibited_file_status: str = "not_executed"
    product_boundary_status: str = "not_executed"
    dependency_boundary_status: str = "not_executed"
    secret_scan_status: str = "not_executed"
    tfvars_status: str = "not_executed"
    local_path_status: str = "not_executed"
    documentation_link_status: str = "not_executed"
    readme_status: str = "not_executed"
    security_document_status: str = "not_executed"
    gitignore_status: str = "not_executed"
    lockfile_status: str = "not_executed"
    permission_status: str = "not_executed"
    symlink_status: str = "not_executed"
    python_test_status: str = "not_executed"
    opentofu_tool_status: str = "not_executed"
    opentofu_format_status: str = "not_executed"
    opentofu_init_status: str = "not_executed"
    opentofu_validate_status: str = "not_executed"
    validation_roots: list[str] = field(default_factory=list)
    aws_boundary_status: str = "not_executed"
    git_boundary_status: str = "not_executed"
    deployment_boundary_status: str = "not_executed"
    subprocess_safety_status: str = "not_executed"
    deterministic_status: str = "not_executed"
    exported_file_count: int = 0
    exported_executable_count: int = 0
    generated_root_file_count: int = 0
    limitations: list[str] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    checks: list[CheckResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return sanitize_value(
            {
                "aws_boundary_status": self.aws_boundary_status,
                "blockers": sorted(self.blockers),
                "checksum_status": self.checksum_status,
                "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
                "defects": [d.to_dict() for d in self.defects],
                "dependency_boundary_status": self.dependency_boundary_status,
                "deployment_boundary_status": self.deployment_boundary_status,
                "deterministic_status": self.deterministic_status,
                "deterministic_tree_status": self.deterministic_tree_status,
                "documentation_link_status": self.documentation_link_status,
                "dual_export_status": self.dual_export_status,
                "exported_executable_count": self.exported_executable_count,
                "exported_file_count": self.exported_file_count,
                "exporter_status": self.exporter_status,
                "failed_checks": self.failed_checks,
                "generated_root_file_count": self.generated_root_file_count,
                "git_boundary_status": self.git_boundary_status,
                "gitignore_status": self.gitignore_status,
                "inventory_status": self.inventory_status,
                "layout_status": self.layout_status,
                "limitations": sorted(self.limitations),
                "local_path_status": self.local_path_status,
                "lockfile_status": self.lockfile_status,
                "manifest_status": self.manifest_status,
                "opentofu_format_status": self.opentofu_format_status,
                "opentofu_init_status": self.opentofu_init_status,
                "opentofu_tool_status": self.opentofu_tool_status,
                "opentofu_validate_status": self.opentofu_validate_status,
                "permission_status": self.permission_status,
                "product_boundary_status": self.product_boundary_status,
                "prohibited_file_status": self.prohibited_file_status,
                "python_test_status": self.python_test_status,
                "readme_status": self.readme_status,
                "required_content_status": self.required_content_status,
                "schema_name": self.schema_name,
                "schema_version": self.schema_version,
                "secret_scan_status": self.secret_scan_status,
                "security_document_status": self.security_document_status,
                "subprocess_safety_status": self.subprocess_safety_status,
                "symlink_status": self.symlink_status,
                "tfvars_status": self.tfvars_status,
                "total_checks": self.total_checks,
                "validation_roots": sorted(self.validation_roots),
                "verdict": self.verdict,
                "verification_id": self.verification_id,
            }
        )

    def write_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
