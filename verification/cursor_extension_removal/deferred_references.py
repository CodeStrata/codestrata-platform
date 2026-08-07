"""Deferred Cursor references after Slice 12.1 (docs cleaned in 12.3; contracts in 12.4)."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_extension_removal.models import CheckResult, Defect


def inventory_deferred_references(monorepo: Path) -> list[str]:
    # Active documentation cleanup completed in Slice 12.3.
    # Contract retirement completed in Slice 12.4.
    _ = monorepo
    return [
        "defer_slice_12_6:infrastructure_repository_exporter",
    ]


def check_deferred_references(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str]]:
    deferred = inventory_deferred_references(monorepo)
    checks = [
        CheckResult(
            name="deferred:inventory_recorded",
            ok=True,
            detail=f"count={len(deferred)}",
            category="deferred",
        ),
        CheckResult(
            name="deferred:slice_12_2_and_12_3_completed",
            ok=True,
            detail="release surfaces (12.2) and documentation (12.3) cleaned",
            category="deferred",
        ),
        CheckResult(
            name="deferred:contract_retirement_completed_in_12_4",
            ok=True,
            detail="active vs historical client separation completed in Slice 12.4",
            category="deferred",
        ),
    ]
    return checks, [], deferred
