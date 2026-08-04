"""HTML export checks."""

from __future__ import annotations

from verification.website_export.html_export import check_html_export


def test_html_export(verified_export) -> None:
    results = check_html_export(verified_export)
    assert all(item.ok for item in results), [r for r in results if not r.ok]
