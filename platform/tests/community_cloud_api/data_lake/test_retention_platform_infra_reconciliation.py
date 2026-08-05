"""Static reconciliation: Platform retention defaults vs OpenTofu HCL (Slice 8.10)."""

from __future__ import annotations

import re
from pathlib import Path

from codestrata_platform.community_cloud_api.data_lake.retention_policy import (
    ACCEPTED_RETENTION_MAX_DAYS,
    ACCEPTED_RETENTION_MIN_DAYS,
    DEFAULT_ACCEPTED_RETENTION_DAYS,
    DEFAULT_INCOMPLETE_MULTIPART_DAYS,
    DEFAULT_NONCURRENT_VERSION_RETENTION_DAYS,
    DEFAULT_QUARANTINE_RETENTION_DAYS,
    INCOMPLETE_MULTIPART_MAX_DAYS,
    INCOMPLETE_MULTIPART_MIN_DAYS,
    NONCURRENT_VERSION_MAX_DAYS,
    NONCURRENT_VERSION_MIN_DAYS,
    QUARANTINE_RETENTION_MAX_DAYS,
    QUARANTINE_RETENTION_MIN_DAYS,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
MODULE = REPO_ROOT / "infrastructure" / "modules" / "community-data-lake"


def _read(name: str) -> str:
    return (MODULE / name).read_text(encoding="utf-8")


def _variable_block(variables: str, name: str) -> str:
    match = re.search(
        rf'variable\s+"{re.escape(name)}"\s*\{{(.*?)\n\}}',
        variables,
        flags=re.DOTALL,
    )
    assert match is not None, f"variable {name} not found"
    return match.group(1)


def _default_int(block: str) -> int:
    match = re.search(r"default\s*=\s*(\d+)", block)
    assert match is not None, f"default missing in block:\n{block}"
    return int(match.group(1))


def _validation_bounds(block: str, var_name: str) -> tuple[int, int]:
    pattern = (
        rf"var\.{re.escape(var_name)}\s*>=\s*(\d+)\s*&&\s*"
        rf"var\.{re.escape(var_name)}\s*<=\s*(\d+)"
    )
    match = re.search(pattern, block)
    assert match is not None, f"bounds for {var_name} not found in:\n{block}"
    return int(match.group(1)), int(match.group(2))


def test_platform_defaults_match_opentofu_variable_defaults() -> None:
    variables = _read("variables.tf")
    assert _default_int(_variable_block(variables, "accepted_retention_days")) == (
        DEFAULT_ACCEPTED_RETENTION_DAYS
    )
    assert _default_int(_variable_block(variables, "quarantine_retention_days")) == (
        DEFAULT_QUARANTINE_RETENTION_DAYS
    )
    assert _default_int(_variable_block(variables, "incomplete_multipart_days")) == (
        DEFAULT_INCOMPLETE_MULTIPART_DAYS
    )
    assert _default_int(
        _variable_block(variables, "noncurrent_version_expiration_days")
    ) == DEFAULT_NONCURRENT_VERSION_RETENTION_DAYS


def test_platform_bounds_match_opentofu_variable_validation() -> None:
    variables = _read("variables.tf")
    assert _validation_bounds(
        _variable_block(variables, "accepted_retention_days"), "accepted_retention_days"
    ) == (ACCEPTED_RETENTION_MIN_DAYS, ACCEPTED_RETENTION_MAX_DAYS)
    assert _validation_bounds(
        _variable_block(variables, "quarantine_retention_days"),
        "quarantine_retention_days",
    ) == (QUARANTINE_RETENTION_MIN_DAYS, QUARANTINE_RETENTION_MAX_DAYS)
    assert _validation_bounds(
        _variable_block(variables, "incomplete_multipart_days"),
        "incomplete_multipart_days",
    ) == (INCOMPLETE_MULTIPART_MIN_DAYS, INCOMPLETE_MULTIPART_MAX_DAYS)
    assert _validation_bounds(
        _variable_block(variables, "noncurrent_version_expiration_days"),
        "noncurrent_version_expiration_days",
    ) == (NONCURRENT_VERSION_MIN_DAYS, NONCURRENT_VERSION_MAX_DAYS)


def test_lifecycle_has_required_stable_rules() -> None:
    lifecycle = _read("lifecycle.tf")
    for rule_id in (
        "accepted-retention",
        "quarantine-retention",
        "abort-incomplete-multipart-uploads",
        "expire-delete-markers",
    ):
        assert f'id     = "{rule_id}"' in lifecycle


def test_lifecycle_has_no_transitions_or_glacier() -> None:
    lifecycle = _read("lifecycle.tf").lower()
    assert "transition {" not in lifecycle
    assert "glacier" not in lifecycle
    assert "deep_archive" not in lifecycle
    assert "intelligent_tiering" not in lifecycle


def test_no_object_lock_resources() -> None:
    blob = "\n".join(p.read_text(encoding="utf-8") for p in MODULE.glob("*.tf")).lower()
    assert "object_lock" not in blob
    assert "aws_s3_bucket_object_lock_configuration" not in blob


def test_storage_versioning_enabled_and_force_destroy_from_var() -> None:
    storage = _read("storage.tf")
    assert 'status = "Enabled"' in storage
    assert "force_destroy = var.force_destroy" in storage
    variables = _read("variables.tf")
    force_block = _variable_block(variables, "force_destroy")
    assert "default     = false" in force_block or "default = false" in force_block


def test_iam_deny_delete_accepted_no_allow_delete() -> None:
    iam = _read("iam.tf")
    assert "DenyAcceptedObjectDeletion" in iam
    assert "DenyQuarantineObjectDeletion" in iam
    assert 'effect = "Deny"' in iam
    assert "s3:DeleteObject" in iam
    in_allow = False
    for line in iam.splitlines():
        stripped = line.strip()
        if stripped.startswith("effect"):
            in_allow = '"Allow"' in stripped
        if in_allow and "DeleteObject" in stripped:
            raise AssertionError(f"Allow DeleteObject found: {stripped}")
