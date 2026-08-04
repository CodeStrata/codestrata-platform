"""Full SV.7 integration runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_api.contract import (
    COMMUNITY_CLOUD_API_VERIFICATION_ID,
    FORBIDDEN_REPORT_FRAGMENTS,
)
from verification.community_cloud_api.pipeline import check_pipeline_order
from verification.community_cloud_api.retries import check_endpoint_separation
from verification.community_cloud_api.runner import run_community_cloud_api_verification
from verification.community_cloud_api.scenarios import check_happy_path_ingestion


def test_pipeline_order() -> None:
    results = check_pipeline_order()
    assert results
    assert all(item.ok for item in results), [r for r in results if not r.ok]


def test_happy_path_and_separation(verification_app) -> None:
    happy = check_happy_path_ingestion(verification_app)
    assert all(item.ok for item in happy), [r for r in happy if not r.ok]
    sep = check_endpoint_separation(verification_app)
    assert all(item.ok for item in sep), [r for r in sep if not r.ok]


def test_full_runner(tmp_path: Path) -> None:
    report = run_community_cloud_api_verification(output_dir=tmp_path)
    assert report.ok
    assert report.verdict == "pass"
    assert report.schema_name == COMMUNITY_CLOUD_API_VERIFICATION_ID
    path = tmp_path / "community-cloud-api-verification.json"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for frag in FORBIDDEN_REPORT_FRAGMENTS:
        assert frag not in text
