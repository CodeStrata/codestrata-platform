"""Safety scan tests."""

from __future__ import annotations

from verification.release_artifacts.models import Sv16VerificationReport
from verification.release_artifacts.safety import scan_text_for_safety


def test_redacted_text_allowed() -> None:
    assert not scan_text_for_safety("path=[REDACTED] secret=[REDACTED]")


def test_aws_key_detected() -> None:
    hits = scan_text_for_safety("key=AKIA0000000000000001")
    assert hits


def test_local_user_path_detected() -> None:
    hits = scan_text_for_safety("file=/Users/alice/project/foo.py")
    assert hits


def test_report_to_dict_sanitizes_paths() -> None:
    report = Sv16VerificationReport(
        schema_name="release-artifact-verification",
        schema_version="1.0.0",
        verification_id="sv16-release-artifact-verification",
        verdict="PASS",
        intended_release_version="0.2.0",
        repository_count=22,
        limitations=["/Users/tester/local/path"],
    )
    payload = report.to_dict()
    assert "/Users/tester" not in str(payload)
    assert "[REDACTED_PATH]" in str(payload)
