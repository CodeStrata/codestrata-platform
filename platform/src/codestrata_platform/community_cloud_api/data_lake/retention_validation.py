"""Bounded validation helpers for Community Data Lake retention values (Slice 8.10)."""

from __future__ import annotations


class RetentionValidationError(ValueError):
    """Raised when retention / lifecycle values fail structural validation."""


def validate_retention_values(
    *,
    accepted_retention_days: int,
    quarantine_retention_days: int,
    incomplete_multipart_cleanup_days: int,
    noncurrent_version_retention_days: int,
    accepted_min: int,
    accepted_max: int,
    quarantine_min: int,
    quarantine_max: int,
    multipart_min: int,
    multipart_max: int,
    noncurrent_min: int,
    noncurrent_max: int,
    require_quarantine_le_accepted: bool = True,
) -> None:
    """Fail closed on zero/negative/out-of-bounds or inverted quarantine/accepted."""

    if not isinstance(accepted_retention_days, int) or isinstance(
        accepted_retention_days, bool
    ):
        raise RetentionValidationError("accepted_retention_days must be an int")
    if not isinstance(quarantine_retention_days, int) or isinstance(
        quarantine_retention_days, bool
    ):
        raise RetentionValidationError("quarantine_retention_days must be an int")
    if not isinstance(incomplete_multipart_cleanup_days, int) or isinstance(
        incomplete_multipart_cleanup_days, bool
    ):
        raise RetentionValidationError("incomplete_multipart_cleanup_days must be an int")
    if not isinstance(noncurrent_version_retention_days, int) or isinstance(
        noncurrent_version_retention_days, bool
    ):
        raise RetentionValidationError("noncurrent_version_retention_days must be an int")

    if accepted_retention_days <= 0:
        raise RetentionValidationError("accepted_retention_days must be greater than zero")
    if quarantine_retention_days <= 0:
        raise RetentionValidationError("quarantine_retention_days must be greater than zero")
    if incomplete_multipart_cleanup_days <= 0:
        raise RetentionValidationError(
            "incomplete_multipart_cleanup_days must be greater than zero"
        )
    if noncurrent_version_retention_days <= 0:
        raise RetentionValidationError(
            "noncurrent_version_retention_days must be greater than zero"
        )

    if not (accepted_min <= accepted_retention_days <= accepted_max):
        raise RetentionValidationError(
            f"accepted_retention_days out of bounds [{accepted_min}, {accepted_max}]"
        )
    if not (quarantine_min <= quarantine_retention_days <= quarantine_max):
        raise RetentionValidationError(
            f"quarantine_retention_days out of bounds [{quarantine_min}, {quarantine_max}]"
        )
    if not (multipart_min <= incomplete_multipart_cleanup_days <= multipart_max):
        raise RetentionValidationError(
            "incomplete_multipart_cleanup_days out of bounds "
            f"[{multipart_min}, {multipart_max}]"
        )
    if not (noncurrent_min <= noncurrent_version_retention_days <= noncurrent_max):
        raise RetentionValidationError(
            "noncurrent_version_retention_days out of bounds "
            f"[{noncurrent_min}, {noncurrent_max}]"
        )

    if require_quarantine_le_accepted and quarantine_retention_days > accepted_retention_days:
        raise RetentionValidationError(
            "quarantine_retention_days must be less than or equal to "
            "accepted_retention_days unless an explicit documented override exists"
        )


__all__ = ["RetentionValidationError", "validate_retention_values"]
