"""CI path consistency."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_ci(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    wf = monorepo / ".github/workflows/ci.yml"
    add_check(checks, defects, "ci:workflow_exists", wf.is_file(), ".github/workflows/ci.yml", "ci")
    if not wf.is_file():
        return checks, defects
    text = wf.read_text(encoding="utf-8")
    lower = text.lower()

    # Cursor paths may appear only in negative assertions (test ! -d), not as working directories
    cursor_as_workdir = "working-directory: cursor-plugin" in lower or "working-directory: codestrata-cursor" in lower
    cursor_positive_path = "cd cursor-plugin" in lower or "./cursor-plugin/" in lower
    add_check(
        checks,
        defects,
        "ci:no_cursor_plugin_path",
        not cursor_as_workdir and not cursor_positive_path,
        "no active cursor working-directory",
        "ci",
    )
    add_check(
        checks,
        defects,
        "ci:no_codestrata_cursor",
        "codestrata-cursor" not in lower or "test ! -d" in lower,
        "cursor only as negative assertion",
        "ci",
    )
    add_check(
        checks,
        defects,
        "ci:no_tofu_apply",
        "tofu apply" not in lower and "terraform apply" not in lower,
        "apply",
        "ci",
    )
    add_check(
        checks,
        defects,
        "ci:no_marketplace_publish",
        "vsce publish" not in lower and "ovsx publish" not in lower,
        "publish",
        "ci",
    )
    add_check(
        checks,
        defects,
        "ci:no_aws_deploy_pipeline",
        "aws deploy" not in lower and "cdk deploy" not in lower,
        "deploy",
        "ci",
    )

    # Referenced working directories exist
    for marker, path in (
        ("working-directory: engine", "engine"),
        ("working-directory: platform", "platform"),
        ("working-directory: vscode-plugin", "vscode-plugin"),
    ):
        if marker in text:
            add_check(
                checks,
                defects,
                f"ci:path_exists:{path}",
                (monorepo / path).is_dir(),
                path,
                "ci",
                classification="ci_deleted_path",
            )

    add_check(
        checks,
        defects,
        "ci:export_targets_documented",
        "community" in lower and "infrastructure" in lower,
        "export targets",
        "ci",
    )
    return checks, defects
