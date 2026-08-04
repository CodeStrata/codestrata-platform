"""Recurring pattern tests."""

from __future__ import annotations

from verification.engineering_intelligence.patterns import (
    check_single_repo_repeat_not_recurrence,
)


def test_single_repo_no_recurrence() -> None:
    assert all(c.ok for c in check_single_repo_repeat_not_recurrence())
