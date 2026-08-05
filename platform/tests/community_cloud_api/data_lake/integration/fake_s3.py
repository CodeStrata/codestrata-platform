"""Re-export fake S3 client from verification package."""

from verification.community_data_lake.fake_s3 import FakeClientError, FakeS3Client, client_error

__all__ = ["FakeClientError", "FakeS3Client", "client_error"]
