"""Domain constants: streams, schemas, fields, privacy."""

from __future__ import annotations

from typing import Any

STREAM_SCHEMA_MAP: tuple[dict[str, Any], ...] = (
    {
        "stream": "telemetry",
        "schema_name": "community-telemetry",
        "schema_version": "1.0",
        "policy": "community-telemetry-policy:1.0",
        "module": "platform/src/codestrata_platform/community_cloud_api/telemetry",
    },
    {
        "stream": "assessment_metadata",
        "schema_name": "community-assessment-metadata",
        "schema_version": "1.0",
        "policy": "community-assessment-metadata-policy:1.0",
        "module": "platform/src/codestrata_platform/community_cloud_api/assessment_metadata",
    },
    {
        "stream": "cli_event",
        "schema_name": "community-cli-event",
        "schema_version": "1.0",
        "policy": "community-cli-event-policy:1.0",
        "module": "platform/src/codestrata_platform/community_cloud_api/cli_events",
    },
    {
        "stream": "extension_event",
        "schema_name": "community-extension-event",
        "schema_version": "1.0",
        "policy": "community-extension-event-policy:1.0",
        "module": "platform/src/codestrata_platform/community_cloud_api/extension_events",
    },
    {
        "stream": "ai_usage",
        "schema_name": "community-ai-usage",
        "schema_version": "1.0",
        "policy": "community-ai-usage-policy:1.0",
        "module": "platform/src/codestrata_platform/community_cloud_api/ai_usage",
    },
    {
        "stream": "lake_envelope",
        "schema_name": "community-data-lake-envelope",
        "schema_version": "1.0",
        "policy": "community-data-lake-policy:1.0",
        "module": "platform/src/codestrata_platform/community_cloud_api/data_lake",
    },
)

# Field classifications for dashboard-relevant surfaces.
FIELD_CLASSIFICATIONS: tuple[dict[str, Any], ...] = (
    {
        "field": "payload.installation_id",
        "classes": [
            "required_for_dashboard",
            "currently_available",
            "currently_optional",
            "privacy_allowed",
            "identity_field",
            "metric_source",
        ],
    },
    {
        "field": "acceptance.partition_date",
        "classes": [
            "required_for_dashboard",
            "currently_available",
            "privacy_allowed",
            "metric_source",
        ],
    },
    {
        "field": "payload.client.version",
        "classes": [
            "required_for_dashboard",
            "currently_available",
            "privacy_allowed",
            "version_dimension",
            "metric_source",
        ],
    },
    {
        "field": "payload.assessment.assessment_status",
        "classes": [
            "required_for_dashboard",
            "currently_available",
            "privacy_allowed",
            "categorical_dimension",
            "metric_source",
        ],
    },
    {
        "field": "payload.execution.result",
        "classes": [
            "required_for_dashboard",
            "currently_available",
            "privacy_allowed",
            "categorical_dimension",
            "metric_source",
        ],
    },
    {
        "field": "payload.assessment.executed_heads",
        "classes": [
            "required_for_dashboard",
            "currently_available",
            "privacy_allowed",
            "categorical_dimension",
            "metric_source",
        ],
    },
    {
        "field": "payload.repository.primary_language",
        "classes": [
            "required_for_dashboard",
            "currently_available",
            "privacy_allowed",
            "categorical_dimension",
            "metric_source",
        ],
    },
    {
        "field": "payload.usage.provider_family",
        "classes": [
            "required_for_dashboard",
            "currently_available",
            "privacy_allowed",
            "categorical_dimension",
            "metric_source",
        ],
    },
    {
        "field": "payload.usage.model_family",
        "classes": [
            "required_for_dashboard",
            "currently_available",
            "privacy_allowed",
            "categorical_dimension",
            "metric_source",
        ],
    },
    {
        "field": "payload.event.operation",
        "classes": [
            "required_for_dashboard",
            "currently_available",
            "privacy_allowed",
            "categorical_dimension",
            "metric_source",
        ],
    },
    {
        "field": "model_id",
        "classes": ["currently_missing", "privacy_forbidden", "not_dashboard_relevant"],
    },
    {
        "field": "repository_name",
        "classes": ["privacy_forbidden", "not_dashboard_relevant"],
    },
    {
        "field": "file_path",
        "classes": ["privacy_forbidden", "not_dashboard_relevant"],
    },
    {
        "field": "prompt",
        "classes": ["privacy_forbidden", "not_dashboard_relevant"],
    },
    {
        "field": "package_ecosystem",
        "classes": [
            "useful_for_dashboard",
            "currently_missing",
            "privacy_allowed",
            "categorical_dimension",
            "historical_compatibility",
        ],
    },
    {
        "field": "open_report",
        "classes": ["operational_only", "not_dashboard_relevant"],
    },
)

PRIVACY_FORBIDDEN: tuple[str, ...] = (
    "repository_name",
    "repository_path",
    "source_file",
    "file_path",
    "finding_details",
    "evidence",
    "recommendation_text",
    "prompt",
    "ai_response",
    "credentials",
    "aws_profile",
    "account_id",
    "endpoint",
    "base_url",
    "organization_identity",
    "customer_identity",
    "email",
    "ip_address",
    "hostname",
    "machine_identity",
    "model_id",
    "package_name",
    "dependency_name",
)

ACTIVITY_OPERATIONS_USAGE: frozenset[str] = frozenset({"assess", "assess_with_ai"})
ACTIVATION_NOT_USAGE: str = "activate"
