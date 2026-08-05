"""KMS must not be operational in the community-data-lake module (Slice 8.11)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"
PRODUCTION = INFRA / "production"


def _module_blob() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in MODULE.glob("*.tf"))


def test_no_aws_kms_resources_in_module() -> None:
    blob = _module_blob()
    assert 'resource "aws_kms_key"' not in blob
    assert 'resource "aws_kms_alias"' not in blob
    assert 'resource "aws_kms_grant"' not in blob
    assert 'resource "aws_kms_' not in blob


def test_no_kms_iam_permissions() -> None:
    iam = (MODULE / "iam.tf").read_text(encoding="utf-8").lower()
    assert "kms:" not in iam
    assert '"kms:encrypt"' not in iam
    assert '"kms:decrypt"' not in iam
    assert '"kms:generatedatakey"' not in iam


def test_no_kms_key_outputs() -> None:
    outputs = (MODULE / "outputs.tf").read_text(encoding="utf-8").lower()
    assert "kms" not in outputs
    assert "key_arn" not in outputs
    assert "key_id" not in outputs


def test_production_root_does_not_introduce_kms_for_data_lake() -> None:
    lake_tf = PRODUCTION / "community-data-lake.tf"
    text = lake_tf.read_text(encoding="utf-8") if lake_tf.is_file() else ""
    assert 'resource "aws_kms_' not in text
    assert "kms_master_key_id" not in text.lower()
