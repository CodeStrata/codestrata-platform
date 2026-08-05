"""Map botocore/boto3 exceptions to bounded, safe storage outcomes (Slice 8.2).

Never places bucket names, object keys, AWS request ids, or raw exception
text into a returned ``safe_code`` — only short, stable identifiers.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.errors import StorageErrorCategory

_PRECONDITION_CODES = frozenset({"PreconditionFailed", "412"})
_ACCESS_DENIED_CODES = frozenset({"AccessDenied", "403", "Forbidden"})
_TRANSIENT_CODES = frozenset(
    {
        "SlowDown",
        "ServiceUnavailable",
        "InternalError",
        "RequestTimeout",
        "503",
        "500",
    }
)
_CHECKSUM_MISMATCH_CODES = frozenset({"BadDigest", "InvalidDigest", "XAmzContentSHA256Mismatch"})
# Unexpected KMS failures only — do not classify every InvalidArgument as
# encryption (too broad). SSE-S3 mode never requests KMS; these codes indicate
# a misconfigured writer or unexpected AWS response.
_KMS_ENCRYPTION_CODES = frozenset(
    {
        "KMS.NotFoundException",
        "KMS.DisabledException",
        "KMS.AccessDeniedException",
        "KMS.InvalidStateException",
    }
)
_TIMEOUT_NAME_TOKENS: tuple[str, ...] = ("connecttimeout", "readtimeout", "timeout")

_TRANSIENT_CATEGORIES = frozenset({StorageErrorCategory.TRANSIENT, StorageErrorCategory.TIMEOUT})


def _error_code(exc: BaseException) -> str | None:
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        code = response.get("Error", {}).get("Code")
        if code:
            return str(code)
    return None


def map_s3_exception(exc: BaseException) -> tuple[StorageWriteStatus, StorageErrorCategory, str]:
    """Classify an S3 client exception into ``(status, category, safe_code)``.

    ``PRECONDITION`` is returned for ``PreconditionFailed`` / ``412`` without
    resolving it further — the caller (:class:`.s3_store.CommunityDataLakeS3Store`)
    is responsible for the single, subsequent ``head_object`` compare.
    """

    code = _error_code(exc)
    exc_name = type(exc).__name__.lower()

    if code in _PRECONDITION_CODES:
        return (
            StorageWriteStatus.CONFLICT,
            StorageErrorCategory.PRECONDITION,
            "storage_precondition_failed",
        )
    if code in _ACCESS_DENIED_CODES:
        return (
            StorageWriteStatus.REJECTED,
            StorageErrorCategory.ACCESS_DENIED,
            "storage_access_denied",
        )
    if code in _CHECKSUM_MISMATCH_CODES:
        return (
            StorageWriteStatus.REJECTED,
            StorageErrorCategory.CHECKSUM_MISMATCH,
            "storage_checksum_mismatch",
        )
    # Unexpected KMS failures must never leak service text and must never be
    # classified as exact-retry / conflict (SSE-S3 mode does not use KMS).
    if code in _KMS_ENCRYPTION_CODES or (code is not None and str(code).startswith("KMS.")):
        return (
            StorageWriteStatus.REJECTED,
            StorageErrorCategory.UNKNOWN,
            "storage_encryption_failed",
        )
    if code in _TRANSIENT_CODES:
        return (
            StorageWriteStatus.UNAVAILABLE,
            StorageErrorCategory.TRANSIENT,
            "storage_unavailable",
        )
    if any(token in exc_name for token in _TIMEOUT_NAME_TOKENS):
        return (StorageWriteStatus.UNAVAILABLE, StorageErrorCategory.TIMEOUT, "storage_timeout")
    return (StorageWriteStatus.REJECTED, StorageErrorCategory.UNKNOWN, "storage_unknown_error")


def is_transient_storage_error(category: StorageErrorCategory) -> bool:
    """Return ``True`` when ``category`` may be safely retried."""

    return category in _TRANSIENT_CATEGORIES
