"""Privacy-safe models for Community Data Lake completion reports (Slice 8.15)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from verification.community_data_lake_completion.contract import (
    COMMUNITY_DATA_LAKE_COMPLETION_ID,
    COMMUNITY_DATA_LAKE_COMPLETION_VERSION,
    EPIC,
    FORBIDDEN_REPORT_FRAGMENTS,
    INTEGRATION_REPORT_FILENAME,
    SLICES_COMPLETED,
)


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    category: str = "structural"
    scenario: str = ""


@dataclass(frozen=True, slots=True)
class CompletionReport:
    schema_name: str = COMMUNITY_DATA_LAKE_COMPLETION_ID
    schema_version: str = COMMUNITY_DATA_LAKE_COMPLETION_VERSION
    verdict: str = "fail"
    epic: str = EPIC
    slices_completed: tuple[str, ...] = SLICES_COMPLETED
    product_contract_versions: dict[str, str] = field(default_factory=dict)
    verification_contract_versions: dict[str, str] = field(default_factory=dict)
    package_inventory: tuple[str, ...] = ()
    stream_matrix: tuple[dict[str, str], ...] = ()
    quarantine_matrix: dict[str, str] = field(default_factory=dict)
    storage_abstraction_status: str = "unknown"
    retention_status: str = "unknown"
    encryption_status: str = "unknown"
    access_status: str = "unknown"
    integration_report_reference: str = INTEGRATION_REPORT_FILENAME
    integration_check_count: int = 0
    production_wiring_status: str = "disabled"
    fail_closed_status: str = "unknown"
    privacy_status: str = "unknown"
    determinism_status: str = "unknown"
    opentofu_status: str = "unknown"
    blockers: tuple[str, ...] = ()
    defects: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    intentionally_excluded: tuple[str, ...] = ()
    checks: tuple[CheckResult, ...] = ()
    scenario_summary: dict[str, int] = field(default_factory=dict)
    ok: bool = False
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "access_status": self.access_status,
            "blockers": list(self.blockers),
            "checks": [asdict(item) for item in self.checks],
            "defects": list(self.defects),
            "determinism_status": self.determinism_status,
            "elapsed_ms": self.elapsed_ms,
            "encryption_status": self.encryption_status,
            "epic": self.epic,
            "fail_closed_status": self.fail_closed_status,
            "integration_check_count": self.integration_check_count,
            "integration_report_reference": self.integration_report_reference,
            "intentionally_excluded": list(self.intentionally_excluded),
            "limitations": list(self.limitations),
            "ok": self.ok,
            "opentofu_status": self.opentofu_status,
            "package_inventory": list(self.package_inventory),
            "privacy_status": self.privacy_status,
            "product_contract_versions": dict(self.product_contract_versions),
            "production_wiring_status": self.production_wiring_status,
            "quarantine_matrix": dict(self.quarantine_matrix),
            "retention_status": self.retention_status,
            "scenario_summary": self.scenario_summary,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "slices_completed": list(self.slices_completed),
            "storage_abstraction_status": self.storage_abstraction_status,
            "stream_matrix": [dict(row) for row in self.stream_matrix],
            "verdict": self.verdict,
            "verification_contract_versions": dict(self.verification_contract_versions),
        }

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
        for frag in FORBIDDEN_REPORT_FRAGMENTS:
            if frag in text:
                raise RuntimeError("completion report would leak forbidden fragment")
        lowered = text.lower()
        for token in ("object_key", "event_id", "installation_id", "raw/stream="):
            if f'"{token}"' in lowered:
                raise RuntimeError(f"completion report must not include {token} fields")
        path.write_text(text, encoding="utf-8")


__all__ = ["CheckResult", "CompletionReport"]
