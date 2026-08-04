"""CloudWatch logging verification."""

from __future__ import annotations

from infrastructure.verification.contract import infra_root
from infrastructure.verification.models import CheckResult


def check_logging() -> list[CheckResult]:
    text = (infra_root() / "modules" / "community-cloud-api" / "logging.tf").read_text(
        encoding="utf-8"
    )
    main = (infra_root() / "modules" / "community-cloud-api" / "main.tf").read_text(
        encoding="utf-8"
    )
    return [
        CheckResult(
            name="logging:explicit_log_group",
            ok='resource "aws_cloudwatch_log_group"' in text,
            detail="log group",
            category="logging",
        ),
        CheckResult(
            name="logging:retention_explicit",
            ok="retention_in_days" in text,
            detail="retention_in_days",
            category="logging",
            scenario="L",
        ),
        CheckResult(
            name="logging:no_indefinite_default",
            ok="retention_in_days = var.log_retention_days" in text
            or "retention_in_days=var.log_retention_days" in text,
            detail="uses log_retention_days",
            category="logging",
            scenario="L",
        ),
        CheckResult(
            name="logging:deterministic_name",
            ok="/aws/lambda/" in main or "log_group_name" in main,
            detail="deterministic local name",
            category="logging",
        ),
        CheckResult(
            name="logging:no_access_log_settings",
            ok="access_log_settings" not in text and "request_body" not in text,
            detail="no access_log_settings",
            category="logging",
        ),
        CheckResult(
            name="logging:privacy_documented",
            ok="authorization" in text.lower() and "privacy" in text.lower(),
            detail="privacy comments present",
            category="logging",
        ),
    ]
