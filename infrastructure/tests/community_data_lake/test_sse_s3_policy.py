"""SSE-S3-only encryption mode policy in HCL (Slice 8.11)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def test_encryption_mode_variable_constrained_to_sse_s3() -> None:
    variables = (MODULE / "variables.tf").read_text(encoding="utf-8")
    assert 'variable "encryption_mode"' in variables
    assert 'default     = "sse_s3"' in variables or 'default = "sse_s3"' in variables
    assert 'condition     = var.encryption_mode == "sse_s3"' in variables


def test_validation_tf_reasserts_sse_s3() -> None:
    validation = (MODULE / "validation.tf").read_text(encoding="utf-8")
    assert 'var.encryption_mode == "sse_s3"' in validation
    assert "SSE-KMS" in validation or "sse_kms" in validation.lower()


def test_encryption_tf_documents_sse_s3_only() -> None:
    encryption = (MODULE / "encryption.tf").read_text(encoding="utf-8")
    assert "SSE-S3" in encryption or "AES256" in encryption
    assert "sse_s3" in encryption
    assert 'resource "aws_kms_' not in encryption
    assert 'sse_algorithm = "AES256"' in encryption
