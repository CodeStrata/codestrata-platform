"""Shared fixtures for SV.7 Community Cloud API verification tests."""

from __future__ import annotations

import pytest

from verification.community_cloud_api.app_factory import (
    VerificationApp,
    build_verification_app,
)


@pytest.fixture()
def verification_app() -> VerificationApp:
    return build_verification_app()
