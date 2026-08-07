"""Strict extension event request models (Slice 7.10)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, StrictBool, StrictStr, field_validator, model_validator

from codestrata_platform.community_cloud_api.extension_events.enums import (
    SCHEMA_EXTENSION_CLIENTS,
    ExtensionDurationBucket,
    ExtensionEditor,
    ExtensionFailureCategory,
    ExtensionInvocationSource,
    ExtensionLifecycle,
    ExtensionReportSurface,
    ExtensionResult,
    ExtensionWorkspaceState,
)
from codestrata_platform.community_cloud_api.extension_events.policy import (
    COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION,
    default_extension_event_policy,
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


class ExtensionClient(CommunityApiRequestModel):
    """Extension-only client descriptor — CLI clients rejected."""

    name: StrictStr = Field(min_length=1, max_length=64)
    version: ApiClientVersion
    editor: StrictStr = Field(min_length=1, max_length=32)
    editor_version: ApiClientVersion
    platform: ApiPlatformName

    @field_validator("name")
    @classmethod
    def _extension_only(cls, value: str) -> str:
        # Schema 1.0 retains historical cursor_extension for deserialize only.
        # Current ingestion rejects retired clients via policy.allowed_clients.
        text = value.strip()
        if text not in SCHEMA_EXTENSION_CLIENTS:
            raise ValueError("invalid_enum")
        return text

    @field_validator("editor")
    @classmethod
    def _editor(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in ExtensionEditor}:
            raise ValueError("invalid_enum")
        return text

    @model_validator(mode="after")
    def _client_editor_pair(self) -> ExtensionClient:
        policy = default_extension_event_policy()
        expected = policy.expected_editor_for_client(self.name)
        if expected is not None and self.editor != expected:
            raise ValueError("invalid_enum")
        return self


class ExtensionEventContext(CommunityApiRequestModel):
    """Bounded anonymous extension execution context."""

    invocation_source: StrictStr = Field(min_length=1, max_length=32)
    user_initiated: StrictBool
    offline_mode: StrictBool
    ai_requested: StrictBool
    selected_assessment_heads: list[StrictStr] = Field(default_factory=list, max_length=16)
    report_surface: StrictStr = Field(min_length=1, max_length=32)
    workspace_state: StrictStr = Field(min_length=1, max_length=32)

    @field_validator("invocation_source")
    @classmethod
    def _source(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in ExtensionInvocationSource}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("report_surface")
    @classmethod
    def _surface(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in ExtensionReportSurface}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("workspace_state")
    @classmethod
    def _workspace(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in ExtensionWorkspaceState}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("selected_assessment_heads")
    @classmethod
    def _heads(cls, value: list[str]) -> list[str]:
        policy = default_extension_event_policy()
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


class ExtensionEvent(CommunityApiRequestModel):
    """Canonical extension operational classification — no command IDs or paths."""

    operation: StrictStr = Field(min_length=1, max_length=64)
    lifecycle: StrictStr = Field(min_length=1, max_length=32)
    result: StrictStr = Field(min_length=1, max_length=32)
    duration_bucket: StrictStr = Field(min_length=1, max_length=32)
    failure_category: StrictStr | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("operation")
    @classmethod
    def _operation(cls, value: str) -> str:
        policy = default_extension_event_policy()
        canonical = policy.operation_catalog().canonicalize(value.strip())
        if canonical is None or canonical not in policy.allowed_operations:
            raise ValueError("invalid_enum")
        return canonical

    @field_validator("lifecycle")
    @classmethod
    def _lifecycle(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in ExtensionLifecycle}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("result")
    @classmethod
    def _result(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in ExtensionResult}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("duration_bucket")
    @classmethod
    def _duration(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in ExtensionDurationBucket}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("failure_category")
    @classmethod
    def _failure(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if text not in {item.value for item in ExtensionFailureCategory}:
            raise ValueError("invalid_enum")
        return text

    @model_validator(mode="after")
    def _lifecycle_result_rules(self) -> ExtensionEvent:
        policy = default_extension_event_policy()
        failedish = self.lifecycle in {
            ExtensionLifecycle.FAILED.value,
            ExtensionLifecycle.CANCELLED.value,
        } or self.result in {
            ExtensionResult.FAILED.value,
            ExtensionResult.CANCELLED.value,
        }
        successish = self.result == ExtensionResult.SUCCEEDED.value and self.lifecycle in {
            ExtensionLifecycle.COMPLETED.value,
            ExtensionLifecycle.STARTED.value,
        }
        if self.lifecycle == ExtensionLifecycle.STARTED.value and self.result not in {
            ExtensionResult.UNAVAILABLE.value,
            ExtensionResult.SUCCEEDED.value,
            ExtensionResult.CANCELLED.value,
            ExtensionResult.FAILED.value,
        }:
            raise ValueError("invalid_enum")
        if (
            policy.require_failure_category_on_failure
            and failedish
            and self.failure_category is None
            and self.lifecycle == ExtensionLifecycle.FAILED.value
        ):
            raise ValueError("missing")
        if (
            policy.forbid_failure_category_on_success
            and successish
            and self.failure_category is not None
        ):
            raise ValueError("invalid_enum")
        if (
            self.lifecycle == ExtensionLifecycle.COMPLETED.value
            and self.result == ExtensionResult.FAILED.value
        ):
            raise ValueError("invalid_enum")
        if self.lifecycle == ExtensionLifecycle.FAILED.value and self.result not in {
            ExtensionResult.FAILED.value,
            ExtensionResult.CANCELLED.value,
            ExtensionResult.UNAVAILABLE.value,
        }:
            raise ValueError("invalid_enum")
        return self


class ExtensionEventRequest(CommunityApiRequestModel):
    """Privacy-first extension event envelope."""

    schema_version: Literal["1.0"]  # type: ignore[valid-type]
    event_id: ApiEventId
    client: ExtensionClient
    installation_id: ApiInstallationId | None = None
    event: ExtensionEvent
    context: ExtensionEventContext

    def fingerprint_payload(self) -> dict[str, Any]:
        """Material for fingerprinting — no timestamps; event_id included (7.7 decision)."""

        return self.to_stable_dict()

    def schema_version_value(self) -> str:
        return COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION
