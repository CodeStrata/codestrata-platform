"""Expired delete-marker lifecycle rule (Slice 8.10)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _lifecycle() -> str:
    return (MODULE / "lifecycle.tf").read_text(encoding="utf-8")


def test_expire_delete_markers_rule_present_and_separate() -> None:
    lifecycle = _lifecycle()
    assert 'id     = "expire-delete-markers"' in lifecycle
    assert "expired_object_delete_marker = true" in lifecycle


def test_delete_marker_rule_is_bucket_wide_empty_filter() -> None:
    lifecycle = _lifecycle()
    start = lifecycle.index('id     = "expire-delete-markers"')
    block = lifecycle[start:]
    assert "filter {}" in block
    assert "local.accepted_prefix" not in block
    assert "local.quarantine_prefix" not in block
    assert "expired_object_delete_marker = true" in block
    # Must not combine expired_object_delete_marker with expiration.days.
    assert "days =" not in block


def test_delete_marker_rule_id_unique() -> None:
    lifecycle = _lifecycle()
    assert lifecycle.count('id     = "expire-delete-markers"') == 1
