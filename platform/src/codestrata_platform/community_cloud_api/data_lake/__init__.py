"""Platform Community Data Lake domain (Slice 8.1 / 8.2 / 8.3).

Persistence-neutral policy, envelope, identifier, partition-key, canonical
storage-serialization, and storage-port definitions for archiving
already-validated Community Cloud API events into an immutable,
privacy-scoped data lake.

Slice 8.2 adds the immutable raw-JSON storage contract: canonical byte-exact
JSON serialization, the resolved :class:`~.objects.ImmutableRawStorageObject`
model, fail-closed existing-object conflict classification, and privacy-safe
:class:`~.receipts.StorageReceipt` outcomes. It does **not** claim
exactly-once delivery anywhere.

Slice 8.3 evolves the envelope's canonical serialized shape from Slice 8.1's
flat fields to a nested ``acceptance``/``client``/``identity``/
``source_contract`` contract (still envelope schema **1.0** — a
pre-persistence foundation refinement, not a runtime migration; see
``platform/docs/community-cloud-api/data-lake-event-envelope.md``), and adds
the typed per-stream registry (:mod:`.envelope_registry`,
:mod:`.source_contracts`, :mod:`.streams`), high-level builders
(:mod:`.envelope_builders`), fail-closed validation
(:mod:`.envelope_validation`), and serialize/deserialize helpers
(:mod:`.envelope_serialization`) needed to build an envelope from a typed
endpoint request model.

Explicitly out of scope for this slice:

- No wiring into ``app.py``, ``deployment/wiring.py``, or any HTTP endpoint.
- No durable event-identity/deduplication store.
- No stream-specific partition policy ownership (deferred to Slice 8.4).
- No ``boto3`` import anywhere under this package **except**
  :mod:`codestrata_platform.community_cloud_api.data_lake.infrastructure`,
  a separate, unwired subpackage holding the production-capable (but not
  production-connected) S3 adapter. Every module directly under this
  package (``data_lake/*.py``) remains ``boto3``-free.
  :class:`InMemoryCommunityDataLakeStore` remains the reference
  implementation used by tests.
"""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import (
    AcceptanceClock,
    AcceptanceClockError,
    FixedAcceptanceClock,
    SystemAcceptanceClock,
    format_accepted_at,
    partition_components,
    partition_date_from_accepted_at,
)
from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    CONTENT_DIGEST_PREFIX,
    CONTENT_TYPE_APPLICATION_JSON,
    CanonicalJsonError,
    CanonicalRawJson,
    checksum_sha256_b64,
    content_digest_hex,
    digest_matches,
    serialize_canonical_raw_json,
    validate_utf8_json_object_bytes,
)
from codestrata_platform.community_cloud_api.data_lake.decisions import (
    classify_existing_object,
    is_valid_content_digest,
)
from codestrata_platform.community_cloud_api.data_lake.diagnostics import (
    safe_storage_diagnostic,
    sanitize_exception_message,
)
from codestrata_platform.community_cloud_api.data_lake.access_diagnostics import (
    ALLOWED_ACCESS_DIAGNOSTIC_STATUSES,
    AccessPolicyDiagnostics,
    diagnostics_from_access_policy,
)
from codestrata_platform.community_cloud_api.data_lake.access_policy import (
    COMMUNITY_DATA_LAKE_ACCESS_POLICY_ID,
    COMMUNITY_DATA_LAKE_ACCESS_POLICY_URN,
    COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION,
    WRITER_ALLOWED_ACTIONS,
    WRITER_FORBIDDEN_ACTIONS,
    CommunityDataLakeAccessPolicy,
    default_access_policy,
)
from codestrata_platform.community_cloud_api.data_lake.access_validation import (
    AccessValidationError,
    validate_access_action_sets,
)
from codestrata_platform.community_cloud_api.data_lake.storage import (
    COMMUNITY_DATA_LAKE_STORAGE_POLICY_ID,
    COMMUNITY_DATA_LAKE_STORAGE_POLICY_URN,
    COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION,
    CommunityDataLakeStoragePolicy,
    default_storage_policy,
)
from codestrata_platform.community_cloud_api.data_lake.storage_capabilities import (
    FORBIDDEN_STORAGE_CAPABILITIES,
    StorageCapabilities,
    StorageCapability,
)
from codestrata_platform.community_cloud_api.data_lake.storage_configuration import (
    DataLakeStorageConfiguration,
    StorageAdapterType,
)
from codestrata_platform.community_cloud_api.data_lake.storage_diagnostics import (
    ALLOWED_STORAGE_DIAGNOSTIC_STATUSES,
    StorageAbstractionDiagnostics,
    diagnostics_from_storage,
)
from codestrata_platform.community_cloud_api.data_lake.storage_errors import (
    CANONICAL_STORAGE_SAFE_CODES,
    STORAGE_ACCESS_DENIED,
    STORAGE_CHECKSUM_MISMATCH,
    STORAGE_CONFIGURATION_INVALID,
    STORAGE_CONFLICT,
    STORAGE_ENCRYPTION_FAILED,
    STORAGE_INTERNAL_ERROR,
    STORAGE_PRECONDITION_FAILED,
    STORAGE_REJECTED,
    STORAGE_SERIALIZATION_FAILED,
    STORAGE_TIMEOUT,
    STORAGE_UNAVAILABLE,
)
from codestrata_platform.community_cloud_api.data_lake.storage_factory import (
    create_community_data_lake_store,
)
from codestrata_platform.community_cloud_api.data_lake.storage_results import (
    ALLOWED_STORAGE_WRITE_STATUSES,
    storage_result_to_public_dict,
)
from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
    assert_accepted_storage_object,
    assert_quarantine_storage_object,
    validate_storage_policy_invariants,
)
from codestrata_platform.community_cloud_api.data_lake.encryption_diagnostics import (
    ALLOWED_ENCRYPTION_DIAGNOSTIC_STATUSES,
    EncryptionPolicyDiagnostics,
    diagnostics_from_encryption_policy,
)
from codestrata_platform.community_cloud_api.data_lake.encryption_policy import (
    COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_ID,
    COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_URN,
    COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION,
    DEFAULT_ENCRYPTION_MODE,
    SSE_S3_ALGORITHM,
    CommunityDataLakeEncryptionPolicy,
    default_encryption_policy,
)
from codestrata_platform.community_cloud_api.data_lake.encryption_validation import (
    EncryptionValidationError,
    assert_no_kms_key_id,
    validate_encryption_mode,
)
from codestrata_platform.community_cloud_api.data_lake.enums import (
    EncryptionMode,
    EventStream,
    QuarantineReasonCode,
    QuarantineValidationStage,
    StorageClass,
    StorageWriteStatus,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
    build_data_lake_envelope,
    build_storage_object_from_request,
    put_request_via_store,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_models import EnvelopeErrorCode
from codestrata_platform.community_cloud_api.data_lake.envelope_registry import (
    UnknownEventStreamError,
    get_source_contract,
    list_source_contracts,
    registered_event_streams,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_serialization import (
    deserialize_data_lake_envelope,
    serialize_data_lake_envelope,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_validation import (
    EnvelopeBuildError,
    revalidate_payload_against_source_contract,
)
from codestrata_platform.community_cloud_api.data_lake.envelopes import (
    FORBIDDEN_ENVELOPE_KEY_NAMES,
    FORBIDDEN_ENVELOPE_KEYS,
    DataLakeEnvelope,
    DataLakeEventEnvelope,
    EnvelopeAcceptance,
    EnvelopeClient,
    EnvelopeIdentity,
    EnvelopeValidationError,
    SourceContract,
    build_envelope,
    validate_envelope_privacy,
)
from codestrata_platform.community_cloud_api.data_lake.errors import (
    DataLakeStorageError,
    StorageErrorCategory,
)
from codestrata_platform.community_cloud_api.data_lake.identifiers import (
    LAKE_OBJECT_ID_PREFIX,
    QUARANTINE_OBJECT_ID_PREFIX,
    LakeIdentifierError,
    build_lake_object_id,
    build_opaque_object_filename,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_diagnostics import (
    ALLOWED_QUARANTINE_PROJECTION_STATUSES,
    QuarantineDiagnosticsError,
    QuarantineProjectionDiagnostics,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_error_mapping import (
    QuarantineErrorMapping,
    map_exception_to_quarantine,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_identity import (
    QUARANTINE_REFERENCE_PREFIX,
    QuarantineIdentifierError,
    build_quarantine_object_id,
    opaque_quarantine_hex,
    quarantine_reference_from_object_id,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_models import (
    COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION,
    QuarantineRecord,
    build_quarantine_record,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    ALLOWED_QUARANTINE_DIAGNOSTIC_CODES,
    COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_ID,
    COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_URN,
    COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION,
    FORBIDDEN_QUARANTINE_FIELD_NAMES,
    QUARANTINE_S3_METADATA_ALLOWLIST,
    CommunityDataLakeQuarantinePolicy,
    default_quarantine_policy,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    ImmutableQuarantineStorageObject,
    QuarantineProjectionResult,
    QuarantineStorageObjectError,
    build_quarantine_storage_object,
    project_quarantine_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_receipts import (
    DEFAULT_QUARANTINE_RECEIPT_LIMITATIONS,
    QUARANTINE_STREAM_MARKER,
    QuarantineStorageReceipt,
    build_quarantine_receipt_from_object,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_serialization import (
    QuarantineSerializationError,
    serialize_quarantine_record,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_validation import (
    QuarantineValidationError,
    assert_no_forbidden_diagnostics_map,
    validate_quarantine_record,
)
from codestrata_platform.community_cloud_api.data_lake.immutable_write import (
    build_immutable_raw_storage_object,
    put_envelope_via_store,
)
from codestrata_platform.community_cloud_api.data_lake.objects import (
    ALLOWED_S3_METADATA_KEYS,
    BASE_S3_METADATA_KEYS,
    FORBIDDEN_S3_METADATA_KEYS,
    ImmutableRawStorageObject,
    StorageObjectError,
)
from codestrata_platform.community_cloud_api.data_lake.partition_diagnostics import (
    ALLOWED_PROJECTION_STATUSES,
    PartitionDiagnosticsError,
    PartitionProjectionDiagnostics,
)
from codestrata_platform.community_cloud_api.data_lake.partition_policies import (
    GENERIC_REQUIRED_PATH_DIMENSIONS,
    PartitionPolicyError,
    StreamPartitionPolicy,
)
from codestrata_platform.community_cloud_api.data_lake.partitions import (
    PartitionKeyError,
    assert_key_excludes_identity_material,
    build_accepted_object_key,
    build_quarantine_object_key,
)
from codestrata_platform.community_cloud_api.data_lake.policy import (
    COMMUNITY_DATA_LAKE_POLICY_ID,
    COMMUNITY_DATA_LAKE_POLICY_URN,
    CommunityDataLakePolicy,
    default_data_lake_policy,
)
from codestrata_platform.community_cloud_api.data_lake.ports import (
    CommunityDataLakeStore,
    InMemoryCommunityDataLakeStore,
    StorageWriteResult,
)
from codestrata_platform.community_cloud_api.data_lake.receipts import (
    DEFAULT_RECEIPT_LIMITATIONS,
    STORED_OBJECT_REFERENCE_PREFIX,
    StorageReceipt,
    build_receipt_from_object,
)
from codestrata_platform.community_cloud_api.data_lake.retention_diagnostics import (
    RetentionPolicyDiagnostics,
    diagnostics_from_retention_policy,
)
from codestrata_platform.community_cloud_api.data_lake.retention_policy import (
    ACCEPTED_RETENTION_MAX_DAYS,
    ACCEPTED_RETENTION_MIN_DAYS,
    COMMUNITY_DATA_LAKE_RETENTION_POLICY_ID,
    COMMUNITY_DATA_LAKE_RETENTION_POLICY_URN,
    COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION,
    DEFAULT_ACCEPTED_RETENTION_DAYS,
    DEFAULT_INCOMPLETE_MULTIPART_DAYS,
    DEFAULT_NONCURRENT_VERSION_RETENTION_DAYS,
    DEFAULT_QUARANTINE_RETENTION_DAYS,
    INCOMPLETE_MULTIPART_MAX_DAYS,
    INCOMPLETE_MULTIPART_MIN_DAYS,
    NONCURRENT_VERSION_MAX_DAYS,
    NONCURRENT_VERSION_MIN_DAYS,
    QUARANTINE_RETENTION_MAX_DAYS,
    QUARANTINE_RETENTION_MIN_DAYS,
    CommunityDataLakeRetentionPolicy,
    default_retention_policy,
)
from codestrata_platform.community_cloud_api.data_lake.retention_validation import (
    RetentionValidationError,
)
from codestrata_platform.community_cloud_api.data_lake.schema_compatibility import (
    ENVELOPE_SCHEMA_VERSION,
    is_compatible,
)
from codestrata_platform.community_cloud_api.data_lake.source_contracts import (
    SourceContractDescriptor,
    SourceContractError,
)
from codestrata_platform.community_cloud_api.data_lake.source_projection import (
    SourceProjectionError,
    extract_client_type,
    project_request_payload,
)
from codestrata_platform.community_cloud_api.data_lake.stream_partitions import (
    StreamPartitionError,
    assert_partition_key_matches_policy,
    assert_s3_metadata_matches_policy,
    parse_hive_dimensions,
)
from codestrata_platform.community_cloud_api.data_lake.stream_storage import (
    StorageProjectionResult,
    merge_extra_s3_metadata,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    ASSESSMENT_METADATA_PARTITION_POLICY_ID,
    ASSESSMENT_METADATA_PARTITION_POLICY_URN,
    ASSESSMENT_METADATA_PARTITION_POLICY_VERSION,
    ASSESSMENT_SCHEMA_METADATA_KEY,
    PartitionProjectionError,
    default_assessment_metadata_partition_policy,
    extract_assessment_schema_version,
    project_assessment_metadata_storage_object,
    store_projected_assessment_metadata,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    ALLOWED_PARTITION_PROJECTION_ERROR_CODES as TELEMETRY_PARTITION_PROJECTION_ERROR_CODES,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    CLIENT_TYPE_METADATA_KEY,
    TELEMETRY_PARTITION_POLICY_ID,
    TELEMETRY_PARTITION_POLICY_URN,
    TELEMETRY_PARTITION_POLICY_VERSION,
    default_telemetry_partition_policy,
    project_telemetry_storage_object,
    store_projected_telemetry,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    PartitionProjectionError as TelemetryPartitionProjectionError,
)
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    ALLOWED_PARTITION_PROJECTION_ERROR_CODES as CLI_EVENT_PARTITION_PROJECTION_ERROR_CODES,
)
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    CLI_EVENT_PARTITION_POLICY_ID,
    CLI_EVENT_PARTITION_POLICY_URN,
    CLI_EVENT_PARTITION_POLICY_VERSION,
    default_cli_event_partition_policy,
    project_cli_event_storage_object,
    store_projected_cli_event,
)
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    PartitionProjectionError as CliEventPartitionProjectionError,
)
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    ALLOWED_PARTITION_PROJECTION_ERROR_CODES as EXTENSION_EVENT_PARTITION_PROJECTION_ERROR_CODES,
)
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    EXTENSION_EVENT_PARTITION_POLICY_ID,
    EXTENSION_EVENT_PARTITION_POLICY_URN,
    EXTENSION_EVENT_PARTITION_POLICY_VERSION,
    default_extension_event_partition_policy,
    project_extension_event_storage_object,
    store_projected_extension_event,
)
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    PartitionProjectionError as ExtensionEventPartitionProjectionError,
)
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    ALLOWED_PARTITION_PROJECTION_ERROR_CODES as AI_USAGE_PARTITION_PROJECTION_ERROR_CODES,
)
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    AI_USAGE_PARTITION_POLICY_ID,
    AI_USAGE_PARTITION_POLICY_URN,
    AI_USAGE_PARTITION_POLICY_VERSION,
    default_ai_usage_partition_policy,
    project_ai_usage_storage_object,
    store_projected_ai_usage,
)
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    PartitionProjectionError as AiUsagePartitionProjectionError,
)
from codestrata_platform.community_cloud_api.data_lake.validation import (
    DataLakeValidationError,
    reject_mutable_overwrite,
    validate_event_stream,
    validate_partition_date,
    validate_quarantine_reason,
    validate_retention_bounds,
    validate_schema_version,
)

__all__ = [
    "ALLOWED_ACCESS_DIAGNOSTIC_STATUSES",
    "ALLOWED_STORAGE_DIAGNOSTIC_STATUSES",
    "ALLOWED_STORAGE_WRITE_STATUSES",
    "ALLOWED_ENCRYPTION_DIAGNOSTIC_STATUSES",
    "ALLOWED_PROJECTION_STATUSES",
    "ALLOWED_QUARANTINE_DIAGNOSTIC_CODES",
    "ALLOWED_QUARANTINE_PROJECTION_STATUSES",
    "ALLOWED_S3_METADATA_KEYS",
    "AI_USAGE_PARTITION_POLICY_ID",
    "AI_USAGE_PARTITION_POLICY_URN",
    "AI_USAGE_PARTITION_POLICY_VERSION",
    "AI_USAGE_PARTITION_PROJECTION_ERROR_CODES",
    "ASSESSMENT_METADATA_PARTITION_POLICY_ID",
    "ASSESSMENT_METADATA_PARTITION_POLICY_URN",
    "ASSESSMENT_METADATA_PARTITION_POLICY_VERSION",
    "ASSESSMENT_SCHEMA_METADATA_KEY",
    "BASE_S3_METADATA_KEYS",
    "CLIENT_TYPE_METADATA_KEY",
    "CLI_EVENT_PARTITION_POLICY_ID",
    "CLI_EVENT_PARTITION_POLICY_URN",
    "CLI_EVENT_PARTITION_POLICY_VERSION",
    "CLI_EVENT_PARTITION_PROJECTION_ERROR_CODES",
    "ACCEPTED_RETENTION_MAX_DAYS",
    "ACCEPTED_RETENTION_MIN_DAYS",
    "CANONICAL_STORAGE_SAFE_CODES",
    "COMMUNITY_DATA_LAKE_ACCESS_POLICY_ID",
    "COMMUNITY_DATA_LAKE_ACCESS_POLICY_URN",
    "COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION",
    "COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_ID",
    "COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_URN",
    "COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION",
    "COMMUNITY_DATA_LAKE_POLICY_ID",
    "COMMUNITY_DATA_LAKE_POLICY_URN",
    "COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_ID",
    "COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_URN",
    "COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION",
    "COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION",
    "COMMUNITY_DATA_LAKE_RETENTION_POLICY_ID",
    "COMMUNITY_DATA_LAKE_RETENTION_POLICY_URN",
    "COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION",
    "COMMUNITY_DATA_LAKE_STORAGE_POLICY_ID",
    "COMMUNITY_DATA_LAKE_STORAGE_POLICY_URN",
    "COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION",
    "FORBIDDEN_STORAGE_CAPABILITIES",
    "WRITER_ALLOWED_ACTIONS",
    "WRITER_FORBIDDEN_ACTIONS",
    "CONTENT_DIGEST_PREFIX",
    "CONTENT_TYPE_APPLICATION_JSON",
    "DEFAULT_ACCEPTED_RETENTION_DAYS",
    "DEFAULT_ENCRYPTION_MODE",
    "DEFAULT_INCOMPLETE_MULTIPART_DAYS",
    "DEFAULT_NONCURRENT_VERSION_RETENTION_DAYS",
    "DEFAULT_QUARANTINE_RECEIPT_LIMITATIONS",
    "DEFAULT_QUARANTINE_RETENTION_DAYS",
    "DEFAULT_RECEIPT_LIMITATIONS",
    "ENVELOPE_SCHEMA_VERSION",
    "INCOMPLETE_MULTIPART_MAX_DAYS",
    "INCOMPLETE_MULTIPART_MIN_DAYS",
    "NONCURRENT_VERSION_MAX_DAYS",
    "NONCURRENT_VERSION_MIN_DAYS",
    "QUARANTINE_RETENTION_MAX_DAYS",
    "QUARANTINE_RETENTION_MIN_DAYS",
    "EXTENSION_EVENT_PARTITION_POLICY_ID",
    "EXTENSION_EVENT_PARTITION_POLICY_URN",
    "EXTENSION_EVENT_PARTITION_POLICY_VERSION",
    "EXTENSION_EVENT_PARTITION_PROJECTION_ERROR_CODES",
    "FORBIDDEN_ENVELOPE_KEY_NAMES",
    "FORBIDDEN_ENVELOPE_KEYS",
    "FORBIDDEN_QUARANTINE_FIELD_NAMES",
    "FORBIDDEN_S3_METADATA_KEYS",
    "GENERIC_REQUIRED_PATH_DIMENSIONS",
    "LAKE_OBJECT_ID_PREFIX",
    "QUARANTINE_OBJECT_ID_PREFIX",
    "QUARANTINE_REFERENCE_PREFIX",
    "QUARANTINE_S3_METADATA_ALLOWLIST",
    "QUARANTINE_STREAM_MARKER",
    "SSE_S3_ALGORITHM",
    "STORED_OBJECT_REFERENCE_PREFIX",
    "TELEMETRY_PARTITION_POLICY_ID",
    "TELEMETRY_PARTITION_POLICY_URN",
    "TELEMETRY_PARTITION_POLICY_VERSION",
    "TELEMETRY_PARTITION_PROJECTION_ERROR_CODES",
    "AcceptanceClock",
    "AcceptanceClockError",
    "AccessPolicyDiagnostics",
    "AccessValidationError",
    "AiUsagePartitionProjectionError",
    "CanonicalJsonError",
    "CanonicalRawJson",
    "CliEventPartitionProjectionError",
    "CommunityDataLakeAccessPolicy",
    "CommunityDataLakeEncryptionPolicy",
    "CommunityDataLakePolicy",
    "CommunityDataLakeQuarantinePolicy",
    "CommunityDataLakeRetentionPolicy",
    "CommunityDataLakeStoragePolicy",
    "DataLakeStorageConfiguration",
    "CommunityDataLakeStore",
    "DataLakeEnvelope",
    "DataLakeEventEnvelope",
    "DataLakeStorageError",
    "DataLakeValidationError",
    "EncryptionMode",
    "EncryptionPolicyDiagnostics",
    "EncryptionValidationError",
    "EnvelopeAcceptance",
    "EnvelopeBuildError",
    "EnvelopeClient",
    "EnvelopeErrorCode",
    "EnvelopeIdentity",
    "EnvelopeValidationError",
    "EventStream",
    "ExtensionEventPartitionProjectionError",
    "FixedAcceptanceClock",
    "ImmutableQuarantineStorageObject",
    "ImmutableRawStorageObject",
    "InMemoryCommunityDataLakeStore",
    "LakeIdentifierError",
    "PartitionDiagnosticsError",
    "PartitionKeyError",
    "PartitionPolicyError",
    "PartitionProjectionDiagnostics",
    "PartitionProjectionError",
    "QuarantineDiagnosticsError",
    "QuarantineErrorMapping",
    "QuarantineIdentifierError",
    "QuarantineProjectionDiagnostics",
    "QuarantineProjectionResult",
    "QuarantineReasonCode",
    "QuarantineRecord",
    "QuarantineSerializationError",
    "QuarantineStorageObjectError",
    "QuarantineStorageReceipt",
    "QuarantineValidationError",
    "QuarantineValidationStage",
    "RetentionPolicyDiagnostics",
    "RetentionValidationError",
    "SourceContract",
    "SourceContractDescriptor",
    "SourceContractError",
    "SourceProjectionError",
    "StorageErrorCategory",
    "StorageObjectError",
    "StorageProjectionResult",
    "StorageReceipt",
    "StorageAbstractionDiagnostics",
    "StorageAdapterType",
    "StorageCapabilities",
    "StorageCapability",
    "StorageClass",
    "StorageValidationError",
    "StorageWriteResult",
    "StorageWriteStatus",
    "StreamPartitionError",
    "StreamPartitionPolicy",
    "SystemAcceptanceClock",
    "TelemetryPartitionProjectionError",
    "UnknownEventStreamError",
    "assert_accepted_storage_object",
    "assert_key_excludes_identity_material",
    "assert_quarantine_storage_object",
    "assert_no_forbidden_diagnostics_map",
    "assert_no_kms_key_id",
    "assert_partition_key_matches_policy",
    "assert_s3_metadata_matches_policy",
    "build_accepted_object_key",
    "build_data_lake_envelope",
    "build_envelope",
    "build_immutable_raw_storage_object",
    "build_lake_object_id",
    "build_opaque_object_filename",
    "build_quarantine_object_id",
    "build_quarantine_object_key",
    "build_quarantine_receipt_from_object",
    "build_quarantine_record",
    "build_quarantine_storage_object",
    "build_receipt_from_object",
    "build_storage_object_from_request",
    "checksum_sha256_b64",
    "classify_existing_object",
    "content_digest_hex",
    "create_community_data_lake_store",
    "default_access_policy",
    "default_ai_usage_partition_policy",
    "default_assessment_metadata_partition_policy",
    "default_cli_event_partition_policy",
    "default_data_lake_policy",
    "default_encryption_policy",
    "default_extension_event_partition_policy",
    "default_quarantine_policy",
    "default_retention_policy",
    "default_storage_policy",
    "default_telemetry_partition_policy",
    "deserialize_data_lake_envelope",
    "diagnostics_from_access_policy",
    "diagnostics_from_encryption_policy",
    "diagnostics_from_retention_policy",
    "diagnostics_from_storage",
    "digest_matches",
    "extract_assessment_schema_version",
    "extract_client_type",
    "format_accepted_at",
    "get_source_contract",
    "is_compatible",
    "is_valid_content_digest",
    "list_source_contracts",
    "map_exception_to_quarantine",
    "merge_extra_s3_metadata",
    "opaque_quarantine_hex",
    "parse_hive_dimensions",
    "partition_components",
    "partition_date_from_accepted_at",
    "project_ai_usage_storage_object",
    "project_assessment_metadata_storage_object",
    "project_cli_event_storage_object",
    "project_extension_event_storage_object",
    "project_quarantine_storage_object",
    "project_request_payload",
    "project_telemetry_storage_object",
    "put_envelope_via_store",
    "put_request_via_store",
    "quarantine_reference_from_object_id",
    "registered_event_streams",
    "reject_mutable_overwrite",
    "revalidate_payload_against_source_contract",
    "safe_storage_diagnostic",
    "sanitize_exception_message",
    "serialize_canonical_raw_json",
    "serialize_data_lake_envelope",
    "serialize_quarantine_record",
    "store_projected_ai_usage",
    "store_projected_assessment_metadata",
    "store_projected_cli_event",
    "store_projected_extension_event",
    "store_projected_telemetry",
    "validate_access_action_sets",
    "validate_storage_policy_invariants",
    "storage_result_to_public_dict",
    "STORAGE_ACCESS_DENIED",
    "STORAGE_CHECKSUM_MISMATCH",
    "STORAGE_CONFIGURATION_INVALID",
    "STORAGE_CONFLICT",
    "STORAGE_ENCRYPTION_FAILED",
    "STORAGE_INTERNAL_ERROR",
    "STORAGE_PRECONDITION_FAILED",
    "STORAGE_REJECTED",
    "STORAGE_SERIALIZATION_FAILED",
    "STORAGE_TIMEOUT",
    "STORAGE_UNAVAILABLE",
    "validate_encryption_mode",
    "validate_envelope_privacy",
    "validate_event_stream",
    "validate_partition_date",
    "validate_quarantine_reason",
    "validate_quarantine_record",
    "validate_retention_bounds",
    "validate_schema_version",
    "validate_utf8_json_object_bytes",
]

# NOTE: codestrata_platform.community_cloud_api.data_lake.infrastructure is
# intentionally NOT imported or re-exported here. It is a separate,
# boto3-importing subpackage that stays out of this package's default
# import surface so importing `data_lake` itself never requires boto3.
