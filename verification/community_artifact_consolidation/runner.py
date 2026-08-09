"""Runner for Slice 17.12."""

from __future__ import annotations

from pathlib import Path

from verification.community_artifact_consolidation.checks import (
    check_engine_layout,
    check_epic17_boundary,
    check_policy,
    check_verification_output_paths,
)
from verification.community_artifact_consolidation.contract import (
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SV1712_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_artifact_consolidation.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_artifact_consolidation.models import CheckResult, Defect, Report, Verdict
from verification.community_artifact_consolidation.reporting import write_report
from verification.community_artifact_consolidation.scenarios import check_scenarios
from verification.community_artifact_consolidation import (
    COMMUNITY_ARTIFACT_CONSOLIDATION_ID,
    VERSION,
)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_12 is True
    assert contract.start_slice_17_13 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy, register = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, layout = check_engine_layout(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, validation = check_verification_output_paths(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17 = check_epic17_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    flags = {
        "engine_package": any(x.check_id == "engine:artifacts_package" and x.ok for x in checks),
        "default_output": any(x.check_id == "engine:default_output" and x.ok for x in checks),
        "heads_writer": any(x.check_id == "engine:heads_writer" and x.ok for x in checks),
        "lightweight_manifest": any(x.check_id == "engine:lightweight_manifest_writer" and x.ok for x in checks),
        "validation_paths": any(x.check_id == "verification:sv17_12_path" and x.ok for x in checks),
        "data_lake_forbidden": policy.get("data_lake_report_upload_forbidden") is True,
        "vscode_default": any(x.check_id == "vscode:default_output" and x.ok for x in checks),
        "gitignore": any(x.check_id == "gitignore:artifacts" and x.ok for x in checks),
        "slice_17_13_absent": epic17.get("start_slice_17_13") is False,
        "single_root": policy.get("artifact_root") == ".codestrata-artifacts",
    }
    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    failed = sum(1 for x in checks if not x.ok)
    # Soft limitations that always apply until Epic cutover / EI rename.
    limitations = {
        "monorepo_remains_source_authority_pre_cutover",
        "worktree_uncommitted",
        "engineering_intelligence_filenames_retain_report_suffix",
    }
    # Cleared by final 17.12 cleanup once legacy reports/ no longer exists.
    legacy_reports = monorepo / "reports"
    if legacy_reports.is_dir() and any(legacy_reports.iterdir()):
        limitations.add("legacy_reports_may_still_exist_until_migrated")
    limitations = sorted(limitations & SOFT_LIMITATION_CODES)

    if failed == 0:
        verdict = Verdict.PASS_WITH_LIMITATIONS.value if limitations else Verdict.PASS.value
    else:
        verdict = Verdict.FAIL.value

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_ARTIFACT_CONSOLIDATION_ID,
        package_version=VERSION,
        epic=17,
        slice="17.12",
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=limitations,
        statuses={
            "policy": _status(checks, "policy"),
            "engine": _status(checks, "engine"),
            "validation": _status(checks, "validation"),
            "vscode": _status(checks, "vscode"),
            "cli": _status(checks, "cli"),
            "epic17_boundary": _status(checks, "epic17_boundary"),
            "scenarios": _status(checks, "scenarios"),
        },
        layout=layout,
        epic17_boundary=epic17,
        scenario_results=scenario_results,
    )
    text = dict_to_canonical_json(report.to_dict())
    assert report_text_is_safe(text)
    return report


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report, SV1712_OUTPUT_RELATIVE, REPORT_JSON, REPORT_MD)
    print(
        f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} report={path.relative_to(monorepo)}"
    )
    print(
        f"start_slice_17_12=true start_slice_17_13=false artifact_root=.codestrata-artifacts"
    )
    return 0 if report.failed_checks == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
