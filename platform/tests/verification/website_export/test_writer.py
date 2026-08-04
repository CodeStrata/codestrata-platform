"""Static writer checks."""

from __future__ import annotations

from pathlib import Path

from verification.website_export.writer import check_writer


def test_writer(verified_export, tmp_path: Path) -> None:
    results = check_writer(verified_export, tmp_path)
    assert all(item.ok for item in results), [r for r in results if not r.ok]
