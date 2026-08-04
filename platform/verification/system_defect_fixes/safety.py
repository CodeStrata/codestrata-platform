"""Privacy acceptance / rejection fixtures for SV.13."""

from __future__ import annotations

import copy
from typing import Any

from codestrata.security.customer_safe_text import ensure_customer_safe_report_document
from codestrata_platform.intelligence_reporting.application.errors import (
    UnsafeAssessmentMetadataError,
)
from codestrata_platform.intelligence_reporting.application.validation import (
    validate_report_document,
)

from verification.system_defect_fixes.models import CheckResult
from verification.system_defect_fixes.unsafe_metadata import (
    SAFE_DESCRIPTIVE_PHRASES,
    UNSAFE_FIXTURE_DESCRIPTIONS,
)


def _minimal_report(description: str) -> dict[str, Any]:
    return {
        "schema_version": "1.2",
        "assessment": {
            "findings": [
                {
                    "id": "00000000-0000-4000-8000-000000000001",
                    "rule_id": "SEC002",
                    "title": "Private key material detected",
                    "description": description,
                    "severity": "critical",
                }
            ]
        },
    }


def check_safe_phrases_accepted() -> CheckResult:
    failures: list[str] = []
    for phrase in SAFE_DESCRIPTIVE_PHRASES:
        try:
            validate_report_document(_minimal_report(phrase))
        except UnsafeAssessmentMetadataError:
            failures.append("safe_phrase_rejected")
            break
        except Exception:  # noqa: BLE001
            failures.append("unexpected_error")
            break
    return CheckResult(
        name="safe_descriptive_phrases_accepted",
        ok=not failures,
        detail=f"phrases={len(SAFE_DESCRIPTIVE_PHRASES)} failures={failures}",
    )


def check_unsafe_fixtures_rejected() -> CheckResult:
    accepted: list[str] = []
    for fixture in UNSAFE_FIXTURE_DESCRIPTIONS:
        try:
            validate_report_document(_minimal_report(fixture))
            accepted.append("accepted")
            break
        except UnsafeAssessmentMetadataError as exc:
            # Diagnostics must not echo the fixture value.
            if fixture in str(exc):
                accepted.append("leaked_in_diagnostic")
                break
        except Exception:  # noqa: BLE001
            accepted.append("unexpected_error")
            break
    return CheckResult(
        name="unsafe_fixtures_rejected",
        ok=not accepted,
        detail=f"fixtures={len(UNSAFE_FIXTURE_DESCRIPTIONS)} issues={accepted}",
    )


def check_engine_redaction_makes_legacy_safe(raw: dict[str, Any]) -> CheckResult:
    """Legacy PEM-header descriptions become Platform-safe after Engine projection."""

    unsafe_before = False
    try:
        validate_report_document(raw)
    except UnsafeAssessmentMetadataError:
        unsafe_before = True
    safe = ensure_customer_safe_report_document(copy.deepcopy(raw))
    try:
        validate_report_document(safe)
        ok_after = True
    except UnsafeAssessmentMetadataError:
        ok_after = False
    return CheckResult(
        name="engine_redaction_customer_safe",
        ok=unsafe_before and ok_after,
        detail=f"unsafe_before={unsafe_before} safe_after={ok_after}",
    )
