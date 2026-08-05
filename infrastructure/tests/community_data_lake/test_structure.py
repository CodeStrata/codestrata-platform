"""Structural checks for the community-data-lake module (Slice 8.1)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _read(name: str) -> str:
    return (MODULE / name).read_text(encoding="utf-8")


def test_module_directory_exists() -> None:
    assert MODULE.is_dir()
    assert not (INFRA / "modules" / "data-lake").exists()


def test_required_files_present() -> None:
    for name in (
        "main.tf",
        "variables.tf",
        "outputs.tf",
        "versions.tf",
        "locals.tf",
        "storage.tf",
        "encryption.tf",
        "lifecycle.tf",
        "iam.tf",
        "validation.tf",
        "README.md",
    ):
        assert (MODULE / name).is_file(), name


def test_single_bucket_strategy() -> None:
    blob = "\n".join(p.read_text(encoding="utf-8") for p in MODULE.glob("*.tf"))
    assert blob.count('resource "aws_s3_bucket" ') == 1
    storage = _read("storage.tf")
    assert 'resource "aws_s3_bucket"' in storage
    locals_tf = _read("locals.tf")
    assert 'accepted_prefix   = "raw/"' in locals_tf
    assert 'quarantine_prefix = "quarantine/"' in locals_tf


def test_public_access_block_present() -> None:
    storage = _read("storage.tf")
    assert "aws_s3_bucket_public_access_block" in storage
    assert "block_public_acls       = true" in storage
    assert "block_public_policy     = true" in storage
    assert "ignore_public_acls      = true" in storage
    assert "restrict_public_buckets = true" in storage


def test_ownership_controls_and_versioning() -> None:
    storage = _read("storage.tf")
    assert "BucketOwnerEnforced" in storage
    assert "aws_s3_bucket_versioning" in storage
    assert 'status = "Enabled"' in storage


def test_no_website_no_acl_no_cors() -> None:
    blob = "\n".join(p.read_text(encoding="utf-8") for p in MODULE.glob("*.tf"))
    assert "aws_s3_bucket_website_configuration" not in blob
    assert "aws_s3_bucket_acl" not in blob
    assert "aws_s3_bucket_cors_configuration" not in blob
    assert "cors_rule" not in blob.lower()


def test_bucket_naming_uses_project_and_environment() -> None:
    locals_tf = _read("locals.tf")
    assert (
        'bucket_name       = "${var.project_name}-community-data-lake-${var.environment_name}"'
        in locals_tf
    )
