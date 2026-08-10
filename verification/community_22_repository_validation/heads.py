"""Assessment head artifact checks for Slice 17.13."""

from __future__ import annotations

import ast
from pathlib import Path

from verification.community_22_repository_validation.contract import ENGINE_HEADS_MODULE
from verification.community_22_repository_validation.helpers import add_check, read_text
from verification.community_22_repository_validation.models import CheckResult, Defect


def load_head_spec_count(monorepo: Path) -> int:
    path = monorepo / ENGINE_HEADS_MODULE
    if not path.is_file():
        return 0
    tree = ast.parse(read_text(path))
    for node in tree.body:
        target_name: str | None = None
        value_node = None
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    target_name = target.id
                    value_node = node.value
                    break
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
            value_node = node.value
        if target_name == "ASSESSMENT_HEAD_SPECS" and isinstance(value_node, ast.Tuple):
            return len(value_node.elts)
    return 0


def check_heads_policy(monorepo: Path, *, head_artifacts_enabled: bool) -> tuple[list[CheckResult], list[Defect], dict[str, int | bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    count = load_head_spec_count(monorepo)
    summary = {"head_spec_count": count, "head_artifacts_enabled": head_artifacts_enabled}

    add_check(
        checks,
        defects,
        "heads:module_exists",
        (monorepo / ENGINE_HEADS_MODULE).is_file(),
        ENGINE_HEADS_MODULE,
        "heads",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "heads:spec_count_positive",
        count > 0,
        str(count),
        "heads",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "heads:policy_enabled",
        head_artifacts_enabled is True,
        "true",
        "heads",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects, summary
