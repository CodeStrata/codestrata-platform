"""Website-safe export policy tests."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.errors import InvalidValueError, InvariantViolationError
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    ReportScope,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from codestrata_platform.intelligence_reporting.domain.visibility import (
    WebsiteExportPolicy,
)
from tests.intelligence_reporting.domain.conftest import make_dataset, make_ref, make_report


def test_website_safe_allows_explicitly_public_oss() -> None:
    dataset = make_dataset(
        (
            make_ref(
                repository_id="repo:public-one",
                assessment_id="assessment:public-one",
                assessment_run_id="run:public-one",
                source_type=SourceType.PUBLIC_OSS,
                visibility=DataVisibility.PUBLIC,
                display_name="Public Repo One",
                source_reference="https://github.com/example/public-one",
                publication_permitted=True,
            ),
            make_ref(
                repository_id="repo:public-two",
                assessment_id="assessment:public-two",
                assessment_run_id="run:public-two",
                source_type=SourceType.PUBLIC_OSS,
                visibility=DataVisibility.PUBLIC,
                display_name="Public Repo Two",
                source_reference="https://github.com/example/public-two",
                publication_permitted=True,
            ),
        )
    )
    report = EngineeringIntelligenceReport.create(
        title="Public OSS validation report",
        report_scope=ReportScope.PUBLIC_OSS_DATASET,
        dataset=dataset,
    )
    safe = report.to_website_safe(WebsiteExportPolicy.public_default())
    assert safe.schema_version == "1.0"
    assert "repo:public-one" in safe.included_repository_ids
    assert "Public Repo One" in safe.public_repository_display_names


def test_private_repository_names_rejected_from_public_export() -> None:
    dataset = make_dataset(
        (
            make_ref(
                repository_id="repo:private-one",
                assessment_id="assessment:private-one",
                assessment_run_id="run:private-one",
                source_type=SourceType.PRIVATE,
                visibility=DataVisibility.CUSTOMER_PRIVATE,
                display_name="Acme Internal Billing",
            ),
            make_ref(
                repository_id="repo:private-two",
                assessment_id="assessment:private-two",
                assessment_run_id="run:private-two",
                source_type=SourceType.PRIVATE,
                visibility=DataVisibility.CUSTOMER_PRIVATE,
                display_name="Acme Internal Payments",
            ),
        )
    )
    report = EngineeringIntelligenceReport.create(
        title="Customer portfolio report",
        report_scope=ReportScope.CUSTOMER_PORTFOLIO,
        dataset=dataset,
    )
    with pytest.raises((InvalidValueError, InvariantViolationError)):
        report.to_website_safe(WebsiteExportPolicy.public_default())


def test_anonymized_export_supported() -> None:
    report = make_report()
    safe = report.to_website_safe(WebsiteExportPolicy.anonymized_default())
    assert safe.visibility_mode == DataVisibility.ANONYMIZED.value
    assert all(name.startswith("repository-") for name in safe.public_repository_display_names)
    payload = safe.to_stable_dict()
    assert "source_body" not in payload
    assert "snippet" not in payload
