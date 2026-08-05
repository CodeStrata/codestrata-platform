"""Quarantine IAM assertions for community-data-lake (Slice 8.9).

Reaffirms Put/Get prefix scope, no DeleteObject allow, and unattached policy.
No HCL changes expected for this slice.
"""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _iam() -> str:
    return (MODULE / "iam.tf").read_text(encoding="utf-8")


def test_writer_policy_put_get_scoped_to_quarantine_prefix() -> None:
    iam = _iam()
    assert "s3:PutObject" in iam
    assert "s3:GetObject" in iam
    assert "local.quarantine_prefix" in iam


def test_no_delete_object_allow_on_quarantine() -> None:
    iam = _iam()
    # DeleteObject may appear only in Deny statements.
    lines = [line.strip() for line in iam.splitlines()]
    for i, line in enumerate(lines):
        if "s3:DeleteObject" in line:
            window = "\n".join(lines[max(0, i - 8) : i + 1])
            assert 'effect = "Deny"' in window or "Effect" in window


def test_writer_policy_remains_unattached() -> None:
    blob = "\n".join(p.read_text(encoding="utf-8") for p in MODULE.glob("*.tf"))
    assert 'resource "aws_iam_role"' not in blob
    assert "aws_iam_role_policy_attachment" not in blob
    assert "aws_lambda_function" not in blob
