"""Community Cloud current API + historical deserialize checks (Slice 12.4)."""

from __future__ import annotations

from pathlib import Path

from verification.community_client_boundary_cleanup.models import CheckResult, Defect


def _extension_body(*, cursor: bool) -> dict[str, object]:
    client: dict[str, object]
    if cursor:
        client = {
            "name": "cursor_extension",
            "version": "0.2.0",
            "editor": "cursor",
            "editor_version": "0.45.0",
            "platform": "darwin",
        }
    else:
        client = {
            "name": "vscode_extension",
            "version": "0.2.0",
            "editor": "vscode",
            "editor_version": "1.85.0",
            "platform": "darwin",
        }
    return {
        "schema_version": "1.0",
        "event_id": "ext-evt-sv124-0001",
        "client": client,
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


def _ai_usage_body(*, cursor: bool) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "event_id": "ai-usage-sv124-0001",
        "client": {
            "name": "cursor_extension" if cursor else "codestrata_cli",
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


def check_api_contracts(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _ = monorepo

    try:
        from codestrata_platform.community_cloud_api.ai_usage.enums import (
            ALLOWED_AI_USAGE_CLIENTS,
            SCHEMA_AI_USAGE_CLIENTS,
        )
        from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
        from codestrata_platform.community_cloud_api.ai_usage.validation import (
            validate_ai_usage_semantics,
        )
        from codestrata_platform.community_cloud_api.extension_events.enums import (
            ALLOWED_EXTENSION_CLIENTS,
            SCHEMA_EXTENSION_CLIENTS,
        )
        from codestrata_platform.community_cloud_api.extension_events.validation import (
            validate_extension_event_semantics,
        )
        from codestrata_platform.community_cloud_api.historical_client_compatibility import (
            deserialize_historical_extension_event_payload,
        )
    except Exception as exc:  # pragma: no cover
        return (
            [CheckResult("api:import_failed", ok=False, detail=type(exc).__name__, category="api")],
            [Defect("API compatibility defect", "imports", "importable", type(exc).__name__)],
        )

    checks.append(
        CheckResult(
            "api:active_extension_clients",
            ok=ALLOWED_EXTENSION_CLIENTS == ("vscode_extension",),
            detail="allowed_extension=vscode_extension",
            category="api",
        )
    )
    checks.append(
        CheckResult(
            "api:schema_extension_retains_historical",
            ok="cursor_extension" in SCHEMA_EXTENSION_CLIENTS,
            detail="schema retains historical cursor_extension",
            category="api",
        )
    )
    checks.append(
        CheckResult(
            "api:active_ai_usage_excludes_cursor",
            ok="cursor_extension" not in ALLOWED_AI_USAGE_CLIENTS,
            detail="allowed_ai_usage excludes cursor",
            category="api",
        )
    )
    checks.append(
        CheckResult(
            "api:schema_ai_usage_retains_historical",
            ok="cursor_extension" in SCHEMA_AI_USAGE_CLIENTS,
            detail="schema retains historical cursor_extension",
            category="api",
        )
    )

    try:
        model = deserialize_historical_extension_event_payload(_extension_body(cursor=True))
        hist_ok = model.client.name == "cursor_extension"
        reject_ok = any(
            err.field == "client.name" for err in validate_extension_event_semantics(model)
        )
    except Exception as exc:
        hist_ok = False
        reject_ok = False
        defects.append(
            Defect(
                "historical-deserialization defect",
                "extension_event",
                "deserialize+reject",
                type(exc).__name__,
            )
        )

    checks.append(
        CheckResult(
            "api:historical_extension_deserializes",
            ok=hist_ok,
            detail="historical extension payload deserializes",
            category="api",
        )
    )
    checks.append(
        CheckResult(
            "api:current_policy_rejects_cursor",
            ok=reject_ok,
            detail="current policy rejects retired extension client",
            category="api",
        )
    )

    try:
        ai_model = AiUsageRequest.model_validate(_ai_usage_body(cursor=True))
        ai_hist_ok = ai_model.client.name == "cursor_extension"
        ai_reject_ok = any(
            err.field == "client.name" for err in validate_ai_usage_semantics(ai_model)
        )
    except Exception as exc:
        ai_hist_ok = False
        ai_reject_ok = False
        defects.append(
            Defect(
                "historical-deserialization defect",
                "ai_usage",
                "deserialize+reject",
                type(exc).__name__,
            )
        )

    checks.append(
        CheckResult(
            "api:historical_ai_usage_deserializes",
            ok=ai_hist_ok,
            detail="historical ai_usage payload deserializes",
            category="api",
        )
    )
    checks.append(
        CheckResult(
            "api:current_ai_usage_policy_rejects_cursor",
            ok=ai_reject_ok,
            detail="current policy rejects retired ai_usage client",
            category="api",
        )
    )

    vscode_ok = True
    try:
        from codestrata_platform.community_cloud_api.extension_events.models import (
            ExtensionEventRequest,
        )

        vscode_model = ExtensionEventRequest.model_validate(_extension_body(cursor=False))
        vscode_ok = (
            vscode_model.client.name == "vscode_extension"
            and not validate_extension_event_semantics(vscode_model)
        )
    except Exception:
        vscode_ok = False
    checks.append(
        CheckResult(
            "api:vscode_remains_valid",
            ok=vscode_ok,
            detail="vscode_extension remains accepted",
            category="api",
        )
    )
    if not vscode_ok:
        defects.append(
            Defect("VS Code regression", "extension_event", "vscode valid", "invalid")
        )

    return checks, defects
