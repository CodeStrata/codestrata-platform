"""Integration smoke for SV.13 package imports."""

from __future__ import annotations

from verification.system_defect_fixes import (
    SYSTEM_DEFECT_FIXES_ID,
    SYSTEM_DEFECT_FIXES_VERSION,
)


def test_package_metadata() -> None:
    assert SYSTEM_DEFECT_FIXES_ID.startswith("sv13")
    assert SYSTEM_DEFECT_FIXES_VERSION
