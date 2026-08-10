"""Presence-only credential checks (never log values)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from verification.community_ai_providers.helpers import check, env_present
from verification.community_ai_providers.models import CheckResult, Defect


def check_credentials(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    _ = monorepo
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    openai_present = env_present("OPENAI_API_KEY")
    openrouter_present = env_present("OPENROUTER_API_KEY")
    aws_profile = bool(os.environ.get("AWS_PROFILE", "").strip())
    aws_region = bool(
        os.environ.get("AWS_REGION", "").strip()
        or os.environ.get("AWS_DEFAULT_REGION", "").strip()
    )
    # Presence-only: do not read or echo values.
    bedrock_chain_hint = aws_profile or aws_region or env_present("AWS_ACCESS_KEY_ID")

    checks.append(
        check(
            "credentials:openai_presence_only",
            True,
            "openai_env " + ("present" if openai_present else "absent"),
            "credentials",
        )
    )
    checks.append(
        check(
            "credentials:openrouter_presence_only",
            True,
            "openrouter_env " + ("present" if openrouter_present else "absent"),
            "credentials",
        )
    )
    checks.append(
        check(
            "credentials:bedrock_chain_hint",
            True,
            "aws_chain_hint " + ("present" if bedrock_chain_hint else "absent"),
            "credentials",
        )
    )

    openai_class = "configured" if openai_present else "OWNER_CREDENTIAL_REQUIRED"
    openrouter_class = (
        "configured" if openrouter_present else "OWNER_CREDENTIAL_REQUIRED"
    )
    bedrock_class = "configured" if bedrock_chain_hint else "OWNER_CREDENTIAL_REQUIRED"

    if not openai_present:
        limitations.append("owner_credential_required_openai")
    if not openrouter_present:
        limitations.append("owner_credential_required_openrouter")

    summary = {
        "openai": {
            "env_name": "OPENAI_API_KEY",
            "present": openai_present,
            "classification": openai_class,
        },
        "openrouter": {
            "env_name": "OPENROUTER_API_KEY",
            "present": openrouter_present,
            "classification": openrouter_class,
        },
        "bedrock": {
            "credential_source_class": "aws_sdk_default_chain",
            "aws_profile_set": aws_profile,
            "aws_region_set": aws_region,
            "classification": bedrock_class,
        },
        "values_logged": False,
    }
    return checks, defects, summary, limitations
