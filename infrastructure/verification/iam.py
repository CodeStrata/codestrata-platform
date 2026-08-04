"""IAM least-privilege verification."""

from __future__ import annotations

from infrastructure.verification.contract import FORBIDDEN_IAM_ACTIONS, infra_root
from infrastructure.verification.models import CheckResult


def check_iam() -> list[CheckResult]:
    text = (infra_root() / "modules" / "community-cloud-api" / "iam.tf").read_text(
        encoding="utf-8"
    )
    forbidden_hits = [
        action for action in FORBIDDEN_IAM_ACTIONS if action.lower() in text.lower()
    ]
    # Documented exception: ecr:GetAuthorizationToken with Resource="*"
    star_resources = text.count('resources = ["*"]')
    return [
        CheckResult(
            name="iam:lambda_trust",
            ok='identifiers = ["lambda.amazonaws.com"]' in text
            and "sts:AssumeRole" in text,
            detail="lambda service trust",
            category="iam",
        ),
        CheckResult(
            name="iam:logging_actions_bounded",
            ok="logs:CreateLogStream" in text and "logs:PutLogEvents" in text,
            detail="log stream/events",
            category="iam",
        ),
        CheckResult(
            name="iam:ecr_pull_bounded",
            ok="ecr:BatchGetImage" in text and "ecr:GetDownloadUrlForLayer" in text,
            detail="ecr pull",
            category="iam",
        ),
        CheckResult(
            name="iam:auth_token_exception_documented",
            ok="ecr:GetAuthorizationToken" in text
            and "documented exception" in text.lower()
            and star_resources == 1,
            detail="single Resource=* exception",
            category="iam",
        ),
        CheckResult(
            name="iam:no_data_plane_services",
            ok=not forbidden_hits,
            detail="ok" if not forbidden_hits else ",".join(forbidden_hits[:6]),
            category="iam",
            scenario="N",
        ),
        CheckResult(
            name="iam:no_admin_star_actions",
            ok='actions = ["*"]' not in text and "Action = \"*\"" not in text,
            detail="no Action=*",
            category="iam",
            scenario="M",
        ),
    ]
