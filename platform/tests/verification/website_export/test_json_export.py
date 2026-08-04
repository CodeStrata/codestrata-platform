"""JSON export checks."""

from __future__ import annotations

from verification.website_export.json_export import check_json_export


def test_json_export(verified_export) -> None:
    results = check_json_export(verified_export)
    assert all(item.ok for item in results), [r for r in results if not r.ok]
