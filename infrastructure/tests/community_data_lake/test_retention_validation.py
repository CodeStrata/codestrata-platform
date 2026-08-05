"""Module-level retention validation checks (Slice 8.10)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _validation() -> str:
    return (MODULE / "validation.tf").read_text(encoding="utf-8")


def test_quarantine_must_be_le_accepted() -> None:
    validation = _validation()
    assert "var.quarantine_retention_days <= var.accepted_retention_days" in validation


def test_retention_bounds_reasserted_in_check_block() -> None:
    validation = _validation()
    assert "var.accepted_retention_days >= 30 && var.accepted_retention_days <= 2555" in validation
    assert (
        "var.quarantine_retention_days >= 7 && var.quarantine_retention_days <= 365"
        in validation
    )
    assert (
        "var.incomplete_multipart_days >= 1 && var.incomplete_multipart_days <= 90"
        in validation
    )
    assert (
        "var.noncurrent_version_expiration_days >= 1 && "
        "var.noncurrent_version_expiration_days <= 2555"
    ) in validation


def test_force_destroy_must_remain_false() -> None:
    assert "var.force_destroy == false" in _validation()
