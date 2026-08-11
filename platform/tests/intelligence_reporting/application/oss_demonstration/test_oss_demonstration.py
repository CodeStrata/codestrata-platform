"""Public OSS demonstration report (Slice 6.11) regression tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.intelligence_reporting.application.oss_demonstration import (
    build_oss_demonstration_report,
    default_demo_directory,
    generate_oss_demonstration_artifacts,
    load_oss_demonstration_catalog,
)
from codestrata_platform.intelligence_reporting.application.website_export import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)
from codestrata_platform.intelligence_reporting.application.website_export.manifest import (
    sha256_bytes,
)
from codestrata_platform.intelligence_reporting.application.website_export.validation import (
    validate_html_artifact,
    validate_website_safe_document,
)
from codestrata_platform.intelligence_reporting.domain.enums import ReportScope
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)


DEMO = default_demo_directory()


@pytest.fixture(scope="module")
def demonstration():
    return build_oss_demonstration_report(catalog_path=DEMO / "catalog.json")


def test_catalog_lists_five_public_oss_repositories() -> None:
    catalog = load_oss_demonstration_catalog(DEMO / "catalog.json")
    assert catalog.catalog_id == "public-oss-demonstration-v1"
    assert len(catalog.repositories) == 5
    ids = {item.repository_id for item in catalog.repositories}
    assert ids == {
        "repo:angular-realworld-example-app",
        "repo:bookstack",
        "repo:eshop",
        "repo:full-stack-fastapi-template",
        "repo:spring-petclinic",
    }
    for item in catalog.repositories:
        assert item.source_reference.startswith("https://github.com/")
        assert len(item.pinned_revision) >= 7
        assert (DEMO / item.report_path).is_file()


def test_fixtures_are_schema_1_2() -> None:
    for path in (DEMO / "fixtures").rglob("report.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["schema_version"] == "1.2" == ASSESSMENT_JSON_SCHEMA_VERSION


def test_full_pipeline_populates_sections(demonstration) -> None:
    report = demonstration.report
    assert report.report_scope is ReportScope.PUBLIC_OSS_DATASET
    assert report.schema_version == ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert report.dataset.repository_count == 5
    assert report.technology_distribution.observations
    assert report.capability_comparisons
    assert report.assessment_head_distributions
    assert report.recurring_patterns
    assert report.modernization_observations
    assert len(report.repository_drilldowns) == 5
    assert report.confidence is not None
    assert report.limitations
    assert report.interpretation_policy_bundle_id.startswith("interp-bundle:")
    assert report.methodology.interpretation_policy_bundle_id == (
        report.interpretation_policy_bundle_id
    )


def test_website_export_and_committed_artifacts(demonstration) -> None:
    bundle = demonstration.export_bundle
    assert bundle.document.export_schema_version == WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION
    assert bundle.document.scope == "public_oss"
    assert bundle.document.classification == "Public OSS report"
    validate_website_safe_document(bundle.document, policy=bundle.policy)
    validate_html_artifact(bundle.html_bytes.decode("utf-8"))

    def _stable(doc: dict) -> dict:
        clone = json.loads(json.dumps(doc))
        clone.pop("generated_at", None)
        clone.pop("exported_at", None)
        for item in clone.get("artifacts") or []:
            if isinstance(item, dict) and str(item.get("filename", "")).endswith(".html"):
                item.pop("byte_size", None)
                item.pop("sha256", None)
        return clone

    # ACTIVE_CURRENT_PLATFORM_CONTRACT: JSON/manifest identity after dropping
    # volatile timestamps and HTML digest/size (HTML is structural, not golden bytes).
    for name, payload in (
        ("engineering-intelligence-report.json", bundle.json_bytes),
        ("export-manifest.json", bundle.manifest_bytes),
    ):
        on_disk = json.loads((DEMO / name).read_text(encoding="utf-8"))
        fresh = json.loads(payload.decode("utf-8"))
        assert _stable(on_disk) == _stable(fresh), f"{name} drifted from generator output"
    assert (DEMO / "engineering-intelligence-report.html").is_file()


def test_manifest_digests_and_identities(demonstration) -> None:
    manifest = json.loads(demonstration.export_bundle.manifest_bytes.decode("utf-8"))
    assert manifest["source_report_id"] == demonstration.report.report_id.value
    assert (
        manifest["interpretation_policy_bundle_id"]
        == demonstration.report.interpretation_policy_bundle_id
    )
    assert manifest["export_id"].startswith("eir-export:")
    assert "export-manifest.json" not in {
        item["filename"] for item in manifest["artifacts"]
    }
    by_name = {item["filename"]: item for item in manifest["artifacts"]}
    assert by_name["engineering-intelligence-report.json"]["sha256"] == sha256_bytes(
        demonstration.export_bundle.json_bytes
    )
    assert by_name["engineering-intelligence-report.html"]["sha256"] == sha256_bytes(
        demonstration.export_bundle.html_bytes
    )


def test_determinism(demonstration) -> None:
    again = build_oss_demonstration_report(catalog_path=DEMO / "catalog.json")
    assert again.report.report_id.value == demonstration.report.report_id.value
    assert again.report.dataset.dataset_id.value == (
        demonstration.report.dataset.dataset_id.value
    )
    assert again.export_bundle.document.export_metadata.export_id == (
        demonstration.export_bundle.document.export_metadata.export_id
    )
    assert again.export_bundle.json_bytes == demonstration.export_bundle.json_bytes
    assert again.export_bundle.html_bytes == demonstration.export_bundle.html_bytes
    assert again.export_bundle.manifest_bytes == demonstration.export_bundle.manifest_bytes


def test_website_safety_bytes(demonstration) -> None:
    blob = (
        demonstration.export_bundle.json_bytes
        + demonstration.export_bundle.html_bytes
        + demonstration.export_bundle.manifest_bytes
    ).decode("utf-8")
    for marker in (
        "/Users/",
        "/home/",
        "file://",
        "BEGIN PRIVATE",
        "AKIA",
        "validation/repos/",
    ):
        assert marker not in blob
    # Internal Engine UUID repository identities from manifests must not appear.
    for uuid_fragment in (
        "af4c07cb-225c-4004-bd5a-4affab536a9c",
        "379c5894-9a03-4fe6-86c0-4825b415b826",
        "57467893-5288-45f1-8e94-0c86f079c48f",
        "32f792fa-2547-4ffa-9fa5-52d528972eda",
        "1fceabc5-9238-4656-8085-5d5216a20c40",
    ):
        assert uuid_fragment not in blob
    # Display names are public-safe.
    for name in (
        "spring-petclinic",
        "BookStack",
        "eShop",
        "full-stack-fastapi-template",
        "angular-realworld-example-app",
    ):
        assert name in blob


def test_limitations_disclose_selection_bias(demonstration) -> None:
    statements = " ".join(item.statement.lower() for item in demonstration.report.limitations)
    categories = {item.category.value for item in demonstration.report.limitations}
    assert "non_temporal" in categories or "non-temporal" in statements or "snapshot" in statements
    assert "selection" in statements or "curated" in statements or "validation" in statements


def test_no_ranking_or_roi_language(demonstration) -> None:
    html = demonstration.export_bundle.html_bytes.decode("utf-8").lower()
    assert "league table" not in html
    assert "maturity score" not in html
    assert "health score" not in html
    assert "roi" not in html
    assert "staffing" not in html


def test_generate_writer_round_trip(tmp_path: Path) -> None:
    result = generate_oss_demonstration_artifacts(
        catalog_path=DEMO / "catalog.json",
        output_directory=tmp_path,
        overwrite=True,
    )
    assert (tmp_path / "engineering-intelligence-report.json").is_file()
    assert (tmp_path / "engineering-intelligence-report.html").is_file()
    assert (tmp_path / "export-manifest.json").is_file()
    assert result.write_result is not None
    assert len(result.write_result.artifacts) == 3


def test_schema_constants_unchanged() -> None:
    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
