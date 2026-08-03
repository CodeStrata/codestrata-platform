"""Projection, schema, identity, section, and JSON tests."""

from __future__ import annotations

import json

import pytest

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.website_export import (
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
    ExportScope,
    RepositoryIdentityPolicy,
    WebsiteExportBuildPolicy,
    build_export_id,
    build_website_safe_export,
    project_website_safe_export,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    ReportScope,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
)
from tests.intelligence_reporting.application.website_export.conftest import prepare_export


def test_projection_allowlist_and_schema() -> None:
    _, _, _, report, bundle, policy = prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        )
    )
    doc = bundle.document
    assert doc.export_schema_version == WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
    assert doc.report_schema_version == ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION
    assert doc.report_id == report.report_id.value
    assert doc.export_metadata is not None
    assert doc.export_metadata.export_policy_id == policy.policy_token
    assert doc.export_metadata.interpretation_policy_bundle_id == (
        report.interpretation_policy_bundle_id
    )
    payload = json.loads(bundle.json_bytes.decode("utf-8"))
    assert "diagnostics" not in payload
    assert "generated_artifact_metadata" not in payload
    assert payload["export_schema_version"] == "1.0"


def test_anonymized_aliases_stable_and_hide_original_ids() -> None:
    _, _, _, report, bundle, _ = prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        )
    )
    blob = bundle.json_bytes.decode("utf-8") + bundle.html_bytes.decode("utf-8")
    for repository_id in report.dataset.included_repository_ids:
        assert repository_id not in blob
    aliases = [alias for alias, _ in bundle.document.repository_population]
    assert aliases
    assert all(alias.startswith("repository-") for alias in aliases)
    # Stable across rebuild
    again = build_website_safe_export(
        report,
        policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        ),
    )
    assert again.json_bytes == bundle.json_bytes


def test_private_export_labeled_non_public() -> None:
    _, _, _, _, bundle, _ = prepare_export(
        scope=ReportScope.CUSTOMER_PORTFOLIO,
        visibility=DataVisibility.CUSTOMER_PRIVATE,
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.CUSTOMER_PRIVATE,
            repository_identity_policy=RepositoryIdentityPolicy.PRIVATE_DISPLAY_ALLOWED,
        ),
    )
    assert "not for public" in bundle.document.classification.lower()
    assert bundle.document.scope == ExportScope.CUSTOMER_PRIVATE.value


def test_scope_mismatch_rejected() -> None:
    _, _, _, report, _, _ = prepare_export()
    with pytest.raises(InvalidValueError, match="incompatible"):
        project_website_safe_export(
            report,
            policy=WebsiteExportBuildPolicy(
                export_scope=ExportScope.PUBLIC_OSS,
                repository_identity_policy=RepositoryIdentityPolicy.PUBLIC_WHEN_PERMITTED,
            ),
        )


def test_technology_and_capability_factual() -> None:
    _, _, _, _, bundle, _ = prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        )
    )
    html = bundle.html_bytes.decode("utf-8").lower()
    assert "lifecycle support claims" in html
    assert "league table" not in html
    assert "industry benchmarks" in html
    assert "composite portfolio scores" in html
    assert "health score" not in html
    assert "maturity score" not in html
    for row in bundle.document.technology_distribution:
        assert row.repository_count >= 0
        assert row.denominator >= 0


def test_patterns_and_observations_safe() -> None:
    _, _, _, _, bundle, _ = prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        )
    )
    for pattern in bundle.document.recurring_patterns:
        assert pattern.statement
        assert not hasattr(pattern, "severity")
    for observation in bundle.document.modernization_observations:
        assert "portfolio recommendation" in observation.observation_label.lower()
    html = bundle.html_bytes.decode("utf-8").lower()
    assert "roi" not in html
    assert "staffing" not in html


def test_confidence_disclaimer_no_gauge() -> None:
    _, _, _, _, bundle, _ = prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        )
    )
    assert bundle.document.confidence is not None
    assert "accuracy percentage" in bundle.document.confidence.disclaimer.lower()
    html = bundle.html_bytes.decode("utf-8").lower()
    assert "progress" not in html or "progress bar" not in html
    assert "precision" not in html
    assert "recall" not in html


