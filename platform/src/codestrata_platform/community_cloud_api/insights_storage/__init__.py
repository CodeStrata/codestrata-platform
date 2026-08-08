"""Insights storage package — bounded S3 reader (injected client)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.insights_storage.fake_s3 import FakeInsightsS3Client
from codestrata_platform.community_cloud_api.insights_storage.reader import (
    BoundedS3Reader,
    ObjectRecord,
    ReaderResult,
)

__all__ = [
    "BoundedS3Reader",
    "FakeInsightsS3Client",
    "ObjectRecord",
    "ReaderResult",
]
