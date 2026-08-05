"""Quarantine lifecycle retention rule (Slice 8.10)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _lifecycle() -> str:
    return (MODULE / "lifecycle.tf").read_text(encoding="utf-8")


def _variables() -> str:
    return (MODULE / "variables.tf").read_text(encoding="utf-8")


def test_quarantine_retention_rule_id_stable() -> None:
    assert 'id     = "quarantine-retention"' in _lifecycle()


def test_quarantine_rule_uses_quarantine_prefix_only() -> None:
    lifecycle = _lifecycle()
    start = lifecycle.index('id     = "quarantine-retention"')
    end = lifecycle.index('id     = "abort-incomplete-multipart-uploads"')
    block = lifecycle[start:end]
    assert "prefix = local.quarantine_prefix" in block
    assert "local.accepted_prefix" not in block
    assert "days = var.quarantine_retention_days" in block
    assert "noncurrent_days = var.noncurrent_version_expiration_days" in block


def test_quarantine_retention_default_ninety_days() -> None:
    variables = _variables()
    assert 'variable "quarantine_retention_days"' in variables
    assert "default     = 90" in variables


def test_quarantine_rule_has_no_storage_class_transition() -> None:
    lifecycle = _lifecycle()
    start = lifecycle.index('id     = "quarantine-retention"')
    end = lifecycle.index('id     = "abort-incomplete-multipart-uploads"')
    block = lifecycle[start:end].lower()
    assert "transition" not in block
    assert "glacier" not in block
