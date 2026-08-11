"""Module-level encryption validation checks (Slice 8.11)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _validation() -> str:
    return (MODULE / "validation.tf").read_text(encoding="utf-8")


def test_encryption_mode_must_be_sse_s3() -> None:
    assert 'var.encryption_mode == "sse_s3"' in _validation()


def test_encryption_validation_error_message_mentions_future_kms() -> None:
    validation = _validation()
    assert "encryption_mode must be sse_s3" in validation
    assert "future" in validation.lower() or "SSE-KMS" in validation


def test_encryption_validation_does_not_force_ingestion_wire_off() -> None:
    assert "var.enable_ingestion_wire == false" not in _validation()
    assert 'var.encryption_mode == "sse_s3"' in _validation()
