"""Static reconciliation: Platform access policy vs OpenTofu HCL (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

from codestrata_platform.community_cloud_api.data_lake.access_policy import (
    default_access_policy,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
MODULE = REPO_ROOT / "infrastructure" / "modules" / "community-data-lake"
API_MODULE = REPO_ROOT / "infrastructure" / "modules" / "community-cloud-api"
PRODUCTION = REPO_ROOT / "infrastructure" / "production"
S3_STORE = (
    REPO_ROOT
    / "platform"
    / "src"
    / "codestrata_platform"
    / "community_cloud_api"
    / "data_lake"
    / "infrastructure"
    / "s3_store.py"
)


def _read(module: Path, name: str) -> str:
    return (module / name).read_text(encoding="utf-8")


def _module_blob(module: Path = MODULE) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in module.glob("*.tf"))


def test_put_object_sids_present_for_raw_and_quarantine() -> None:
    iam = _read(MODULE, "iam.tf")
    assert 'sid    = "WriteAcceptedRawObjects"' in iam
    assert 'sid    = "WriteQuarantineRecords"' in iam
    assert "s3:PutObject" in iam
    assert "local.accepted_prefix" in iam
    assert "local.quarantine_prefix" in iam


def test_get_object_sids_present_for_raw_and_quarantine() -> None:
    iam = _read(MODULE, "iam.tf")
    assert 'sid    = "VerifyAcceptedRawObjects"' in iam
    assert 'sid    = "VerifyQuarantineRecords"' in iam
    assert "s3:GetObject" in iam


def test_deny_delete_on_both_prefixes() -> None:
    iam = _read(MODULE, "iam.tf")
    assert 'sid    = "DenyAcceptedObjectDeletion"' in iam
    assert 'sid    = "DenyQuarantineObjectDeletion"' in iam
    assert "s3:DeleteObject" in iam
    assert "s3:DeleteObjectVersion" in iam


def test_no_list_bucket_or_list_all_my_buckets_in_iam() -> None:
    iam = _read(MODULE, "iam.tf").lower()
    assert "s3:listbucket" not in iam
    assert "s3:listallmybuckets" not in iam


def test_no_kms_in_iam() -> None:
    iam = _read(MODULE, "iam.tf").lower()
    assert "kms:" not in iam


def test_no_wildcard_resource_in_iam() -> None:
    iam = _read(MODULE, "iam.tf")
    assert 'resources = ["*"]' not in iam
    assert 'Resource = ["*"]' not in iam


def test_s3_store_uses_put_object_and_head_object_only() -> None:
    source = S3_STORE.read_text(encoding="utf-8")
    assert "put_object" in source
    assert "head_object" in source
    assert "list_objects" not in source
    assert "delete_object" not in source


def test_production_enable_ingestion_wire_false() -> None:
    text = _read(PRODUCTION, "community-data-lake.tf")
    assert "enable_ingestion_wire = false" in text


def test_community_cloud_api_has_no_s3_or_data_lake() -> None:
    blob = _module_blob(API_MODULE)
    assert "s3:" not in blob.lower()
    assert "community-data-lake" not in blob
    assert "community_data_lake" not in blob


def test_no_writer_policy_attachment_in_lake_module() -> None:
    blob = _module_blob(MODULE)
    assert "aws_iam_role_policy_attachment" not in blob
    assert 'resource "aws_iam_role"' not in blob


def test_platform_writer_policy_attached_is_false() -> None:
    policy = default_access_policy()
    assert policy.writer_policy_attached is False


def test_bucket_policy_has_deny_insecure_transport() -> None:
    bucket_policy = _read(MODULE, "bucket_policy.tf")
    assert "DenyInsecureTransport" in bucket_policy
    assert "aws:SecureTransport" in bucket_policy


def test_future_analytics_must_not_auto_include_quarantine() -> None:
    policy = default_access_policy()
    assert policy.analytics_quarantine_separated is True
    assert "analytics_must_not_auto_include_quarantine" in policy.limitations


def test_platform_allowed_actions_match_iam_put_get() -> None:
    policy = default_access_policy()
    assert policy.writer_allowed_actions == frozenset({"s3:PutObject", "s3:GetObject"})
    iam = _read(MODULE, "iam.tf")
    for action in ("s3:PutObject", "s3:GetObject"):
        assert action in iam


def test_no_data_lake_env_vars_in_community_cloud_api_lambda() -> None:
    lambda_tf = _read(API_MODULE, "lambda.tf")
    assert "DATA_LAKE" not in lambda_tf
    config = _read(API_MODULE, "configuration.tf")
    assert "DATA_LAKE" not in config


def test_writer_policy_name_output_present() -> None:
    outputs = _read(MODULE, "outputs.tf")
    assert 'output "writer_policy_name"' in outputs
    assert "aws_iam_policy.writer.name" in outputs
