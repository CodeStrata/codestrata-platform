"""JSON/HTML parity checks."""

from __future__ import annotations

from verification.website_export.parity import check_parity


def test_parity(verified_export) -> None:
    results = check_parity(verified_export)
    assert all(item.ok for item in results), [r for r in results if not r.ok]
