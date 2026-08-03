"""WebsiteExportBuildPolicy and bundle participation."""

from __future__ import annotations

import pytest

from codestrata_platform.intelligence_reporting.application.report_quality.policy import (
    build_interpretation_policy_bundle_id,
)
from codestrata_platform.intelligence_reporting.application.website_export import (
    ExportScope,
    RepositoryIdentityPolicy,
    WebsiteExportBuildPolicy,
)
from codestrata_platform.intelligence_reporting.domain.enums import ReportScope


def test_policy_token_stable() -> None:
    left = WebsiteExportBuildPolicy().policy_token
    right = WebsiteExportBuildPolicy().policy_token
    assert left == right
    assert left.startswith("website-export:v1:")


def test_external_assets_prohibited() -> None:
    with pytest.raises(ValueError, match="external assets"):
        WebsiteExportBuildPolicy(allow_external_assets=True)


def test_public_cannot_allow_private_display() -> None:
    with pytest.raises(ValueError, match="private display"):
        WebsiteExportBuildPolicy(
            export_scope=ExportScope.PUBLIC_OSS,
            repository_identity_policy=RepositoryIdentityPolicy.PRIVATE_DISPLAY_ALLOWED,
        )


def test_bounded_output_required() -> None:
    with pytest.raises(ValueError, match="must be >= 1"):
        WebsiteExportBuildPolicy(maximum_repository_drilldowns=0)


def test_for_report_scope_mapping() -> None:
    public = WebsiteExportBuildPolicy.for_report_scope(ReportScope.PUBLIC_OSS_DATASET)
    assert public.export_scope is ExportScope.PUBLIC_OSS
    private = WebsiteExportBuildPolicy.for_report_scope(ReportScope.CUSTOMER_PORTFOLIO)
    assert private.export_scope is ExportScope.CUSTOMER_PRIVATE
    internal = WebsiteExportBuildPolicy.for_report_scope(
        ReportScope.INTERNAL_VALIDATION_DATASET
    )
    assert internal.export_scope is ExportScope.INTERNAL


def test_export_policy_in_interpretation_bundle() -> None:
    base = dict(
        technology_policy_token="t",
        capability_policy_token="c",
        recurring_pattern_policy_token="p",
        modernization_policy_token="m",
        report_quality_policy_token="q",
        repository_drilldown_policy_token="d",
        website_export_policy_token="e1",
    )
    left = build_interpretation_policy_bundle_id(**base)
    right = build_interpretation_policy_bundle_id(
        **{**base, "website_export_policy_token": "e2"}
    )
    assert left != right
