"""Privacy chain tests."""

from __future__ import annotations

from verification.cross_schema_compatibility.privacy import check_privacy_chain


def test_privacy_chain() -> None:
    checks, failures = check_privacy_chain()
    assert all(c.ok for c in checks), [(c.name, c.detail) for c in checks if not c.ok]
    assert not failures
