"""Unit tests for validate_retention_values (Slice 8.10).

Negatives A–J mirror the slice brief failure modes.
"""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.retention_policy import (
    ACCEPTED_RETENTION_MAX_DAYS,
    ACCEPTED_RETENTION_MIN_DAYS,
    INCOMPLETE_MULTIPART_MAX_DAYS,
    INCOMPLETE_MULTIPART_MIN_DAYS,
    NONCURRENT_VERSION_MAX_DAYS,
    NONCURRENT_VERSION_MIN_DAYS,
    QUARANTINE_RETENTION_MAX_DAYS,
    QUARANTINE_RETENTION_MIN_DAYS,
)
from codestrata_platform.community_cloud_api.data_lake.retention_validation import (
    RetentionValidationError,
    validate_retention_values,
)

_BOUNDS = dict(
    accepted_min=ACCEPTED_RETENTION_MIN_DAYS,
    accepted_max=ACCEPTED_RETENTION_MAX_DAYS,
    quarantine_min=QUARANTINE_RETENTION_MIN_DAYS,
    quarantine_max=QUARANTINE_RETENTION_MAX_DAYS,
    multipart_min=INCOMPLETE_MULTIPART_MIN_DAYS,
    multipart_max=INCOMPLETE_MULTIPART_MAX_DAYS,
    noncurrent_min=NONCURRENT_VERSION_MIN_DAYS,
    noncurrent_max=NONCURRENT_VERSION_MAX_DAYS,
)


def _ok(**overrides: object) -> None:
    values: dict[str, object] = {
        "accepted_retention_days": 365,
        "quarantine_retention_days": 90,
        "incomplete_multipart_cleanup_days": 7,
        "noncurrent_version_retention_days": 30,
        **_BOUNDS,
        "require_quarantine_le_accepted": True,
    }
    values.update(overrides)
    validate_retention_values(**values)  # type: ignore[arg-type]


def test_valid_defaults_accepted() -> None:
    _ok()


def test_a_accepted_not_int() -> None:
    with pytest.raises(RetentionValidationError, match="accepted_retention_days must be an int"):
        _ok(accepted_retention_days="365")


def test_b_quarantine_not_int() -> None:
    with pytest.raises(RetentionValidationError, match="quarantine_retention_days must be an int"):
        _ok(quarantine_retention_days=90.0)


def test_c_bool_rejected_as_int() -> None:
    with pytest.raises(RetentionValidationError, match="must be an int"):
        _ok(accepted_retention_days=True)
    with pytest.raises(RetentionValidationError, match="must be an int"):
        _ok(incomplete_multipart_cleanup_days=False)


def test_d_accepted_zero_or_negative() -> None:
    with pytest.raises(RetentionValidationError, match="greater than zero"):
        _ok(accepted_retention_days=0)
    with pytest.raises(RetentionValidationError, match="greater than zero"):
        _ok(accepted_retention_days=-1)


def test_e_quarantine_zero_or_negative() -> None:
    with pytest.raises(RetentionValidationError, match="greater than zero"):
        _ok(quarantine_retention_days=0)
    with pytest.raises(RetentionValidationError, match="greater than zero"):
        _ok(quarantine_retention_days=-3)


def test_f_multipart_and_noncurrent_zero_or_negative() -> None:
    with pytest.raises(RetentionValidationError, match="greater than zero"):
        _ok(incomplete_multipart_cleanup_days=0)
    with pytest.raises(RetentionValidationError, match="greater than zero"):
        _ok(noncurrent_version_retention_days=-1)


def test_g_accepted_out_of_bounds() -> None:
    with pytest.raises(RetentionValidationError, match="out of bounds"):
        _ok(accepted_retention_days=ACCEPTED_RETENTION_MIN_DAYS - 1, quarantine_retention_days=7)
    with pytest.raises(RetentionValidationError, match="out of bounds"):
        _ok(accepted_retention_days=ACCEPTED_RETENTION_MAX_DAYS + 1)


def test_h_quarantine_out_of_bounds() -> None:
    with pytest.raises(RetentionValidationError, match="out of bounds"):
        _ok(quarantine_retention_days=QUARANTINE_RETENTION_MIN_DAYS - 1)
    with pytest.raises(RetentionValidationError, match="out of bounds"):
        _ok(quarantine_retention_days=QUARANTINE_RETENTION_MAX_DAYS + 1)


def test_i_multipart_and_noncurrent_out_of_bounds() -> None:
    with pytest.raises(RetentionValidationError, match="out of bounds"):
        _ok(incomplete_multipart_cleanup_days=INCOMPLETE_MULTIPART_MAX_DAYS + 1)
    with pytest.raises(RetentionValidationError, match="out of bounds"):
        _ok(noncurrent_version_retention_days=NONCURRENT_VERSION_MAX_DAYS + 1)


def test_j_quarantine_greater_than_accepted() -> None:
    with pytest.raises(RetentionValidationError, match="less than or equal"):
        _ok(accepted_retention_days=30, quarantine_retention_days=90)


def test_quarantine_gt_accepted_allowed_when_override_disabled() -> None:
    _ok(
        accepted_retention_days=30,
        quarantine_retention_days=90,
        require_quarantine_le_accepted=False,
    )
