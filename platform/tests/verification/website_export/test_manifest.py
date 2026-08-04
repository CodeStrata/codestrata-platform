"""Manifest checks."""

from __future__ import annotations

from verification.website_export.manifest import check_manifest


def test_manifest(verified_export) -> None:
    results = check_manifest(verified_export)
    assert all(item.ok for item in results), [r for r in results if not r.ok]
