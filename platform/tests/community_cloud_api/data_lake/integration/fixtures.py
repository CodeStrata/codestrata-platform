"""Shared fixtures for data lake integration tests."""

from __future__ import annotations

import pytest

from verification.community_data_lake.fake_s3 import FakeS3Client


@pytest.fixture()
def fake_s3_client() -> FakeS3Client:
    return FakeS3Client()
