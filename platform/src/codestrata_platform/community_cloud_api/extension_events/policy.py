"""Community Cloud extension event policy (Slice 7.10)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.assessment_metadata.enums import AssessmentHead
from codestrata_platform.community_cloud_api.extension_events.catalog import (
    EXTENSION_OPERATION_CATALOG_VERSION,
    ExtensionOperationCatalog,
    default_operation_catalog,
)
from codestrata_platform.community_cloud_api.extension_events.enums import (
    ALLOWED_EXTENSION_CLIENTS,
    CURSOR_EXTENSION_CLIENT,
    VSCODE_EXTENSION_CLIENT,
    ExtensionDurationBucket,
    ExtensionEditor,
    ExtensionFailureCategory,
    ExtensionInvocationSource,
    ExtensionLifecycle,
    ExtensionReportSurface,
    ExtensionResult,
    ExtensionWorkspaceState,
)

COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION = "1.0"
COMMUNITY_EXTENSION_EVENT_POLICY_ID = "community-extension-event-policy"
COMMUNITY_EXTENSION_EVENT_POLICY_VERSION = "1.0"
COMMUNITY_EXTENSION_EVENT_POLICY_URN = (
    f"{COMMUNITY_EXTENSION_EVENT_POLICY_ID}:{COMMUNITY_EXTENSION_EVENT_POLICY_VERSION}"
)

FORBIDDEN_FIELD_NAMES: tuple[str, ...] = (
    "account",
    "active_file",
    "args",
    "arguments",
    "branch",
    "clipboard",
    "column",
    "command",
    "command_id",
    "command_line",
    "commit",
    "completion",
    "configuration",
    "cost",
    "cursor",
    "document",
    "document_path",
    "document_uri",
    "email",
    "env",
    "environment",
    "error_message",
    "exception",
    "exception_message",
    "extension_path",
    "extension_storage_path",
    "file",
    "file_path",
    "filename",
    "folder",
    "folder_name",
    "folder_path",
    "language_id",
    "line",
    "model",
    "open_files",
    "open_tabs",
    "organization",
    "origin",
    "project",
    "project_name",
    "prompt",
    "provider",
    "query",
    "remote",
    "repository",
    "repository_name",
    "repository_path",
    "repository_url",
    "response",
    "search",
    "selected_text",
    "selection",
    "settings",
    "snippet",
    "source",
    "source_code",
    "stack_trace",
    "stderr",
    "stdout",
    "symbol",
    "terminal",
    "terminal_text",
    "token_count",
    "user",
    "username",
    "workspace",
    "workspace_name",
    "workspace_path",
    "workspace_uri",
)


@dataclass(frozen=True, slots=True)
class CommunityExtensionEventPolicy:
    """Deterministic privacy-first extension event policy."""

    policy_id: str = COMMUNITY_EXTENSION_EVENT_POLICY_ID
    policy_version: str = COMMUNITY_EXTENSION_EVENT_POLICY_VERSION
    schema_version: str = COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION
    operation_catalog_version: str = EXTENSION_OPERATION_CATALOG_VERSION
    allowed_clients: tuple[str, ...] = ALLOWED_EXTENSION_CLIENTS
    allowed_editors: tuple[str, ...] = tuple(
        sorted(item.value for item in ExtensionEditor)
    )
    allowed_operations: tuple[str, ...] = ()
    operation_alias_mapping: dict[str, str] | None = None
    allowed_lifecycles: tuple[str, ...] = tuple(
        sorted(item.value for item in ExtensionLifecycle)
    )
    allowed_results: tuple[str, ...] = tuple(
        sorted(item.value for item in ExtensionResult)
    )
    allowed_duration_buckets: tuple[str, ...] = tuple(
        sorted(item.value for item in ExtensionDurationBucket)
    )
    allowed_failure_categories: tuple[str, ...] = tuple(
        sorted(item.value for item in ExtensionFailureCategory)
    )
    allowed_invocation_sources: tuple[str, ...] = tuple(
        sorted(item.value for item in ExtensionInvocationSource)
    )
    allowed_report_surfaces: tuple[str, ...] = tuple(
        sorted(item.value for item in ExtensionReportSurface)
    )
    allowed_workspace_states: tuple[str, ...] = tuple(
        sorted(item.value for item in ExtensionWorkspaceState)
    )
    allowed_assessment_heads: tuple[str, ...] = tuple(
        sorted(item.value for item in AssessmentHead)
    )
    maximum_head_count: int = len(AssessmentHead)
    allow_installation_id: bool = True
    require_failure_category_on_failure: bool = True
    forbid_failure_category_on_success: bool = True
    forbidden_field_names: tuple[str, ...] = FORBIDDEN_FIELD_NAMES
    limitations: tuple[str, ...] = (
        "no_production_event_store",
        "no_exactly_once_guarantee",
        "sink_and_identity_record_not_atomic",
        "unauthenticated_endpoint",
        "no_rate_limiting",
        "no_extension_emitter_wiring",
        "canonical_operations_only",
        "no_document_workspace_or_source_identity",
        "ai_requested_boolean_only",
        "other_extension_deferred",
    )

    def __post_init__(self) -> None:
        if self.policy_id != COMMUNITY_EXTENSION_EVENT_POLICY_ID:
            raise ValueError("unsupported extension event policy id")
        if self.policy_version != COMMUNITY_EXTENSION_EVENT_POLICY_VERSION:
            raise ValueError("unsupported extension event policy version")
        if self.schema_version != COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION:
            raise ValueError("unsupported extension event schema version in policy")
        catalog = default_operation_catalog()
        if self.operation_catalog_version != catalog.catalog_version:
            raise ValueError("extension operation catalog version mismatch")
        clients = tuple(sorted(set(self.allowed_clients)))
        if not clients:
            raise ValueError("allowed clients required")
        for client in clients:
            if client not in ALLOWED_EXTENSION_CLIENTS:
                raise ValueError(f"invalid allowed client: {client}")
        editors = tuple(sorted(set(self.allowed_editors)))
        if not editors:
            raise ValueError("allowed editors required")
        allowed_editor_set = {item.value for item in ExtensionEditor}
        for editor in editors:
            if editor not in allowed_editor_set:
                raise ValueError(f"invalid allowed editor: {editor}")
        ops = tuple(self.allowed_operations) or catalog.canonical_operations
        for op in ops:
            if op not in catalog.canonical_operations:
                raise ValueError(f"invalid allowed operation: {op}")
        aliases = dict(self.operation_alias_mapping or catalog.aliases or {})
        for alias, target in aliases.items():
            if target not in ops:
                raise ValueError(f"alias maps outside allowlist: {alias}")
        if self.maximum_head_count < 1:
            raise ValueError("invalid maximum_head_count")
        object.__setattr__(self, "allowed_clients", clients)
        object.__setattr__(self, "allowed_editors", editors)
        object.__setattr__(self, "allowed_operations", tuple(sorted(ops)))
        object.__setattr__(
            self, "operation_alias_mapping", {k: aliases[k] for k in sorted(aliases)}
        )
        object.__setattr__(
            self, "forbidden_field_names", tuple(sorted(set(self.forbidden_field_names)))
        )
        object.__setattr__(self, "limitations", tuple(sorted(self.limitations)))

    @property
    def policy_token(self) -> str:
        return f"{self.policy_id}:{self.policy_version}"

    def operation_catalog(self) -> ExtensionOperationCatalog:
        return ExtensionOperationCatalog(
            canonical_operations=self.allowed_operations,
            aliases=dict(self.operation_alias_mapping or {}),
        )

    def expected_editor_for_client(self, client_name: str) -> str | None:
        if client_name == VSCODE_EXTENSION_CLIENT:
            return ExtensionEditor.VSCODE.value
        if client_name == CURSOR_EXTENSION_CLIENT:
            return ExtensionEditor.CURSOR.value
        return None

    @classmethod
    def default(cls) -> CommunityExtensionEventPolicy:
        return cls()

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "allow_installation_id": self.allow_installation_id,
            "allowed_assessment_heads": list(self.allowed_assessment_heads),
            "allowed_clients": list(self.allowed_clients),
            "allowed_duration_buckets": list(self.allowed_duration_buckets),
            "allowed_editors": list(self.allowed_editors),
            "allowed_failure_categories": list(self.allowed_failure_categories),
            "allowed_invocation_sources": list(self.allowed_invocation_sources),
            "allowed_lifecycles": list(self.allowed_lifecycles),
            "allowed_operations": list(self.allowed_operations),
            "allowed_report_surfaces": list(self.allowed_report_surfaces),
            "allowed_results": list(self.allowed_results),
            "allowed_workspace_states": list(self.allowed_workspace_states),
            "forbid_failure_category_on_success": self.forbid_failure_category_on_success,
            "forbidden_field_names": list(self.forbidden_field_names),
            "limitations": list(self.limitations),
            "maximum_head_count": self.maximum_head_count,
            "operation_alias_mapping": dict(self.operation_alias_mapping or {}),
            "operation_catalog_version": self.operation_catalog_version,
            "policy_id": self.policy_id,
            "policy_token": self.policy_token,
            "policy_version": self.policy_version,
            "require_failure_category_on_failure": self.require_failure_category_on_failure,
            "schema_version": self.schema_version,
        }


def default_extension_event_policy() -> CommunityExtensionEventPolicy:
    return CommunityExtensionEventPolicy.default()
