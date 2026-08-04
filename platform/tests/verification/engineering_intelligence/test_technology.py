"""Technology distribution / alias tests."""

from __future__ import annotations

from verification.engineering_intelligence.technology import check_technology_aliases


def test_technology_aliases() -> None:
    assert all(c.ok for c in check_technology_aliases())
