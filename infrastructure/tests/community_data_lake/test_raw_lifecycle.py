"""Accepted (raw/) lifecycle retention rule (Slice 8.10)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _lifecycle() -> str:
    return (MODULE / "lifecycle.tf").read_text(encoding="utf-8")


def test_accepted_retention_rule_id_stable() -> None:
    assert 'id     = "accepted-retention"' in _lifecycle()


def test_accepted_rule_uses_accepted_prefix_only() -> None:
    lifecycle = _lifecycle()
    # Extract the accepted-retention rule block roughly by slicing between rule ids.
    start = lifecycle.index('id     = "accepted-retention"')
    end = lifecycle.index('id     = "quarantine-retention"')
    block = lifecycle[start:end]
    assert "prefix = local.accepted_prefix" in block
    assert "local.quarantine_prefix" not in block
    assert "days = var.accepted_retention_days" in block
    assert "noncurrent_days = var.noncurrent_version_expiration_days" in block


def test_accepted_rule_has_no_storage_class_transition() -> None:
    lifecycle = _lifecycle()
    start = lifecycle.index('id     = "accepted-retention"')
    end = lifecycle.index('id     = "quarantine-retention"')
    block = lifecycle[start:end].lower()
    assert "transition" not in block
    assert "glacier" not in block
