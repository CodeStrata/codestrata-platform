"""Projection and identity checks."""

from __future__ import annotations

from verification.website_export.projection import (
    check_export_identity,
    check_export_policy,
    check_projection,
)


def test_policy_and_projection(verified_export) -> None:
    results = (
        check_export_policy(verified_export)
        + check_projection(verified_export)
        + check_export_identity(verified_export)
    )
    assert all(item.ok for item in results), [r for r in results if not r.ok]
