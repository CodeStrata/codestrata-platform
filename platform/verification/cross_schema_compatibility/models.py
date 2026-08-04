"""Models for SV.14 cross-schema compatibility verification."""

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
class CompatibilityFailure:
    classification: str
    producer: str
    consumer: str
    schema: str
    field: str
    expected: str
    actual: str
    release_impact: str = "blocking"
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CompatibilityWarning:
    code: str
    detail: str
    release_impact: str = "informational"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Sv14VerificationReport:
    schema_name: str
    schema_version: str
    verification_id: str
    verdict: str
    repository_count: int
    contract_registry: list[dict[str, Any]] = field(default_factory=list)
    producer_consumer_matrix: list[dict[str, Any]] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    compatibility_failures: list[CompatibilityFailure] = field(default_factory=list)
    warnings: list[CompatibilityWarning] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    confirmations: dict[str, bool] = field(default_factory=dict)
    dataset_disclaimer: str = ""
    identities: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
            "verdict": self.verdict,
            "repository_count": self.repository_count,
            "contract_registry": list(self.contract_registry),
            "producer_consumer_matrix": list(self.producer_consumer_matrix),
            "checks": [c.to_dict() for c in self.checks],
            "compatibility_failures": [
                f.to_dict() for f in self.compatibility_failures
            ],
            "warnings": [w.to_dict() for w in self.warnings],
            "limitations": list(self.limitations),
            "confirmations": dict(self.confirmations),
            "dataset_disclaimer": self.dataset_disclaimer,
            "identities": dict(self.identities),
            "checks_pass": sum(1 for c in self.checks if c.ok),
            "checks_total": len(self.checks),
        }

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
