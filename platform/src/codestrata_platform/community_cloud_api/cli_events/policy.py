"""Community Cloud CLI event policy (Slice 7.9)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.assessment_metadata.enums import AssessmentHead
from codestrata_platform.community_cloud_api.cli_events.catalog import (
    CLI_OPERATION_CATALOG_VERSION,
    CliOperationCatalog,
    default_operation_catalog,
)
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

COMMUNITY_CLI_EVENT_SCHEMA_VERSION = "1.0"
COMMUNITY_CLI_EVENT_POLICY_ID = "community-cli-event-policy"
COMMUNITY_CLI_EVENT_POLICY_VERSION = "1.0"
COMMUNITY_CLI_EVENT_POLICY_URN = (
    f"{COMMUNITY_CLI_EVENT_POLICY_ID}:{COMMUNITY_CLI_EVENT_POLICY_VERSION}"
)

FORBIDDEN_FIELD_NAMES: tuple[str, ...] = (
    "account",
    "args",
    "arguments",
    "argv",
    "branch",
    "command",
    "command_line",
    "commit",
    "config",
    "config_path",
    "cost",
    "credential",
    "cwd",
    "dependencies",
    "email",
    "env",
    "environment",
    "error_message",
    "evidence",
    "exception",
    "exception_message",
    "file",
    "file_path",
    "filename",
    "findings",
    "flags",
    "home",
    "model",
    "options",
    "organization",
    "origin",
    "output_path",
    "path",
    "priority_actions",
    "prompt",
    "provider",
    "recommendations",
    "remote",
    "report_path",
    "repository",
    "repository_name",
    "repository_path",
    "repository_url",
    "response",
    "roadmap",
    "shell_history",
    "snippet",
    "source",
    "source_code",
    "stack_trace",
    "stderr",
    "stdout",
    "technologies",
    "token",
    "token_count",
    "username",
    "working_directory",
    "workspace",
)


@dataclass(frozen=True, slots=True)
class CommunityCliEventPolicy:
    """Deterministic privacy-first CLI event policy."""

    policy_id: str = COMMUNITY_CLI_EVENT_POLICY_ID
    policy_version: str = COMMUNITY_CLI_EVENT_POLICY_VERSION
    schema_version: str = COMMUNITY_CLI_EVENT_SCHEMA_VERSION
    operation_catalog_version: str = CLI_OPERATION_CATALOG_VERSION
    allowed_client_name: str = CLI_CLIENT_NAME
    allowed_operations: tuple[str, ...] = ()
    operation_alias_mapping: dict[str, str] | None = None
    allowed_lifecycles: tuple[str, ...] = tuple(
        sorted(item.value for item in CliLifecycle)
    )
    allowed_results: tuple[str, ...] = tuple(sorted(item.value for item in CliResult))
    allowed_duration_buckets: tuple[str, ...] = tuple(
        sorted(item.value for item in CliDurationBucket)
    )
    allowed_failure_categories: tuple[str, ...] = tuple(
        sorted(item.value for item in CliFailureCategory)
    )
    allowed_execution_modes: tuple[str, ...] = tuple(
        sorted(item.value for item in CliExecutionMode)
    )
    allowed_output_formats: tuple[str, ...] = tuple(
        sorted(item.value for item in CliOutputFormat)
    )
    allowed_invocation_sources: tuple[str, ...] = tuple(
        sorted(item.value for item in CliInvocationSource)
    )
    allowed_terminal_environments: tuple[str, ...] = tuple(
        sorted(item.value for item in CliTerminalEnvironment)
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
        "no_cli_emitter_wiring",
        "canonical_operations_only",
        "no_command_lines_or_arguments",
        "ai_requested_boolean_only",
    )

    def __post_init__(self) -> None:
        if self.policy_id != COMMUNITY_CLI_EVENT_POLICY_ID:
            raise ValueError("unsupported cli event policy id")
        if self.policy_version != COMMUNITY_CLI_EVENT_POLICY_VERSION:
            raise ValueError("unsupported cli event policy version")
        if self.schema_version != COMMUNITY_CLI_EVENT_SCHEMA_VERSION:
            raise ValueError("unsupported cli event schema version in policy")
        catalog = default_operation_catalog()
        if self.operation_catalog_version != catalog.catalog_version:
            raise ValueError("cli operation catalog version mismatch")
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

    @classmethod
    def default(cls) -> CommunityCliEventPolicy:
        return cls()

    def operation_catalog(self) -> CliOperationCatalog:
        return CliOperationCatalog(
            canonical_operations=self.allowed_operations,
            aliases=dict(self.operation_alias_mapping or {}),
        )

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "allow_installation_id": self.allow_installation_id,
            "allowed_assessment_heads": list(self.allowed_assessment_heads),
            "allowed_client_name": self.allowed_client_name,
            "allowed_duration_buckets": list(self.allowed_duration_buckets),
            "allowed_execution_modes": list(self.allowed_execution_modes),
            "allowed_failure_categories": list(self.allowed_failure_categories),
            "allowed_invocation_sources": list(self.allowed_invocation_sources),
            "allowed_lifecycles": list(self.allowed_lifecycles),
            "allowed_operations": list(self.allowed_operations),
            "allowed_output_formats": list(self.allowed_output_formats),
            "allowed_results": list(self.allowed_results),
            "allowed_terminal_environments": list(self.allowed_terminal_environments),
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


def default_cli_event_policy() -> CommunityCliEventPolicy:
    return CommunityCliEventPolicy.default()
