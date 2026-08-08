"""Checks orchestrator for Slice 15.11 validation verification."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation.access_control import check_access_control
from verification.community_insights_validation.accessibility import check_accessibility
from verification.community_insights_validation.athena_boundary import check_athena_boundary
from verification.community_insights_validation.auth import check_auth
from verification.community_insights_validation.auth_privacy import check_auth_privacy
from verification.community_insights_validation.cost import check_cost
from verification.community_insights_validation.cross_metric import check_cross_metric
from verification.community_insights_validation.dependencies import check_dependencies
from verification.community_insights_validation.deployment_boundary import check_deployment_boundary
from verification.community_insights_validation.design_system import check_design_system
from verification.community_insights_validation.epic_completion_boundary import (
    check_epic_completion_boundary,
)
from verification.community_insights_validation.export import check_export
from verification.community_insights_validation.failure_isolation import check_failure_isolation
from verification.community_insights_validation.iam import check_iam
from verification.community_insights_validation.metric_correctness import check_metric_correctness
from verification.community_insights_validation.models import CheckResult, Defect
from verification.community_insights_validation.overview_requests import check_overview_requests
from verification.community_insights_validation.performance import check_performance
from verification.community_insights_validation.policy import check_contract, check_policy
from verification.community_insights_validation.privacy import check_privacy
from verification.community_insights_validation.production_ingestion_boundary import (
    check_production_ingestion_boundary,
)
from verification.community_insights_validation.query_bounds import check_query_bounds
from verification.community_insights_validation.responsive import check_responsive
from verification.community_insights_validation.scenario_checks import check_scenarios
from verification.community_insights_validation.schema_boundary import check_schema_boundary
from verification.community_insights_validation.security import check_security
from verification.community_insights_validation.standalone_build import check_standalone_build
from verification.community_insights_validation.suppression import check_suppression
from verification.community_insights_validation.ui import check_ui
from verification.community_insights_validation.visualizations import check_visualizations


def run_all_checks(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for fn in (
        check_policy,
        check_contract,
        check_schema_boundary,
        check_metric_correctness,
        check_cross_metric,
        check_suppression,
        check_privacy,
        check_query_bounds,
        check_performance,
        check_cost,
        check_overview_requests,
        check_athena_boundary,
        check_auth,
        check_access_control,
        check_auth_privacy,
        check_iam,
        check_ui,
        check_visualizations,
        check_design_system,
        check_accessibility,
        check_responsive,
        check_security,
        check_dependencies,
        check_export,
        check_standalone_build,
        check_failure_isolation,
        check_production_ingestion_boundary,
        check_deployment_boundary,
        check_epic_completion_boundary,
        check_scenarios,
    ):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)

    return checks, defects
