"""CLI event semantic validation (Slice 7.9)."""

from __future__ import annotations

from collections.abc import Sequence

from codestrata_platform.community_cloud_api.cli_events.enums import CliLifecycle, CliResult
from codestrata_platform.community_cloud_api.cli_events.models import CliEventRequest
from codestrata_platform.community_cloud_api.cli_events.policy import (
    COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
    CommunityCliEventPolicy,
    default_cli_event_policy,
)
from codestrata_platform.community_cloud_api.validation.errors import (
    FIELD_INVALID_ENUM,
    FIELD_INVALID_FORMAT,
    FIELD_MISSING,
    FIELD_TOO_LARGE,
    FIELD_UNKNOWN,
    FIELD_UNSAFE_VALUE,
    field_error,
)
from codestrata_platform.community_cloud_api.validation.models import (
    CommunityApiRequestModel,
    ValidationFieldError,
)


def validate_cli_event_semantics(
    model: CommunityApiRequestModel,
    *,
    policy: CommunityCliEventPolicy | None = None,
) -> Sequence[ValidationFieldError]:
    active = policy or default_cli_event_policy()
    if not isinstance(model, CliEventRequest):
        return (field_error("request", FIELD_INVALID_FORMAT),)

    errors: list[ValidationFieldError] = []

    if model.schema_version != active.schema_version:
        errors.append(field_error("schema_version", FIELD_INVALID_ENUM))
    if model.client.name != active.allowed_client_name:
        errors.append(field_error("client.name", FIELD_INVALID_ENUM))
    if model.installation_id is not None and not active.allow_installation_id:
        errors.append(field_error("installation_id", FIELD_UNKNOWN))

    event = model.event
    if event.operation not in active.allowed_operations:
        errors.append(field_error("event.operation", FIELD_INVALID_ENUM))
    if event.lifecycle not in active.allowed_lifecycles:
        errors.append(field_error("event.lifecycle", FIELD_INVALID_ENUM))
    if event.result not in active.allowed_results:
        errors.append(field_error("event.result", FIELD_INVALID_ENUM))
    if event.duration_bucket not in active.allowed_duration_buckets:
        errors.append(field_error("event.duration_bucket", FIELD_INVALID_ENUM))

    failedish = event.lifecycle == CliLifecycle.FAILED.value or event.result == CliResult.FAILED.value
    if (
        active.require_failure_category_on_failure
        and event.lifecycle == CliLifecycle.FAILED.value
        and event.failure_category is None
    ):
        errors.append(field_error("event.failure_category", FIELD_MISSING))
    if event.failure_category is not None:
        if event.failure_category not in active.allowed_failure_categories:
            errors.append(field_error("event.failure_category", FIELD_INVALID_ENUM))
        if (
            active.forbid_failure_category_on_success
            and event.result == CliResult.SUCCEEDED.value
            and event.lifecycle == CliLifecycle.COMPLETED.value
        ):
            errors.append(field_error("event.failure_category", FIELD_INVALID_ENUM))

    ctx = model.context
    if ctx.execution_mode not in active.allowed_execution_modes:
        errors.append(field_error("context.execution_mode", FIELD_INVALID_ENUM))
    if ctx.output_format not in active.allowed_output_formats:
        errors.append(field_error("context.output_format", FIELD_INVALID_ENUM))
    if ctx.invocation_source not in active.allowed_invocation_sources:
        errors.append(field_error("context.invocation_source", FIELD_INVALID_ENUM))
    if ctx.terminal_environment not in active.allowed_terminal_environments:
        errors.append(field_error("context.terminal_environment", FIELD_INVALID_ENUM))
    if len(ctx.selected_assessment_heads) > active.maximum_head_count:
        errors.append(field_error("context.selected_assessment_heads", FIELD_TOO_LARGE))
    for head in ctx.selected_assessment_heads:
        if head not in active.allowed_assessment_heads:
            errors.append(field_error("context.selected_assessment_heads", FIELD_INVALID_ENUM))

    _ = failedish
    dumped = model.to_stable_dict()
    _scan_forbidden(dumped, path="", forbidden=set(active.forbidden_field_names), out=errors)

    if COMMUNITY_CLI_EVENT_SCHEMA_VERSION != "1.0":
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
            _scan_forbidden(value[key], path=field_path, forbidden=forbidden, out=out)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_forbidden(item, path=f"{path}[{index}]", forbidden=forbidden, out=out)
