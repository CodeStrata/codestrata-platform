"""S3 Data Lake store configuration model (Slice 8.2 infrastructure).

Deliberately a pure, validated data model: it never reads environment
variables, files, or any other ambient configuration source — the caller
(future wiring, not part of this slice) is responsible for constructing it
from whatever configuration mechanism the deployment uses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from codestrata_platform.community_cloud_api.data_lake.enums import EncryptionMode

_BUCKET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$")
_BUCKET_FORBIDDEN_SUBSTRINGS: tuple[str, ...] = ("s3://", "/", ":", "@")

_CONNECT_TIMEOUT_MIN_SECONDS = 0.5
_CONNECT_TIMEOUT_MAX_SECONDS = 30.0
_READ_TIMEOUT_MIN_SECONDS = 1.0
_READ_TIMEOUT_MAX_SECONDS = 60.0
_MAX_ATTEMPTS_MIN = 1
_MAX_ATTEMPTS_MAX = 5

_SUPPORTED_POLICY_VERSION = "1.0"
_REQUIRED_RAW_PREFIX = "raw/"
_REQUIRED_QUARANTINE_PREFIX = "quarantine/"


class S3ConfigurationError(ValueError):
    """Raised when the S3 Data Lake store configuration is invalid."""


@dataclass(frozen=True, slots=True)
class S3DataLakeStoreConfiguration:
    """Validated, boto3-free configuration for :class:`.s3_store.CommunityDataLakeS3Store`.

    ``endpoint_url`` exists for tests only (e.g. a local S3-compatible
    server) and requires ``allow_endpoint_override=True`` — production
    configuration must never set either field together.
    """

    bucket_name: str
    raw_prefix: str = _REQUIRED_RAW_PREFIX
    quarantine_prefix: str = _REQUIRED_QUARANTINE_PREFIX
    encryption_mode: str = EncryptionMode.SSE_S3.value
    conditional_write_required: bool = True
    checksum_required: bool = True
    metadata_digest_key: str = "codestrata-content-sha256"
    connect_timeout_seconds: float = 3.0
    read_timeout_seconds: float = 10.0
    max_attempts: int = 3
    endpoint_url: str | None = None
    policy_version: str = _SUPPORTED_POLICY_VERSION
    allow_endpoint_override: bool = False

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        bucket = self.bucket_name
        if not bucket or not _BUCKET_NAME_RE.match(bucket):
            raise S3ConfigurationError(
                "bucket_name must be lowercase alphanumeric/hyphen, 3-63 characters"
            )
        if not (3 <= len(bucket) <= 63):
            raise S3ConfigurationError("bucket_name must be 3-63 characters")
        for forbidden in _BUCKET_FORBIDDEN_SUBSTRINGS:
            if forbidden in bucket:
                raise S3ConfigurationError(f"bucket_name must not contain {forbidden!r}")

        if self.raw_prefix != _REQUIRED_RAW_PREFIX:
            raise S3ConfigurationError(f"raw_prefix must be {_REQUIRED_RAW_PREFIX!r} in this slice")
        if self.quarantine_prefix != _REQUIRED_QUARANTINE_PREFIX:
            raise S3ConfigurationError(
                f"quarantine_prefix must be {_REQUIRED_QUARANTINE_PREFIX!r} in this slice"
            )
        if self.raw_prefix == self.quarantine_prefix:
            raise S3ConfigurationError("accepted and quarantine prefixes must not collide")

        if self.encryption_mode != EncryptionMode.SSE_S3.value:
            raise S3ConfigurationError("only sse_s3 encryption is supported in this slice")

        # Slice 8.11: SSE-S3 must never carry a KMS key identifier.
        if getattr(self, "kms_key_id", None):
            raise S3ConfigurationError("kms_key_forbidden in sse_s3 mode")

        if not (_CONNECT_TIMEOUT_MIN_SECONDS <= self.connect_timeout_seconds <= _CONNECT_TIMEOUT_MAX_SECONDS):
            raise S3ConfigurationError(
                "connect_timeout_seconds out of bounds "
                f"[{_CONNECT_TIMEOUT_MIN_SECONDS}, {_CONNECT_TIMEOUT_MAX_SECONDS}]"
            )
        if not (_READ_TIMEOUT_MIN_SECONDS <= self.read_timeout_seconds <= _READ_TIMEOUT_MAX_SECONDS):
            raise S3ConfigurationError(
                "read_timeout_seconds out of bounds "
                f"[{_READ_TIMEOUT_MIN_SECONDS}, {_READ_TIMEOUT_MAX_SECONDS}]"
            )
        if not (_MAX_ATTEMPTS_MIN <= self.max_attempts <= _MAX_ATTEMPTS_MAX):
            raise S3ConfigurationError(
                f"max_attempts out of bounds [{_MAX_ATTEMPTS_MIN}, {_MAX_ATTEMPTS_MAX}]"
            )

        if self.endpoint_url is not None and not self.allow_endpoint_override:
            raise S3ConfigurationError("endpoint_url requires allow_endpoint_override=True")

        if self.policy_version != _SUPPORTED_POLICY_VERSION:
            raise S3ConfigurationError("unsupported data lake policy version")
