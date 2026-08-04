"""Full SV.8 integration runner."""

from __future__ import annotations

from pathlib import Path

from verification.website_export.contract import (
    FORBIDDEN_REPORT_FRAGMENTS,
    WEBSITE_EXPORT_VERIFICATION_ID,
)
from verification.website_export.runner import run_website_export_verification


def test_full_runner(tmp_path: Path) -> None:
    report = run_website_export_verification(output_dir=tmp_path)
    assert report.ok
    assert report.verdict == "pass"
    assert report.schema_name == WEBSITE_EXPORT_VERIFICATION_ID
    assert report.source_report_id.startswith("eir:")
    assert report.export_id.startswith("eir-export:")
    assert report.repository_count == 5
    path = tmp_path / "website-export-verification.json"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for frag in FORBIDDEN_REPORT_FRAGMENTS:
        assert frag not in text
