"""SV.12 regression helper import smoke."""

from __future__ import annotations

from verification.system_defect_fixes import sv12_regression


def test_sv12_regression_importable() -> None:
    assert callable(sv12_regression.build_full_22_pipeline)
