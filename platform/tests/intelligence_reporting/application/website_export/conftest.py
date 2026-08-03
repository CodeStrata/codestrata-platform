"""Helpers for website-safe export tests."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.website_export import (
    WebsiteExportBuildPolicy,
    build_website_safe_export,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    ReportScope,
)
from tests.intelligence_reporting.application.repository_drilldowns.conftest import (
    prepare_drilldown_report,
)


def prepare_export(
    *,
    scope: ReportScope = ReportScope.INTERNAL_VALIDATION_DATASET,
    visibility: DataVisibility = DataVisibility.ANONYMIZED,
    export_policy: WebsiteExportBuildPolicy | None = None,
    repos=None,
):
    result, aggregation, source, report = prepare_drilldown_report(
        scope=scope, visibility=visibility, repos=repos
    )
    policy = export_policy or WebsiteExportBuildPolicy.for_report_scope(scope)
    # Rebuild quality so website export policy token is in the bundle.
    from codestrata_platform.intelligence_reporting.application.report_quality import (
        populate_report_quality,
    )
    from codestrata_platform.intelligence_reporting.application.repository_drilldowns import (
        populate_report_repository_drilldowns,
    )

    report = populate_report_quality(
        report, aggregation, website_export_policy=policy
    )
    report = populate_report_repository_drilldowns(report, aggregation)
    bundle = build_website_safe_export(report, policy=policy)
    return result, aggregation, source, report, bundle, policy
