"""Analytics vs quarantine IAM separation (Slice 8.12).

No operational analytics reader role/policy exists yet. Future analytics
roles must not auto-include quarantine read access; quarantine GetObject is
only granted to the writer via VerifyQuarantineRecords until a separate
quarantine-reader role is explicitly reviewed and approved.
"""

from __future__ import annotations

from pathlib import Path

INFRA = Path(__file__).resolve().parents[2]
MODULE = INFRA / "modules" / "community-data-lake"


def _module_blob() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in MODULE.glob("*.tf"))


def test_no_analytics_reader_role_or_policy_exists() -> None:
    blob = _module_blob().lower()
    assert "analytics" not in blob
    assert 'resource "aws_iam_role"' not in blob


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


def test_quarantine_get_only_in_verify_quarantine_records() -> None:
    iam = (MODULE / "iam.tf").read_text(encoding="utf-8")
    block = _statement_block(iam, "VerifyQuarantineRecords")
    assert "s3:GetObject" in block
    assert "local.quarantine_prefix" in block
    get_sids_with_quarantine = []
    for sid in (
        "WriteAcceptedRawObjects",
        "WriteQuarantineRecords",
        "VerifyAcceptedRawObjects",
        "VerifyQuarantineRecords",
        "DenyAcceptedObjectDeletion",
        "DenyQuarantineObjectDeletion",
    ):
        statement = _statement_block(iam, sid)
        if "s3:GetObject" in statement and "local.quarantine_prefix" in statement:
            get_sids_with_quarantine.append(sid)
    assert get_sids_with_quarantine == ["VerifyQuarantineRecords"]