def test_json_sorted_keys_stable_no_nan() -> None:
    _, _, _, report, bundle, policy = prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        )
    )
    again = build_website_safe_export(report, policy=policy)
    assert again.json_bytes == bundle.json_bytes
    text = bundle.json_bytes.decode("utf-8")
    assert "NaN" not in text
    assert "Infinity" not in text
    payload = json.loads(text)
    assert list(payload.keys()) == sorted(payload.keys())


def test_export_id_deterministic_and_policy_sensitive() -> None:
    left = build_export_id(
        source_report_id="eir:abc",
        interpretation_policy_bundle_id="interp-bundle:x",
        export_policy_token="website-export:v1:a",
        export_schema_version="1.0",
        artifact_template_version="eir-export-artifacts-v1",
    )
    right = build_export_id(
        source_report_id="eir:abc",
        interpretation_policy_bundle_id="interp-bundle:x",
        export_policy_token="website-export:v1:a",
        export_schema_version="1.0",
        artifact_template_version="eir-export-artifacts-v1",
    )
    assert left == right
    assert left.startswith("eir-export:")
    changed = build_export_id(
        source_report_id="eir:abc",
        interpretation_policy_bundle_id="interp-bundle:x",
        export_policy_token="website-export:v1:b",
        export_schema_version="1.0",
        artifact_template_version="eir-export-artifacts-v1",
    )
    assert changed != left


def test_changed_export_policy_changes_report_and_export_identity() -> None:
    result, aggregation, _, report, bundle, _ = prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
            policy_version="v1",
        )
    )
    from codestrata_platform.intelligence_reporting.application.report_quality import (
        populate_report_quality,
    )
    from codestrata_platform.intelligence_reporting.application.repository_drilldowns import (
        populate_report_repository_drilldowns,
    )
    from codestrata_platform.intelligence_reporting.domain.report import (
        EngineeringIntelligenceReport,
    )

    base = EngineeringIntelligenceReport.create(
        title=report.title,
        report_scope=report.report_scope,
        dataset=result.dataset,
        technology_distribution=report.technology_distribution,
        capability_comparisons=report.capability_comparisons,
        recurring_patterns=report.recurring_patterns,
        assessment_head_distributions=report.assessment_head_distributions,
        modernization_observations=report.modernization_observations,
        confidence=report.confidence,
        limitations=report.limitations,
    )
    altered_policy = WebsiteExportBuildPolicy(
        export_scope=ExportScope.ANONYMIZED_EXTERNAL,
        repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        policy_version="v2",
    )
    with_quality = populate_report_quality(
        base, aggregation, website_export_policy=altered_policy
    )
    with_drilldowns = populate_report_repository_drilldowns(with_quality, aggregation)
    altered = build_website_safe_export(with_drilldowns, policy=altered_policy)
    assert with_quality.interpretation_policy_bundle_id != (
        report.interpretation_policy_bundle_id
    )
    assert with_quality.report_id.value != report.report_id.value
    assert altered.document.export_metadata is not None
    assert bundle.document.export_metadata is not None
    assert (
        altered.document.export_metadata.export_id
        != bundle.document.export_metadata.export_id
    )
    assert result.dataset.dataset_id.value == report.dataset.dataset_id.value


def test_empty_sections_factual() -> None:
    _, _, _, _, bundle, _ = prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        )
    )
    html = bundle.html_bytes.decode("utf-8")
    notes = " ".join(bundle.document.empty_section_notes).lower()
    assert "no risk" not in notes
    assert "healthy" not in notes
    if not bundle.document.recurring_patterns:
        assert "multi-repository threshold" in html
    if not bundle.document.modernization_observations:
        assert "deterministic support policy" in html


def test_drilldowns_bounded() -> None:
    _, _, _, _, bundle, _ = prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
            maximum_finding_refs_per_drilldown=2,
        )
    )
    assert bundle.document.repository_drilldowns
    for item in bundle.document.repository_drilldowns:
        assert len(item.finding_refs) <= 2
        assert "authorized users" in item.canonical_assessment_availability.lower()
        assert "snippet" not in " ".join(item.limitations).lower()
