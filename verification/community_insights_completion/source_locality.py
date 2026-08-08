"""Source locality preservation gate."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.inventory import add_check, exists
from verification.community_insights_completion.models import CheckResult, Defect


def check_source_locality(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "source_locality:vscode_package", exists(monorepo, "verification/vscode_source_locality/runner.py"), "present", "source_locality")
    add_check(checks, defects, "source_locality:ingestion_policy", exists(monorepo, "platform/policies/community_insights_ingestion_policy.json"), "present", "source_locality")
    return checks, defects
