"""No wildcard S3 resources or actions in writer IAM (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _iam() -> str:
    return (MODULE / "iam.tf").read_text(encoding="utf-8")


def test_no_wildcard_resource_in_iam() -> None:
    iam = _iam()
    assert 'resources = ["*"]' not in iam
    assert 'Resource = ["*"]' not in iam


def test_no_s3_wildcard_action_in_writer_iam() -> None:
    iam = _iam()
    assert '"s3:*"' not in iam
    assert "s3:*" not in iam.replace('"', "")
