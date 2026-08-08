"""Frontend API client checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, frontend_blob
from verification.community_insights_auth.inventory import read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_api_client(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    auth_client = read_text(monorepo, "insights/src/api/authClient.ts")
    blob = frontend_blob(monorepo)

    add_check(
        checks,
        defects,
        "frontend:credentials_include",
        auth_client.count('credentials: "include"') >= 3,
        "include",
        "frontend",
    )
    add_check(
        checks,
        defects,
        "frontend:no_local_storage_tokens",
        "localStorage" not in blob and "sessionStorage" not in blob,
        "absent",
        "frontend",
    )
    add_check(
        checks,
        defects,
        "frontend:no_secrets_manager",
        "SecretsManager" not in blob,
        "absent",
        "frontend",
    )
    add_check(
        checks,
        defects,
        "frontend:no_aws_sdk",
        "@aws-sdk" not in blob and "aws-sdk" not in blob,
        "absent",
        "frontend",
    )
    return checks, defects
