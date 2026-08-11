---
title: Collected Fields
description: Developer field reference for Community Cloud ingestion and report-publish APIs, generated from Slice 18.1 runtime inventory.
---

# Collected Fields

This page is generated from the authoritative Slice 18.1 register
`community-telemetry-field-register:1.0` (runtime pydantic models).

**Field count:** 137

Do not treat every event below as actively emitted by the current Engine
assess path. See [Data Collection](/security/data-collection) for honest
producer status.

Related: [Telemetry](/reference/telemetry) · [Privacy](/security/privacy) ·
[Community Cloud API](/reference/community-api/)

## Product telemetry (`POST /api/v1/telemetry`)

API route: `POST /api/v1/telemetry` · Destination: `community_data_lake_raw` · Retention class: `raw_365d`

| Field | Type | Required | Privacy classification | Insights? |
| --- | --- | --- | --- | --- |
| `client` | `TelemetryClient` | required | bounded_client_descriptor | yes |
| `client.name` | `str` | required | bounded_enum_like_label | yes |
| `client.platform` | `str` | required | bounded_platform_label | yes |
| `client.version` | `str` | required | product_version | yes |
| `event_id` | `str` | required | opaque_event_id | no |
| `event_type` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `installation_id` | `optional[Annotated]` | optional | optional_privacy_safe_client_id | no |
| `occurred_at` | `optional[Annotated]` | optional | privacy_safe_aggregate_or_metadata | yes |
| `properties` | `codestrata_platform.community_cloud_api.telemetry.models.TelemetryProperties | None` | optional | privacy_safe_aggregate_or_metadata | yes |
| `schema_version` | `Literal` | required | contract_metadata | yes |

## Assessment metadata (`POST /api/v1/assessment-metadata`)

API route: `POST /api/v1/assessment-metadata` · Destination: `community_data_lake_raw` · Retention class: `raw_365d`

| Field | Type | Required | Privacy classification | Insights? |
| --- | --- | --- | --- | --- |
| `artifacts` | `AssessmentArtifactMetadata` | required | privacy_safe_aggregate_or_metadata | yes |
| `artifacts.artifact_count` | `int` | required | privacy_safe_aggregate_or_metadata | yes |
| `artifacts.findings_json_generated` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `artifacts.html_report_generated` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `artifacts.recommendations_json_generated` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `artifacts.report_json_generated` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `assessment` | `AssessmentMetadataBlock` | required | privacy_safe_aggregate_or_metadata | yes |
| `assessment.assessment_mode` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `assessment.assessment_schema_version` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `assessment.assessment_status` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `assessment.evidence_count` | `int` | required | privacy_safe_aggregate_or_metadata | yes |
| `assessment.executed_heads` | `list[Annotated]` | optional | privacy_safe_aggregate_or_metadata | yes |
| `assessment.finding_count` | `int` | required | privacy_safe_aggregate_or_metadata | yes |
| `assessment.limitation_count` | `int` | required | privacy_safe_aggregate_or_metadata | yes |
| `assessment.priority_action_count` | `int` | required | privacy_safe_aggregate_or_metadata | yes |
| `assessment.recommendation_count` | `int` | required | privacy_safe_aggregate_or_metadata | yes |
| `assessment.roadmap_initiative_count` | `int` | required | privacy_safe_aggregate_or_metadata | yes |
| `client` | `TelemetryClient` | required | bounded_client_descriptor | yes |
| `client.name` | `str` | required | bounded_enum_like_label | yes |
| `client.platform` | `str` | required | bounded_platform_label | yes |
| `client.version` | `str` | required | product_version | yes |
| `event_id` | `str` | required | opaque_event_id | no |
| `execution` | `AssessmentExecutionMetadata` | required | privacy_safe_aggregate_or_metadata | yes |
| `execution.ai_used` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `execution.client_version` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `execution.duration_bucket` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `execution.offline_mode` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `execution.platform` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `execution.result` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `installation_id` | `optional[Annotated]` | optional | optional_privacy_safe_client_id | no |
| `repository` | `RepositoryMetadata` | required | privacy_safe_aggregate_or_metadata | yes |
| `repository.dependency_ecosystem_count` | `int` | required | privacy_safe_aggregate_or_metadata | yes |
| `repository.file_count_bucket` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `repository.has_build_files` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `repository.has_dependency_manifests` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `repository.has_tests` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `repository.language_count` | `int` | required | privacy_safe_aggregate_or_metadata | yes |
| `repository.package_ecosystem` | `optional[Annotated]` | optional | privacy_safe_aggregate_or_metadata | yes |
| `repository.primary_language` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `repository.repository_shape` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `repository.source_file_count_bucket` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `repository.test_file_count_bucket` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `schema_version` | `Literal` | required | contract_metadata | yes |

## CLI events (`POST /api/v1/cli-events`)

API route: `POST /api/v1/cli-events` · Destination: `community_data_lake_raw` · Retention class: `raw_365d`

