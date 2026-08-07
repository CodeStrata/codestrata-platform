"""Extension event enums and vocabularies (Slice 7.10)."""

from __future__ import annotations

from enum import Enum


class ExtensionLifecycle(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExtensionResult(str, Enum):
    SUCCEEDED = "succeeded"
    PARTIALLY_SUCCEEDED = "partially_succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


class ExtensionDurationBucket(str, Enum):
    UNDER_1S = "under_1s"
    ONE_TO_5S = "1s_to_5s"
    FIVE_TO_30S = "5s_to_30s"
    THIRTY_TO_2M = "30s_to_2m"
    TWO_TO_10M = "2m_to_10m"
    OVER_10M = "over_10m"
    UNAVAILABLE = "unavailable"


class ExtensionFailureCategory(str, Enum):
    INVALID_CONFIGURATION = "invalid_configuration"
    UNSUPPORTED_WORKSPACE = "unsupported_workspace"
    ASSESSMENT_FAILED = "assessment_failed"
    REPORT_OPEN_FAILED = "report_open_failed"
    EXTENSION_NOT_READY = "extension_not_ready"
    ENGINE_UNAVAILABLE = "engine_unavailable"
    NETWORK_UNAVAILABLE = "network_unavailable"
    PERMISSION_DENIED = "permission_denied"
    INTERNAL_ERROR = "internal_error"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


class ExtensionInvocationSource(str, Enum):
    COMMAND_PALETTE = "command_palette"
    STATUS_BAR = "status_bar"
    EDITOR_ACTION = "editor_action"
    AUTOMATIC_ACTIVATION = "automatic_activation"
    API = "api"
    UNKNOWN = "unknown"


class ExtensionReportSurface(str, Enum):
    EDITOR_TAB = "editor_tab"
    EXTERNAL_BROWSER = "external_browser"
    NONE = "none"
    UNAVAILABLE = "unavailable"


class ExtensionWorkspaceState(str, Enum):
    WORKSPACE_OPEN = "workspace_open"
    FOLDER_OPEN = "folder_open"
    NO_WORKSPACE = "no_workspace"
    UNKNOWN = "unknown"


class ExtensionEditor(str, Enum):
    VSCODE = "vscode"
    CURSOR = "cursor"


class ExtensionEventIngestionStatus(str, Enum):
    ACCEPTED = "accepted"
    ALREADY_ACCEPTED = "already_accepted"


class ExtensionEventSinkStatus(str, Enum):
    ACCEPTED = "accepted"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"


EXTENSION_EVENT_SOURCE_TYPE = "extension_event_submitted"
VSCODE_EXTENSION_CLIENT = "vscode_extension"
# Retired historical client value (Slice 12.4). Retained for schema 1.0
# deserialization of previously accepted records only — not an active emitter.
CURSOR_EXTENSION_CLIENT = "cursor_extension"

ACTIVE_EXTENSION_CLIENTS: tuple[str, ...] = (VSCODE_EXTENSION_CLIENT,)
HISTORICAL_EXTENSION_CLIENTS: tuple[str, ...] = (CURSOR_EXTENSION_CLIENT,)
# Schema 1.0 deserializable set (Approach A — no silent schema meaning change).
SCHEMA_EXTENSION_CLIENTS: tuple[str, ...] = (
    *ACTIVE_EXTENSION_CLIENTS,
    *HISTORICAL_EXTENSION_CLIENTS,
)
# Active emission / current ingestion / active projection allowlist.
ALLOWED_EXTENSION_CLIENTS: tuple[str, ...] = ACTIVE_EXTENSION_CLIENTS
