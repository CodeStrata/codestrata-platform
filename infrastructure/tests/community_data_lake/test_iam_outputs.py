"""IAM outputs for community-data-lake (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _outputs() -> str:
    return (MODULE / "outputs.tf").read_text(encoding="utf-8")


def test_writer_policy_outputs_present() -> None:
    outputs = _outputs()
    assert 'output "writer_policy_arn"' in outputs
    assert 'output "writer_policy_name"' in outputs
    assert "aws_iam_policy.writer.arn" in outputs
    assert "aws_iam_policy.writer.name" in outputs


def test_prefix_outputs_present() -> None:
    outputs = _outputs()
    assert 'output "accepted_prefix"' in outputs
    assert 'output "quarantine_prefix"' in outputs
    assert "local.accepted_prefix" in outputs
    assert "local.quarantine_prefix" in outputs


def test_outputs_contain_no_secrets() -> None:
    outputs = _outputs().lower()
    for token in ("secret", "password", "access_key", "private_key"):
        assert token not in outputs
