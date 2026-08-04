"""Full SV.9 integration runner."""

from __future__ import annotations

from pathlib import Path

from infrastructure.verification.contract import (
    FORBIDDEN_REPORT_FRAGMENTS,
    PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_ID,
)
from infrastructure.verification.runner import (
    run_platform_deployment_foundation_verification,
)
from infrastructure.verification.scenarios import check_scenarios


def test_scenarios() -> None:
    results = check_scenarios()
    assert results and all(item.ok for item in results)


def test_full_runner(tmp_path: Path) -> None:
    # Hermetic structural/runtime verification. OpenTofu CLI fmt/init/validate is
    # exercised by the full SV.9 / SV.16 runners (needs provider download + writable
    # .terraform); keep this unit path offline-safe.
    report = run_platform_deployment_foundation_verification(
        output_dir=tmp_path,
        run_opentofu_cli=False,
    )
    assert report.ok
    assert report.verdict == "pass"
    assert report.schema_name == PLATFORM_DEPLOYMENT_FOUNDATION_VERIFICATION_ID
    assert report.environment_name == "production"
    assert report.lambda_count == 1
    assert report.opentofu_validation_status in {
        "pass",
        "fail",
        "not_executed_tool_unavailable",
        "pending",
    }
    path = tmp_path / "platform-deployment-foundation-verification.json"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for frag in FORBIDDEN_REPORT_FRAGMENTS:
        assert frag not in text
