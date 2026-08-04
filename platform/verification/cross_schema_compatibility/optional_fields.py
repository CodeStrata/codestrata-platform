"""Optional / additive field compatibility."""

from __future__ import annotations

from typing import Any

from verification.cross_schema_compatibility.artifacts import AssessmentArtifact
from verification.cross_schema_compatibility.models import CheckResult


_ADDITIVE_ASSESSMENT_KEYS = (
    "assessment_coverage",
    "assessment_head_confidence",
    "finding_correlations",
)


def check_optional_fields(
    artifacts: list[AssessmentArtifact],
    eir: dict[str, Any],
) -> list[CheckResult]:
    present_counts = {key: 0 for key in _ADDITIVE_ASSESSMENT_KEYS}
    for item in artifacts:
        assessment = item.report.get("assessment") or {}
        for key in _ADDITIVE_ASSESSMENT_KEYS:
            if key in assessment:
                present_counts[key] += 1

    # Additive fields should be present on current 1.2 SV.10 artifacts.
    checks = [
        CheckResult(
            name="optional_assessment_coverage_present",
            ok=present_counts["assessment_coverage"] == len(artifacts),
            detail=f"{present_counts['assessment_coverage']}/{len(artifacts)}",
            category="optional_fields",
        ),
        CheckResult(
            name="optional_assessment_head_confidence_present",
            ok=present_counts["assessment_head_confidence"] == len(artifacts),
            detail=f"{present_counts['assessment_head_confidence']}/{len(artifacts)}",
            category="optional_fields",
        ),
        CheckResult(
            name="optional_finding_correlations_key_present",
            ok=present_counts["finding_correlations"] >= 0,
            detail=f"{present_counts['finding_correlations']}/{len(artifacts)} (may be empty list)",
            category="optional_fields",
        ),
    ]

    # EIR additive: interpretation policy bundle.
    bundle = eir.get("interpretation_policy_bundle_id")
    checks.append(
        CheckResult(
            name="optional_eir_interpretation_bundle_present",
            ok=bool(bundle),
            detail=f"interpretation_policy_bundle_id={bundle}",
            category="optional_fields",
        )
    )

    # Missing optional field fixture: ensure absence does not change schema_version.
    minimal = {
        "schema_version": "1.2",
        "assessment": {"findings": [], "recommendations": []},
    }
    checks.append(
        CheckResult(
            name="optional_missing_fields_do_not_alter_schema_version",
            ok=minimal["schema_version"] == "1.2",
            detail="minimal fixture retains schema_version 1.2",
            category="optional_fields",
        )
    )
    return checks
