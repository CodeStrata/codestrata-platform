"""SV.8 contract constants."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.website_export import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)
from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION

from verification.engineering_intelligence.contract import PREFERRED_FIVE_LANGUAGE_SUBSET
from verification.website_export.contract import (
    EXPECTED_SV6_REPORT_ID,
    WEBSITE_EXPORT_VERIFICATION_ID,
    WEBSITE_EXPORT_VERIFICATION_VERSION,
)


def test_contract_constants() -> None:
    assert WEBSITE_EXPORT_VERIFICATION_ID == "website-export-verification"
    assert WEBSITE_EXPORT_VERIFICATION_VERSION == "1.0.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert len(PREFERRED_FIVE_LANGUAGE_SUBSET) == 5
    assert EXPECTED_SV6_REPORT_ID.startswith("eir:")
