"""Bounded validation helpers for Community Data Lake encryption (Slice 8.11)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.enums import EncryptionMode

_OPERATIONAL_MODES: frozenset[str] = frozenset({EncryptionMode.SSE_S3.value})
# Recognized for forward documentation only — never operational in v0.2.0.
_FUTURE_MODES: frozenset[str] = frozenset({EncryptionMode.SSE_KMS.value})


class EncryptionValidationError(ValueError):
    """Raised when encryption policy / configuration fails structural validation."""


def validate_encryption_mode(mode: str, *, allow_future_documented: bool = False) -> str:
    """Accept only ``sse_s3`` as operational; optionally recognize ``sse_kms`` as future."""

    if not isinstance(mode, str) or not mode.strip():
        raise EncryptionValidationError("encryption_mode is required")
    normalized = mode.strip()
    if normalized in _OPERATIONAL_MODES:
        return normalized
    if normalized in _FUTURE_MODES:
        if allow_future_documented:
            raise EncryptionValidationError(
                "encryption_mode_unsupported: sse_kms is documented but not operational"
            )
        raise EncryptionValidationError(
            "encryption_mode_unsupported: only sse_s3 is supported in v0.2.0"
        )
    raise EncryptionValidationError(f"encryption_mode_unsupported: {normalized!r}")


def assert_no_kms_key_id(kms_key_id: str | None) -> None:
    """Reject any KMS key identifier under the current SSE-S3 foundation."""

    if kms_key_id is not None and str(kms_key_id).strip():
        raise EncryptionValidationError("kms_key_forbidden in sse_s3 mode")


__all__ = [
    "EncryptionValidationError",
    "assert_no_kms_key_id",
    "validate_encryption_mode",
]
