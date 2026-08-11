"""IAM least-privilege checks for the community-data-lake writer policy (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _iam() -> str:
    return (MODULE / "iam.tf").read_text(encoding="utf-8")


def test_writer_policy_document_present() -> None:
    iam = _iam()
    assert 'data "aws_iam_policy_document" "writer_policy"' in iam
    assert 'resource "aws_iam_policy" "writer"' in iam


def test_writer_policy_sids_are_stable() -> None:
    iam = _iam()
    for sid in (
        "WriteAcceptedRawObjects",
        "WriteQuarantineRecords",
        "VerifyAcceptedRawObjects",
        "VerifyQuarantineRecords",
        "DenyAcceptedObjectDeletion",
        "DenyQuarantineObjectDeletion",
    ):
        assert f'sid    = "{sid}"' in iam


def test_writer_policy_allows_put_object_on_raw_and_quarantine() -> None:
    iam = _iam()
    assert "s3:PutObject" in iam
    assert "local.accepted_prefix" in iam
    assert "local.quarantine_prefix" in iam


def test_writer_policy_allows_get_object_for_verification() -> None:
    iam = _iam()
    assert "s3:GetObject" in iam


def test_deny_delete_object_on_raw_and_quarantine() -> None:
    iam = _iam()
    assert 'effect = "Deny"' in iam
    assert "s3:DeleteObject" in iam
    assert "s3:DeleteObjectVersion" in iam
    assert "DenyAcceptedObjectDeletion" in iam
    assert "DenyQuarantineObjectDeletion" in iam


def test_list_bucket_is_prefix_scoped_and_list_all_my_buckets_absent() -> None:
    iam = _iam()
    iam_lower = iam.lower()
    assert "s3:ListBucket" in iam
    assert "ListApprovedWriterPrefixes" in iam
    assert "s3:prefix" in iam
    assert "s3:listallmybuckets" not in iam_lower


def test_no_admin_wildcard_resource_for_s3() -> None:
    iam = _iam()
    assert 'actions = ["*"]' not in iam
    assert 'Action = "*"' not in iam
    assert 'resources = ["*"]' not in iam


def test_no_role_created_or_attached() -> None:
    blob = "\n".join(p.read_text(encoding="utf-8") for p in MODULE.glob("*.tf"))
    assert 'resource "aws_iam_role"' not in blob
    assert "aws_iam_role_policy_attachment" not in blob
    assert "aws_lambda_function" not in blob
