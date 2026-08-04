"""Models for SV.16 release artifact verification."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_ABS_PATH_RE = re.compile(r"(?<![\w.-])/Users/[\w./-]+")
_HOME_PATH_RE = re.compile(r"(?<![\w.-])/home/[\w./-]+")
_USERNAME_RE = re.compile(r"(?<![\w@])[\w.-]+@[\w.-]+\.\w+")


def _sanitize_text(value: str) -> str:
    text = _ABS_PATH_RE.sub("[REDACTED_PATH]", value)
    text = _HOME_PATH_RE.sub("[REDACTED_PATH]", text)
    text = _USERNAME_RE.sub("[REDACTED_USER]", text)
    return text


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    category: str = "general"
    status: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["detail"] = _sanitize_text(payload["detail"])
        return payload


@dataclass(frozen=True, slots=True)
class Defect:
    classification: str
    component: str
    expected: str
    actual: str
    release_impact: str = "blocking"
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["detail"] = _sanitize_text(payload["detail"])
        payload["expected"] = _sanitize_text(payload["expected"])
        payload["actual"] = _sanitize_text(payload["actual"])
        return payload


@dataclass(frozen=True, slots=True)
class Blocker:
    code: str
    detail: str
    category: str = "blocker"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "detail": _sanitize_text(self.detail),
            "category": self.category,
        }


@dataclass(frozen=True, slots=True)
class Warning:
    code: str
    detail: str
    release_impact: str = "informational"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "detail": _sanitize_text(self.detail),
            "release_impact": self.release_impact,
        }


@dataclass
class Sv16VerificationReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: str
    intended_release_version: str
    repository_count: int
    checks: list[CheckResult] = field(default_factory=list)
    defects: list[Defect] = field(default_factory=list)
    blockers: list[Blocker] = field(default_factory=list)
    warnings: list[Warning] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    confirmations: dict[str, bool] = field(default_factory=dict)
    artifact_paths: dict[str, str] = field(default_factory=dict)
    checksums: dict[str, str] = field(default_factory=dict)
    ei_identities: dict[str, str] = field(default_factory=dict)
    dataset_disclaimer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _sanitize_value(
            {
                "schema_name": self.schema_name,
                "schema_version": self.schema_version,
                "verification_id": self.verification_id,
                "verdict": self.verdict,
                "intended_release_version": self.intended_release_version,
                "repository_count": self.repository_count,
                "checks": [c.to_dict() for c in self.checks],
                "defects": [d.to_dict() for d in self.defects],
                "blockers": [b.to_dict() for b in self.blockers],
                "warnings": [w.to_dict() for w in self.warnings],
                "limitations": list(self.limitations),
                "confirmations": dict(self.confirmations),
                "artifact_paths": dict(self.artifact_paths),
                "checksums": dict(self.checksums),
                "ei_identities": dict(self.ei_identities),
                "dataset_disclaimer": self.dataset_disclaimer,
                "checks_pass": sum(1 for c in self.checks if c.ok),
                "checks_total": len(self.checks),
            }
        )

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
