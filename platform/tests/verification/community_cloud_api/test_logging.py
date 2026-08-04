"""Structured logging verification."""

from __future__ import annotations

from verification.community_cloud_api.logging_checks import check_logging


def test_logging(verification_app) -> None:
    results = check_logging(verification_app)
    assert results
    assert all(item.ok for item in results), [r for r in results if not r.ok]
