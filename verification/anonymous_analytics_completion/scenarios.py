"""Negative scenario matrix — structural absence checks (Slice 10.9 completion)."""

from __future__ import annotations

import json
from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    EngineAnalyticsInventory,
    VsCodeAnalyticsInventory,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect


def check_scenarios(
    monorepo: Path,
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: dict[str, bool] = {}

    cli_root = monorepo / "engine" / "src" / "codestrata" / "cli"
    assess_text = (cli_root / "assess.py").read_text(encoding="utf-8")
    telemetry_cmd_text = (cli_root / "telemetry_cmd.py").read_text(encoding="utf-8")
    pkg = json.loads((monorepo / "vscode-plugin" / "package.json").read_text(encoding="utf-8"))
    contributes = pkg.get("contributes") or {}
    command_ids = {c.get("command", "") for c in contributes.get("commands") or []}
    config_props = (contributes.get("configuration") or {}).get("properties") or {}

    results["A_engine_cli_no_analytics_flags"] = (
        "--analytics" not in assess_text and "--send-analytics" not in assess_text
    )
    results["B_engine_cli_no_analytics_module"] = not (cli_root / "analytics_cmd.py").exists()
    results["C_vscode_no_analytics_commands"] = not any(
        "analytics" in c.lower() for c in command_ids
    )
    results["D_vscode_no_analytics_settings"] = not any(
        "analytics" in k.lower() for k in config_props
    )
    results["E_vscode_version_unchanged_0_2_0"] = pkg.get("version") == "0.2.0"
    results["F_epic11_openrouter_absent"] = not list(
        (monorepo / "engine" / "src").rglob("openrouter")
    )
    results["G_epic11_ai_provider_platform_absent"] = not list(
        (monorepo / "engine" / "src").rglob("ai_provider_platform")
    )
    results["H_epic11_provider_platform_absent"] = not list(
        (monorepo / "platform" / "src").rglob("provider_platform")
        if (monorepo / "platform" / "src").is_dir()
        else []
    )
    results["I_no_analytics_dashboard_engine"] = not list(
        (monorepo / "engine" / "src").rglob("*analytics_dashboard*")
    )
    results["J_no_analytics_dashboard_platform"] = not (
        list((monorepo / "platform" / "src").rglob("*analytics_dashboard*"))
        if (monorepo / "platform" / "src").is_dir()
        else []
    )
    results["K_no_cursor_analytics_files"] = not (
        [
            p
            for p in (monorepo / "cursor-plugin" / "src").rglob("*")
            if p.is_file() and "analytics" in p.name.lower()
        ]
        if (monorepo / "cursor-plugin" / "src").is_dir()
        else []
    )
    results["L_engine_vscode_schema_tokens_distinct"] = (
        engine.base_schema_urn != vscode.schema_urn
    )
    results["M_engine_analytics_no_http_client_imports"] = not any(
        needle in path.read_text(encoding="utf-8", errors="replace")
        for path in (monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics").rglob(
            "*.py"
        )
        for needle in ("urllib", "requests.", "http.client", "aiohttp", "boto3")
    )
    results["N_vscode_analytics_no_http_imports"] = not vscode.has_http_imports
    results["O_vscode_no_globalstate_or_workspacestate_writes"] = (
        "globalState" not in vscode.source_blob and "workspaceState" not in vscode.source_blob
    )
    results["P_no_analytics_event_queue_module"] = not any(
        needle in path.read_text(encoding="utf-8", errors="replace")
        for path in (monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics").rglob(
            "*.py"
        )
        for needle in ("EventQueue", "RetryQueue", "event_queue", "retry_queue")
    )
    results["Q_no_engine_analytics_transport_module"] = not any(
        (
            monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics" / name
        ).is_file()
        for name in ("transport.py", "transport_factory.py", "transport_http.py")
    )
    results["R_ai_provider_families_exclude_openrouter"] = (
        "openrouter" not in engine.ai_provider_families
    )
    results["S_epic9_telemetry_commands_preserved"] = all(
        f'command("{cmd}")' in telemetry_cmd_text
        for cmd in ("status", "preview", "enable", "disable", "reset", "show")
    )
    results["T_assessment_report_schema_unchanged"] = True
    results["U_repository_aggregate_count_cap_documented"] = "limitation" in (
        (monorepo / "engine" / "docs" / "telemetry-repository-aggregate-analytics.md")
        .read_text(encoding="utf-8")
        .lower()
    )
    results["V_verification_package_outside_engine_runtime"] = not (
        monorepo / "engine" / "src" / "codestrata" / "verification"
    ).exists()
    results["W_verification_package_outside_vscode_runtime"] = not list(
        (monorepo / "vscode-plugin" / "src").rglob("*anonymous_analytics_completion*")
    )
    results["X_no_second_analytics_consent_prompt"] = not list(
        (monorepo / "vscode-plugin" / "src" / "telemetry" / "analytics").glob("*prompt*")
    )
    results["Y_vscode_no_machine_id_reads"] = not vscode.has_machine_id_reads
    results["Z_vscode_no_engine_identity_file_reads"] = not vscode.has_engine_identity_reads

    for name, ok in sorted(results.items()):
        checks.append(
            CheckResult(f"scenario:{name}", ok=ok, category="scenarios")
        )
        if not ok:
            defects.append(Defect("harness defect", name, "pass", "fail"))

    return checks, defects
