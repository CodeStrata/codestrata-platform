"""Models for Epic 9 completion verification reports."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Verdict = Literal["pass", "pass_with_limitations", "fail", "blocked"]

_ABS_PATH_RE = re.compile(r"(?<![\w.-])/Users/[\w./-]+")
_HOME_PATH_RE = re.compile(r"(?<![\w.-])/home/[\w./-]+")


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


def report_contains_forbidden_leak(blob: str, fragments: tuple[str, ...]) -> list[str]:
    return [token for token in fragments if token in blob]


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    category: str = "general"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "detail": sanitize_text(self.detail),
            "category": self.category,
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
            "classification": self.classification,
            "component": self.component,
            "expected": sanitize_text(self.expected),
            "actual": sanitize_text(self.actual),
            "detail": sanitize_text(self.detail),
        }


@dataclass(frozen=True, slots=True)
class SliceEvidence:
    slice_id: str
    purpose: str
    implementation_evidence: str
    documentation_evidence: str
    test_evidence: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "purpose": self.purpose,
            "implementation_evidence": sanitize_text(self.implementation_evidence),
            "documentation_evidence": sanitize_text(self.documentation_evidence),
            "test_evidence": sanitize_text(self.test_evidence),
            "status": self.status,
        }


@dataclass
class Epic9CompletionReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    epic: str
    completed_slices: list[str] = field(default_factory=list)
    expected_slice_count: int = 15
    completed_slice_count: int = 0
    engine_runtime_status: str = "unknown"
    vscode_runtime_status: str = "unknown"
    cross_client_status: str = "unknown"
    consent_status: str = "unknown"
    privacy_status: str = "unknown"
    identity_status: str = "unknown"
    persistence_status: str = "unknown"
    transport_status: str = "unknown"
    assessment_isolation_status: str = "unknown"
    extension_isolation_status: str = "unknown"
    catalog_status: str = "unknown"
    preview_status: str = "unknown"
    status_command_status: str = "unknown"
    documentation_status: str = "unknown"
    public_export_status: str = "unknown"
    packaging_status: str = "unknown"
    platform_boundary_status: str = "unknown"
    data_lake_boundary_status: str = "unknown"
    cursor_boundary_status: str = "unknown"
    epic10_absence_status: str = "unknown"
    production_posture: dict[str, str] = field(default_factory=dict)
    schema_registry: dict[str, str] = field(default_factory=dict)
    policy_registry: dict[str, str] = field(default_factory=dict)
    verification_registry: dict[str, str] = field(default_factory=dict)
    slice_matrix: list[SliceEvidence] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    intentionally_excluded: list[str] = field(default_factory=list)
    confirmations: dict[str, bool] = field(default_factory=dict)
    total_checks: int = 0
    failed_checks: int = 0

    def to_stable_dict(self) -> dict[str, Any]:
        payload = {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
            "verdict": self.verdict,
            "epic": self.epic,
            "completed_slices": list(self.completed_slices),
            "expected_slice_count": self.expected_slice_count,
            "completed_slice_count": self.completed_slice_count,
            "engine_runtime_status": self.engine_runtime_status,
            "vscode_runtime_status": self.vscode_runtime_status,
            "cross_client_status": self.cross_client_status,
            "consent_status": self.consent_status,
            "privacy_status": self.privacy_status,
            "identity_status": self.identity_status,
            "persistence_status": self.persistence_status,
            "transport_status": self.transport_status,
            "assessment_isolation_status": self.assessment_isolation_status,
            "extension_isolation_status": self.extension_isolation_status,
            "catalog_status": self.catalog_status,
            "preview_status": self.preview_status,
            "status_command_status": self.status_command_status,
            "documentation_status": self.documentation_status,
            "public_export_status": self.public_export_status,
            "packaging_status": self.packaging_status,
            "platform_boundary_status": self.platform_boundary_status,
            "data_lake_boundary_status": self.data_lake_boundary_status,
            "cursor_boundary_status": self.cursor_boundary_status,
            "epic10_absence_status": self.epic10_absence_status,
            "production_posture": dict(sorted(self.production_posture.items())),
            "schema_registry": dict(sorted(self.schema_registry.items())),
            "policy_registry": dict(sorted(self.policy_registry.items())),
            "verification_registry": dict(sorted(self.verification_registry.items())),
            "slice_matrix": [s.to_dict() for s in self.slice_matrix],
            "checks": [c.to_dict() for c in self.checks],
            "defects": [d.to_dict() for d in self.defects],
            "blockers": list(self.blockers),
            "limitations": list(self.limitations),
            "intentionally_excluded": list(self.intentionally_excluded),
            "confirmations": dict(sorted(self.confirmations.items())),
            "total_checks": self.total_checks,
            "failed_checks": self.failed_checks,
        }
        return sanitize_value(payload)

    def to_stable_json(self) -> str:
        return json.dumps(self.to_stable_dict(), indent=2, sort_keys=True) + "\n"

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_stable_json(), encoding="utf-8")
