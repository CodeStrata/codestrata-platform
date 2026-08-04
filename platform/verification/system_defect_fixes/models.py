"""Models for SV.13 verification artifacts."""

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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DefectLedgerEntry:
    defect_id: str
    original_sv12_failure: str
    affected_repositories: list[str]
    affected_rule_ids: list[str]
    root_cause_classification: list[str]
    fix_boundary: str
    product_files_changed: list[str]
    regression_tests: list[str]
    before_population: str
    after_population: str
    privacy_outcome: str
    schema_outcome: str
    determinism_outcome: str
    closure_status: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Sv13VerificationReport:
    schema_name: str
    schema_version: str
    verdict: str
    repository_count: int
    included_repository_ids: list[str]
    checks: list[CheckResult] = field(default_factory=list)
    ledger: DefectLedgerEntry | None = None
    dataset_id: str | None = None
    aggregation_id: str | None = None
    eir_report_id: str | None = None
    website_export_id: str | None = None
    interpretation_policy_bundle_id: str | None = None
    dataset_disclaimer: str = ""
    confirmations: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "verdict": self.verdict,
            "repository_count": self.repository_count,
            "included_repository_ids": list(self.included_repository_ids),
            "checks": [c.to_dict() for c in self.checks],
            "ledger": self.ledger.to_dict() if self.ledger else None,
            "dataset_id": self.dataset_id,
            "aggregation_id": self.aggregation_id,
            "eir_report_id": self.eir_report_id,
            "website_export_id": self.website_export_id,
            "interpretation_policy_bundle_id": self.interpretation_policy_bundle_id,
            "dataset_disclaimer": self.dataset_disclaimer,
            "confirmations": dict(self.confirmations),
        }
        return payload

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
