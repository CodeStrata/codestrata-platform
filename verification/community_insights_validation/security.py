"""Security header and CSP checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check, frontend_source_blob
from verification.community_insights_validation.inventory import read_text
from verification.community_insights_validation.models import CheckResult, Defect


def check_security(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    html = read_text(monorepo, "insights/index.html")
    source = frontend_source_blob(monorepo)

    add_check(
        checks,
        defects,
        "security:csp_present",
        "Content-Security-Policy" in html,
        "present",
        "security",
    )
    add_check(
        checks,
        defects,
        "security:robots_noindex",
        'name="robots" content="noindex,nofollow"' in html,
        "present",
        "security",
    )
    add_check(
        checks,
        defects,
        "security:no_aws_sdk_frontend",
        "@aws-sdk" not in source and "boto3" not in source,
        "absent",
        "security",
    )
    add_check(
        checks,
        defects,
        "security:no_secrets_manager_frontend",
        "SecretsManager" not in source,
        "absent",
        "security",
    )
    add_check(
        checks,
        defects,
        "security:no_local_storage_session",
        "localStorage" not in read_text(monorepo, "insights/src/auth/AuthContext.tsx")
        and "sessionStorage" not in read_text(monorepo, "insights/src/auth/AuthContext.tsx"),
        "absent",
        "security",
    )
    return checks, defects
