"""No KMS permissions in community-data-lake IAM or bucket policy (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def test_no_kms_in_iam() -> None:
    iam = (MODULE / "iam.tf").read_text(encoding="utf-8").lower()
    assert "kms:" not in iam


def test_no_kms_in_bucket_policy() -> None:
    bucket_policy = (MODULE / "bucket_policy.tf").read_text(encoding="utf-8").lower()
    assert "kms:" not in bucket_policy
    assert "aws:kms" not in bucket_policy
