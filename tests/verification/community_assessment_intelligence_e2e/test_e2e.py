"""Pytest wrapper for Slice 20.11 verification evidence."""

from __future__ import annotations

from pathlib import Path

from verification.community_assessment_intelligence_e2e.evidence import (
    build_evidence_report,
    write_report,
)


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_slice_20_11_evidence_matrix_pass() -> None:
    report = build_evidence_report()
    assert report.verdict == "PASS"
    reqs = {row.requirement for row in report.rows}
    for req in (
        "R1",
        "R2",
        "R3",
        "R4",
        "R5",
        "R6",
        "R7",
        "R8",
        "R9",
        "R10",
        "R11",
        "R12",
        "R13",
        "R14",
        "R15",
    ):
        assert req in reqs
    assert all(row.status == "PASS" for row in report.rows)


def test_slice_20_11_writes_artifact() -> None:
    report = write_report(_root())
    path = (
        _root()
        / ".codestrata-artifacts/validation/suites/sv20-11"
        / "community-assessment-intelligence-e2e.json"
    )
    assert path.is_file()
    assert report.verdict == "PASS"
