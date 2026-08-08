"""Schema / assessment-truth boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.assessment_report_redesign.contract import (
    ASSESSMENT_SCHEMA_CONSTANTS,
    ASSESSMENT_SCHEMA_JSON,
)
from verification.assessment_report_redesign.models import CheckResult, Defect


def check_schema_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    constants = (monorepo / ASSESSMENT_SCHEMA_CONSTANTS).read_text(encoding="utf-8")
    schema = (monorepo / ASSESSMENT_SCHEMA_JSON).read_text(encoding="utf-8")
    ok_const = (
        'ASSESSMENT_JSON_SCHEMA_VERSION = "1.2"' in constants
        and 'ASSESSMENT_JSON_REPORT_VERSION = "1.2"' in constants
    )
    checks.append(
        CheckResult("schema:constants_1_2", ok_const, "1.2", "schema_boundary")
    )
    checks.append(
        CheckResult(
            "schema:json_const_1_2",
            '"const": "1.2"' in schema or '"const":"1.2"' in schema,
            "1.2",
            "schema_boundary",
        )
    )
    # Presentation HTML version may move independently.
    checks.append(
        CheckResult(
            "schema:html_version_independent",
            "REPORT_HTML_VERSION" in constants,
            "present",
            "schema_boundary",
        )
    )
    if not ok_const:
        defects.append(
            Defect(
                "schema/assessment regression",
                "assessment_schema",
                "1.2",
                "changed",
            )
        )
    return checks, defects
