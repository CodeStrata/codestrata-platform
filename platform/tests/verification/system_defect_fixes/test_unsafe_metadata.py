"""Unsafe-metadata classification and fixtures."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.errors import (
    UnsafeAssessmentMetadataError,
)
from codestrata_platform.intelligence_reporting.application.validation import (
    validate_report_document,
)

from verification.system_defect_fixes.safety import (
    check_safe_phrases_accepted,
    check_unsafe_fixtures_rejected,
)
from verification.system_defect_fixes.unsafe_metadata import (
    SAFE_DESCRIPTIVE_PHRASES,
    UNSAFE_FIXTURE_DESCRIPTIONS,
    classify_description_shape,
)


def test_classify_header_shape() -> None:
    assert (
        classify_description_shape("x -----BEGIN RSA PRIVATE KEY----- y")
        == "pem_header_marker_in_description"
    )


def test_safe_phrases_accepted() -> None:
    assert check_safe_phrases_accepted().ok
    for phrase in SAFE_DESCRIPTIVE_PHRASES:
        validate_report_document(
            {
                "schema_version": "1.2",
                "assessment": {
                    "findings": [{"description": phrase, "title": "t", "id": "1"}]
                },
            }
        )


def test_unsafe_fixtures_rejected_without_echo() -> None:
    assert check_unsafe_fixtures_rejected().ok
    for fixture in UNSAFE_FIXTURE_DESCRIPTIONS:
        try:
            validate_report_document(
                {
                    "schema_version": "1.2",
                    "assessment": {
                        "findings": [
                            {"description": fixture, "title": "t", "id": "1"}
                        ]
                    },
                }
            )
            raise AssertionError("expected rejection")
        except UnsafeAssessmentMetadataError as exc:
            assert fixture not in str(exc)
