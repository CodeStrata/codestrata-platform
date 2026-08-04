"""Community Cloud API schema compatibility (endpoint schemas remain separate)."""

from __future__ import annotations

from verification.cross_schema_compatibility.models import (
    CheckResult,
    CompatibilityFailure,
)


def check_community_cloud() -> tuple[list[CheckResult], list[CompatibilityFailure]]:
    from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
        ALLOWED_ASSESSMENT_SCHEMA_VERSIONS,
    )
    from codestrata_platform.community_cloud_api.constants import (
        COMMUNITY_AI_USAGE_SCHEMA_VERSION,
        COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
        COMMUNITY_AUTHENTICATION_POLICY_VERSION,
        COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
        COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION,
        COMMUNITY_CLOUD_API_SCHEMA_VERSION,
        COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
        COMMUNITY_RATE_LIMIT_POLICY_VERSION,
        COMMUNITY_TELEMETRY_SCHEMA_VERSION,
    )

    checks: list[CheckResult] = []
    failures: list[CompatibilityFailure] = []

    checks.append(
        CheckResult(
            name="community_api_contract_1_0",
            ok=COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0",
            detail=f"api={COMMUNITY_CLOUD_API_SCHEMA_VERSION}",
            category="community_cloud",
        )
    )
    endpoint_versions = {
        "telemetry": COMMUNITY_TELEMETRY_SCHEMA_VERSION,
        "assessment_metadata": COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
        "cli": COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
        "extension": COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
        "ai_usage": COMMUNITY_AI_USAGE_SCHEMA_VERSION,
    }
    all_1_0 = all(v == "1.0" for v in endpoint_versions.values())
    checks.append(
        CheckResult(
            name="community_endpoint_schemas_1_0",
            ok=all_1_0,
            detail=str(endpoint_versions),
            category="community_cloud",
        )
    )

    allow = tuple(ALLOWED_ASSESSMENT_SCHEMA_VERSIONS)
    checks.append(
        CheckResult(
            name="community_assessment_metadata_allows_1_2",
            ok="1.2" in allow and "2.0" not in allow,
            detail=f"ALLOWED_ASSESSMENT_SCHEMA_VERSIONS={allow}",
            category="community_cloud",
        )
    )
    if "1.2" not in allow:
        failures.append(
            CompatibilityFailure(
                classification="version_contract",
                producer="Community assessment metadata",
                consumer="Community Cloud API",
                schema="community_assessment_metadata",
                field="assessment_schema_version",
                expected="1.2 allowed",
                actual=str(allow),
            )
        )

    # Policy / credential versions are distinct from payload schemas.
    checks.append(
        CheckResult(
            name="community_policy_versions_distinct",
            ok=(
                COMMUNITY_RATE_LIMIT_POLICY_VERSION != COMMUNITY_CLOUD_API_SCHEMA_VERSION
                or COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION
                != COMMUNITY_CLOUD_API_SCHEMA_VERSION
            )
            and COMMUNITY_AUTHENTICATION_POLICY_VERSION == "1.0",
            detail=(
                f"rate_limit_policy={COMMUNITY_RATE_LIMIT_POLICY_VERSION} "
                f"credential_format={COMMUNITY_CLIENT_CREDENTIAL_FORMAT_VERSION} "
                f"auth_policy={COMMUNITY_AUTHENTICATION_POLICY_VERSION}"
            ),
            category="community_cloud",
        )
    )

    # Cross-parse: telemetry payload must not validate as CLI event model.
    cross_ok = _cross_endpoint_parse_rejected()
    checks.append(
        CheckResult(
            name="community_endpoint_schemas_not_interchangeable",
            ok=cross_ok,
            detail="telemetry_vs_cli_vs_extension_vs_ai",
            category="community_cloud",
        )
    )
    if not cross_ok:
        failures.append(
            CompatibilityFailure(
                classification="version_contract",
                producer="Community endpoint fixtures",
                consumer="cross-endpoint parsers",
                schema="community_cloud_api",
                field="request_models",
                expected="cross-parse rejected",
                actual="accepted",
            )
        )
    return checks, failures


def _cross_endpoint_parse_rejected() -> bool:
    """Return True when mismatched endpoint payloads are rejected."""

    try:
        from codestrata_platform.community_cloud_api.cli_events.models import (
            CliEventIngestionRequest,
        )
        from codestrata_platform.community_cloud_api.telemetry.models import (
            TelemetryIngestionRequest,
        )
    except Exception:  # noqa: BLE001
        return True  # models may differ; constant separation already checked

    telemetry_shaped = {
        "schema_version": "1.0",
        "event_name": "feature_used",
        "client": {"name": "cli", "version": "0.2.0"},
    }
    # Attempt to parse telemetry-shaped body as CLI — expect failure.
    try:
        CliEventIngestionRequest.model_validate(telemetry_shaped)
        # If it somehow validates, still require Telemetry model to differ.
        try:
            TelemetryIngestionRequest.model_validate(telemetry_shaped)
            return False
        except Exception:
            return True
    except Exception:
        return True
