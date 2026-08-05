"""Encryption variable defaults (Slice 8.11)."""

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


def test_encryption_mode_default_is_sse_s3() -> None:
    block = _variable_block("encryption_mode")
    assert 'default     = "sse_s3"' in block or 'default = "sse_s3"' in block


def test_encryption_mode_description_notes_kms_deferred() -> None:
    block = _variable_block("encryption_mode")
    lower = block.lower()
    assert "sse-s3" in lower or "aes256" in lower
    assert "kms" in lower or "future" in lower


def test_no_kms_key_id_variable() -> None:
    variables = _variables().lower()
    assert 'variable "kms_key' not in variables
    assert 'variable "kms_master_key' not in variables
    assert 'variable "bucket_key_enabled"' not in variables
