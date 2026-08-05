"""IAM / bucket-policy validation posture (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _blob() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in MODULE.glob("*.tf"))


def test_deny_insecure_transport_present() -> None:
    bucket_policy = (MODULE / "bucket_policy.tf").read_text(encoding="utf-8")
    assert "DenyInsecureTransport" in bucket_policy
    assert "aws:SecureTransport" in bucket_policy


def test_public_access_block_present() -> None:
    storage = (MODULE / "storage.tf").read_text(encoding="utf-8")
    assert 'resource "aws_s3_bucket_public_access_block" "community_data_lake"' in storage


def test_bucket_owner_enforced() -> None:
    storage = (MODULE / "storage.tf").read_text(encoding="utf-8")
    assert "BucketOwnerEnforced" in storage
