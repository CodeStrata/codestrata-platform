"""Integration smoke for SV.15."""

from __future__ import annotations

from verification.deterministic_outputs import (
    DETERMINISTIC_OUTPUTS_ID,
    DETERMINISTIC_OUTPUTS_VERSION,
)


def test_package_metadata() -> None:
    assert DETERMINISTIC_OUTPUTS_ID.startswith("sv15")
    assert DETERMINISTIC_OUTPUTS_VERSION == "1.0.0"
