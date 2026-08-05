"""Privacy-safe models for Community Data Lake verification reports (Slice 8.14)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from verification.community_data_lake.contract import (
    COMMUNITY_DATA_LAKE_VERIFICATION_ID,
    COMMUNITY_DATA_LAKE_VERIFICATION_VERSION,
    FORBIDDEN_REPORT_FRAGMENTS,
)


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    category: str = "structural"
    scenario: str = ""


@dataclass(frozen=True, slots=True)
class PolicyVersions:
    data_lake_policy: str
    envelope: str
    quarantine_schema: str
    quarantine_policy: str
    retention: str
    encryption: str
    access: str
    storage: str
    telemetry_partition: str
    assessment_metadata_partition: str
    cli_event_partition: str
    extension_event_partition: str
    ai_usage_partition: str
    verification: str


@dataclass(frozen=True, slots=True)
class VerificationReport:
    schema_name: str = COMMUNITY_DATA_LAKE_VERIFICATION_ID
    schema_version: str = COMMUNITY_DATA_LAKE_VERIFICATION_VERSION
    verification_id: str = COMMUNITY_DATA_LAKE_VERIFICATION_ID
    ok: bool = False
    verdict: str = "fail"
    policy_versions: PolicyVersions | None = None
    streams_tested: tuple[str, ...] = ()
    quarantine_tested: bool = False
    adapter_matrix: dict[str, dict[str, str]] = field(default_factory=dict)
    privacy_status: str = "unknown"
    retention_status: str = "unknown"
    encryption_status: str = "unknown"
    iam_status: str = "unknown"
    opentofu_status: str = "unknown"
    production_fail_closed_status: str = "unknown"
    checks: tuple[CheckResult, ...] = ()
    scenario_summary: dict[str, int] = field(default_factory=dict)
    defects: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    excluded_work: tuple[str, ...] = ()
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "adapter_matrix": self.adapter_matrix,
            "checks": [asdict(item) for item in self.checks],
            "defects": list(self.defects),
            "elapsed_ms": self.elapsed_ms,
            "encryption_status": self.encryption_status,
            "excluded_work": list(self.excluded_work),
            "iam_status": self.iam_status,
            "limitations": list(self.limitations),
            "ok": self.ok,
            "opentofu_status": self.opentofu_status,
            "privacy_status": self.privacy_status,
            "production_fail_closed_status": self.production_fail_closed_status,
            "quarantine_tested": self.quarantine_tested,
            "retention_status": self.retention_status,
            "scenario_summary": self.scenario_summary,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "streams_tested": list(self.streams_tested),
            "verdict": self.verdict,
            "verification_id": self.verification_id,
            "warnings": list(self.warnings),
        }
        if self.policy_versions is not None:
            payload["policy_versions"] = asdict(self.policy_versions)
        return payload

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
        for frag in FORBIDDEN_REPORT_FRAGMENTS:
            if frag in text:
                raise RuntimeError("verification report would leak forbidden fragment")
        # Structural privacy: never write object keys or event IDs into the report.
        lowered = text.lower()
        for token in ("object_key", "event_id", "installation_id", "raw/stream="):
            if f'"{token}"' in lowered or f"/{token}" in lowered:
                # Allow limitation/status strings that mention the words conceptually.
                if token in ("object_key",) and '"object_key"' in text:
                    raise RuntimeError("verification report must not include object_key fields")
        path.write_text(text, encoding="utf-8")


__all__ = ["CheckResult", "PolicyVersions", "VerificationReport"]
