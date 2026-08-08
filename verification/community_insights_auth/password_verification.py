"""Runtime password verification checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth._common import add_check, ensure_platform_importable
from verification.community_insights_auth.models import CheckResult, Defect


def check_password_runtime(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ensure_platform_importable(monorepo)

    from codestrata_platform.community_cloud_api.insights_auth.password import (
        hash_password,
        verify_password,
    )
    from codestrata_platform.community_cloud_api.insights_auth.secrets import (
        TEST_PASSWORD_PLAINTEXT,
    )

    stored = hash_password(TEST_PASSWORD_PLAINTEXT)
    add_check(
        checks,
        defects,
        "runtime:scrypt_hash_verify",
        verify_password(submitted=TEST_PASSWORD_PLAINTEXT, stored_secret=stored),
        "ok",
        "runtime",
    )
    add_check(
        checks,
        defects,
        "runtime:scrypt_rejects_wrong",
        not verify_password(submitted="wrong-password", stored_secret=stored),
        "rejected",
        "runtime",
    )
    return checks, defects
