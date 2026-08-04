"""Negative scenario tests."""

from __future__ import annotations

from verification.deterministic_outputs.scenarios import check_negative_scenarios


def test_negative_scenarios() -> None:
    checks = check_negative_scenarios()
    assert all(c.ok for c in checks), [(c.name, c.detail) for c in checks if not c.ok]
