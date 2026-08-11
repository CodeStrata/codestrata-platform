"""Verification-only schema registry referencing product constants."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SchemaRegistryEntry:
    contract_name: str
    owning_layer: str
    schema_version: str
    serializer: str
    parser_or_validator: str
    compatibility_mode: str
    supported_input_versions: tuple[str, ...]
    unsupported_future_version_behavior: str
    missing_version_behavior: str
    additive_field_behavior: str
    identity_fields: tuple[str, ...]
    privacy_boundary: str
    primary_producer: str
    primary_consumers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["supported_input_versions"] = list(self.supported_input_versions)
        payload["identity_fields"] = list(self.identity_fields)
        payload["primary_consumers"] = list(self.primary_consumers)
        return payload


def build_schema_registry() -> list[SchemaRegistryEntry]:
    """Build registry from live product constants (not a new authority)."""

    from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
    from codestrata_platform.community_cloud_api.constants import (
        COMMUNITY_AI_USAGE_SCHEMA_VERSION,
        COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
        COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
        COMMUNITY_CLOUD_API_SCHEMA_VERSION,
        COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
        COMMUNITY_TELEMETRY_SCHEMA_VERSION,
    )
    from codestrata_platform.intelligence_reporting.application.contracts import (
        LEGACY_COMPATIBLE_SCHEMA_VERSIONS,
        SUPPORTED_ASSESSMENT_SCHEMA_VERSION,
    )
    from codestrata_platform.intelligence_reporting.domain.report import (
        ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
    )
    from codestrata_platform.intelligence_reporting.application.website_export.policy import (
        WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
    )
    try:
        from validation.recording import RECORD_SCHEMA_VERSION
        from validation.summary_artifact import SUMMARY_SCHEMA_VERSION
    except ImportError:
        RECORD_SCHEMA_VERSION = "1.0"
        SUMMARY_SCHEMA_VERSION = "1.0"

    assert ASSESSMENT_JSON_SCHEMA_VERSION == SUPPORTED_ASSESSMENT_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"
    assert RECORD_SCHEMA_VERSION == SUMMARY_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_CLOUD_API_SCHEMA_VERSION == "1.0"

    legacy = tuple(sorted(LEGACY_COMPATIBLE_SCHEMA_VERSIONS))

    return [
        SchemaRegistryEntry(
            contract_name="assessment_report",
            owning_layer="engine",
            schema_version=ASSESSMENT_JSON_SCHEMA_VERSION,
            serializer="codestrata.reporting.assessment_json.assessment_json_to_text",
            parser_or_validator=(
                "codestrata.reporting.traceability.preservation."
                "validate_canonical_assessment / Platform validate_report_document"
            ),
            compatibility_mode="require_1_2_complete_or_legacy_limited",
            supported_input_versions=(ASSESSMENT_JSON_SCHEMA_VERSION, *legacy),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="reject_or_legacy_limited_by_policy",
            additive_field_behavior="preserve_optional_confidence_coverage_correlations",
            identity_fields=("finding.id", "recommendation.id", "assessment ids"),
            privacy_boundary="customer_safe_text + Platform validate_report_document",
            primary_producer="Engine assessment reporting",
            primary_consumers=(
                "Engine HTML",
                "SV.4/SV.5",
                "Epic 4 validation",
                "Platform EI ingestion",
                "SV.11/SV.12",
            ),
        ),
        SchemaRegistryEntry(
            contract_name="findings_companion",
            owning_layer="engine",
            schema_version=ASSESSMENT_JSON_SCHEMA_VERSION,
            serializer="findings.json companion of report.json",
            parser_or_validator="reconcile with assessment.findings",
            compatibility_mode="must_reconcile_with_report_json",
            supported_input_versions=(ASSESSMENT_JSON_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="inherit_from_report_json",
            additive_field_behavior="subset_of_report_findings",
            identity_fields=("finding.id",),
            privacy_boundary="customer_safe_text",
            primary_producer="Engine assessment reporting",
            primary_consumers=("SV.5", "Epic 4 validation", "human review"),
        ),
        SchemaRegistryEntry(
            contract_name="recommendations_companion",
            owning_layer="engine",
            schema_version=ASSESSMENT_JSON_SCHEMA_VERSION,
            serializer="recommendations.json companion of report.json",
            parser_or_validator="reconcile with assessment.recommendations",
            compatibility_mode="must_reconcile_with_report_json",
            supported_input_versions=(ASSESSMENT_JSON_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="inherit_from_report_json",
            additive_field_behavior="subset_of_report_recommendations",
            identity_fields=("recommendation.id", "supporting_finding_ids"),
            privacy_boundary="customer_safe_text",
            primary_producer="Engine assessment reporting",
            primary_consumers=("SV.5", "Epic 4 validation", "human review"),
        ),
        SchemaRegistryEntry(
            contract_name="validation_record",
            owning_layer="engine_validation",
            schema_version=RECORD_SCHEMA_VERSION,
            serializer="validation.recording.write_repository_validation_record",
            parser_or_validator="validation.recording.load_repository_validation_record",
            compatibility_mode="exact_1_0",
            supported_input_versions=(RECORD_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="reject",
            additive_field_behavior="precision_recall_fp_fn_optional",
            identity_fields=("run_id", "repository_id", "fp_id", "fn_id"),
            privacy_boundary="no_absolute_paths_no_secrets",
            primary_producer="Epic 4 Slice 4.11 recorder",
            primary_consumers=(
                "record loader",
                "FP/FN tracking",
                "summary generator",
                "verification tooling",
            ),
        ),
        SchemaRegistryEntry(
            contract_name="validation_summary",
            owning_layer="engine_validation",
            schema_version=SUMMARY_SCHEMA_VERSION,
            serializer="validation.summary_from_records.write_summary_artifacts",
            parser_or_validator="ValidationSummaryArtifact JSON load",
            compatibility_mode="exact_1_0",
            supported_input_versions=(SUMMARY_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="reject",
            additive_field_behavior="pack_precision_recall_fp_fn_optional",
            identity_fields=("summary identity fields",),
            privacy_boundary="no_customer_report_consumer",
            primary_producer="Epic 4 Slice 4.12 summary",
            primary_consumers=("engineering review", "release verification"),
        ),
        SchemaRegistryEntry(
            contract_name="engineering_intelligence_report",
            owning_layer="platform",
            schema_version=ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
            serializer="report_to_stable_dict",
            parser_or_validator="from_stable_dict",
            compatibility_mode="exact_1_0",
            supported_input_versions=(ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="reject",
            additive_field_behavior="preserve_sections_bundle_drilldowns",
            identity_fields=(
                "report_id",
                "dataset_id",
                "interpretation_policy_bundle_id",
            ),
            privacy_boundary="safe_facts_no_full_assessment_embed",
            primary_producer="Platform EI application pipeline",
            primary_consumers=(
                "stable deserializer",
                "report quality",
                "drill-downs",
                "website-safe export",
                "SV.6/SV.8/SV.12",
            ),
        ),
        SchemaRegistryEntry(
            contract_name="website_safe_eir_export",
            owning_layer="platform",
            schema_version=WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
            serializer="build_website_safe_export / serialize_website_safe_json",
            parser_or_validator="export document validation (not full EIR)",
            compatibility_mode="exact_1_0_allowlisted_projection",
            supported_input_versions=(WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="reject",
            additive_field_behavior="omit_eir_internal_intentionally",
            identity_fields=("export_id", "source_report_id"),
            privacy_boundary="allowlisted_projection_no_findings_evidence",
            primary_producer="Platform website export",
            primary_consumers=(
                "static HTML",
                "JSON artifact",
                "manifest",
                "OSS demo",
                "SV.8",
            ),
        ),
        SchemaRegistryEntry(
            contract_name="community_cloud_api",
            owning_layer="platform_community_cloud",
            schema_version=COMMUNITY_CLOUD_API_SCHEMA_VERSION,
            serializer="HTTP JSON responses",
            parser_or_validator="endpoint request validators",
            compatibility_mode="api_contract_independent_of_assessment_eir",
            supported_input_versions=(COMMUNITY_CLOUD_API_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="reject",
            additive_field_behavior="endpoint_schemas_remain_separate",
            identity_fields=("event_id", "safe_reference"),
            privacy_boundary="request_validation_privacy_first",
            primary_producer="Community Cloud API",
            primary_consumers=("future Community clients", "SV.7"),
        ),
        SchemaRegistryEntry(
            contract_name="community_telemetry",
            owning_layer="platform_community_cloud",
            schema_version=COMMUNITY_TELEMETRY_SCHEMA_VERSION,
            serializer="TelemetryIngestionRequest",
            parser_or_validator="telemetry.validation",
            compatibility_mode="endpoint_specific",
            supported_input_versions=(COMMUNITY_TELEMETRY_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="reject",
            additive_field_behavior="not_interchangeable_with_other_endpoints",
            identity_fields=("event_id",),
            privacy_boundary="telemetry_privacy_policy",
            primary_producer="Community clients",
            primary_consumers=("Community Cloud telemetry endpoint",),
        ),
        SchemaRegistryEntry(
            contract_name="community_assessment_metadata",
            owning_layer="platform_community_cloud",
            schema_version=COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
            serializer="AssessmentMetadata request models",
            parser_or_validator="assessment_metadata validators + ALLOWED_ASSESSMENT_SCHEMA_VERSIONS",
            compatibility_mode="informational_assessment_schema_version_only",
            supported_input_versions=(COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject_assessment_schema_not_in_allowlist",
            missing_version_behavior="reject",
            additive_field_behavior="no_report_json_upload",
            identity_fields=("event_id",),
            privacy_boundary="aggregate_metadata_only",
            primary_producer="future Community client",
            primary_consumers=("Community Cloud assessment-metadata endpoint",),
        ),
        SchemaRegistryEntry(
            contract_name="community_cli_event",
            owning_layer="platform_community_cloud",
            schema_version=COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
            serializer="CLI event request models",
            parser_or_validator="cli_events.validation",
            compatibility_mode="endpoint_specific",
            supported_input_versions=(COMMUNITY_CLI_EVENT_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="reject",
            additive_field_behavior="not_interchangeable_with_telemetry",
            identity_fields=("event_id",),
            privacy_boundary="cli_event_privacy_policy",
            primary_producer="Community CLI",
            primary_consumers=("Community Cloud CLI-events endpoint",),
        ),
        SchemaRegistryEntry(
            contract_name="community_extension_event",
            owning_layer="platform_community_cloud",
            schema_version=COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
            serializer="Extension event request models",
            parser_or_validator="extension_events.validation",
            compatibility_mode="endpoint_specific",
            supported_input_versions=(COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="reject",
            additive_field_behavior="not_interchangeable_with_cli",
            identity_fields=("event_id",),
            privacy_boundary="extension_event_privacy_policy",
            primary_producer="Community extensions",
            primary_consumers=("Community Cloud extension-events endpoint",),
        ),
        SchemaRegistryEntry(
            contract_name="community_ai_usage",
            owning_layer="platform_community_cloud",
            schema_version=COMMUNITY_AI_USAGE_SCHEMA_VERSION,
            serializer="AI usage request models",
            parser_or_validator="ai_usage.validation",
            compatibility_mode="endpoint_specific",
            supported_input_versions=(COMMUNITY_AI_USAGE_SCHEMA_VERSION,),
            unsupported_future_version_behavior="reject",
            missing_version_behavior="reject",
            additive_field_behavior="not_interchangeable_with_telemetry",
            identity_fields=("event_id",),
            privacy_boundary="ai_usage_privacy_policy",
            primary_producer="Community AI clients",
            primary_consumers=("Community Cloud AI-usage endpoint",),
        ),
        SchemaRegistryEntry(
            contract_name="system_verification_reports",
            owning_layer="verification",
            schema_version="1.0.0",
            serializer="verification package report writers",
            parser_or_validator="human/release review only",
            compatibility_mode="verification_1_0_0_distinct_from_product_1_0",
            supported_input_versions=("1.0.0",),
            unsupported_future_version_behavior="document_as_new_verification_contract",
            missing_version_behavior="fail_closed_for_readers",
            additive_field_behavior="safe_diagnostics_only",
            identity_fields=("verification_id", "schema_name"),
            privacy_boundary="no_secrets_source_absolute_paths",
            primary_producer="SV packages",
            primary_consumers=("release verification", "human review"),
        ),
    ]


def producer_consumer_matrix() -> list[dict[str, Any]]:
    return [
        {
            "flow": "A_engine_assessment",
            "producer": "Engine assessment reporting",
            "consumers": [
                "Engine report HTML",
                "SV.4",
                "SV.5",
                "Epic 4 validation recording",
                "Platform EI ingestion",
                "SV.11 readiness",
                "SV.12 quality review",
            ],
            "schema": "assessment_report@1.2",
        },
        {
            "flow": "B_validation_record",
            "producer": "Epic 4 Slice 4.11 recorder",
            "consumers": [
                "record loader",
                "historical FP/FN tracking",
                "summary generator",
                "verification tooling",
            ],
            "schema": "validation_record@1.0",
        },
        {
            "flow": "C_validation_summary",
            "producer": "Epic 4 Slice 4.12 summary",
            "consumers": ["engineering review", "release verification"],
            "schema": "validation_summary@1.0",
            "note": "not a customer report consumer",
        },
        {
            "flow": "D_engineering_intelligence_report",
            "producer": "Platform EI application pipeline",
            "consumers": [
                "stable deserializer",
                "report quality",
                "repository drill-downs",
                "website-safe export",
                "SV.6",
                "SV.8",
                "SV.12",
            ],
            "schema": "engineering_intelligence_report@1.0",
        },
        {
            "flow": "E_website_safe_export",
            "producer": "Platform website export",
            "consumers": [
                "static HTML renderer",
                "JSON artifact",
                "manifest writer",
                "OSS demonstration",
                "release artifact verification",
            ],
            "schema": "website_safe_eir_export@1.0",
        },
        {
            "flow": "F_community_assessment_metadata",
            "producer": "future Community client",
            "consumers": ["Community Cloud API"],
            "schema": "community_assessment_metadata@1.0",
            "note": "assessment_schema_version informational; no report.json upload",
        },
        {
            "flow": "G_system_verification_reports",
            "producer": "verification packages",
            "consumers": ["release verification", "human review"],
            "schema": "system_verification_reports@1.0.0",
            "note": "never product runtime inputs",
        },
    ]
