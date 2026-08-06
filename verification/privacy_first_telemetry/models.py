"""Models for Slice 9.14 cross-client telemetry privacy verification."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

Verdict = Literal["pass", "pass_with_limitations", "fail", "blocked"]

_ABS_PATH_RE = re.compile(r"(?<![\w.-])/Users/[\w./-]+")
_HOME_PATH_RE = re.compile(r"(?<![\w.-])/home/[\w./-]+")
_USERNAME_RE = re.compile(r"(?<![\w@])[\w.-]+@[\w.-]+\.\w+")
# Exact identity / payload leak tokens (avoid matching limitation codes).
_FORBIDDEN_REPORT_TOKENS = (
    '"installation_id"',
    '"machineId"',
    '"telemetrySessionId"',
    "/Users/",
    "/home/",
    "file://",
    "-----BEGIN",
)


def sanitize_text(value: str) -> str:
    text = _ABS_PATH_RE.sub("[REDACTED_PATH]", value)
    text = _HOME_PATH_RE.sub("[REDACTED_PATH]", text)
    text = _USERNAME_RE.sub("[REDACTED_USER]", text)
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
    client: str = "both"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "ok": self.ok,
            "detail": sanitize_text(self.detail),
            "category": self.category,
            "client": self.client,
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
class PrincipleStatus:
    principle: str
    engine_status: str
    vscode_status: str
    evidence: str
    intentional_difference: str = ""
    verdict: str = "pass"

    def to_dict(self) -> dict[str, Any]:
        return {
            "principle": self.principle,
            "engine_status": self.engine_status,
            "vscode_status": self.vscode_status,
            "evidence": sanitize_text(self.evidence),
            "intentional_difference": sanitize_text(self.intentional_difference),
            "verdict": self.verdict,
        }


@dataclass
class CrossClientTelemetryPrivacyReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: Verdict
    engine_runtime_policy_version: str
    engine_event_schema_version: str
    vscode_runtime_policy_version: str
    vscode_event_schema_version: str
    shared_principles: list[PrincipleStatus] = field(default_factory=list)
    intentional_differences: list[str] = field(default_factory=list)
    consent_matrix: list[CheckResult] = field(default_factory=list)
    privacy_matrix: list[CheckResult] = field(default_factory=list)
    event_matrix: list[CheckResult] = field(default_factory=list)
    preview_matrix: list[CheckResult] = field(default_factory=list)
    transport_matrix: list[CheckResult] = field(default_factory=list)
    isolation_matrix: list[CheckResult] = field(default_factory=list)
    persistence_matrix: list[CheckResult] = field(default_factory=list)
    identity_matrix: list[CheckResult] = field(default_factory=list)
    diagnostics_matrix: list[CheckResult] = field(default_factory=list)
    boundary_matrix: list[CheckResult] = field(default_factory=list)
    deterministic_checks: list[CheckResult] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    confirmations: dict[str, bool] = field(default_factory=dict)
    total_checks: int = 0
    failed_checks: int = 0

    def to_stable_dict(self) -> dict[str, Any]:
        payload = {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
            "verdict": self.verdict,
            "engine_runtime_policy_version": self.engine_runtime_policy_version,
            "engine_event_schema_version": self.engine_event_schema_version,
            "vscode_runtime_policy_version": self.vscode_runtime_policy_version,
            "vscode_event_schema_version": self.vscode_event_schema_version,
            "shared_principles": [p.to_dict() for p in self.shared_principles],
            "intentional_differences": list(self.intentional_differences),
            "consent_matrix": [c.to_dict() for c in self.consent_matrix],
            "privacy_matrix": [c.to_dict() for c in self.privacy_matrix],
            "event_matrix": [c.to_dict() for c in self.event_matrix],
            "preview_matrix": [c.to_dict() for c in self.preview_matrix],
            "transport_matrix": [c.to_dict() for c in self.transport_matrix],
            "isolation_matrix": [c.to_dict() for c in self.isolation_matrix],
            "persistence_matrix": [c.to_dict() for c in self.persistence_matrix],
            "identity_matrix": [c.to_dict() for c in self.identity_matrix],
            "diagnostics_matrix": [c.to_dict() for c in self.diagnostics_matrix],
            "boundary_matrix": [c.to_dict() for c in self.boundary_matrix],
            "deterministic_checks": [c.to_dict() for c in self.deterministic_checks],
            "checks": [c.to_dict() for c in self.checks],
            "defects": [d.to_dict() for d in self.defects],
            "limitations": list(self.limitations),
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
