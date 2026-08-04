"""Privacy-safe models for SV.8 verification reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from verification.website_export.contract import (
    FORBIDDEN_REPORT_FRAGMENTS,
    WEBSITE_EXPORT_VERIFICATION_ID,
    WEBSITE_EXPORT_VERIFICATION_VERSION,
)


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    category: str = "structural"
    scenario: str = ""


@dataclass(frozen=True, slots=True)
class VerificationReport:
    schema_name: str = WEBSITE_EXPORT_VERIFICATION_ID
    schema_version: str = WEBSITE_EXPORT_VERIFICATION_VERSION
    verification_id: str = WEBSITE_EXPORT_VERIFICATION_ID
    ok: bool = False
    verdict: str = "fail"
    source_report_id: str = ""
    source_dataset_id: str = ""
    interpretation_policy_bundle_id: str = ""
    export_policy_token: str = ""
    website_export_schema_version: str = ""
    export_id: str = ""
    scope: str = ""
    repository_count: int = 0
    artifact_inventory: tuple[str, ...] = ()
    json_digest: str = ""
    html_digest: str = ""
    checks: tuple[CheckResult, ...] = ()
    scenario_summary: dict[str, int] = field(default_factory=dict)
    defects: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
            "ok": self.ok,
            "verdict": self.verdict,
            "source_report_id": self.source_report_id,
            "source_dataset_id": self.source_dataset_id,
            "interpretation_policy_bundle_id": self.interpretation_policy_bundle_id,
            "export_policy_token": self.export_policy_token,
            "website_export_schema_version": self.website_export_schema_version,
            "export_id": self.export_id,
            "scope": self.scope,
            "repository_count": self.repository_count,
            "artifact_inventory": list(self.artifact_inventory),
            "json_digest": self.json_digest,
            "html_digest": self.html_digest,
            "scenario_summary": self.scenario_summary,
            "checks": [asdict(item) for item in self.checks],
            "defects": list(self.defects),
            "warnings": list(self.warnings),
            "limitations": list(self.limitations),
            "elapsed_ms": self.elapsed_ms,
        }

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
        for frag in FORBIDDEN_REPORT_FRAGMENTS:
            if frag in text:
                raise RuntimeError("verification report would leak forbidden fragment")
        path.write_text(text, encoding="utf-8")
