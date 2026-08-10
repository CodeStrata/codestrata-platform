"""Concurrency checks for Slice 17.15."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.contract import ENGINE_LIFECYCLE
from verification.report_artifact_lifecycle.helpers import add_check, read_text
from verification.report_artifact_lifecycle.models import CheckResult, Defect


def check_concurrency(monorepo: Path, policy: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"atomic_rotation": policy.get("rotation_atomic") is True}

    add_check(
        checks,
        defects,
        "concurrency:rotation_atomic_policy",
        policy.get("rotation_atomic") is True,
        str(policy.get("rotation_atomic")),
        "concurrency",
    )

    path = monorepo / ENGINE_LIFECYCLE
    if path.is_file():
        text = read_text(path)
        has_lock = any(token in text for token in ("lock", "Lock", "fcntl", "atomic", "os.replace"))
        add_check(
            checks,
            defects,
            "concurrency:engine_safety",
            has_lock,
            "lock or atomic write in lifecycle",
            "concurrency",
            soft=True,
        )
    else:
        add_check(
            checks,
            defects,
            "concurrency:lifecycle_deferred",
            True,
            "lifecycle module not yet wired",
            "concurrency",
            soft=True,
        )

    manifest_path = monorepo / "engine/src/codestrata/artifacts/manifest.py"
    if manifest_path.is_file():
        text = read_text(manifest_path)
        add_check(
            checks,
            defects,
            "concurrency:manifest_atomic_write",
            "os.replace" in text or "_atomic_write" in text,
            "atomic manifest write",
            "concurrency",
        )

    return checks, defects, summary
