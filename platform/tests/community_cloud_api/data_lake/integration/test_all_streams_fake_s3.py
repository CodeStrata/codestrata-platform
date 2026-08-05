"""Fake-S3 accepted-stream integration tests (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.streams import check_accepted_streams_fake_s3

from .assertions import assert_all_ok


def test_all_streams_fake_s3() -> None:
    assert_all_ok(check_accepted_streams_fake_s3(), label="fake_s3_streams")
