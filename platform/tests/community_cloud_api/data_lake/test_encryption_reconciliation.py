"""Static reconciliation: Platform encryption vs OpenTofu HCL (Slice 8.11)."""

from __future__ import annotations

import re
from pathlib import Path

from codestrata_platform.community_cloud_api.data_lake.encryption_policy import (
    DEFAULT_ENCRYPTION_MODE,
    SSE_S3_ALGORITHM,
    default_encryption_policy,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
    CommunityDataLakeS3Store,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
MODULE = REPO_ROOT / "infrastructure" / "modules" / "community-data-lake"
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


def _read(name: str) -> str:
    return (MODULE / name).read_text(encoding="utf-8")


def _module_blob() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in MODULE.glob("*.tf"))


def _variable_block(variables: str, name: str) -> str:
    match = re.search(
        rf'variable\s+"{re.escape(name)}"\s*\{{(.*?)\n\}}',
        variables,
        flags=re.DOTALL,
    )
    assert match is not None, f"variable {name} not found"
    return match.group(1)


def test_platform_mode_matches_opentofu_default() -> None:
    policy = default_encryption_policy()
    variables = _read("variables.tf")
    block = _variable_block(variables, "encryption_mode")
    assert 'default     = "sse_s3"' in block or 'default = "sse_s3"' in block
    assert policy.encryption_mode == DEFAULT_ENCRYPTION_MODE == "sse_s3"
    assert 'condition     = var.encryption_mode == "sse_s3"' in block


def test_hcl_aes256_and_bucket_key_disabled() -> None:
    encryption = _read("encryption.tf")
    assert 'sse_algorithm = "AES256"' in encryption
    assert "bucket_key_enabled = false" in encryption
    assert default_encryption_policy().sse_algorithm == SSE_S3_ALGORITHM == "AES256"
    assert default_encryption_policy().bucket_key_enabled is False


def test_no_aws_kms_resources_or_outputs() -> None:
    blob = _module_blob()
    assert 'resource "aws_kms_' not in blob
    assert "kms_master_key_id" not in blob.lower()
    outputs = _read("outputs.tf")
    assert "kms" not in outputs.lower()
    # encryption_mode output is the mode string only, not a key id.
    assert 'output "encryption_mode"' in outputs
    assert "value       = var.encryption_mode" in outputs


def test_no_kms_iam_actions() -> None:
    iam = _read("iam.tf").lower()
    assert "kms:" not in iam
    assert "kmsencrypt" not in iam.replace(":", "")
    assert "kmsdecrypt" not in iam.replace(":", "")


def test_validation_requires_sse_s3_only() -> None:
    validation = _read("validation.tf")
    assert 'var.encryption_mode == "sse_s3"' in validation


def test_adapter_always_sets_aes256() -> None:
    source = S3_STORE.read_text(encoding="utf-8")
    assert 'kwargs["ServerSideEncryption"] = "AES256"' in source
    assert "SSEKMSKeyId" in source  # forbidden check present
    assert "encryption_mode_unsupported" in source
    config = S3DataLakeStoreConfiguration(bucket_name="codestrata-test-lake-bucket")
    assert config.encryption_mode == "sse_s3"
    # Store construction succeeds with default SSE-S3 config.
    assert CommunityDataLakeS3Store is not None


def test_platform_policy_parity_flags_match_intent() -> None:
    policy = default_encryption_policy()
    assert policy.accepted_prefix_encrypted is True
    assert policy.quarantine_prefix_encrypted is True
    assert policy.explicit_put_encryption_required is True
    assert policy.bucket_default_encryption_required is True
    assert policy.kms_key_required is False
