"""Determinism helper import smoke (full order check runs in SV.13 runner)."""

from __future__ import annotations

from verification.system_defect_fixes import determinism


def test_determinism_module_importable() -> None:
    assert callable(determinism.check_order_independent_ids)
