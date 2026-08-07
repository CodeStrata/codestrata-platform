"""Slice 13.15 Epic 13 completion runner."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_epic13_completion import VSCODE_EPIC13_COMPLETION_ID
from verification.vscode_epic13_completion.checks import (
    assemble_domain_checks,
    check_release_posture_fields,
    check_slice_matrix_integrity,
)
from verification.vscode_epic13_completion.contract import (
    ALLOWED_LIMITATIONS,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV1315_OUTPUT_RELATIVE,
    TOTAL_SLICES,
    default_contract,
    monorepo_root_from_here,
)
from verification.vscode_epic13_completion.models import (
    CheckResult,
    Defect,
    Verdict,
    VsCodeEpic13CompletionReport,
)
from verification.vscode_epic13_completion.policy_registry import (
    build_policy_registry,
    check_policy_registry,
)
from verification.vscode_epic13_completion.prior_runners import run_prior_slice_verifiers
from verification.vscode_epic13_completion.safety import report_text_is_safe
from verification.vscode_epic13_completion.schema_registry import (
    build_schema_registry,
    check_schema_registry,
)
from verification.vscode_epic13_completion.slice_matrix import build_slice_matrix


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(monorepo: Path) -> VsCodeEpic13CompletionReport:
    contract = default_contract()
    assert contract.start_epic_14 is False
    assert contract.marketplace_published is False
    assert contract.no_commit is True

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    # Prior authoritative Slice 13.1–13.14 runners
    prior_results, prior_checks, prior_defects = run_prior_slice_verifiers(monorepo)
    checks.extend(prior_checks)
    defects.extend(prior_defects)
    prior_verdicts = {
        sid: data.get("verdict", "missing") for sid, data in prior_results.items()
    }

    # Policy / schema registries
    policy_checks, policy_defects = check_policy_registry(monorepo)
    checks.extend(policy_checks)
    defects.extend(policy_defects)

    schema_checks, schema_defects = check_schema_registry(monorepo)
    checks.extend(schema_checks)
    defects.extend(schema_defects)

    domain_checks, meta = assemble_domain_checks(monorepo)
    checks.extend(domain_checks)
    release_posture = meta.get("release_posture") or check_release_posture_fields()

    # Provisional matrix without marking 13.15 complete yet
    provisional = build_slice_matrix(
        monorepo,
        prior_verdicts=prior_verdicts,
        completion_runner_ok=False,
    )
    matrix_checks, matrix_defects = check_slice_matrix_integrity(
        monorepo, provisional, completion_ok=False
    )
    checks.extend(matrix_checks)
    defects.extend(matrix_defects)

    failed = sum(1 for c in checks if not c.ok)
    # Unique defects only
    uniq_defects: list[Defect] = []
    seen: set[tuple[str, str, str, str]] = set()
    for d in defects:
        key = (d.classification, d.surface, d.expected, d.observed)
        if key not in seen:
            seen.add(key)
            uniq_defects.append(d)

    limitations = sorted(ALLOWED_LIMITATIONS)
    # 13.15 complete only when all checks pass
    completion_ok = failed == 0 and not uniq_defects
    if not completion_ok:
        checks.append(
            CheckResult(
                name="completion:self_green",
                ok=False,
                detail="pending_failures",
                category="slice_matrix",
            )
        )
        failed = sum(1 for c in checks if not c.ok)
    else:
        checks.append(
            CheckResult(
                name="completion:self_green",
                ok=True,
                detail="green",
                category="slice_matrix",
            )
        )

    final_matrix = build_slice_matrix(
        monorepo,
        prior_verdicts=prior_verdicts,
        completion_runner_ok=completion_ok,
    )
    completed = sum(1 for r in final_matrix if r.completion_status == "complete")

    # If self_green flipped failed count, recompute
    failed = sum(1 for c in checks if not c.ok)
    completion_ok = failed == 0 and not uniq_defects
    if completion_ok:
        final_matrix = build_slice_matrix(
            monorepo,
            prior_verdicts=prior_verdicts,
            completion_runner_ok=True,
        )
        completed = TOTAL_SLICES
        release_posture = {**release_posture, "epic_13_complete": True}
    else:
        final_matrix = build_slice_matrix(
            monorepo,
            prior_verdicts=prior_verdicts,
            completion_runner_ok=False,
        )
        completed = sum(1 for r in final_matrix if r.completion_status == "complete")
        release_posture = {**release_posture, "epic_13_complete": False}

    verdict = _decide(failed, uniq_defects, limitations)

    report = VsCodeEpic13CompletionReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=VSCODE_EPIC13_COMPLETION_ID,
        verdict=verdict,
        slice_matrix=[r.to_dict() for r in final_matrix],
        policy_registry=build_policy_registry(monorepo),
        schema_registry=build_schema_registry(),
        extension_version="0.2.0",
        workflow_status=_status(checks, "workflow"),
        cli_status=_status(checks, "cli"),
        initialization_status=_status(checks, "initialization"),
        assessment_status=_status(checks, "assessment"),
        progress_status=_status(checks, "progress"),
        report_status=_status(checks, "report"),
        recovery_status=_status(checks, "recovery"),
        telemetry_status=_status(checks, "telemetry"),
        locality_status=_status(checks, "locality"),
        compatibility_status=_status(checks, "cli"),  # compat folded into cli checks
        marketplace_branding_status=_status(checks, "marketplace_branding"),
        marketplace_documentation_status=_status(
            checks, "marketplace_documentation"
        ),
        clean_install_status=(
            "pass"
            if prior_verdicts.get("13.14") in {"PASS", "PASS_WITH_LIMITATIONS"}
            else "fail"
        ),
        package_boundary_status=_status(checks, "package_boundary"),
        privacy_status=_status(checks, "privacy"),
        security_status=_status(checks, "security"),
        engine_authority_status=_status(checks, "engine_authority"),
        platform_boundary_status=_status(checks, "platform_boundary"),
        cloud_boundary_status=_status(checks, "cloud_boundary"),
        data_lake_boundary_status=_status(checks, "data_lake_boundary"),
        documentation_status=_status(checks, "documentation"),
        release_posture=release_posture,
        epic14_absence_status=_status(checks, "epic14_absence"),
        defects=uniq_defects,
        blockers=[],
        limitations=limitations,
        checks=checks,
        total_checks=len(checks),
        failed_checks=failed,
        completed_slices=completed,
        total_slices=TOTAL_SLICES,
    )
    return report


def write_report(monorepo: Path, report: VsCodeEpic13CompletionReport) -> Path:
    out_dir = monorepo / SV1315_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / REPORT_JSON
    text = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    safe, reason = report_text_is_safe(text)
    assert safe, f"unsafe report content: {reason}"
    assert "/Users/" not in text
    assert "file://" not in text
    json_path.write_text(text, encoding="utf-8")
    (out_dir / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Completed slices: {report.completed_slices}/{report.total_slices}\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Epic 13 – VS Code Extension is complete for the CodeStrata v0.2.0 epic "
        "scope when verdict is PASS or PASS_WITH_LIMITATIONS.\n\n"
        "Marketplace publication, release tagging, and production deployment "
        "remain separate release gates. Epic 14 Product Experience not started. "
        "No commit/tag/publish/deploy.\n",
        encoding="utf-8",
    )
    return json_path


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        f"{SCHEMA_NAME}:{SCHEMA_VERSION} verdict={report.verdict} "
        f"completed={report.completed_slices}/{report.total_slices} "
        f"checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.name}"
    )
    return 0 if report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
