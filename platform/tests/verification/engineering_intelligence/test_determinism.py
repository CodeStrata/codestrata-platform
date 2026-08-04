"""Determinism tests."""

from __future__ import annotations

from verification.engineering_intelligence.determinism import check_determinism


def test_determinism_order_invariant() -> None:
    assert all(c.ok for c in check_determinism())
