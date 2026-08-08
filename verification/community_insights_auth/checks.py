"""Checks orchestrator for Slice 15.9 auth verification."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_auth.accessibility import check_accessibility
from verification.community_insights_auth.aggregation_boundary import check_aggregation_boundary
from verification.community_insights_auth.api_client import check_api_client
from verification.community_insights_auth.auth_contract import check_auth_contract
from verification.community_insights_auth.browser_validation import check_browser_validation
from verification.community_insights_auth.cookies import check_cookies_runtime
from verification.community_insights_auth.cors import check_cors
from verification.community_insights_auth.csrf import check_csrf
from verification.community_insights_auth.deployment_boundary import check_deployment_boundary
from verification.community_insights_auth.errors import check_errors
from verification.community_insights_auth.frontend_flow import check_frontend_flow
from verification.community_insights_auth.infrastructure_boundary import (
    check_infrastructure_boundary,
)
from verification.community_insights_auth.inventory_checks import check_platform_package
from verification.community_insights_auth.login import (
    check_login_logout_session,
    check_overview_requires_auth,
)
from verification.community_insights_auth.metrics_boundary import check_metrics_boundary
from verification.community_insights_auth.middleware import check_authorization, check_middleware
from verification.community_insights_auth.models import CheckResult, Defect
from verification.community_insights_auth.password_verification import check_password_runtime
from verification.community_insights_auth.policy import check_policy
from verification.community_insights_auth.rate_limit import check_rate_limit
from verification.community_insights_auth.responsive import check_responsive
from verification.community_insights_auth.scenario_checks import check_scenarios
from verification.community_insights_auth.secret_authority import check_secret_authority
from verification.community_insights_auth.security_headers import check_robots, check_security_headers
from verification.community_insights_auth.session import check_session_runtime


def run_all_checks(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for fn in (
        check_policy,
        check_auth_contract,
        check_platform_package,
        check_password_runtime,
        check_session_runtime,
        check_cookies_runtime,
        check_login_logout_session,
        check_overview_requires_auth,
        check_middleware,
        check_authorization,
        check_errors,
        check_rate_limit,
        check_cors,
        check_csrf,
        check_secret_authority,
        check_infrastructure_boundary,
        check_aggregation_boundary,
        check_metrics_boundary,
        check_deployment_boundary,
        check_frontend_flow,
        check_api_client,
        check_security_headers,
        check_robots,
        check_accessibility,
        check_responsive,
        check_browser_validation,
        check_scenarios,
    ):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)

    return checks, defects
