"""Helpers for repository drill-down tests."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.capability_comparison import (
    populate_report_capability_comparisons,
)
from codestrata_platform.intelligence_reporting.application.modernization_observations import (
    populate_report_modernization_observations,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns import (
    populate_report_recurring_patterns,
)
from codestrata_platform.intelligence_reporting.application.report_quality import (
    populate_report_quality,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns import (
    RepositoryDrilldownPolicy,
    populate_report_repository_drilldowns,
)
from codestrata_platform.intelligence_reporting.application.technology_distribution import (
    populate_report_technology_distribution,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    ReportScope,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from tests.intelligence_reporting.application.aggregation.conftest import prepare_aggregation


def prepare_drilldown_report(
    *,
    scope: ReportScope = ReportScope.INTERNAL_VALIDATION_DATASET,
    visibility: DataVisibility = DataVisibility.ANONYMIZED,
    repos=None,
    drilldown_policy: RepositoryDrilldownPolicy | None = None,
):
    result, aggregation, source = prepare_aggregation(
        repos=repos, visibility=visibility
    )
    report = EngineeringIntelligenceReport.create(
        title="Drilldown fixture",
        report_scope=scope,
        dataset=result.dataset,
    )
    report = populate_report_technology_distribution(report, aggregation)
    report = populate_report_capability_comparisons(report, aggregation)
    report = populate_report_recurring_patterns(report, aggregation)
    report = populate_report_modernization_observations(report, aggregation)
    report = populate_report_quality(
        report, aggregation, repository_drilldown_policy=drilldown_policy
    )
    report = populate_report_repository_drilldowns(
        report, aggregation, policy=drilldown_policy
    )
    return result, aggregation, source, report
