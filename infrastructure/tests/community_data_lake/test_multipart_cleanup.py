"""Incomplete multipart upload abort rule (Slice 8.10)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _lifecycle() -> str:
    return (MODULE / "lifecycle.tf").read_text(encoding="utf-8")


def test_multipart_abort_rule_id_stable_and_unique() -> None:
    lifecycle = _lifecycle()
    assert 'id     = "abort-incomplete-multipart-uploads"' in lifecycle
    assert lifecycle.count('id     = "abort-incomplete-multipart-uploads"') == 1


def test_multipart_is_separate_empty_filter_rule() -> None:
    lifecycle = _lifecycle()
    start = lifecycle.index('id     = "abort-incomplete-multipart-uploads"')
    end = lifecycle.index('id     = "expire-delete-markers"')
    block = lifecycle[start:end]
    assert "filter {}" in block or "filter {\n    }" in block
    assert "abort_incomplete_multipart_upload" in block
    assert "days_after_initiation = var.incomplete_multipart_days" in block
    assert "local.accepted_prefix" not in block
    assert "local.quarantine_prefix" not in block


def test_multipart_not_duplicated_under_prefix_rules() -> None:
    lifecycle = _lifecycle()
    accepted_start = lifecycle.index('id     = "accepted-retention"')
    quarantine_start = lifecycle.index('id     = "quarantine-retention"')
    multipart_start = lifecycle.index('id     = "abort-incomplete-multipart-uploads"')
    accepted_block = lifecycle[accepted_start:quarantine_start]
    quarantine_block = lifecycle[quarantine_start:multipart_start]
    assert "abort_incomplete_multipart_upload" not in accepted_block
    assert "abort_incomplete_multipart_upload" not in quarantine_block
