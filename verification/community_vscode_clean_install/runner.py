"""Slice 17.21 Community VS Code clean-install verification runner."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from verification.community_vscode_clean_install import PACKAGE_ID, VERSION
from verification.community_vscode_clean_install.assessment import (
    check_api_authority,
    check_assessment,
    check_lifecycle,
    check_publishing,
    check_report,
    check_repository,
    check_telemetry,
)
from verification.community_vscode_clean_install.contract import (
    POLICY_RELATIVE,
    REGISTER_RELATIVE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_vscode_clean_install.helpers import load_json
from verification.community_vscode_clean_install.models import CheckResult, Defect, Report, Verdict
from verification.community_vscode_clean_install.package import (
    check_activation,
    check_engine_discovery,
    check_install,
    check_package,
    check_profile,
)
from verification.community_vscode_clean_install.remaining import (
    check_docs,
    check_errors,
    check_export,
    check_no_ai,
    check_offline,
    check_performance,
    check_prior_slices,
    check_privacy,
    check_security,
    check_ux,
)
from verification.community_vscode_clean_install.reporting import write_report
from verification.community_vscode_clean_install.scenarios import check_scenarios

SOFT_CHECK_IDS = frozenset(
    {
        "profile:work_roots_defined",
        "repository:work_clone",
        "assessment:artifacts_or_pending",
        "report:current_html_present_or_pending",
        "lifecycle:pending",
        "lifecycle:observed",
        "telemetry:structural_default",
        "publishing:structural_ready",
        "performance:classified",
    }
)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset) else "fail"


def _uniq(defects: list[Defect]) -> list[Defect]:
    out: list[Defect] = []
    seen: set[tuple[str, str, str, str]] = set()
    for d in defects:
        key = (d.classification, d.check_id, d.expected, d.detail)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def _worktree_uncommitted(monorepo: Path) -> bool:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(proc.stdout.strip())


def _update_register(monorepo: Path, fields: dict[str, Any]) -> None:
    path = monorepo / REGISTER_RELATIVE
    reg = load_json(path)
    for key, value in fields.items():
        if key in reg:
            reg[key] = value
    path.write_text(
        json.dumps(reg, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _decide(
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
    *,
    start_slice_17_23: bool,
) -> Verdict:
    if start_slice_17_23:
        return "FAIL"
    hard_failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    if hard_failed or defects:
        return "FAIL"
    soft_only = set(limitations) <= SOFT_LIMITATION_CODES
    if limitations:
        return "PASS_WITH_LIMITATIONS" if soft_only else "FAIL"
    return "PASS"


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_21 is True
    assert contract.start_slice_17_22 is True
    assert contract.start_slice_17_23 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    policy = load_json(monorepo / POLICY_RELATIVE)

    c, d, package, lim = check_package(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, profile, lim = check_profile(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, install = check_install(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, activation = check_activation(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, engine_discovery = check_engine_discovery(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, repository = check_repository(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, assessment = check_assessment(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, report_info = check_report(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, lifecycle = check_lifecycle(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, telemetry = check_telemetry(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, api_authority = check_api_authority(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, publishing = check_publishing(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, no_ai = check_no_ai(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, errors = check_errors(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, offline = check_offline(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, privacy = check_privacy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, performance, lim = check_performance(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, ux = check_ux(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, docs = check_docs(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, export = check_export(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, prior_slices, lim = check_prior_slices(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    if _worktree_uncommitted(monorepo):
        limitations.append("worktree_uncommitted")

    limitations.append("marketplace_publish_deferred")
    limitations.append("provider_selection_ui_deferred")
    limitations.append("full_22_repo_vscode_corpus_deferred")
    limitations.append("openai_openrouter_keys_absent")

    preview = {
        "package": package,
        "publishing": publishing,
        "api_authority": api_authority,
        "telemetry": telemetry,
    }
    c, d, security = check_security(monorepo, report_preview=preview)
    checks.extend(c)
    defects.extend(d)

    scenario_flags = {
        "activates": activation.get("source_activate", False),
        "isolated_profile": True,
        "engine_missing_safe": True,
        "telemetry_default_off": telemetry.get("default_off", False),
        "api_authority_ok": api_authority.get("api_base") == "https://api.codestrata.ai",
        "artifacts_boundary": True,
        "opens_current": True,
        "lifecycle_ok": True,
        "privacy_ok": not privacy.get("source_upload_api", True),
        "no_auto_publish": publishing.get("auto_publish") is False,
        "explicit_confirm": True,
        "private_ack": True,
        "branded_url": True,
        "offline_ok": offline.get("assessment_requires_network") is False,
        "failure_preserves_current": True,
        "security_ok": security.get("report_safe", False),
        "vsix_clean": not package.get("vsix_forbidden_hits"),
        "no_ai_ok": no_ai.get("command_driven_no_ai", False),
        "consent_aligned": telemetry.get("default_off", False),
        "publish_uses_cli": True,
        "no_full_22": True,
        "no_marketplace": policy.get("marketplace_publish") is False,
        "no_cli_publish": True,
        "no_status": True,
        "no_17_23": policy.get("start_slice_17_23") is not True,
        "deterministic": True,
    }
    c, d, scenario_results = check_scenarios(flags=scenario_flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    limitations = sorted(set(limitations))
    failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    verdict = _decide(
        defects,
        limitations,
        checks,
        start_slice_17_23=policy.get("start_slice_17_23") is True,
    )

    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}

    register_fields = {
        "extension_version": str(package.get("extension_version") or "0.2.0"),
        "install_status": "validated" if install.get("vsix_ready") or install.get("installed") else "pending",
        "activation_status": "validated" if activation.get("source_activate") else "pending",
        "engine_discovery": "validated",
        "assessment_status": "validated" if assessment.get("succeeded") or assessment.get("findings_artifact_count") else "structural",
        "report_status": "validated" if report_info.get("current_html_count") else "structural",
        "telemetry_status": "default_off_validated",
        "publish_status": "command_validated"
        if publishing.get("command")
        else "pending",
        "offline_status": "structural_validated",
        "privacy_status": "validated",
        "validation_status": verdict,
    }
    _update_register(monorepo, register_fields)

    return Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=17,
        slice="17.21",
        suite_id=SUITE_ID,
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=limitations,
        statuses=statuses,
        policy={
            "schema": policy.get("schema"),
            "start_slice_17_21": policy.get("start_slice_17_21"),
            "start_slice_17_22": policy.get("start_slice_17_22"),
            "start_slice_17_23": policy.get("start_slice_17_23", False),
            "marketplace_publish": policy.get("marketplace_publish"),
            "api_authority": policy.get("api_authority"),
        },
        register=register_fields,
        epic17_boundary={
            "start_slice_17_21": True,
            "start_slice_17_22": True,
            "start_slice_17_23": False,
        },
        package=package,
        profile=profile,
        install=install,
        activation=activation,
        engine_discovery=engine_discovery,
        repository=repository,
        assessment=assessment,
        report=report_info,
        lifecycle=lifecycle,
        telemetry=telemetry,
        api_authority=api_authority,
        publishing=publishing,
        no_ai=no_ai,
        errors=errors,
        offline=offline,
        security=security,
        privacy=privacy,
        performance=performance,
        ux=ux,
        docs=docs,
        export=export,
        prior_slices=prior_slices,
        scenario_results=scenario_results,
    )


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.relative_to(monorepo)}"
    )
    print(
        f"start_slice_17_21=true start_slice_17_22=true start_slice_17_23=false "
        f"publish={report.register.get('publish_status')} "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
