"""Assessment metadata semantic validation (Slice 7.8)."""

from __future__ import annotations

from collections.abc import Sequence

from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
    CommunityAssessmentMetadataPolicy,
    default_assessment_metadata_policy,
)
from codestrata_platform.community_cloud_api.validation.errors import (
    FIELD_INVALID_ENUM,
    FIELD_INVALID_FORMAT,
    FIELD_TOO_LARGE,
    FIELD_UNKNOWN,
    FIELD_UNSAFE_VALUE,
    field_error,
)
from codestrata_platform.community_cloud_api.validation.models import (
    CommunityApiRequestModel,
    ValidationFieldError,
)


def validate_assessment_metadata_semantics(
    model: CommunityApiRequestModel,
    *,
    policy: CommunityAssessmentMetadataPolicy | None = None,
) -> Sequence[ValidationFieldError]:
    active = policy or default_assessment_metadata_policy()
    if not isinstance(model, AssessmentMetadataRequest):
        return (field_error("request", FIELD_INVALID_FORMAT),)

    errors: list[ValidationFieldError] = []

    if model.schema_version != active.schema_version:
        errors.append(field_error("schema_version", FIELD_INVALID_ENUM))

    if model.client.name not in active.allowed_clients:
        errors.append(field_error("client.name", FIELD_INVALID_ENUM))

    if model.installation_id is not None and not active.allow_installation_id:
        errors.append(field_error("installation_id", FIELD_UNKNOWN))

    assessment = model.assessment
    if assessment.assessment_status not in active.allowed_assessment_statuses:
        errors.append(field_error("assessment.assessment_status", FIELD_INVALID_ENUM))
    if assessment.assessment_mode not in active.allowed_assessment_modes:
        errors.append(field_error("assessment.assessment_mode", FIELD_INVALID_ENUM))
    if (
        assessment.assessment_schema_version
        not in active.allowed_assessment_schema_versions
    ):
        errors.append(
            field_error("assessment.assessment_schema_version", FIELD_INVALID_ENUM)
        )
    if len(assessment.executed_heads) > active.maximum_head_count:
        errors.append(field_error("assessment.executed_heads", FIELD_TOO_LARGE))
    for head in assessment.executed_heads:
        if head not in active.allowed_heads:
            errors.append(field_error("assessment.executed_heads", FIELD_INVALID_ENUM))

    if model.repository.primary_language not in active.allowed_primary_languages:
        errors.append(field_error("repository.primary_language", FIELD_INVALID_ENUM))
    if model.repository.repository_shape not in active.allowed_repository_shapes:
        errors.append(field_error("repository.repository_shape", FIELD_INVALID_ENUM))
    for field_name, bucket in (
        ("file_count_bucket", model.repository.file_count_bucket),
        ("source_file_count_bucket", model.repository.source_file_count_bucket),
        ("test_file_count_bucket", model.repository.test_file_count_bucket),
    ):
        if bucket not in active.count_bucket_vocabulary:
            errors.append(field_error(f"repository.{field_name}", FIELD_INVALID_ENUM))

    if model.execution.duration_bucket not in active.duration_bucket_vocabulary:
        errors.append(field_error("execution.duration_bucket", FIELD_INVALID_ENUM))
    if model.execution.result not in active.execution_result_vocabulary:
        errors.append(field_error("execution.result", FIELD_INVALID_ENUM))

    if model.artifacts.artifact_count > active.maximum_artifact_count:
        errors.append(field_error("artifacts.artifact_count", FIELD_TOO_LARGE))

    dumped = model.to_stable_dict()
    _scan_forbidden(dumped, path="", forbidden=set(active.forbidden_field_names), out=errors)

    if COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION != "1.0":
        errors.append(field_error("schema_version", FIELD_INVALID_ENUM))

    unique: dict[tuple[str, str], ValidationFieldError] = {}
    for item in errors:
        unique[(item.field, item.code)] = item
    return tuple(
        sorted(unique.values(), key=lambda err: (err.field, err.code, err.message))
    )


def _scan_forbidden(
    value: object,
    *,
    path: str,
    forbidden: set[str],
    out: list[ValidationFieldError],
) -> None:
    if isinstance(value, dict):
        for key in sorted(value, key=str):
            name = str(key)
            field_path = f"{path}.{name}" if path else name
            if name in forbidden:
                out.append(field_error(field_path, FIELD_UNSAFE_VALUE))
            _scan_forbidden(
                value[key], path=field_path, forbidden=forbidden, out=out
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_forbidden(
                item, path=f"{path}[{index}]", forbidden=forbidden, out=out
            )
