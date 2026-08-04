"""Validation summary schema 1.0 compatibility."""

from __future__ import annotations

from typing import Any

from verification.cross_schema_compatibility.models import (
    CheckResult,
    CompatibilityFailure,
    CompatibilityWarning,
)


def check_validation_summary(
    summary: dict[str, Any] | None,
) -> tuple[list[CheckResult], list[CompatibilityFailure], list[CompatibilityWarning]]:
    from validation.summary_artifact import SUMMARY_SCHEMA_VERSION

    checks: list[CheckResult] = []
    failures: list[CompatibilityFailure] = []
    warnings: list[CompatibilityWarning] = []

    checks.append(
        CheckResult(
            name="validation_summary_product_constant_1_0",
            ok=SUMMARY_SCHEMA_VERSION == "1.0",
            detail=f"SUMMARY_SCHEMA_VERSION={SUMMARY_SCHEMA_VERSION}",
            category="validation_summary",
        )
    )
    if summary is None:
        warnings.append(
            CompatibilityWarning(
                code="validation_summary_missing",
                detail="latest validation-summary.json not present; constant check only",
            )
        )
        checks.append(
            CheckResult(
                name="validation_summary_artifact_present",
                ok=True,
                detail="absent — warned; not blocking when constant is 1.0",
                category="validation_summary",
            )
        )
        return checks, failures, warnings

    version = str(
        summary.get("summary_schema_version") or summary.get("schema_version") or ""
    )
    ok = version == "1.0"
    if not ok:
        failures.append(
            CompatibilityFailure(
                classification="version_contract",
                producer="Epic 4 summary",
                consumer="release verification",
                schema="validation_summary",
                field="summary_schema_version",
                expected="1.0",
                actual=version or "<missing>",
            )
        )
    checks.append(
        CheckResult(
            name="validation_summary_schema_1_0",
            ok=ok,
            detail=f"summary_schema_version={version}",
            category="validation_summary",
        )
    )

    # Customer reports must not consume validation summary as accuracy claim.
    blob = str(summary.get("disclaimer") or "")
    checks.append(
        CheckResult(
            name="validation_summary_has_disclaimer",
            ok=bool(blob),
            detail="disclaimer present" if blob else "missing disclaimer",
            category="validation_summary",
        )
    )
    # Absolute path scan (bounded).
    text = str(summary)[:200_000]
    has_abs = "/Users/" in text or "/home/" in text
    checks.append(
        CheckResult(
            name="validation_summary_no_absolute_paths",
            ok=not has_abs,
            detail="absolute_path_scan",
            category="privacy",
        )
    )
    if has_abs:
        failures.append(
            CompatibilityFailure(
                classification="privacy",
                producer="validation summary",
                consumer="release verification",
                schema="validation_summary",
                field="source_refs",
                expected="no absolute paths",
                actual="absolute_path_detected",
            )
        )
    return checks, failures, warnings
