"""Models for Slice 12.5 Infrastructure repository contract verification."""

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
class InfrastructureRepositoryContractReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    repository_name: str
    repository_visibility: str
    source_authority_decision: str
    destination_layout_decision: str
    export_allowlist_status: str = "not_executed"
    prohibited_file_status: str = "not_executed"
    shared_file_status: str = "not_executed"
    state_boundary_status: str = "not_executed"
    secrets_boundary_status: str = "not_executed"
    dependency_boundary_status: str = "not_executed"
    opentofu_validation_contract_status: str = "not_executed"
    versioning_status: str = "not_executed"
    git_boundary_status: str = "not_executed"
    synchronization_status: str = "not_executed"
    manifest_contract_status: str = "not_executed"
    inventory_contract_status: str = "not_executed"
    permission_contract_status: str = "not_executed"
    documentation_link_status: str = "not_executed"
    public_private_boundary_status: str = "not_executed"
    ci_contract_status: str = "not_executed"
    migration_contract_status: str = "not_executed"
    rollback_status: str = "not_executed"
    required_source_inventory: list[str] = field(default_factory=list)
    optional_source_inventory: list[str] = field(default_factory=list)
    excluded_category_inventory: list[str] = field(default_factory=list)
    validation_roots: list[str] = field(default_factory=list)
    implementation_requirements_for_12_6: list[str] = field(default_factory=list)
    verification_requirements_for_12_7: list[str] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    total_checks: int = 0
    failed_checks: int = 0
    checks: list[CheckResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return sanitize_value(
            {
                "blockers": sorted(self.blockers),
                "checks": [c.to_dict() for c in sorted(self.checks, key=lambda x: x.name)],
                "ci_contract_status": self.ci_contract_status,
                "defects": [d.to_dict() for d in self.defects],
                "dependency_boundary_status": self.dependency_boundary_status,
                "destination_layout_decision": self.destination_layout_decision,
                "documentation_link_status": self.documentation_link_status,
                "excluded_category_inventory": sorted(self.excluded_category_inventory),
                "export_allowlist_status": self.export_allowlist_status,
                "failed_checks": self.failed_checks,
                "git_boundary_status": self.git_boundary_status,
                "implementation_requirements_for_12_6": sorted(
                    self.implementation_requirements_for_12_6
                ),
                "inventory_contract_status": self.inventory_contract_status,
                "limitations": sorted(self.limitations),
                "manifest_contract_status": self.manifest_contract_status,
                "migration_contract_status": self.migration_contract_status,
                "opentofu_validation_contract_status": self.opentofu_validation_contract_status,
                "optional_source_inventory": sorted(self.optional_source_inventory),
                "permission_contract_status": self.permission_contract_status,
                "prohibited_file_status": self.prohibited_file_status,
                "public_private_boundary_status": self.public_private_boundary_status,
                "repository_name": self.repository_name,
                "repository_visibility": self.repository_visibility,
                "required_source_inventory": sorted(self.required_source_inventory),
                "rollback_status": self.rollback_status,
                "schema_name": self.schema_name,
                "schema_version": self.schema_version,
                "secrets_boundary_status": self.secrets_boundary_status,
                "shared_file_status": self.shared_file_status,
                "source_authority_decision": self.source_authority_decision,
                "state_boundary_status": self.state_boundary_status,
                "synchronization_status": self.synchronization_status,
                "total_checks": self.total_checks,
                "validation_roots": sorted(self.validation_roots),
                "verdict": self.verdict,
                "verification_id": self.verification_id,
                "verification_requirements_for_12_7": sorted(
                    self.verification_requirements_for_12_7
                ),
                "versioning_status": self.versioning_status,
            }
        )

    def write_json(self, path: Path) -> None:
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
