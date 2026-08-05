"""Delete deny posture for writer IAM (Slice 8.12)."""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _iam() -> str:
    return (MODULE / "iam.tf").read_text(encoding="utf-8")


def test_deny_accepted_and_quarantine_deletion_sids_present() -> None:
    iam = _iam()
    assert "DenyAcceptedObjectDeletion" in iam
    assert "DenyQuarantineObjectDeletion" in iam


def test_no_allow_delete_object_anywhere() -> None:
    iam = _iam()
    lines = iam.splitlines()
    in_allow = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("effect"):
            in_allow = '"Allow"' in stripped
        if in_allow and ("DeleteObject" in stripped or "DeleteObjectVersion" in stripped):
            raise AssertionError(f"Allow DeleteObject found: {stripped}")


def test_delete_actions_only_in_deny_statements() -> None:
    iam = _iam()
    for sid in ("DenyAcceptedObjectDeletion", "DenyQuarantineObjectDeletion"):
        marker = f'sid    = "{sid}"'
        start = iam.index(marker)
        window = iam[max(0, start - 120) : start + 400]
        assert 'effect = "Deny"' in window
        assert "s3:DeleteObject" in window
        assert "s3:DeleteObjectVersion" in window
