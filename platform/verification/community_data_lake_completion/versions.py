"""Product and verification contract version registry (Slice 8.15)."""

from __future__ import annotations

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata_platform.community_cloud_api.constants import (
    COMMUNITY_AI_USAGE_POLICY_VERSION,
    COMMUNITY_AI_USAGE_SCHEMA_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
    COMMUNITY_AUTHENTICATION_POLICY_VERSION,
    COMMUNITY_CLI_EVENT_POLICY_VERSION,
    COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
    COMMUNITY_CLOUD_API_SCHEMA_VERSION,
    COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION,
    COMMUNITY_DATA_LAKE_POLICY_VERSION,
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
from codestrata_platform.community_cloud_api.data_lake.access_policy import (
    COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.encryption_policy import (
    COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_models import (
    COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.retention_policy import (
    COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.schema_compatibility import (
    ENVELOPE_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.storage import (
    COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    AI_USAGE_PARTITION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    ASSESSMENT_METADATA_PARTITION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    CLI_EVENT_PARTITION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    EXTENSION_EVENT_PARTITION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    TELEMETRY_PARTITION_POLICY_VERSION,
)
from verification.community_data_lake.contract import COMMUNITY_DATA_LAKE_VERIFICATION_VERSION
from verification.community_data_lake_completion.contract import (
    COMMUNITY_DATA_LAKE_COMPLETION_VERSION,
)
from verification.community_data_lake_completion.models import CheckResult
from verification.engineering_intelligence.contract import EIR_SCHEMA_VERSION
from verification.engineering_intelligence_quality.contract import (
    WEBSITE_EXPORT_SCHEMA_VERSION,
)


def build_product_contract_versions() -> dict[str, str]:
    return {
        "ai_usage_policy": COMMUNITY_AI_USAGE_POLICY_VERSION,
        "ai_usage_schema": COMMUNITY_AI_USAGE_SCHEMA_VERSION,
        "ai_usage_partition": AI_USAGE_PARTITION_POLICY_VERSION,
        "assessment_metadata_policy": COMMUNITY_ASSESSMENT_METADATA_POLICY_VERSION,
        "assessment_metadata_schema": COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
        "assessment_metadata_partition": ASSESSMENT_METADATA_PARTITION_POLICY_VERSION,
        "assessment_report": ASSESSMENT_JSON_SCHEMA_VERSION,
        "authentication_policy": COMMUNITY_AUTHENTICATION_POLICY_VERSION,
        "cli_event_policy": COMMUNITY_CLI_EVENT_POLICY_VERSION,
        "cli_event_schema": COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
        "cli_event_partition": CLI_EVENT_PARTITION_POLICY_VERSION,
        "community_cloud_api": COMMUNITY_CLOUD_API_SCHEMA_VERSION,
        "data_lake_access": COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION,
        "data_lake_encryption": COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION,
        "data_lake_envelope": ENVELOPE_SCHEMA_VERSION,
        "data_lake_envelope_constants": COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION,
        "data_lake_policy": COMMUNITY_DATA_LAKE_POLICY_VERSION,
        "data_lake_quarantine_policy": COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION,
        "data_lake_quarantine_schema": COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION,
        "data_lake_retention": COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION,
        "data_lake_storage": COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION,
        "eir": EIR_SCHEMA_VERSION,
        "event_identity_policy": COMMUNITY_EVENT_IDENTITY_POLICY_VERSION,
        "extension_event_policy": COMMUNITY_EXTENSION_EVENT_POLICY_VERSION,
        "extension_event_schema": COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
        "extension_event_partition": EXTENSION_EVENT_PARTITION_POLICY_VERSION,
        "logging_policy": COMMUNITY_LOGGING_POLICY_VERSION,
        "payload_limit_policy": COMMUNITY_PAYLOAD_LIMIT_POLICY_VERSION,
        "rate_limit_policy": COMMUNITY_RATE_LIMIT_POLICY_VERSION,
        "request_validation_policy": COMMUNITY_REQUEST_VALIDATION_POLICY_VERSION,
        "telemetry_policy": COMMUNITY_TELEMETRY_POLICY_VERSION,
        "telemetry_schema": COMMUNITY_TELEMETRY_SCHEMA_VERSION,
        "telemetry_partition": TELEMETRY_PARTITION_POLICY_VERSION,
        "website_export": WEBSITE_EXPORT_SCHEMA_VERSION,
    }


def build_verification_contract_versions() -> dict[str, str]:
    return {
        "community_data_lake_integration": COMMUNITY_DATA_LAKE_VERIFICATION_VERSION,
        "community_data_lake_completion": COMMUNITY_DATA_LAKE_COMPLETION_VERSION,
    }


def check_versions() -> list[CheckResult]:
    product = build_product_contract_versions()
    verification = build_verification_contract_versions()
    checks: list[CheckResult] = [
        CheckResult(
            name="versions:product_data_lake_policies_1_0",
            ok=all(
                product[key] == "1.0"
                for key in (
                    "data_lake_policy",
                    "data_lake_envelope",
                    "data_lake_quarantine_policy",
                    "data_lake_quarantine_schema",
                    "data_lake_retention",
                    "data_lake_encryption",
                    "data_lake_access",
                    "data_lake_storage",
                    "telemetry_partition",
                    "assessment_metadata_partition",
                    "cli_event_partition",
                    "extension_event_partition",
                    "ai_usage_partition",
                )
            ),
            detail="lake policies 1.0",
            category="versions",
        ),
        CheckResult(
            name="versions:assessment_report_1_2",
            ok=product["assessment_report"] == "1.2",
            detail=product["assessment_report"],
            category="versions",
        ),
        CheckResult(
            name="versions:rate_limit_1_1",
            ok=product["rate_limit_policy"] == "1.1",
            detail=product["rate_limit_policy"],
            category="versions",
        ),
        CheckResult(
            name="versions:verification_namespace_1_0_0",
            ok=all(v.endswith(".0.0") for v in verification.values()),
            detail=",".join(sorted(verification)),
            category="versions",
        ),
        CheckResult(
            name="versions:product_not_verification_namespace",
            ok=all(
                not product_value.endswith(".0.0") for product_value in product.values()
            ),
            detail="product uses 1.0 / 1.1 / 1.2",
            category="versions",
        ),
        CheckResult(
            name="versions:integration_vs_completion_distinct",
            ok=(
                "community_data_lake_integration" in verification
                and "community_data_lake_completion" in verification
            ),
            detail="distinct verification registry keys",
            category="versions",
        ),
    ]
    return checks


__all__ = [
    "build_product_contract_versions",
    "build_verification_contract_versions",
    "check_versions",
]
