"""SV.6 integration tests."""

from __future__ import annotations

import os

import pytest

from verification.engineering_intelligence.contract import PREFERRED_FIVE_LANGUAGE_SUBSET
from verification.engineering_intelligence.runner import (
    run_engineering_intelligence_verification,
)
from verification.engineering_intelligence.scenarios import run_offline_scenarios


def test_offline_scenarios_pass() -> None:
    checks = run_offline_scenarios()
    failed = [c.name for c in checks if not c.ok]
    assert not failed, failed


def test_offline_scenarios_only_runner(tmp_path) -> None:
    report = run_engineering_intelligence_verification(
        output_dir=tmp_path,
        offline_scenarios_only=True,
    )
    assert report.ok
    assert report.verdict == "pass"
    assert (tmp_path / "engineering-intelligence-verification.json").is_file()


@pytest.mark.skipif(
    os.environ.get("CODESTRATA_SV6_CATALOG_NETWORK") != "1",
    reason="set CODESTRATA_SV6_CATALOG_NETWORK=1 for five-repo catalog-backed SV.6",
)
def test_five_language_catalog_pipeline(tmp_path) -> None:
    report = run_engineering_intelligence_verification(
        output_dir=tmp_path,
        cache_dir=tmp_path / "cache",
        repository_ids=PREFERRED_FIVE_LANGUAGE_SUBSET,
        with_catalog_network=True,
    )
    assert report.ok, report.defects
    assert report.pipeline is not None
    assert list(report.pipeline.repository_ids) == list(PREFERRED_FIVE_LANGUAGE_SUBSET)
    assert report.pipeline.eir_schema_version == "1.0"
    assert report.pipeline.section_population["repository_drilldowns"] == 5
