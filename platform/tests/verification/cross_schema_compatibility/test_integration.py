"""Integration smoke for SV.14."""

from __future__ import annotations

from verification.cross_schema_compatibility import (
    CROSS_SCHEMA_COMPATIBILITY_ID,
    CROSS_SCHEMA_COMPATIBILITY_VERSION,
)


def test_package_metadata() -> None:
    assert CROSS_SCHEMA_COMPATIBILITY_ID.startswith("sv14")
    assert CROSS_SCHEMA_COMPATIBILITY_VERSION == "1.0.0"
