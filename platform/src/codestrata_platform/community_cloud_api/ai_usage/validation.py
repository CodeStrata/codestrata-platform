"""AI usage semantic validation and raw-content safety (Slice 7.11)."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence

from codestrata_platform.community_cloud_api.ai_usage.enums import AiOutcome
from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.ai_usage.policy import (
    COMMUNITY_AI_USAGE_SCHEMA_VERSION,
    CommunityAiUsagePolicy,
    default_ai_usage_policy,
)
from codestrata_platform.community_cloud_api.validation.errors import (
    FIELD_INVALID_ENUM,
    FIELD_INVALID_FORMAT,
    FIELD_MISSING,
    FIELD_UNKNOWN,
    FIELD_UNSAFE_VALUE,
    field_error,
)
from codestrata_platform.community_cloud_api.validation.models import (
    CommunityApiRequestModel,
    ValidationFieldError,
)
from codestrata_platform.community_cloud_api.validation.sanitization import (
    contains_secret_like_value,
)

_CODE_FENCE_RE = re.compile(r"```")
_JSON_BLOB_RE = re.compile(r"^\s*[\{\[]")
_RAW_MODEL_ID_RE = re.compile(
    r"(?i)^(gpt-|claude-|amazon\.|anthropic\.|meta\.|mistral\.|gemini-)"
)
_MULTILINE_RE = re.compile(r"\n")


def looks_like_raw_ai_content(value: str) -> bool:
    """Detect prompt/completion-like free text that must never appear in labels."""

    text = value or ""
    if not text:
        return False
    if contains_secret_like_value(text):
        return True
    if _CODE_FENCE_RE.search(text):
        return True
    if _MULTILINE_RE.search(text) and len(text) > 40:
        return True
    if len(text) > 128 and " " in text:
        return True
    if _RAW_MODEL_ID_RE.match(text.strip()):
        return True
    stripped = text.strip()
    if _JSON_BLOB_RE.match(stripped) and len(stripped) > 2:
        try:
            json.loads(stripped)
            return True
        except (json.JSONDecodeError, TypeError, ValueError):
            if stripped.startswith("{") or stripped.startswith("["):
                return True
    return False


def validate_ai_usage_semantics(
    model: CommunityApiRequestModel,
    *,
    policy: CommunityAiUsagePolicy | None = None,
) -> Sequence[ValidationFieldError]:
    active = policy or default_ai_usage_policy()
    if not isinstance(model, AiUsageRequest):
        return (field_error("request", FIELD_INVALID_FORMAT),)

    errors: list[ValidationFieldError] = []

    if model.schema_version != active.schema_version:
        errors.append(field_error("schema_version", FIELD_INVALID_ENUM))
    if model.client.name not in active.allowed_clients:
        errors.append(field_error("client.name", FIELD_INVALID_ENUM))
    if model.installation_id is not None and not active.allow_installation_id:
        errors.append(field_error("installation_id", FIELD_UNKNOWN))

    usage = model.usage
    if usage.capability not in active.allowed_capabilities:
        errors.append(field_error("usage.capability", FIELD_INVALID_ENUM))
    if usage.execution_mode not in active.allowed_execution_modes:
        errors.append(field_error("usage.execution_mode", FIELD_INVALID_ENUM))
    if usage.provider_ownership not in active.allowed_provider_ownership:
        errors.append(field_error("usage.provider_ownership", FIELD_INVALID_ENUM))
    if usage.provider_family not in active.allowed_provider_families:
        errors.append(field_error("usage.provider_family", FIELD_INVALID_ENUM))
    if usage.model_family not in active.allowed_model_families:
        errors.append(field_error("usage.model_family", FIELD_INVALID_ENUM))
    if usage.outcome not in active.allowed_outcomes:
        errors.append(field_error("usage.outcome", FIELD_INVALID_ENUM))
    if usage.duration_bucket not in active.duration_buckets:
        errors.append(field_error("usage.duration_bucket", FIELD_INVALID_ENUM))
    for field_name, bucket in (
        ("usage.input_token_bucket", usage.input_token_bucket),
        ("usage.output_token_bucket", usage.output_token_bucket),
        ("usage.total_token_bucket", usage.total_token_bucket),
    ):
        if bucket not in active.token_buckets:
            errors.append(field_error(field_name, FIELD_INVALID_ENUM))
    for field_name, state in (
        ("usage.tool_usage", usage.tool_usage),
        ("usage.rag_usage", usage.rag_usage),
        ("usage.graph_usage", usage.graph_usage),
    ):
        if state not in active.allowed_usage_states:
            errors.append(field_error(field_name, FIELD_INVALID_ENUM))

    if (
        active.require_failure_category_on_failure
        and usage.outcome == AiOutcome.FAILED.value
        and usage.failure_category is None
    ):
        errors.append(field_error("usage.failure_category", FIELD_MISSING))
    if usage.failure_category is not None:
        if usage.failure_category not in active.allowed_failure_categories:
            errors.append(field_error("usage.failure_category", FIELD_INVALID_ENUM))
        if (
            active.forbid_failure_category_on_success
            and usage.outcome == AiOutcome.SUCCEEDED.value
        ):
            errors.append(field_error("usage.failure_category", FIELD_INVALID_ENUM))

    ctx = model.context
    if ctx.assessment_head not in active.allowed_assessment_heads:
        errors.append(field_error("context.assessment_head", FIELD_INVALID_ENUM))
    if ctx.invocation_source not in active.allowed_invocation_sources:
        errors.append(field_error("context.invocation_source", FIELD_INVALID_ENUM))
    if ctx.data_scope not in active.allowed_data_scopes:
        errors.append(field_error("context.data_scope", FIELD_INVALID_ENUM))
    if ctx.output_usage not in active.allowed_output_usage:
        errors.append(field_error("context.output_usage", FIELD_INVALID_ENUM))

    dumped = model.to_stable_dict()
    _scan_forbidden(dumped, path="", forbidden=set(active.forbidden_field_names), out=errors)
    _scan_raw_content(dumped, path="", out=errors)

    if COMMUNITY_AI_USAGE_SCHEMA_VERSION != "1.0":
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


def _scan_raw_content(
    value: object,
    *,
    path: str,
    out: list[ValidationFieldError],
) -> None:
    if isinstance(value, dict):
        for key in sorted(value, key=str):
            name = str(key)
            field_path = f"{path}.{name}" if path else name
            _scan_raw_content(value[key], path=field_path, out=out)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_raw_content(item, path=f"{path}[{index}]", out=out)
    elif isinstance(value, str) and looks_like_raw_ai_content(value):
        out.append(field_error(path or "request", FIELD_UNSAFE_VALUE))