| Field | Type | Required | Privacy classification | Insights? |
| --- | --- | --- | --- | --- |
| `client` | `CliClient` | required | bounded_client_descriptor | yes |
| `client.name` | `str` | required | bounded_enum_like_label | yes |
| `client.platform` | `str` | required | bounded_platform_label | yes |
| `client.version` | `str` | required | product_version | yes |
| `context` | `CliEventContext` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.ai_requested` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.execution_mode` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.invocation_source` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.offline_mode` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.output_format` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.selected_assessment_heads` | `list[Annotated]` | optional | privacy_safe_aggregate_or_metadata | yes |
| `context.terminal_environment` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `event` | `CliEvent` | required | privacy_safe_aggregate_or_metadata | yes |
| `event.duration_bucket` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `event.failure_category` | `optional[Annotated]` | optional | privacy_safe_aggregate_or_metadata | yes |
| `event.lifecycle` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `event.operation` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `event.result` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `event_id` | `str` | required | opaque_event_id | no |
| `installation_id` | `optional[Annotated]` | optional | optional_privacy_safe_client_id | no |
| `schema_version` | `Literal` | required | contract_metadata | yes |

## Extension events (`POST /api/v1/extension-events`)

API route: `POST /api/v1/extension-events` · Destination: `community_data_lake_raw` · Retention class: `raw_365d`

| Field | Type | Required | Privacy classification | Insights? |
| --- | --- | --- | --- | --- |
| `client` | `ExtensionClient` | required | bounded_client_descriptor | yes |
| `client.editor` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `client.editor_version` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `client.name` | `str` | required | bounded_enum_like_label | yes |
| `client.platform` | `str` | required | bounded_platform_label | yes |
| `client.version` | `str` | required | product_version | yes |
| `context` | `ExtensionEventContext` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.ai_requested` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.invocation_source` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.offline_mode` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.report_surface` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.selected_assessment_heads` | `list[Annotated]` | optional | privacy_safe_aggregate_or_metadata | yes |
| `context.user_initiated` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.workspace_state` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `event` | `ExtensionEvent` | required | privacy_safe_aggregate_or_metadata | yes |
| `event.duration_bucket` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `event.failure_category` | `optional[Annotated]` | optional | privacy_safe_aggregate_or_metadata | yes |
| `event.lifecycle` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `event.operation` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `event.result` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `event_id` | `str` | required | opaque_event_id | no |
| `installation_id` | `optional[Annotated]` | optional | optional_privacy_safe_client_id | no |
| `schema_version` | `Literal` | required | contract_metadata | yes |

## AI usage metadata (`POST /api/v1/ai-usage`)

API route: `POST /api/v1/ai-usage` · Destination: `community_data_lake_raw` · Retention class: `raw_365d`

| Field | Type | Required | Privacy classification | Insights? |
| --- | --- | --- | --- | --- |
| `client` | `AiUsageClient` | required | bounded_client_descriptor | yes |
| `client.name` | `str` | required | bounded_enum_like_label | yes |
| `client.platform` | `str` | required | bounded_platform_label | yes |
| `client.version` | `str` | required | product_version | yes |
| `context` | `AiUsageContext` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.assessment_head` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.data_scope` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.invocation_source` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.offline_mode` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.output_usage` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `context.user_initiated` | `bool` | required | privacy_safe_aggregate_or_metadata | yes |
| `event_id` | `str` | required | opaque_event_id | no |
| `installation_id` | `optional[Annotated]` | optional | optional_privacy_safe_client_id | no |
| `schema_version` | `Literal` | required | contract_metadata | yes |
| `usage` | `AiUsage` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.capability` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.duration_bucket` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.execution_mode` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.failure_category` | `optional[Annotated]` | optional | privacy_safe_aggregate_or_metadata | yes |
| `usage.graph_usage` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.input_token_bucket` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.model_family` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.outcome` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.output_token_bucket` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.provider_family` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.provider_ownership` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.rag_usage` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.tool_usage` | `str` | required | privacy_safe_aggregate_or_metadata | yes |
| `usage.total_token_bucket` | `str` | required | privacy_safe_aggregate_or_metadata | yes |

## Report upload intents (`POST /api/v1/reports/upload-intents`)

API route: `POST /api/v1/reports/upload-intents` · Destination: `community_report_artifacts_staging` · Retention class: `report_current_previous`

| Field | Type | Required | Privacy classification | Insights? |
| --- | --- | --- | --- | --- |
| `artifacts` | `list[str]` | required | privacy_safe_aggregate_or_metadata | no |
| `confirm_public_publish` | `bool` | optional | privacy_safe_aggregate_or_metadata | no |
| `logical_identity_key` | `str` | required | privacy_safe_aggregate_or_metadata | no |
| `logical_identity_type` | `str` | required | privacy_safe_aggregate_or_metadata | no |
| `private_repository_acknowledged` | `bool` | optional | privacy_safe_aggregate_or_metadata | no |
| `report_type` | `str` | required | privacy_safe_aggregate_or_metadata | no |
| `schema_version` | `Literal` | optional | contract_metadata | no |

## Report publish (`POST /api/v1/reports`)

API route: `POST /api/v1/reports` · Destination: `community_report_artifacts` · Retention class: `report_current_previous`

| Field | Type | Required | Privacy classification | Insights? |
| --- | --- | --- | --- | --- |
| `confirm_public_publish` | `bool` | optional | privacy_safe_aggregate_or_metadata | no |
| `private_repository_acknowledged` | `bool` | optional | privacy_safe_aggregate_or_metadata | no |
| `schema_version` | `Literal` | optional | contract_metadata | no |
| `upload_id` | `str` | required | privacy_safe_aggregate_or_metadata | no |

