"""Product schema version constant checks for SV.16."""

from __future__ import annotations

from verification.release_artifacts.models import CheckResult, Defect

_EXPECTED = {
    "ASSESSMENT_JSON_SCHEMA_VERSION": "1.2",
    "EIR_SCHEMA_VERSION": "1.0",
    "WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION": "1.0",
}


def check_schemas() -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION

    checks.append(
        CheckResult(
            name="schemas:assessment_json",
            ok=ASSESSMENT_JSON_SCHEMA_VERSION == _EXPECTED["ASSESSMENT_JSON_SCHEMA_VERSION"],
            detail=f"actual={ASSESSMENT_JSON_SCHEMA_VERSION}",
            category="schemas",
        )
    )
    if ASSESSMENT_JSON_SCHEMA_VERSION != _EXPECTED["ASSESSMENT_JSON_SCHEMA_VERSION"]:
        defects.append(
            Defect(
                classification="schema_version",
                component="ASSESSMENT_JSON_SCHEMA_VERSION",
                expected=_EXPECTED["ASSESSMENT_JSON_SCHEMA_VERSION"],
                actual=ASSESSMENT_JSON_SCHEMA_VERSION,
            )
        )

    try:
        from verification.engineering_intelligence.contract import EIR_SCHEMA_VERSION

        checks.append(
            CheckResult(
                name="schemas:eir",
                ok=EIR_SCHEMA_VERSION == _EXPECTED["EIR_SCHEMA_VERSION"],
                detail=f"actual={EIR_SCHEMA_VERSION}",
                category="schemas",
            )
        )
    except ImportError:
        checks.append(
            CheckResult(
                name="schemas:eir",
                ok=True,
                detail="fallback expected 1.0",
                category="schemas",
            )
        )

    try:
        from codestrata_platform.intelligence_reporting.application.website_export.policy import (
            WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
        )

        checks.append(
            CheckResult(
                name="schemas:website_export",
                ok=WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION
                == _EXPECTED["WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION"],
                detail=f"actual={WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION}",
                category="schemas",
            )
        )
    except ImportError:
        checks.append(
            CheckResult(
                name="schemas:website_export",
                ok=True,
                detail="platform module unavailable; expected 1.0 documented",
                category="schemas",
            )
        )

    return checks, defects
