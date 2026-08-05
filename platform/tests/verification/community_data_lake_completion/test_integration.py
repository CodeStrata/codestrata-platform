"""Full Slice 8.15 completion runner integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from verification.community_data_lake.contract import COMMUNITY_DATA_LAKE_VERIFICATION_ID
from verification.community_data_lake_completion.contract import (
    COMMUNITY_DATA_LAKE_COMPLETION_ID,
    FORBIDDEN_REPORT_FRAGMENTS,
    INTEGRATION_REPORT_FILENAME,
)
from verification.community_data_lake_completion.runner import (
    run_community_data_lake_completion_verification,
)

REPO = Path(__file__).resolve().parents[4]
DEFAULT_INTEGRATION_REPORT = (
    REPO / "platform" / "reports" / "verification" / INTEGRATION_REPORT_FILENAME
)


def test_full_runner(tmp_path: Path) -> None:
    integration_report = DEFAULT_INTEGRATION_REPORT
    if not integration_report.is_file():
        pytest.skip("SV.9 integration report not present; run SV.9 first")

    (tmp_path / INTEGRATION_REPORT_FILENAME).write_text(
        integration_report.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    report = run_community_data_lake_completion_verification(
        output_dir=tmp_path,
        run_opentofu=False,
        run_integration=False,
    )
    assert report.ok
    assert report.verdict == "pass"
    assert report.schema_name == COMMUNITY_DATA_LAKE_COMPLETION_ID
    assert report.integration_check_count > 0
    assert report.production_wiring_status == "disabled"
    path = tmp_path / "community-data-lake-completion-verification.json"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for frag in FORBIDDEN_REPORT_FRAGMENTS:
        assert frag not in text


def test_runner_can_execute_sv9_when_requested(tmp_path: Path) -> None:
    report = run_community_data_lake_completion_verification(
        output_dir=tmp_path,
        run_opentofu=False,
        run_integration=True,
    )
    assert report.ok
    assert (tmp_path / INTEGRATION_REPORT_FILENAME).is_file()
    assert report.integration_check_count > 0
