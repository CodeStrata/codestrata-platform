"""Quarantine-prefix IAM permissions (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _iam() -> str:
    return (MODULE / "iam.tf").read_text(encoding="utf-8")


def _statement_block(iam: str, sid: str) -> str:
    marker = f'sid    = "{sid}"'
    start = iam.index(marker)
    brace_start = iam.rfind("statement {", 0, start)
    assert brace_start != -1, sid
    depth = 0
    for i in range(brace_start, len(iam)):
        if iam[i : i + 1] == "{":
            depth += 1
        elif iam[i : i + 1] == "}":
            depth -= 1
            if depth == 0:
                return iam[brace_start : i + 1]
    raise AssertionError(f"unclosed statement for {sid}")


def test_write_quarantine_records_put_scoped_to_quarantine_prefix() -> None:
    block = _statement_block(_iam(), "WriteQuarantineRecords")
    assert 'effect = "Allow"' in block
    assert "s3:PutObject" in block
    assert "local.quarantine_prefix" in block
    assert "local.accepted_prefix" not in block


def test_verify_quarantine_records_get_scoped_to_quarantine_prefix() -> None:
    block = _statement_block(_iam(), "VerifyQuarantineRecords")
    assert 'effect = "Allow"' in block
    assert "s3:GetObject" in block
    assert "local.quarantine_prefix" in block
    assert "local.accepted_prefix" not in block


def test_deny_quarantine_object_deletion_scoped_to_quarantine_prefix() -> None:
    block = _statement_block(_iam(), "DenyQuarantineObjectDeletion")
    assert 'effect = "Deny"' in block
    assert "s3:DeleteObject" in block
    assert "s3:DeleteObjectVersion" in block
    assert "local.quarantine_prefix" in block
    assert "local.accepted_prefix" not in block
