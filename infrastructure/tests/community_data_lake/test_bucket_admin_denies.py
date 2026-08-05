"""Bucket admin actions must not appear in writer IAM (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"

_ADMIN_ACTIONS = (
    "s3:PutBucketPolicy",
    "s3:PutEncryptionConfiguration",
    "s3:PutLifecycleConfiguration",
    "s3:PutPublicAccessBlock",
    "s3:CreateBucket",
    "s3:DeleteBucket",
    "s3:ListAllMyBuckets",
)


def _iam() -> str:
    return (MODULE / "iam.tf").read_text(encoding="utf-8")


def test_no_bucket_admin_actions_in_writer_iam() -> None:
    iam = _iam()
    for action in _ADMIN_ACTIONS:
        assert action not in iam
