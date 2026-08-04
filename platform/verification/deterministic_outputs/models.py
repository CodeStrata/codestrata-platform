"""Models for SV.15 deterministic output verification."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    category: str = "general"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeterminismDefect:
    classification: str
    contract: str
    expected: str
    actual: str
    release_impact: str = "blocking"
    detail: str = ""
    affected_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeterminismWarning:
    code: str
    detail: str
    release_impact: str = "informational"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Sv15VerificationReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: str
    repository_count: int
    input_artifact_identities: dict[str, str] = field(default_factory=dict)
    deterministic_contract_registry: list[dict[str, Any]] = field(default_factory=list)
    approved_volatile_fields: list[dict[str, Any]] = field(default_factory=list)
    forbidden_environment_fields: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    fingerprints: dict[str, str] = field(default_factory=dict)
    defects: list[DeterminismDefect] = field(default_factory=list)
    warnings: list[DeterminismWarning] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    confirmations: dict[str, bool] = field(default_factory=dict)
    dataset_disclaimer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
            "verdict": self.verdict,
            "repository_count": self.repository_count,
            "input_artifact_identities": dict(self.input_artifact_identities),
            "deterministic_contract_registry": list(self.deterministic_contract_registry),
            "approved_volatile_fields": list(self.approved_volatile_fields),
            "forbidden_environment_fields": list(self.forbidden_environment_fields),
            "checks": [c.to_dict() for c in self.checks],
            "fingerprints": dict(self.fingerprints),
            "defects": [d.to_dict() for d in self.defects],
            "warnings": [w.to_dict() for w in self.warnings],
            "limitations": list(self.limitations),
            "confirmations": dict(self.confirmations),
            "dataset_disclaimer": self.dataset_disclaimer,
            "checks_pass": sum(1 for c in self.checks if c.ok),
            "checks_total": len(self.checks),
        }

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
