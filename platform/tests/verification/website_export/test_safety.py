"""Safety / privacy checks."""

from __future__ import annotations

from verification.website_export.safety import check_safety


def test_safety(verified_export) -> None:
    results = check_safety(verified_export)
    assert all(item.ok for item in results), [r for r in results if not r.ok]
