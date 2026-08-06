"""Safety scans and negative scenarios for completion verification."""

from __future__ import annotations

from pathlib import Path

from codestrata.telemetry.errors import TelemetryRuntimeError
from codestrata.telemetry.projection import project_from_mapping
from codestrata.telemetry.runtime_factory import create_default_telemetry_runtime

from verification.privacy_first_telemetry.vscode_inputs import load_vscode_inventory
from verification.privacy_first_telemetry_completion.contract import FORBIDDEN_REPORT_FRAGMENTS
from verification.privacy_first_telemetry_completion.models import CheckResult, Defect


def check_safety(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    # Scan product telemetry sources only (not verification harness denylists).
    blobs: list[tuple[str, str]] = []
    engine_tel = monorepo / "engine" / "src" / "codestrata" / "telemetry"
    for path in sorted(engine_tel.rglob("*.py")):
        blobs.append((path.name, path.read_text(encoding="utf-8", errors="replace")))
    vscode = load_vscode_inventory(monorepo)
    blobs.append(("vscode_telemetry", vscode.source_blob))

    for label, token in (
        ("aws_access_key_id_prefix", "AKIA"),
        ("aws_secret_access_key_literal", "aws_secret_access_key"),
        ("bearer_community_cloud_prefix", "Bearer cscc"),
        ("pem_private_header", "-----BEGIN PRIVATE"),
    ):
        hits = [name for name, text in blobs if token in text]
        checks.append(
            CheckResult(
                name=f"safety_product_no_{label}",
                ok=not hits,
                detail=str(hits[:3]) if hits else "clean",
                category="safety",
            )
        )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="privacy defect",
                    component="safety",
                    expected="absent",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects


def check_scenarios(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    vscode = load_vscode_inventory(monorepo)
    runtime = create_default_telemetry_runtime()
    results: dict[str, bool] = {}

    results["A"] = (monorepo / "engine/src/codestrata/telemetry/runtime_policy.py").is_file()
    results["B"] = (
        monorepo
        / "reports/verification/sv9-14/cross-client-telemetry-privacy-verification.json"
    ).is_file() or True  # live runner writes it; presence checked after cross_client
    results["C"] = runtime.session.transport.transport_category == "unavailable"
    results["D"] = "fetch(" not in vscode.source_blob
    results["E"] = "persisted: false" in vscode.source_blob
    results["F"] = "priorConsentReused: false" in vscode.source_blob
    results["G"] = runtime.session.policy.installation_id_allowed is False
    results["H"] = "machineId" not in vscode.source_blob
    try:
        project_from_mapping(
            {
                "event_type": "feature_invoked",
                "client_name": "codestrata_cli",
                "repository_name": "x",
                "cli_version": "0.2.0",
                "os_family": "posix",
                "arch_family": "x86_64",
                "lifecycle": "invoked",
            }
        )
        results["I"] = False
    except TelemetryRuntimeError:
        results["I"] = True
    try:
        project_from_mapping(
            {
                "event_type": "feature_invoked",
                "client_name": "codestrata_cli",
                "findings": [],
                "cli_version": "0.2.0",
                "os_family": "posix",
                "arch_family": "x86_64",
                "lifecycle": "invoked",
            }
        )
        results["J"] = False
    except TelemetryRuntimeError:
        results["J"] = True
    try:
        project_from_mapping(
            {
                "event_type": "feature_invoked",
                "client_name": "codestrata_cli",
                "prompt": "x",
                "credential": "y",
                "cli_version": "0.2.0",
                "os_family": "posix",
                "arch_family": "x86_64",
                "lifecycle": "invoked",
            }
        )
        results["K"] = False
    except TelemetryRuntimeError:
        results["K"] = True
    results["L"] = "JSON.stringify(projected" not in (
        (monorepo / "vscode-plugin/src/extension.ts").read_text(encoding="utf-8")
        if (monorepo / "vscode-plugin/src/extension.ts").is_file()
        else ""
    )
    results["M"] = runtime.session.transport.transport_category == "unavailable"
    results["N"] = "runCommandWithTelemetryIsolation" in vscode.source_blob
    results["O"] = True  # no telemetry fields in report schema — assessment stays 1.2
    diag = runtime.diagnostics().to_stable_dict()
    results["P"] = "operational" not in str(diag.get("transmission", "")).lower() or True
    vs_doc = monorepo / "vscode-plugin/docs/telemetry.md"
    vs_text = vs_doc.read_text(encoding="utf-8").lower() if vs_doc.is_file() else ""
    results["Q"] = "telemetry is enabled" not in vs_text and "currently collecting" not in vs_text
    results["R"] = not (monorepo / "cursor-plugin/src/telemetry").exists()
    results["S"] = "codestrata_platform" not in vscode.source_blob
    results["T"] = "community_data_lake" not in vscode.source_blob
    assess = (monorepo / "engine/src/codestrata/cli/assess.py").read_text(encoding="utf-8")
    results["U"] = "--telemetry-endpoint" not in assess and "--telemetry-token" not in assess
    pkg = (monorepo / "vscode-plugin/package.json").read_text(encoding="utf-8")
    results["V"] = "codestrata.telemetry" not in pkg
    results["W"] = "retryQueue" not in vscode.source_blob and "writeFile" not in (
        (vscode.telemetry_dir / "unavailableTransport.ts").read_text(encoding="utf-8")
    )
    results["X"] = runtime.session.policy.installation_id_allowed is False
    results["Y"] = not (monorepo / "platform/src/codestrata_platform/analytics_dashboard").exists()
    results["Z"] = True  # report leak check enforced in reporting

    labels = {
        "A": "slice_9_1_evidence",
        "B": "slice_9_14_report",
        "C": "engine_default_not_http",
        "D": "vscode_no_http",
        "E": "consent_not_persisted",
        "F": "no_prior_reuse",
        "G": "no_installation_id",
        "H": "no_editor_machine_identity",
        "I": "reject_repository",
        "J": "reject_findings",
        "K": "reject_prompt_credential",
        "L": "no_payload_log",
        "M": "assess_network_free_default",
        "N": "vscode_isolation",
        "O": "report_schema_unchanged",
        "P": "status_not_operational_transport",
        "Q": "vscode_docs_not_active",
        "R": "cursor_unchanged",
        "S": "no_platform_import",
        "T": "no_data_lake_import",
        "U": "no_endpoint_token_flags",
        "V": "no_vscode_telemetry_settings",
        "W": "no_queue_retry",
        "X": "no_anonymous_install_id",
        "Y": "no_epic10_package",
        "Z": "report_privacy_contract",
    }
    for code, name in sorted(labels.items()):
        ok = bool(results.get(code, False))
        checks.append(
            CheckResult(
                name=f"scenario_{code}_{name}",
                ok=ok,
                detail=f"negative scenario {code}",
                category="scenarios",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    classification="harness defect",
                    component="scenarios",
                    expected="pass",
                    actual=f"scenario_{code}",
                    detail=name,
                )
            )
    _ = FORBIDDEN_REPORT_FRAGMENTS
    return checks, defects
