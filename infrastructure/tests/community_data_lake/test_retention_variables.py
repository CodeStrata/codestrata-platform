"""Retention variable defaults and bounds (Slice 8.10)."""

from __future__ import annotations

import re
from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _variables() -> str:
    return (MODULE / "variables.tf").read_text(encoding="utf-8")


def _variable_block(name: str) -> str:
    match = re.search(
        rf'variable\s+"{re.escape(name)}"\s*\{{(.*?)\n\}}',
        _variables(),
        flags=re.DOTALL,
    )
    assert match is not None, name
    return match.group(1)


def test_retention_defaults() -> None:
    assert "default     = 365" in _variable_block("accepted_retention_days")
    assert "default     = 90" in _variable_block("quarantine_retention_days")
    assert "default     = 7" in _variable_block("incomplete_multipart_days")
    assert "default     = 30" in _variable_block("noncurrent_version_expiration_days")
    assert "default     = false" in _variable_block("force_destroy")


def test_retention_bounds_in_variable_validation() -> None:
    accepted = _variable_block("accepted_retention_days")
    assert ">= 30" in accepted and "<= 2555" in accepted
    quarantine = _variable_block("quarantine_retention_days")
    assert ">= 7" in quarantine and "<= 365" in quarantine
    multipart = _variable_block("incomplete_multipart_days")
    assert ">= 1" in multipart and "<= 90" in multipart
    noncurrent = _variable_block("noncurrent_version_expiration_days")
    assert ">= 1" in noncurrent and "<= 2555" in noncurrent


def test_quarantine_description_notes_le_accepted() -> None:
    quarantine = _variable_block("quarantine_retention_days")
    assert "less than or equal to accepted_retention_days" in quarantine
