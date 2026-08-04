"""Privacy-safe models for SV.9 verification reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from infrastructure.verification.contract import (
    FORBIDDEN_REPORT_FRAGMENTS,
    PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_ID,
    PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_VERSION,
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
    schema_name: str = PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_ID
    schema_version: str = PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_VERSION
    verification_id: str = PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_ID
    ok: bool = False
    verdict: str = "fail"
    infrastructure_module: str = ""
    environment_name: str = ""
    opentofu_required_version: str = ""
    aws_provider_version_constraint: str = ""
    packaging_strategy: str = ""
    api_gateway_type: str = ""
    lambda_count: int = 0
    lambda_architecture: str = ""
    deployment_mode: str = ""
    authentication_posture: str = ""
    rate_limit_posture: str = ""
    ingestion_posture: str = ""
    opentofu_validation_status: str = "not_executed"
    terraform_tool_status: str = "not_checked"
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
            "infrastructure_module": self.infrastructure_module,
            "environment_name": self.environment_name,
            "opentofu_required_version": self.opentofu_required_version,
            "aws_provider_version_constraint": self.aws_provider_version_constraint,
            "packaging_strategy": self.packaging_strategy,
            "api_gateway_type": self.api_gateway_type,
            "lambda_count": self.lambda_count,
            "lambda_architecture": self.lambda_architecture,
            "deployment_mode": self.deployment_mode,
            "authentication_posture": self.authentication_posture,
            "rate_limit_posture": self.rate_limit_posture,
            "ingestion_posture": self.ingestion_posture,
            "opentofu_validation_status": self.opentofu_validation_status,
            "terraform_tool_status": self.terraform_tool_status,
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
