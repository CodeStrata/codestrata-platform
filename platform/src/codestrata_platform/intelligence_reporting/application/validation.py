"""Schema, identity, and safety validation for dataset ingestion inputs."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentDatasetInput,
    LEGACY_COMPATIBLE_SCHEMA_VERSIONS,
    SUPPORTED_ASSESSMENT_SCHEMA_VERSION,
    SchemaCompatibilityPolicy,
)
from codestrata_platform.intelligence_reporting.application.errors import (
    MalformedAssessmentReportError,
    UnsafeAssessmentMetadataError,
    UnsupportedAssessmentSchemaError,
)
from codestrata_platform.intelligence_reporting.domain._safety import reject_unsafe_text
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    ExclusionReason,
    SourceType,
)

_FILE_URI_RE = re.compile(r"(?i)\bfile://")
_ABS_PATH_RE = re.compile(
    r"(^|[\s\"'=])(/Users/|/home/|/var/folders/|[A-Za-z]:\\|/tmp/|/private/)"
)
_SECRET_RE = re.compile(
    r"(AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|-----BEGIN|"
    r"(password|secret|api[_-]?key)\s*[:=]\s*\S+)",
    re.IGNORECASE,
)
_REDACTED_VALUE_RE = re.compile(
    r"^\[?REDACTED\]?$|^\*+$|^<redacted>$|^xxx+$",
    re.IGNORECASE,
)


def require_input_identity(item: AssessmentDatasetInput) -> None:
    if not str(item.repository_id or "").strip():
        raise MalformedAssessmentReportError(
            "repository_id is required",
            reason_code="incomplete_identity",
        )
    if not str(item.assessment_id or "").strip():
        raise MalformedAssessmentReportError(
            "assessment_id is required",
            reason_code="incomplete_identity",
        )
    if not str(item.assessment_run_id or "").strip():
        raise MalformedAssessmentReportError(
            "assessment_run_id is required",
            reason_code="incomplete_identity",
        )
    if not isinstance(item.visibility, DataVisibility):
        raise UnsafeAssessmentMetadataError(
            "visibility must be an explicit DataVisibility value",
            reason_code=ExclusionReason.UNSAFE_METADATA.value,
        )
    if not isinstance(item.source_type, SourceType):
        raise UnsafeAssessmentMetadataError(
            "source_type must be an explicit SourceType value",
            reason_code=ExclusionReason.UNSAFE_METADATA.value,
        )


def validate_source_reference_safety(
    *,
    source_reference: str | None,
    visibility: DataVisibility,
) -> None:
    if source_reference is None:
        return
    text = str(source_reference).strip()
    if not text:
        raise UnsafeAssessmentMetadataError(
            "source_reference must be non-blank when provided",
            reason_code=ExclusionReason.UNSAFE_METADATA.value,
        )
    if _FILE_URI_RE.search(text) or _ABS_PATH_RE.search(text):
        raise UnsafeAssessmentMetadataError(
            "source_reference must not contain absolute or file:// paths",
            reason_code=ExclusionReason.UNSAFE_METADATA.value,
        )
    if _SECRET_RE.search(text):
        raise UnsafeAssessmentMetadataError(
            "source_reference must not contain secret-like metadata",
            reason_code=ExclusionReason.UNSAFE_METADATA.value,
        )
    # Opaque internal references are allowed for private/anonymized visibility.
    if visibility is DataVisibility.PUBLIC:
        reject_unsafe_text(text, label="source_reference")


def validate_report_document(document: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(document, Mapping):
        raise MalformedAssessmentReportError(
            "report_document must be a JSON object mapping",
            reason_code="malformed_report",
        )
    if not document:
        raise MalformedAssessmentReportError(
            "report_document must not be empty",
            reason_code="malformed_report",
        )
    _reject_unsafe_customer_fields(document)
    return document


def resolve_schema_version(
    document: Mapping[str, Any],
    *,
    policy: SchemaCompatibilityPolicy,
) -> tuple[str, bool]:
    """Return (schema_version, is_legacy)."""

    raw = document.get("schema_version")
    if raw is None and isinstance(document.get("assessment"), Mapping):
        # Nested documents should declare schema at root; missing is legacy.
        schema = ""
    else:
        schema = str(raw or "").strip()
    if not schema:
        if policy is SchemaCompatibilityPolicy.ALLOW_LEGACY_LIMITED:
            return "unknown", True
        raise UnsupportedAssessmentSchemaError(
            "assessment schema_version is required",
            reason_code="missing_schema_version",
        )
    if schema == SUPPORTED_ASSESSMENT_SCHEMA_VERSION:
        return schema, False
    if schema in LEGACY_COMPATIBLE_SCHEMA_VERSIONS:
        if policy is SchemaCompatibilityPolicy.REQUIRE_1_2_COMPLETE:
            raise UnsupportedAssessmentSchemaError(
                f"legacy assessment schema {schema} is not allowed by policy",
                reason_code="legacy_schema_rejected",
            )
        return schema, True
    # Future major / unknown
    major = schema.split(".", 1)[0]
    if major.isdigit() and int(major) > 1:
        raise UnsupportedAssessmentSchemaError(
            f"unsupported future assessment schema version: {schema}",
            reason_code="unsupported_schema",
        )
    if policy is SchemaCompatibilityPolicy.ALLOW_LEGACY_LIMITED:
        return schema, True
    raise UnsupportedAssessmentSchemaError(
        f"unsupported assessment schema version: {schema}",
        reason_code="unsupported_schema",
    )


def _reject_unsafe_customer_fields(node: object, *, path: str = "$") -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            key_text = str(key)
            # Skip large nested technical trees except known customer-facing string fields.
            if key_text in {
                "title",
                "summary",
                "description",
                "rationale",
                "display_name",
                "repository_url",
                "source_reference",
            } and isinstance(value, str):
                _reject_unsafe_string(value, label=f"{path}.{key_text}")
            _reject_unsafe_customer_fields(value, path=f"{path}.{key_text}")
    elif isinstance(node, (list, tuple)):
        for index, item in enumerate(node):
            _reject_unsafe_customer_fields(item, path=f"{path}[{index}]")


def _reject_unsafe_string(value: str, *, label: str) -> None:
    if _FILE_URI_RE.search(value) or _ABS_PATH_RE.search(value):
        raise UnsafeAssessmentMetadataError(
            f"{label} must not contain absolute or file:// paths",
            reason_code=ExclusionReason.UNSAFE_METADATA.value,
        )
    match = _SECRET_RE.search(value)
    if match:
        # Engine reports may retain intentional redaction markers such as
        # password=[REDACTED]. Those are not secret material.
        assigned = match.group(0).split(":", 1)[-1].split("=", 1)[-1].strip()
        if not _REDACTED_VALUE_RE.match(assigned):
            raise UnsafeAssessmentMetadataError(
                f"{label} must not contain secret-like metadata",
                reason_code=ExclusionReason.UNSAFE_METADATA.value,
            )
