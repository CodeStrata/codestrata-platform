"""Cursor product removal completeness checks."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_extension_removal.contract import (
    PRODUCT_FILE_COUNT_EXCL_NODE_MODULES_PRE_REMOVAL,
    TRACKED_CURSOR_FILE_COUNT_PRE_REMOVAL,
)
from verification.cursor_extension_removal.inventory import TRACKED_CURSOR_RELATIVE_PATHS
from verification.cursor_extension_removal.models import CheckResult, Defect


def check_removal(monorepo: Path) -> tuple[list[CheckResult], list[Defect], int]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cursor = monorepo / "cursor-plugin"

    absent = not cursor.exists()
    checks.append(
        CheckResult(
            name="removal:cursor_directory_absent",
            ok=absent,
            detail="cursor-plugin directory absent",
            category="removal",
        )
    )
    if not absent:
        defects.append(
            Defect(
                "removal completeness defect",
                "cursor-plugin",
                "absent",
                "present",
            )
        )

    markers = {
        "package.json": cursor / "package.json",
        "src": cursor / "src",
        "src/extension.ts": cursor / "src" / "extension.ts",
        "src/test": cursor / "src" / "test",
        "src/telemetry": cursor / "src" / "telemetry",
        "src/analytics": cursor / "src" / "analytics",
        "media": cursor / "media",
        "out": cursor / "out",
        "package-lock.json": cursor / "package-lock.json",
    }
    for label, path in sorted(markers.items()):
        present = path.exists()
        checks.append(
            CheckResult(
                name=f"removal:{label.replace('/', '_')}_absent",
                ok=not present,
                detail=f"{label} present={present}",
                category="removal",
            )
        )
        if present:
            defects.append(
                Defect(
                    "removal completeness defect",
                    f"cursor-plugin/{label}",
                    "absent",
                    "present",
                )
            )

    remaining_tracked = [rel for rel in TRACKED_CURSOR_RELATIVE_PATHS if (monorepo / rel).exists()]
    checks.append(
        CheckResult(
            name="removal:tracked_paths_absent",
            ok=not remaining_tracked,
            detail=f"remaining={remaining_tracked[:5] or 'none'}",
            category="removal",
        )
    )
    if remaining_tracked:
        defects.append(
            Defect(
                "removal completeness defect",
                "tracked_cursor_paths",
                "absent",
                ",".join(remaining_tracked[:10]),
            )
        )

    removed_count = TRACKED_CURSOR_FILE_COUNT_PRE_REMOVAL
    checks.append(
        CheckResult(
            name="removal:tracked_file_count_recorded",
            ok=removed_count == len(TRACKED_CURSOR_RELATIVE_PATHS),
            detail=(
                f"tracked={removed_count};"
                f"product_excl_nm_pre={PRODUCT_FILE_COUNT_EXCL_NODE_MODULES_PRE_REMOVAL}"
            ),
            category="removal",
        )
    )
    return checks, defects, removed_count
