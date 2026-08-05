"""Versioning + lifecycle interaction posture (Slice 8.10)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _read(name: str) -> str:
    return (MODULE / name).read_text(encoding="utf-8")


def test_versioning_explicitly_enabled() -> None:
    storage = _read("storage.tf")
    assert 'resource "aws_s3_bucket_versioning"' in storage
    assert 'status = "Enabled"' in storage


def test_lifecycle_depends_on_versioning() -> None:
    lifecycle = _read("lifecycle.tf")
    assert "depends_on = [aws_s3_bucket_versioning.community_data_lake]" in lifecycle


def test_noncurrent_version_expiration_on_prefix_rules() -> None:
    lifecycle = _read("lifecycle.tf")
    assert lifecycle.count("noncurrent_version_expiration {") == 2
    assert "noncurrent_days = var.noncurrent_version_expiration_days" in lifecycle


def test_no_object_lock_configuration() -> None:
    blob = "\n".join(p.read_text(encoding="utf-8") for p in MODULE.glob("*.tf")).lower()
    assert "object_lock" not in blob
    assert "aws_s3_bucket_object_lock_configuration" not in blob


def test_force_destroy_defaults_false() -> None:
    variables = _read("variables.tf")
    assert 'variable "force_destroy"' in variables
    assert "default     = false" in variables
    storage = _read("storage.tf")
    assert "force_destroy = var.force_destroy" in storage
