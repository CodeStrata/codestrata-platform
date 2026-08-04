"""SV.6 contract tests."""

from __future__ import annotations

from verification.engineering_intelligence.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    EIR_SCHEMA_VERSION,
    ENGINEERING_INTELLIGENCE_VERIFICATION_ID,
    ENGINEERING_INTELLIGENCE_VERIFICATION_VERSION,
    PREFERRED_FIVE_LANGUAGE_SUBSET,
)


def test_contract_constants() -> None:
    assert ENGINEERING_INTELLIGENCE_VERIFICATION_ID == "engineering-intelligence-verification"
    assert ENGINEERING_INTELLIGENCE_VERIFICATION_VERSION == "1.0.0"
    assert EIR_SCHEMA_VERSION == "1.0"
    assert ASSESSMENT_SCHEMA_VERSION == "1.2"
    assert len(PREFERRED_FIVE_LANGUAGE_SUBSET) == 5
    assert "cleanarchitecture" in PREFERRED_FIVE_LANGUAGE_SUBSET
