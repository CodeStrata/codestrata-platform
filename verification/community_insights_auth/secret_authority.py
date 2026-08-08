"""Secrets Manager authority boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, frontend_blob
from verification.community_insights_auth.contract import AUTH_PACKAGE
from verification.community_insights_auth.inventory import read_text
from verification.community_insights_auth.models import CheckResult, Defect


def check_secret_authority(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    secrets_py = read_text(monorepo, f"{AUTH_PACKAGE}/secrets.py")
    service_py = read_text(monorepo, f"{AUTH_PACKAGE}/service.py")
    frontend = frontend_blob(monorepo)

    add_check(
        checks,
        defects,
        "secrets:port_abstraction",
        "SecretsPort" in secrets_py and "FakeSecretsPort" in secrets_py,
        "present",
        "privacy",
    )
    add_check(
        checks,
        defects,
        "secrets:service_uses_port",
        "get_secret_value" in service_py,
        "port",
        "privacy",
    )
    add_check(
        checks,
        defects,
        "secrets:no_boto_in_platform_auth",
        "boto3" not in secrets_py and "boto3" not in service_py,
        "absent",
        "privacy",
    )
    add_check(
        checks,
        defects,
        "secrets:no_frontend_access",
        "SecretsManager" not in frontend,
        "absent",
        "privacy",
    )
    return checks, defects
