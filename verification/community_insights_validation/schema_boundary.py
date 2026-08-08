"""Schema boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.contract import (
    POLICY_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
)
from verification.community_insights_validation.inventory import load_json
from verification.community_insights_validation.models import CheckResult, Defect


def check_schema_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    verification = policy.get("verification") or {}

    add_check(
        checks,
        defects,
        "schema:name",
        verification.get("schema") == f"{SCHEMA_NAME}:{SCHEMA_VERSION}",
        str(verification.get("schema")),
        "contract",
    )
    add_check(
        checks,
        defects,
        "schema:package",
        verification.get("package") == "verification/community_insights_validation",
        str(verification.get("package")),
        "contract",
    )
    add_check(
        checks,
        defects,
        "schema:report_path",
        verification.get("report")
        == "reports/verification/sv15-11/community-insights-validation-verification.json",
        str(verification.get("report")),
        "contract",
    )
    return checks, defects
