"""Valid and invalid request factories for Community Cloud ingestion routes."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def valid_telemetry_body(**overrides: object) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "event_id": "evt-sv7-0001",
        "event_type": "application_started",
        "client": {
            "name": "codestrata_cli",
            "version": "0.2.0",
            "platform": "darwin",
        },
    }
    body.update(overrides)
    return body


def valid_assessment_metadata_body(**overrides: object) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "event_id": "amd-sv7-0001",
        "client": {
            "name": "codestrata_cli",
            "version": "0.2.0",
            "platform": "darwin",
        },
        "assessment": {
            "assessment_schema_version": "1.2",
            "assessment_status": "completed",
            "assessment_mode": "deterministic",
            "executed_heads": ["technology_inventory", "security"],
            "finding_count": 3,
            "recommendation_count": 2,
            "priority_action_count": 1,
            "roadmap_initiative_count": 0,
            "evidence_count": 4,
            "limitation_count": 1,
        },
        "repository": {
            "primary_language": "python",
            "language_count": 1,
            "dependency_ecosystem_count": 1,
            "file_count_bucket": "51_to_200",
            "source_file_count_bucket": "11_to_50",
            "test_file_count_bucket": "1_to_10",
            "repository_shape": "application",
            "has_tests": True,
            "has_build_files": True,
            "has_dependency_manifests": True,
        },
        "execution": {
            "duration_bucket": "10s_to_30s",
            "result": "succeeded",
            "ai_used": False,
            "offline_mode": True,
            "client_version": "0.2.0",
            "platform": "darwin",
        },
        "artifacts": {
            "report_json_generated": True,
            "findings_json_generated": True,
            "recommendations_json_generated": True,
            "html_report_generated": True,
            "artifact_count": 4,
        },
    }
    body.update(overrides)
    return body


def valid_cli_event_body(**overrides: object) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "event_id": "cli-sv7-0001",
        "client": {
            "name": "codestrata_cli",
            "version": "0.2.0",
            "platform": "darwin",
        },
        "event": {
            "operation": "assess",
            "lifecycle": "completed",
            "result": "succeeded",
            "duration_bucket": "5s_to_30s",
        },
        "context": {
            "execution_mode": "deterministic",
            "output_format": "multiple",
            "offline_mode": True,
            "ai_requested": False,
            "selected_assessment_heads": ["security", "technology_inventory"],
            "invocation_source": "terminal",
            "terminal_environment": "interactive",
        },
    }
    body.update(overrides)
    return body


def valid_extension_event_body(**overrides: object) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "event_id": "ext-sv7-0001",
        "client": {
            "name": "vscode_extension",
            "version": "0.2.0",
            "editor": "vscode",
            "editor_version": "1.85.0",
            "platform": "darwin",
        },
        "event": {
            "operation": "assess",
            "lifecycle": "completed",
            "result": "succeeded",
            "duration_bucket": "5s_to_30s",
        },
        "context": {
            "invocation_source": "command_palette",
            "user_initiated": True,
            "offline_mode": True,
            "ai_requested": False,
            "selected_assessment_heads": ["security", "technology_inventory"],
            "report_surface": "editor_tab",
            "workspace_state": "folder_open",
        },
    }
    body.update(overrides)
    return body


def valid_ai_usage_body(**overrides: object) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": "1.0",
        "event_id": "ai-sv7-0001",
        "client": {
            "name": "codestrata_cli",
            "version": "0.2.0",
            "platform": "darwin",
        },
        "usage": {
            "capability": "modernization_advisor",
            "execution_mode": "deterministic_with_ai",
            "provider_ownership": "customer_managed",
            "provider_family": "openai",
            "model_family": "gpt_family",
            "outcome": "succeeded",
            "duration_bucket": "1s_to_5s",
            "input_token_bucket": "1k_to_4k",
            "output_token_bucket": "1_to_1k",
            "total_token_bucket": "1k_to_4k",
            "tool_usage": "not_used",
            "rag_usage": "not_used",
            "graph_usage": "not_used",
        },
        "context": {
            "assessment_head": "modernization",
            "invocation_source": "cli",
            "offline_mode": False,
            "user_initiated": True,
            "data_scope": "aggregate_assessment_metadata",
            "output_usage": "included_in_report",
        },
    }
    body.update(overrides)
    return body


def body_for(kind: str, **overrides: object) -> dict[str, Any]:
    builders = {
        "telemetry": valid_telemetry_body,
        "assessment_metadata": valid_assessment_metadata_body,
        "cli_events": valid_cli_event_body,
        "extension_events": valid_extension_event_body,
        "ai_usage": valid_ai_usage_body,
    }
    return builders[kind](**overrides)


def conflict_body_for(kind: str) -> dict[str, Any]:
    if kind == "telemetry":
        return body_for(kind, properties={"feature": "other", "outcome": "failed"})
    if kind == "assessment_metadata":
        body = body_for(kind)
        body["assessment"] = {**body["assessment"], "finding_count": 99}
        return body
    if kind == "cli_events":
        body = body_for(kind)
        body["event"] = {**body["event"], "operation": "doctor"}
        return body
    if kind == "extension_events":
        body = body_for(kind)
        body["event"] = {**body["event"], "operation": "open_report"}
        return body
    body = body_for(kind)
    body["usage"] = {**body["usage"], "provider_family": "aws_bedrock"}
    return body


def mismatched_client_body(kind: str) -> dict[str, Any]:
    """Schema-valid body whose client.name does not match a CLI principal."""

    body = deepcopy(body_for(kind))
    if kind == "extension_events":
        # Extension schema requires editor fields; CLI name is the mismatch shape.
        body["client"] = {
            "name": "codestrata_cli",
            "version": "0.2.0",
            "platform": "darwin",
        }
        return body
    # Telemetry / assessment / AI / CLI: vscode_extension client without editor extras.
    body["client"] = {
        "name": "vscode_extension",
        "version": "0.2.0",
        "platform": "darwin",
    }
    return body
