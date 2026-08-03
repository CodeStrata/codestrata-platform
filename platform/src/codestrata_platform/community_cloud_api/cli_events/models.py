"""Strict CLI event request models (Slice 7.9)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, StrictBool, StrictStr, field_validator, model_validator

from codestrata_platform.community_cloud_api.cli_events.enums import (
    CLI_CLIENT_NAME,
    CliDurationBucket,
    CliExecutionMode,
    CliFailureCategory,
    CliInvocationSource,
    CliLifecycle,
    CliOutputFormat,
    CliResult,
    CliTerminalEnvironment,
)
from codestrata_platform.community_cloud_api.cli_events.policy import (
    COMMUNITY_CLI_EVENT_SCHEMA_VERSION,
    default_cli_event_policy,
)
from codestrata_platform.community_cloud_api.validation.models import (
    CommunityApiRequestModel,
)
from codestrata_platform.community_cloud_api.validation.schema import (
    ApiClientVersion,
    ApiEventId,
    ApiInstallationId,
    ApiPlatformName,
)


class CliClient(CommunityApiRequestModel):
    """CLI-only client descriptor — codestrata_cli exclusively."""

    name: StrictStr = Field(min_length=1, max_length=64)
    version: ApiClientVersion
    platform: ApiPlatformName

    @field_validator("name")
    @classmethod
    def _cli_only(cls, value: str) -> str:
        text = value.strip()
        if text != CLI_CLIENT_NAME:
            raise ValueError("invalid_enum")
        return text


class CliEventContext(CommunityApiRequestModel):
    """Bounded anonymous CLI execution context."""

    execution_mode: StrictStr = Field(min_length=1, max_length=32)
    output_format: StrictStr = Field(min_length=1, max_length=32)
    offline_mode: StrictBool
    ai_requested: StrictBool
    selected_assessment_heads: list[StrictStr] = Field(default_factory=list, max_length=16)
    invocation_source: StrictStr = Field(min_length=1, max_length=32)
    terminal_environment: StrictStr = Field(min_length=1, max_length=32)

    @field_validator("execution_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in CliExecutionMode}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("output_format")
    @classmethod
    def _format(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in CliOutputFormat}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("invocation_source")
    @classmethod
    def _source(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in CliInvocationSource}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("terminal_environment")
    @classmethod
    def _term(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in CliTerminalEnvironment}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("selected_assessment_heads")
    @classmethod
    def _heads(cls, value: list[str]) -> list[str]:
        policy = default_cli_event_policy()
        allowed = set(policy.allowed_assessment_heads)
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            text = item.strip()
            if text not in allowed:
                raise ValueError("invalid_enum")
            if text in seen:
                continue
            seen.add(text)
            cleaned.append(text)
        if len(cleaned) > policy.maximum_head_count:
            raise ValueError("too_long")
        return sorted(cleaned)


class CliEvent(CommunityApiRequestModel):
    """Canonical CLI operational classification — no command text."""

    operation: StrictStr = Field(min_length=1, max_length=64)
    lifecycle: StrictStr = Field(min_length=1, max_length=32)
    result: StrictStr = Field(min_length=1, max_length=32)
    duration_bucket: StrictStr = Field(min_length=1, max_length=32)
    failure_category: StrictStr | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("operation")
    @classmethod
    def _operation(cls, value: str) -> str:
        policy = default_cli_event_policy()
        canonical = policy.operation_catalog().canonicalize(value.strip())
        if canonical is None or canonical not in policy.allowed_operations:
            raise ValueError("invalid_enum")
        return canonical

    @field_validator("lifecycle")
    @classmethod
    def _lifecycle(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in CliLifecycle}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("result")
    @classmethod
    def _result(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in CliResult}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("duration_bucket")
    @classmethod
    def _duration(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in CliDurationBucket}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("failure_category")
    @classmethod
    def _failure(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if text not in {item.value for item in CliFailureCategory}:
            raise ValueError("invalid_enum")
        return text

    @model_validator(mode="after")
    def _lifecycle_result_rules(self) -> CliEvent:
        policy = default_cli_event_policy()
        failedish = self.lifecycle in {
            CliLifecycle.FAILED.value,
            CliLifecycle.CANCELLED.value,
        } or self.result in {
            CliResult.FAILED.value,
            CliResult.CANCELLED.value,
        }
        successish = self.result == CliResult.SUCCEEDED.value and self.lifecycle in {
            CliLifecycle.COMPLETED.value,
            CliLifecycle.STARTED.value,
        }
        if self.lifecycle == CliLifecycle.STARTED.value and self.result not in {
            CliResult.UNAVAILABLE.value,
            CliResult.SUCCEEDED.value,
            CliResult.CANCELLED.value,
            CliResult.FAILED.value,
        }:
            raise ValueError("invalid_enum")
        if (
            policy.require_failure_category_on_failure
            and failedish
            and self.failure_category is None
            and self.lifecycle == CliLifecycle.FAILED.value
        ):
            raise ValueError("missing")
        if (
            policy.forbid_failure_category_on_success
            and successish
            and self.failure_category is not None
        ):
            raise ValueError("invalid_enum")
        if self.lifecycle == CliLifecycle.COMPLETED.value and self.result == CliResult.FAILED.value:
            # completed+failed is inconsistent
            raise ValueError("invalid_enum")
        if self.lifecycle == CliLifecycle.FAILED.value and self.result not in {
            CliResult.FAILED.value,
            CliResult.CANCELLED.value,
            CliResult.UNAVAILABLE.value,
        }:
            raise ValueError("invalid_enum")
        return self


class CliEventRequest(CommunityApiRequestModel):
    """Privacy-first CLI event envelope."""

    schema_version: Literal["1.0"]  # type: ignore[valid-type]
    event_id: ApiEventId
    client: CliClient
    installation_id: ApiInstallationId | None = None
    event: CliEvent
    context: CliEventContext

    def fingerprint_payload(self) -> dict[str, Any]:
        """Material for fingerprinting — no timestamps; event_id included (7.7 decision)."""

        return self.to_stable_dict()

    def schema_version_value(self) -> str:
        return COMMUNITY_CLI_EVENT_SCHEMA_VERSION
