"""Privacy-safe models for SV.7 verification reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from verification.community_cloud_api.contract import (
    COMMUNITY_CLOUD_API_VERIFICATION_ID,
    COMMUNITY_CLOUD_API_VERIFICATION_VERSION,
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
    api_contract: str
    authentication: str
    credential_format: str
    rate_limit: str
    validation: str
    payload_limit: str
    logging: str
    event_identity: str
    telemetry_schema: str
    telemetry_policy: str
    assessment_metadata_schema: str
    assessment_metadata_policy: str
    cli_event_schema: str
    cli_event_policy: str
    extension_event_schema: str
    extension_event_policy: str
    ai_usage_schema: str
    ai_usage_policy: str


@dataclass(frozen=True, slots=True)
class VerificationReport:
    schema_name: str = COMMUNITY_CLOUD_API_VERIFICATION_ID
    schema_version: str = COMMUNITY_CLOUD_API_VERIFICATION_VERSION
    verification_id: str = COMMUNITY_CLOUD_API_VERIFICATION_ID
    ok: bool = False
    verdict: str = "fail"
    policy_versions: PolicyVersions | None = None
    route_inventory: tuple[str, ...] = ()
    checks: tuple[CheckResult, ...] = ()
    scenario_summary: dict[str, int] = field(default_factory=dict)
    defects: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
            "ok": self.ok,
            "verdict": self.verdict,
            "route_inventory": list(self.route_inventory),
            "scenario_summary": self.scenario_summary,
            "checks": [asdict(item) for item in self.checks],
            "defects": list(self.defects),
            "warnings": list(self.warnings),
            "limitations": list(self.limitations),
            "elapsed_ms": self.elapsed_ms,
        }
        if self.policy_versions is not None:
            payload["policy_versions"] = asdict(self.policy_versions)
        return payload

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"
        # Hard safety: never write fake credentials into the report file.
        from verification.community_cloud_api.contract import FORBIDDEN_REPORT_FRAGMENTS

        for frag in FORBIDDEN_REPORT_FRAGMENTS:
            if frag in text:
                raise RuntimeError("verification report would leak forbidden fragment")
        path.write_text(text, encoding="utf-8")
