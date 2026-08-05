"""Full SV.9 integration runner tests."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake.contract import (
    COMMUNITY_DATA_LAKE_VERIFICATION_ID,
    FORBIDDEN_REPORT_FRAGMENTS,
)
from verification.community_data_lake.runner import run_community_data_lake_verification


def test_full_runner(tmp_path: Path) -> None:
    report = run_community_data_lake_verification(
        output_dir=tmp_path,
        run_opentofu=False,
    )
    assert report.ok
    assert report.verdict == "pass"
    assert report.schema_name == COMMUNITY_DATA_LAKE_VERIFICATION_ID
    assert report.quarantine_tested
    assert len(report.streams_tested) == 5
    path = tmp_path / "community-data-lake-verification.json"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for frag in FORBIDDEN_REPORT_FRAGMENTS:
        assert frag not in text
