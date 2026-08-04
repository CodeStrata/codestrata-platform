"""SV.7 Community Cloud API verification runner."""

from __future__ import annotations

import time
from pathlib import Path

from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_AI_USAGE_POLICY_VERSION,
    COMMUNITY_AI_USAGE_SCHEMA_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
    COMMUNITY_AUTHENTICATION_POLICY_VERSION,
    COMMUNITY_CLI_EVENT_POLICY_VERSION,
    COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
    COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION,
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_EVENT_IDENTITY_POLICY_VERSION,
    COMMUNITY_EXTENSION_EVENT_POLICY_VERSION,
    COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
    COMMUNITY_LOGGING_POLICY_VERSION,
    COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION,
    COMMUNITY_RATE_LIMIT_POLICY_VERSION,
    COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION,
    COMMUNITY_TELEMETRY_POLICY_VERSION,
    COMMUNITY_TELEMETRY_SCHEMA_VERSION,
)

from verification.community_cloud_api.app_factory import build_verification_app
from verification.community_cloud_api.authentication import (
    check_authentication,
    check_client_matching,
)
from verification.community_cloud_api.contract import (
    EXPECTED_ROUTE_IDENTITIES,
    CcVerificationContract,
    default_contract,
)
from verification.community_cloud_api.deployment_foundation import check_deployment_foundation
from verification.community_cloud_api.determinism import check_determinism
from verification.community_cloud_api.endpoints import check_health, check_route_inventory
from verification.community_cloud_api.logging_checks import check_logging
from verification.community_cloud_api.models import (
    CheckResult,
    PolicyVersions,
    VerificationReport,
)
from verification.community_cloud_api.pipeline import check_pipeline_order
from verification.community_cloud_api.rate_limiting import check_rate_limiting
from verification.community_cloud_api.reporting import write_verification_report
from verification.community_cloud_api.retries import (
    check_endpoint_separation,
    check_retries,
)
from verification.community_cloud_api.safety import check_safety
from verification.community_cloud_api.scenarios import check_happy_path_ingestion
from verification.community_cloud_api.validation import check_payload_limits, check_validation


def _policy_versions() -> PolicyVersions:
    return PolicyVersions(
        api_contract=COMMUNITY_CLOUD_API_SCHEMA_VERSION,
        authentication=COMMUNITY_AUTHENTICATION_POLICY_VERSION,
        credential_format=COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION,
        rate_limit=COMMUNITY_RATE_LIMIT_POLICY_VERSION,
        validation=COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION,
        payload_limit=COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION,
        logging=COMMUNITY_LOGGING_POLICY_VERSION,
        event_identity=COMMUNITY_EVENT_IDENTITY_POLICY_VERSION,
        telemetry_schema=COMMUNITY_TELEMETRY_SCHEMA_VERSION,
        telemetry_policy=COMMUNITY_TELEMETRY_POLICY_VERSION,
        assessment_metadata_schema=COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
        assessment_metadata_policy=COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION,
        cli_event_schema=COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
        cli_event_policy=COMMUNITY_CLI_EVENT_POLICY_VERSION,
        extension_event_schema=COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
        extension_event_policy=COMMUNITY_EXTENSION_EVENT_POLICY_VERSION,
        ai_usage_schema=COMMUNITY_AI_USAGE_SCHEMA_VERSION,
        ai_usage_policy=COMMUNITY_AI_USAGE_POLICY_VERSION,
    )


def run_community_cloud_api_verification(
    *,
    output_dir: Path | None = None,
    contract: CcVerificationContract | None = None,
) -> VerificationReport:
    started = time.perf_counter()
    contract = contract or default_contract()
    out = (
        output_dir
        or Path(__file__).resolve().parents[2] / "reports" / "verification"
    ).resolve()
    out.mkdir(parents=True, exist_ok=True)

    app = build_verification_app()
    checks: list[CheckResult] = []
    checks.extend(check_route_inventory(app))
    checks.extend(check_health(app))
    checks.extend(check_happy_path_ingestion(app))
    checks.extend(check_authentication(app))
    checks.extend(check_client_matching(app))
    checks.extend(check_rate_limiting())
    checks.extend(check_pipeline_order())
    checks.extend(check_validation(app))
    checks.extend(check_payload_limits())
    checks.extend(check_retries(app))
    checks.extend(check_endpoint_separation(app))
    checks.extend(check_logging(app))
    checks.extend(check_determinism())
    checks.extend(check_deployment_foundation())
    # Safety last so it can scan accumulated logs/responses from this app.
    checks.extend(check_safety(app))

    failures = [f"{c.name}:{c.detail}" for c in checks if not c.ok]
    by_category: dict[str, int] = {}
    for item in checks:
        key = item.category
        by_category[key] = by_category.get(key, 0) + (0 if item.ok else 1)

    report = VerificationReport(
        ok=not failures,
        verdict="pass" if not failures else "fail",
        policy_versions=_policy_versions(),
        route_inventory=EXPECTED_ROUTE_IDENTITIES,
        checks=tuple(checks),
        scenario_summary={
            "total_checks": len(checks),
            "failed_checks": len(failures),
            **{f"failed_{k}": v for k, v in by_category.items() if v},
        },
        defects=tuple(failures),
        limitations=tuple(contract.notes),
        elapsed_ms=(time.perf_counter() - started) * 1000,
    )
    write_verification_report(report, out)
    return report
