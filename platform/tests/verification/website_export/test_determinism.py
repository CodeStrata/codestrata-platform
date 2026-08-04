"""Determinism checks."""

from __future__ import annotations

from verification.website_export.determinism import check_determinism


def test_determinism(verified_export) -> None:
    results = check_determinism(verified_export)
    assert all(item.ok for item in results), [r for r in results if not r.ok]
