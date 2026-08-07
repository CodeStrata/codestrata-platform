"""Epic 13 slice completion matrix."""

from __future__ import annotations

from pathlib import Path

from verification.vscode_epic13_completion.contract import (
    EPIC13_POLICIES,
    PRIOR_SLICE_RUNNERS,
    SLICE_DOCS,
    SLICE_PACKAGES,
    TOTAL_SLICES,
)
from verification.vscode_epic13_completion.inventory import exists
from verification.vscode_epic13_completion.models import SliceRow

SLICE_TITLES: dict[str, str] = {
    "13.1": "Finalize Community Extension Workflow",
    "13.2": "Detect Compatible CodeStrata CLI",
    "13.3": "Install or Guide CLI Installation",
    "13.4": "Initialize Repository",
    "13.5": "Run Assessment",
    "13.6": "Show Assessment Progress",
    "13.7": "Open Generated HTML Report",
    "13.8": "Surface Clear Failures and Recovery Steps",
    "13.9": "Integrate Telemetry Consent with Community Runtime",
    "13.10": "Confirm Source Code Remains Local",
    "13.11": "Add CLI and Extension Version Compatibility Checks",
    "13.12": "Complete Marketplace Branding",
    "13.13": "Complete Marketplace Documentation",
    "13.14": "Validate Clean Install and Update Flow",
    "13.15": "Epic Completion Verification",
}

SLICE_SCHEMAS: dict[str, str] = {
    row[0]: f"{row[2]}:1.0.0" for row in PRIOR_SLICE_RUNNERS
}
SLICE_SCHEMAS["13.15"] = "vscode-epic13-completion-verification:1.0.0"

SLICE_POLICIES: dict[str, str] = {
    f"13.{i + 1}": f"{pid}:1.0" for i, (pid, _ver, _src) in enumerate(EPIC13_POLICIES)
}
SLICE_POLICIES["13.15"] = "n/a (verification contract only)"

VERIFICATION_DIRS: dict[str, str] = {
    "13.1": "verification/vscode_community_workflow",
    "13.2": "verification/vscode_cli_discovery",
    "13.3": "verification/vscode_cli_installation",
    "13.4": "verification/vscode_repository_initialization",
    "13.5": "verification/vscode_assessment_execution",
    "13.6": "verification/vscode_assessment_progress",
    "13.7": "verification/vscode_html_report_opening",
    "13.8": "verification/vscode_failure_recovery",
    "13.9": "verification/vscode_telemetry_consent_integration",
    "13.10": "verification/vscode_source_locality",
    "13.11": "verification/vscode_cli_compatibility",
    "13.12": "verification/vscode_marketplace_branding",
    "13.13": "verification/vscode_marketplace_docs",
    "13.14": "verification/vscode_clean_install",
    "13.15": "verification/vscode_epic13_completion",
}

TEST_DIRS: dict[str, str] = {
    key: value.replace("verification/", "tests/verification/", 1)
    for key, value in VERIFICATION_DIRS.items()
}


def _pkg_present(monorepo: Path, slice_id: str) -> bool:
    if slice_id == "13.15":
        return exists(monorepo, "verification/vscode_epic13_completion/runner.py")
    for sid, rel in SLICE_PACKAGES:
        if sid == slice_id:
            return exists(monorepo, rel)
    return False


def _docs_present(monorepo: Path, slice_id: str) -> bool:
    if slice_id == "13.15":
        return exists(monorepo, "verification/vscode_epic13_completion/README.md")
    for sid, rel in SLICE_DOCS:
        if sid == slice_id:
            return exists(monorepo, rel)
    return False


def _tests_present(monorepo: Path, slice_id: str) -> bool:
    return exists(monorepo, TEST_DIRS[slice_id])


def build_slice_matrix(
    monorepo: Path,
    *,
    prior_verdicts: dict[str, str],
    completion_runner_ok: bool,
) -> list[SliceRow]:
    rows: list[SliceRow] = []
    for i in range(1, TOTAL_SLICES + 1):
        sid = f"13.{i}"
        if sid == "13.15":
            vstatus = "pass" if completion_runner_ok else "pending"
            cstatus = "complete" if completion_runner_ok else "incomplete"
        else:
            verdict = prior_verdicts.get(sid, "missing")
            vstatus = (
                "pass"
                if verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
                else ("fail" if verdict == "FAIL" else "missing")
            )
            cstatus = "complete" if vstatus == "pass" else "incomplete"
        rows.append(
            SliceRow(
                slice=sid,
                title=SLICE_TITLES[sid],
                policy=SLICE_POLICIES[sid],
                verification_schema=SLICE_SCHEMAS[sid],
                source_present=_pkg_present(monorepo, sid),
                tests_present=_tests_present(monorepo, sid),
                docs_present=_docs_present(monorepo, sid),
                verification_status=vstatus,
                completion_status=cstatus,
            )
        )
    return rows
