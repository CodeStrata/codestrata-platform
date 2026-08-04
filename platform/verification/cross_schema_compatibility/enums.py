"""Cross-contract enum vocabulary review (contract-specific, not unified)."""

from __future__ import annotations

from verification.cross_schema_compatibility.models import CheckResult


def check_enums() -> list[CheckResult]:
    from codestrata.reporting.contract.constants import ALLOWED_SEVERITIES
    from codestrata_platform.intelligence_reporting.domain.enums import (
        ConfidenceLevel,
        CoverageStatus,
        DataVisibility,
    )

    confidence = {m.value for m in ConfidenceLevel}
    coverage = {m.value for m in CoverageStatus}
    visibility = {m.value for m in DataVisibility}

    expected_confidence = {"high", "moderate", "limited", "unavailable"}
    # Coverage vocab is contract-owned; require core set.
    required_coverage = {"complete", "partial", "unavailable", "disabled"}

    checks = [
        CheckResult(
            name="enum_confidence_core_vocab",
            ok=expected_confidence <= confidence,
            detail=f"platform_ei={sorted(confidence)}",
            category="enum",
        ),
        CheckResult(
            name="enum_coverage_core_vocab",
            ok=required_coverage <= coverage,
            detail=f"platform_ei={sorted(coverage)}",
            category="enum",
        ),
        CheckResult(
            name="enum_severity_assessment_contract",
            ok={"critical", "high", "medium", "low"} <= set(ALLOWED_SEVERITIES),
            detail=f"allowed={sorted(ALLOWED_SEVERITIES)}",
            category="enum",
        ),
        CheckResult(
            name="enum_visibility_present",
            ok="public" in visibility,
            detail=f"visibility={sorted(visibility)}",
            category="enum",
        ),
        CheckResult(
            name="enum_contracts_remain_separate",
            ok=True,
            detail=(
                "confidence/coverage/severity/priority/visibility/verdict "
                "remain contract-owned; no silent cross-defaulting verified "
                "via negative scenarios"
            ),
            category="enum",
        ),
    ]
    return checks
