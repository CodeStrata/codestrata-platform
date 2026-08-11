"""Writer IAM policy statement checks (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _iam() -> str:
    return (MODULE / "iam.tf").read_text(encoding="utf-8")


def test_all_writer_sids_present() -> None:
    iam = _iam()
    expected = (
        "WriteAcceptedRawObjects",
        "WriteQuarantineRecords",
        "VerifyAcceptedRawObjects",
        "VerifyQuarantineRecords",
        "DenyAcceptedObjectDeletion",
        "DenyQuarantineObjectDeletion",
    )
    for sid in expected:
        assert f'sid    = "{sid}"' in iam


def test_put_and_get_actions_present() -> None:
    iam = _iam()
    assert "s3:PutObject" in iam
    assert "s3:GetObject" in iam


def test_list_bucket_is_prefix_scoped() -> None:
    iam = _iam()
    assert "s3:ListBucket" in iam
    assert "ListApprovedWriterPrefixes" in iam
    assert "s3:prefix" in iam
    assert "s3:ListAllMyBuckets" not in iam


def test_no_bucket_admin_actions() -> None:
    iam = _iam()
    for action in (
        "s3:PutBucketPolicy",
        "s3:PutEncryptionConfiguration",
        "s3:PutLifecycleConfiguration",
        "s3:PutPublicAccessBlock",
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:ListAllMyBuckets",
    ):
        assert action not in iam
