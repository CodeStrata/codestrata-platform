"""Repository export boundary gate."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.inventory import add_check, exists, load_json
from verification.community_insights_completion.models import CheckResult, Defect


def check_export(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    contract = load_json(monorepo, "platform/policies/codestrata_insights_repository_contract.json")
    add_check(checks, defects, "export:contract_present", bool(contract), "present", "export")
    add_check(checks, defects, "export:remote_create_forbidden", contract.get("remote_create_forbidden") is True, str(contract.get("remote_create_forbidden")), "export")
    add_check(checks, defects, "export:insights_root", exists(monorepo, "insights/package.json"), "present", "export")
    return checks, defects
