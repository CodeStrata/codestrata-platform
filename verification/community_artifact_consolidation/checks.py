"""Checks for Slice 17.12 artifact consolidation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_artifact_consolidation.contract import (
    ARTIFACT_ROOT,
    ASSESSMENTS_RELATIVE,
    CLI_REPORT,
    CONTRACT_RELATIVE,
    ENGINE_ARTIFACTS_PACKAGE,
    GITIGNORE,
    INTELLIGENCE_RELATIVE,
    MANIFESTS_RELATIVE,
    MODERNIZATION_SERIALIZATION,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
    REPORT_PATHS,
    SCAN_BOUNDARY,
    TEMPORARY_RELATIVE,
    VALIDATION_RELATIVE,
    VSCODE_POLICY,
    VSCODE_SETTINGS,
)
from verification.community_artifact_consolidation.helpers import read_json, read_text
from verification.community_artifact_consolidation.models import CheckResult, Defect


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
) -> None:
    checks.append(CheckResult(check_id, bool(ok), detail, category))
    if not ok:
        defects.append(Defect(category, check_id, "pass", detail))


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict = {}
    register: dict = {}
    policy_path = monorepo / POLICY_RELATIVE
    register_path = monorepo / REGISTER_RELATIVE
    _add(checks, defects, "policy:exists", policy_path.is_file(), POLICY_RELATIVE, "policy")
    if policy_path.is_file():
        policy = read_json(policy_path)
        _add(
            checks,
            defects,
            "policy:schema",
            policy.get("schema") == POLICY_SCHEMA,
            str(policy.get("schema")),
            "policy",
        )
        _add(checks, defects, "policy:start_17_12", policy.get("start_slice_17_12") is True, "true", "policy")
        _add(checks, defects, "policy:start_17_13_false", policy.get("start_slice_17_13") is False, "false", "policy")
        _add(
            checks,
            defects,
            "policy:artifact_root",
            policy.get("artifact_root") == ARTIFACT_ROOT,
            str(policy.get("artifact_root")),
            "policy",
        )
        _add(
            checks,
            defects,
            "policy:data_lake_forbidden",
            policy.get("data_lake_report_upload_forbidden") is True,
            "true",
            "policy",
        )
        _add(
            checks,
            defects,
            "policy:heads_source_of_truth",
            policy.get("heads_remain_source_of_truth") is True,
            "true",
            "policy",
        )
    _add(checks, defects, "register:exists", register_path.is_file(), REGISTER_RELATIVE, "policy")
    if register_path.is_file():
        register = read_json(register_path)
        _add(
            checks,
            defects,
            "register:schema",
            register.get("schema") == REGISTER_SCHEMA,
            str(register.get("schema")),
            "policy",
        )
    contract_path = monorepo / CONTRACT_RELATIVE
    _add(checks, defects, "contract:exists", contract_path.is_file(), CONTRACT_RELATIVE, "policy")
    return checks, defects, policy, register


def check_engine_layout(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}
    pkg = monorepo / ENGINE_ARTIFACTS_PACKAGE
    _add(checks, defects, "engine:artifacts_package", pkg.is_dir(), ENGINE_ARTIFACTS_PACKAGE, "engine")
    for name in ("__init__.py", "layout.py", "heads.py", "manifest.py", "migration.py"):
        _add(checks, defects, f"engine:artifacts:{name}", (pkg / name).is_file(), name, "engine")

    report_paths = read_text(monorepo / REPORT_PATHS)
    _add(
        checks,
        defects,
        "engine:default_output",
        ".codestrata-artifacts/assessments" in report_paths or 'ASSESSMENTS_DIRNAME' in report_paths,
        "default assessments root",
        "engine",
    )
    _add(
        checks,
        defects,
        "engine:assessment_html",
        "assessment.html" in report_paths or "ASSESSMENT_HTML_BASENAME" in report_paths,
        "assessment.html",
        "engine",
    )

    serialization = read_text(monorepo / MODERNIZATION_SERIALIZATION)
    _add(
        checks,
        defects,
        "engine:lightweight_manifest_writer",
        "build_assessment_manifest" in serialization and "write_assessment_manifest" in serialization,
        "manifest writer wired",
        "engine",
    )
    _add(
        checks,
        defects,
        "engine:no_giant_json_persist",
        "build_assessment_manifest" in serialization
        and "write_assessment_manifest" in serialization
        and "is a manifest" in serialization,
        "manifest-only persist",
        "engine",
    )

    # Head writers use resolve_head_path
    arch = read_text(monorepo / "engine/src/codestrata/application/architecture/assessment/artifacts.py")
    _add(checks, defects, "engine:heads_writer", "resolve_head_path" in arch, "architecture heads path", "engine")

    cli = read_text(monorepo / CLI_REPORT)
    _add(
        checks,
        defects,
        "cli:default_output",
        ".codestrata-artifacts/assessments" in cli,
        "cli open default",
        "cli",
    )
    _add(checks, defects, "cli:assessment_html_search", "assessment.html" in cli, "search assessment.html", "cli")

    vscode_settings = read_text(monorepo / VSCODE_SETTINGS)
    _add(
        checks,
        defects,
        "vscode:default_output",
        ".codestrata-artifacts/assessments" in vscode_settings,
        "vscode default",
        "vscode",
    )
    vscode_policy = read_text(monorepo / VSCODE_POLICY)
    _add(
        checks,
        defects,
        "vscode:assessment_html",
        'assessment.html' in vscode_policy,
        "vscode html basename",
        "vscode",
    )

    gitignore = read_text(monorepo / GITIGNORE)
    _add(checks, defects, "gitignore:artifacts", ".codestrata-artifacts/" in gitignore, "ignored", "repo")

    scan = read_text(monorepo / SCAN_BOUNDARY)
    _add(checks, defects, "scan_boundary:exclude", ".codestrata-artifacts" in scan, "excluded", "engine")

    summary["artifact_root"] = ARTIFACT_ROOT
    summary["assessments"] = ASSESSMENTS_RELATIVE
    summary["intelligence"] = INTELLIGENCE_RELATIVE
    summary["validation"] = VALIDATION_RELATIVE
    summary["manifests"] = MANIFESTS_RELATIVE
    summary["temporary"] = TEMPORARY_RELATIVE
    return checks, defects, summary


def check_verification_output_paths(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    helper = monorepo / "verification/artifact_output.py"
    _add(checks, defects, "verification:artifact_output_helper", helper.is_file(), "present", "validation")
    sample = monorepo / "verification/community_production_site_ux_access/contract.py"
    text = read_text(sample)
    _add(
        checks,
        defects,
        "verification:sv17_11_path_moved",
        ".codestrata-artifacts/validation/suites/sv17-11" in text,
        "sv17-11 output",
        "validation",
    )
    this = monorepo / "verification/community_artifact_consolidation/contract.py"
    this_text = read_text(this)
    _add(
        checks,
        defects,
        "verification:sv17_12_path",
        ".codestrata-artifacts/validation/suites/sv17-12" in this_text,
        "sv17-12 output",
        "validation",
    )
    return checks, defects, {"helper": helper.is_file()}


def check_epic17_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary = {"start_slice_17_12": True, "start_slice_17_13": False}
    policy = read_json(monorepo / POLICY_RELATIVE) if (monorepo / POLICY_RELATIVE).is_file() else {}
    _add(checks, defects, "boundary:17_12_true", policy.get("start_slice_17_12") is True, "true", "epic17_boundary")
    _add(checks, defects, "boundary:17_13_false", policy.get("start_slice_17_13") is False, "false", "epic17_boundary")
    slice_13 = monorepo / "platform/policies/community_cloud_slice_17_13_policy.json"
    _add(checks, defects, "boundary:17_13_policy_absent", not slice_13.exists(), "absent", "epic17_boundary")
    return checks, defects, summary
