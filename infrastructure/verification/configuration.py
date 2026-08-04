"""Deployment configuration posture verification."""

from __future__ import annotations

from infrastructure.verification.contract import (
    AUTHENTICATION_MODE,
    DEPLOYMENT_MODE,
    RATE_LIMIT_MODE,
    infra_root,
)
from infrastructure.verification.models import CheckResult


def check_configuration() -> list[CheckResult]:
    config = (
        infra_root() / "modules" / "community-cloud-api" / "configuration.tf"
    ).read_text(encoding="utf-8")
    variables = (
        infra_root() / "modules" / "community-cloud-api" / "variables.tf"
    ).read_text(encoding="utf-8")
    validation = (
        infra_root() / "modules" / "community-cloud-api" / "validation.tf"
    ).read_text(encoding="utf-8")
    production = (infra_root() / "production" / "main.tf").read_text(encoding="utf-8")
    return [
        CheckResult(
            name="config:deployment_mode",
            ok=DEPLOYMENT_MODE in variables and DEPLOYMENT_MODE in production,
            detail=DEPLOYMENT_MODE,
            category="configuration",
        ),
        CheckResult(
            name="config:api_version_1_0",
            ok="CODESTRATA_COMMUNITY_API_VERSION" in config and "1.0" in config,
            detail="1.0",
            category="configuration",
        ),
        CheckResult(
            name="config:auth_enabled",
            ok="CODESTRATA_AUTHENTICATION_ENABLED" in config
            and AUTHENTICATION_MODE in variables
            and AUTHENTICATION_MODE in production,
            detail=AUTHENTICATION_MODE,
            category="configuration",
            scenario="V",
        ),
        CheckResult(
            name="config:rate_limit_enabled",
            ok="CODESTRATA_RATE_LIMIT_ENABLED" in config
            and RATE_LIMIT_MODE in variables
            and RATE_LIMIT_MODE in production,
            detail=RATE_LIMIT_MODE,
            category="configuration",
        ),
        CheckResult(
            name="config:ingestion_disabled",
            ok="CODESTRATA_INGESTION_ENABLED" in config,
            detail="wired to enable_ingestion",
            category="configuration",
        ),
        CheckResult(
            name="config:fail_closed_checks",
            ok="foundation_fail_closed" in validation or "enable_ingestion" in validation,
            detail="validation.tf checks",
            category="configuration",
        ),
        CheckResult(
            name="config:no_test_adapters_in_hcl",
            ok=all(
                token not in config.lower()
                for token in ("inmemory", "test_only", "cscc_v1_", "fake")
            ),
            detail="no test adapters",
            category="configuration",
            scenario="W",
        ),
    ]
