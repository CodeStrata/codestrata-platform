"""Shared fixtures for SV.8 website-export verification tests."""

from __future__ import annotations

import pytest

from verification.website_export.inputs import (
    VerifiedExportInput,
    build_verified_export,
)


@pytest.fixture(scope="module")
def verified_export() -> VerifiedExportInput:
    return build_verified_export(generated_at=None)
