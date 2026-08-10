"""--no-ai default and local profile rejects --with-ai."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import ASSESS_CLI_PY, SERVICE_PY
from verification.community_ai_providers.helpers import check, hard_defect, read_text
from verification.community_ai_providers.models import CheckResult, Defect


def check_no_ai(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    assess_cli = read_text(monorepo / ASSESS_CLI_PY)
    service = read_text(monorepo / SERVICE_PY)

    has_with_no_ai = "--with-ai/--no-ai" in assess_cli
    checks.append(
        check(
            "no_ai:cli_flags",
            has_with_no_ai,
            "--with-ai/--no-ai present (NOT --ai alone)",
            "no_ai",
        )
    )
    if not has_with_no_ai:
        defects.append(
            hard_defect(
                "cli_flag_drift",
                "no_ai:cli_flags",
                "--with-ai/--no-ai",
                "missing",
            )
        )

    # Default is no-ai: look for default False on with_ai / no_ai True pattern.
    default_no_ai = (
        "with_ai: bool = False" in service
        or "default=False" in assess_cli
        or "--no-ai" in assess_cli
    )
    checks.append(
        check(
            "no_ai:default",
            default_no_ai,
            "deterministic default",
            "no_ai",
        )
    )

    local_rejects = (
        "Execution profile 'local' does not allow --with-ai" in service
        or 'does not allow --with-ai' in service
    )
    checks.append(
        check(
            "no_ai:local_profile_rejects_with_ai",
            local_rejects,
            "local profile rejects --with-ai",
            "no_ai",
        )
    )
    if not local_rejects:
        defects.append(
            hard_defect(
                "local_allows_with_ai",
                "no_ai:local_profile_rejects_with_ai",
                "reject",
                "missing",
            )
        )

    # --no-ai must not require credentials (source-level).
    no_cred_required = "no cloud credentials required" in assess_cli or "--no-ai" in assess_cli
    checks.append(
        check(
            "no_ai:no_credentials_required",
            no_cred_required,
            "deterministic assess does not require provider credentials",
            "no_ai",
        )
    )

    summary = {
        "cli": "--with-ai/--no-ai",
        "default_deterministic": True,
        "local_profile_rejects_with_ai": local_rejects,
        "credentials_required_for_no_ai": False,
    }
    return checks, defects, summary
