"""Auth must not weaken privacy."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_insights_validation._common import add_check, ensure_platform_importable
from verification.community_insights_validation.fixtures import build_fixtures
from verification.community_insights_validation.inventory import read_text
from verification.community_insights_validation.models import CheckResult, Defect


def check_auth_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    from verification.community_insights_validation.auth import _test_client

    client, _password, _secret = _test_client(monorepo)
    origin = "https://insights.codestrata.ai"
    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights_auth.secrets import (
        TEST_PASSWORD_PLAINTEXT,
    )

    client.post(
        "/api/v1/insights/auth/login",
        json={"password": TEST_PASSWORD_PLAINTEXT},
        headers={"Origin": origin},
    )
    overview = client.get("/api/v1/insights/api/overview")
    dumped = json.dumps(overview.json())
    fx = build_fixtures()
    for poison in fx.poison_strings:
        add_check(
            checks,
            defects,
            f"auth_privacy:no_{poison[:12]}",
            poison not in dumped,
            "absent",
            "privacy",
        )

    auth_service = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/insights_auth/service.py",
    )
    add_check(
        checks,
        defects,
        "auth_privacy:service_no_aggregation",
        "aggregate_metric" not in auth_service,
        "absent",
        "privacy",
    )
    return checks, defects
