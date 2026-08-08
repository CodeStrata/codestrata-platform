"""Authoritative audit findings for Slice 15.1."""

from __future__ import annotations

from verification.community_data_lake_audit.models import AuditFinding

# Deterministic ordered findings — classifications are part of the contract.
AUDIT_FINDINGS: tuple[AuditFinding, ...] = (
    AuditFinding(
        "bucket_layout",
        "Accepted",
        "Single private bucket with raw/ and quarantine/ prefix isolation.",
    ),
    AuditFinding(
        "folder_hierarchy",
        "Accepted",
        "Hive-style stream/schema_version/year/month/day hierarchy is authoritative.",
    ),
    AuditFinding(
        "event_categories",
        "Accepted",
        "Five streams: telemetry, assessment_metadata, cli_event, extension_event, ai_usage.",
    ),
    AuditFinding(
        "partition_strategy",
        "Accepted",
        "No identity fields in partition dimensions; opaque object filenames only.",
    ),
    AuditFinding(
        "object_naming",
        "Accepted",
        "lake-object: / quarantine-object: identity prefixes with opaque hex filenames.",
    ),
    AuditFinding(
        "event_schemas",
        "Accepted",
        "Envelope schema 1.0 nested acceptance/client/identity/payload/source_contract.",
    ),
    AuditFinding(
        "schema_versioning",
        "Accepted",
        "Lake and partition policies remain at 1.0; Assessment report schema remains 1.2.",
    ),
    AuditFinding(
        "privacy_boundaries",
        "Accepted",
        "Forbidden envelope keys block source_code, credentials, IPs, prompts, and PII names.",
    ),
    AuditFinding(
        "installation_identity",
        "Accepted",
        "Anonymous installation_id is payload-only; forbidden in path and S3 metadata.",
    ),
    AuditFinding(
        "retention_strategy",
        "Accepted",
        "Defaults 365/90/7/30 are coherent; still provisional pending owner review.",
    ),
    AuditFinding(
        "data_ownership",
        "Accepted",
        "Platform owns lake domain; Engine/CLI/extensions must not import lake packages.",
    ),
    AuditFinding(
        "export_contracts",
        "Accepted",
        "Public export forbids platform/ and infrastructure/; lake stays private.",
    ),
    AuditFinding(
        "build_export_process",
        "Accepted",
        "OpenTofu module and Platform adapters exist; ingestion wire remains false.",
    ),
    AuditFinding(
        "dashboard_readiness",
        "Deferred",
        "Storage contract is ready for future consumers; dashboard/query/aggregations not started.",
    ),
    AuditFinding(
        "production_ingestion_wiring",
        "Deferred",
        "enable_ingestion_wire=false and writer IAM unattached by design.",
    ),
    AuditFinding(
        "sse_kms_migration",
        "Deferred",
        "SSE-S3 is current authority; KMS reserved for a future migration.",
    ),
    AuditFinding(
        "athena_glue_query_layer",
        "Deferred",
        "Analytics/query layer is out of Epic 8 and out of Slice 15.1.",
    ),
    AuditFinding(
        "retention_owner_signoff",
        "Deferred",
        "Retention defaults still marked provisional_requires_release_owner_review.",
    ),
    AuditFinding(
        "stale_epic9_status_in_completion_readme",
        "Accepted",
        "community_data_lake_completion README updated: Epic 9 complete outside this package.",
    ),
    AuditFinding(
        "future_data_lake_doc_epic8_wiring_language",
        "Accepted",
        "future-data-lake.md updated: wiring deferred post-Epic-8, not unfinished Epic 8.",
    ),
    AuditFinding(
        "engine_telemetry_schema_1_0_0_vs_platform_1_0",
        "Historical",
        "Engine TelemetryEvent schema_version 1.0.0 vs Platform Community telemetry 1.0.",
    ),
    AuditFinding(
        "cursor_extension_read_only_metadata",
        "Historical",
        "cursor_extension remains read-only historical client_type metadata.",
    ),
    AuditFinding(
        "epic8_completion_artifacts",
        "Historical",
        "Epic 8 SV.9 and completion verification packages remain historical authority.",
    ),
)
