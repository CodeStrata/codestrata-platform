"""Accessibility checks."""

from __future__ import annotations

from verification.website_export.accessibility import check_accessibility


def test_accessibility(verified_export) -> None:
    results = check_accessibility(verified_export)
    assert all(item.ok for item in results), [r for r in results if not r.ok]
