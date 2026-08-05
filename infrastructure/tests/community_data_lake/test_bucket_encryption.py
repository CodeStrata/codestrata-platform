"""Bucket server-side encryption configuration (Slice 8.11)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _encryption() -> str:
    return (MODULE / "encryption.tf").read_text(encoding="utf-8")


def test_explicit_sse_configuration_resource_exists() -> None:
    encryption = _encryption()
    assert 'resource "aws_s3_bucket_server_side_encryption_configuration"' in encryption
    assert "community_data_lake" in encryption


def test_aes256_default_algorithm() -> None:
    encryption = _encryption()
    assert "apply_server_side_encryption_by_default" in encryption
    assert 'sse_algorithm = "AES256"' in encryption


def test_bucket_key_enabled_is_false() -> None:
    """S3 Bucket Keys are an SSE-KMS cost feature; must stay false under SSE-S3."""

    assert "bucket_key_enabled = false" in _encryption()
    assert "bucket_key_enabled = true" not in _encryption()


def test_no_kms_master_key_id_in_encryption_config() -> None:
    encryption = _encryption().lower()
    assert "kms_master_key_id" not in encryption
    assert "aws:kms" not in encryption
