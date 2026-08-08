"""Aggregate reporting helpers."""

from __future__ import annotations

from pathlib import Path

from verification.vscode_visual_experience.checks import check_all
from verification.vscode_visual_experience.models import CheckResult, Defect


def release_posture() -> dict[str, bool]:
    return {
        "no_commit": True,
        "no_tag": True,
        "no_publish": True,
        "no_deploy": True,
        "start_slice_14_6": False,
        "extension_version_0_2_0": True,
        "runtime_behavior_unchanged": True,
        "marketplace_assets_aligned_via_14_6": True,
        "slice_14_5_complete": True,
    }


def run_checks(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    return check_all(monorepo)
