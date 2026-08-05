"""Lifecycle / retention checks for the community-data-lake module."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _read(name: str) -> str:
    return (MODULE / name).read_text(encoding="utf-8")


def test_retention_variables_present() -> None:
    variables = _read("variables.tf")
    for name, default in (
        ("accepted_retention_days", "default     = 365"),
        ("quarantine_retention_days", "default     = 90"),
        ("incomplete_multipart_days", "default     = 7"),
        ("noncurrent_version_expiration_days", "default     = 30"),
    ):
        assert f'variable "{name}"' in variables
        assert default in variables


def test_lifecycle_configuration_present() -> None:
    lifecycle = _read("lifecycle.tf")
    assert "aws_s3_bucket_lifecycle_configuration" in lifecycle


def test_lifecycle_rules_filter_by_prefix() -> None:
    lifecycle = _read("lifecycle.tf")
    assert "prefix = local.accepted_prefix" in lifecycle
    assert "prefix = local.quarantine_prefix" in lifecycle


def test_lifecycle_expiration_uses_retention_variables() -> None:
    lifecycle = _read("lifecycle.tf")
    assert "days = var.accepted_retention_days" in lifecycle
    assert "days = var.quarantine_retention_days" in lifecycle


def test_abort_incomplete_multipart_and_noncurrent_version_expiration() -> None:
    lifecycle = _read("lifecycle.tf")
    assert "abort_incomplete_multipart_upload" in lifecycle
    assert "days_after_initiation = var.incomplete_multipart_days" in lifecycle
    assert "noncurrent_version_expiration" in lifecycle
    assert "noncurrent_days = var.noncurrent_version_expiration_days" in lifecycle


def test_expire_delete_markers_rule_present() -> None:
    lifecycle = _read("lifecycle.tf")
    assert 'id     = "expire-delete-markers"' in lifecycle
    assert "expired_object_delete_marker = true" in lifecycle


def test_lifecycle_rule_ids_unique() -> None:
    lifecycle = _read("lifecycle.tf")
    for rule_id in (
        "accepted-retention",
        "quarantine-retention",
        "abort-incomplete-multipart-uploads",
        "expire-delete-markers",
    ):
        assert lifecycle.count(f'id     = "{rule_id}"') == 1


def test_no_storage_class_transitions() -> None:
    lifecycle = _read("lifecycle.tf").lower()
    assert "transition {" not in lifecycle
    assert "glacier" not in lifecycle
    assert "deep_archive" not in lifecycle


def test_retention_defaults_labeled_review_required() -> None:
    variables = _read("variables.tf")
    assert "review-required" in variables.lower()
