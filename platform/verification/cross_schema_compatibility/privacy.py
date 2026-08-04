"""Privacy-contract chain alignment (SV.13 cases)."""

from __future__ import annotations

from codestrata.security.customer_safe_text import (
    PRIVATE_KEY_FINDING_EVIDENCE,
    ensure_customer_safe_report_document,
    sanitize_customer_text,
)
from codestrata.security.redaction import REDACTED, redact_secrets
from codestrata_platform.intelligence_reporting.application.errors import (
    UnsafeAssessmentMetadataError,
)
from codestrata_platform.intelligence_reporting.application.validation import (
    validate_report_document,
)

from verification.cross_schema_compatibility.models import (
    CheckResult,
    CompatibilityFailure,
)
from verification.system_defect_fixes.unsafe_metadata import (
    SAFE_DESCRIPTIVE_PHRASES,
    UNSAFE_FIXTURE_DESCRIPTIONS,
)


def _minimal(description: str) -> dict:
    return {
        "schema_version": "1.2",
        "assessment": {
            "findings": [
                {
                    "id": "00000000-0000-4000-8000-000000000001",
                    "rule_id": "SEC002",
                    "title": "Private key material detected",
                    "description": description,
                }
            ]
        },
    }


def check_privacy_chain() -> tuple[list[CheckResult], list[CompatibilityFailure]]:
    checks: list[CheckResult] = []
    failures: list[CompatibilityFailure] = []

    # PEM header sanitized by Engine.
    header = "-----BEGIN RSA PRIVATE KEY-----"
    sanitized = redact_secrets(f"detected: {header}")
    pem_ok = "-----BEGIN" not in sanitized and REDACTED in sanitized
    checks.append(
        CheckResult(
            name="privacy_engine_redacts_pem_header",
            ok=pem_ok,
            detail="header_only → [REDACTED]",
            category="privacy",
        )
    )
    if not pem_ok:
        failures.append(
            CompatibilityFailure(
                classification="privacy",
                producer="Engine redaction",
                consumer="customer-safe serialization",
                schema="assessment_report",
                field="description",
                expected="PEM header redacted",
                actual="marker survived",
            )
        )

    # Legacy document with header becomes Platform-safe after projection.
    legacy = _minimal(f"Private key material detected in keys/x.pem: {header}")
    unsafe_before = False
    try:
        validate_report_document(legacy)
    except UnsafeAssessmentMetadataError:
        unsafe_before = True
    safe = ensure_customer_safe_report_document(legacy)
    safe_after = True
    try:
        validate_report_document(safe)
    except UnsafeAssessmentMetadataError:
        safe_after = False
    checks.append(
        CheckResult(
            name="privacy_customer_safe_then_platform_accepts",
            ok=unsafe_before and safe_after,
            detail=f"unsafe_before={unsafe_before} safe_after={safe_after}",
            category="privacy",
        )
    )

    # Safe descriptive phrases accepted.
    safe_phrase_fail = False
    for phrase in SAFE_DESCRIPTIVE_PHRASES:
        try:
            validate_report_document(_minimal(phrase))
        except UnsafeAssessmentMetadataError:
            safe_phrase_fail = True
            failures.append(
                CompatibilityFailure(
                    classification="privacy",
                    producer="safe descriptive fixture",
                    consumer="Platform validate_report_document",
                    schema="assessment_report",
                    field="description",
                    expected="accepted",
                    actual="rejected",
                )
            )
            break
    checks.append(
        CheckResult(
            name="privacy_safe_descriptive_phrases_accepted",
            ok=not safe_phrase_fail,
            detail=f"phrases={len(SAFE_DESCRIPTIVE_PHRASES)}",
            category="privacy",
        )
    )

    # Unsafe fixtures rejected without echoing values.
    unsafe_fail = False
    for fixture in UNSAFE_FIXTURE_DESCRIPTIONS:
        try:
            validate_report_document(_minimal(fixture))
            unsafe_fail = True
            failures.append(
                CompatibilityFailure(
                    classification="privacy",
                    producer="unsafe fixture",
                    consumer="Platform validate_report_document",
                    schema="assessment_report",
                    field="description",
                    expected="rejected",
                    actual="accepted",
                )
            )
            break
        except UnsafeAssessmentMetadataError as exc:
            if fixture in str(exc):
                unsafe_fail = True
                failures.append(
                    CompatibilityFailure(
                        classification="privacy",
                        producer="Platform validation",
                        consumer="diagnostics",
                        schema="assessment_report",
                        field="error_message",
                        expected="no value echo",
                        actual="fixture echoed",
                    )
                )
                break
    checks.append(
        CheckResult(
            name="privacy_unsafe_fixtures_rejected",
            ok=not unsafe_fail,
            detail=f"fixtures={len(UNSAFE_FIXTURE_DESCRIPTIONS)}",
            category="privacy",
        )
    )

    checks.append(
        CheckResult(
            name="privacy_sec002_categorical_evidence",
            ok="BEGIN" not in PRIVATE_KEY_FINDING_EVIDENCE
            and "redacted" in PRIVATE_KEY_FINDING_EVIDENCE.lower(),
            detail="PRIVATE_KEY_FINDING_EVIDENCE categorical",
            category="privacy",
        )
    )
    checks.append(
        CheckResult(
            name="privacy_sanitize_customer_text_stable",
            ok=sanitize_customer_text(f"x={REDACTED}") == f"x={REDACTED}",
            detail="redacted marker stable",
            category="privacy",
        )
    )
    return checks, failures
