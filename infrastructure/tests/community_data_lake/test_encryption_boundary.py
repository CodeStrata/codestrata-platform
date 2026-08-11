"""Encryption architecture boundary (Slice 8.11)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
LAKE_MODULE = INFRA / "modules" / "community-data-lake"
API_MODULE = INFRA / "modules" / "community-cloud-api"


def _blob(module: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in module.glob("*.tf"))


def test_encryption_tf_present_and_single_sse_resource() -> None:
    encryption = (LAKE_MODULE / "encryption.tf").read_text(encoding="utf-8")
    assert encryption.count('resource "aws_s3_bucket_server_side_encryption_configuration"') == 1


def test_single_data_lake_bucket_remains() -> None:
    blob = _blob(LAKE_MODULE)
    assert blob.count('resource "aws_s3_bucket" ') == 1


def test_community_cloud_api_module_unaffected_by_data_lake_encryption() -> None:
    blob = _blob(API_MODULE)
    assert "community-data-lake" not in blob
    assert "community_data_lake" not in blob
    assert "sse_s3" not in blob


def test_enable_ingestion_wire_defaults_false() -> None:
    variables = (LAKE_MODULE / "variables.tf").read_text(encoding="utf-8")
    assert "default     = false" in variables or "default = false" in variables


def test_encryption_mode_output_is_mode_string_not_key() -> None:
    outputs = (LAKE_MODULE / "outputs.tf").read_text(encoding="utf-8")
    assert 'output "encryption_mode"' in outputs
    assert "value       = var.encryption_mode" in outputs
    assert "kms" not in outputs.lower()
