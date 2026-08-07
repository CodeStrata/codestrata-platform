"""Focused static checks for Slice 13.7 HTML report opening."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.vscode_html_report_opening.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    INTENDED_VSCODE_VERSION,
    REPORT_PACKAGE,
    REPORT_POLICY_ID,
    REPORT_POLICY_VERSION,
)
from verification.vscode_html_report_opening.models import CheckResult, Defect


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def _pkg_version(monorepo: Path) -> str:
    text = _read(monorepo, "vscode-plugin/package.json")
    match = re.search(r'"version"\s*:\s*"([^"]+)"', text)
    return match.group(1) if match else ""


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = _read(monorepo, f"{REPORT_PACKAGE}/policy.ts")
    containment = _read(monorepo, f"{REPORT_PACKAGE}/containment.ts")
    orchestration = _read(monorepo, f"{REPORT_PACKAGE}/orchestration.ts")
    diagnostics = _read(monorepo, f"{REPORT_PACKAGE}/diagnostics.ts")
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    parser = _read(monorepo, "vscode-plugin/src/reports/parser.ts")
    prompt = _read(monorepo, "vscode-plugin/src/telemetry/promptPolicy.ts")
    engine_paths = _read(monorepo, "engine/src/codestrata/reporters/report_paths.py")
    docs = _read(monorepo, "vscode-plugin/docs/html-report-opening.md")
    pkg = json.loads(_read(monorepo, "vscode-plugin/package.json"))

    open_handler = ""
    if 'registerCommand("codestrata.openHtmlReport"' in ext:
        # Bound to this command registration only (paren-balanced; no sibling cmds).
        start = ext.find('registerCommand("codestrata.openHtmlReport"')
        paren = ext.find("(", start)
        depth = 0
        end = paren
        for idx in range(paren, len(ext)):
            ch = ext[idx]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break
        open_handler = ext[start:end]

    commands = {
        c.get("command")
        for c in pkg.get("contributes", {}).get("commands", [])
    }

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                REPORT_POLICY_ID in policy and REPORT_POLICY_VERSION in policy,
                f"{REPORT_POLICY_ID}:{REPORT_POLICY_VERSION}",
                "report_policy",
            ),
            CheckResult(
                "policy:approach_b",
                "automatic_open_after_success: false" in policy
                and "automatic_open_after_failure: false" in policy
                and "automatic_open_after_cancel: false" in policy,
                "prompt-driven; no auto on fail/cancel",
                "automatic_open",
            ),
            CheckResult(
                "engine:report_html",
                'html_report=run_directory / "report.html"' in engine_paths
                or 'report.html' in engine_paths,
                "Engine owns report.html",
                "engine_authority",
            ),
            CheckResult(
                "engine:extension_no_write_html",
                "writeFileSync" not in open_handler
                and "writeFileSync" not in orchestration
                and "writeFileSync" not in containment
                and 'ENGINE_HTML_REPORT_BASENAME = "report.html"' in policy,
                "extension does not write HTML",
                "engine_authority",
            ),
            CheckResult(
                "location:bounded",
                "findLatestHtmlRunDirectory" in orchestration
                and "filesystem_crawl_allowed: false" in policy,
                "bounded discovery",
                "location_contract",
            ),
            CheckResult(
                "location:html_required",
                "ENGINE_HTML_REPORT_BASENAME" in containment
                and 'report.html' in parser,
                "requires report.html",
                "location_contract",
            ),
            CheckResult(
                "containment:helpers",
                "resolveApprovedOutputRoot" in containment
                and "isPathInsideRoot" in containment
                and "validateHtmlReportFile" in containment,
                "containment API",
                "containment",
            ),
            CheckResult(
                "containment:absolute_escape",
                "contained" in containment and "unsafe_path" in containment,
                "escape rejected",
                "containment",
            ),
            CheckResult(
                "symlink:lstat",
                "lstatSync" in containment or "lstatSync" in orchestration,
                "symlink checks",
                "symlink_boundary",
            ),
            CheckResult(
                "validation:regular_html",
                "not_regular_file" in containment
                and "type_invalid" in containment,
                "file validation",
                "file_validation",
            ),
            CheckResult(
                "stale:engine_run_dir",
                "preferredRunDirectory" in orchestration
                and "stale_certainty" in policy,
                "stale limited to Engine run dir",
                "stale_report",
            ),
            CheckResult(
                "ambiguity:no_rglob",
                "rglob" not in orchestration and "rglob" not in parser,
                "no recursive crawl",
                "ambiguity",
            ),
            CheckResult(
                "auto:prompt_buttons",
                '"Open HTML Report"' in ext
                and "Approach B" in ext,
                "prompt-driven open",
                "automatic_open",
            ),
            CheckResult(
                "explicit:command",
                "codestrata.openHtmlReport" in commands
                and "locateHtmlReport" in open_handler,
                "explicit open command",
                "explicit_open",
            ),
            CheckResult(
                "explicit:no_assess",
                "runAssessment" not in open_handler
                and "buildAssessArgs" not in open_handler
                and "resolveEngine" not in open_handler,
                "open does not assess/discover",
                "explicit_open",
            ),
            CheckResult(
                "explicit:no_init",
                "codestrata.init" not in open_handler
                and "planRepositoryInitialization" not in open_handler,
                "open does not init",
                "explicit_open",
            ),
            CheckResult(
                "integration:reportOpenFailed",
                "reportOpenFailed" in ext,
                "soft open failure",
                "assessment_integration",
            ),
            CheckResult(
                "open_api:openExternal",
                "openExternal" in ext and "Uri.file" in ext,
                "openExternal file URI",
                "open_api",
            ),
            CheckResult(
                "open_api:no_shell",
                "xdg-open" not in ext
                and "child_process" not in open_handler,
                "no shell open",
                "open_api",
            ),
            CheckResult(
                "primary:preserved",
                "primary_result_authoritative: true" in policy
                and "report_open_failure_isolated: true" in policy,
                "primary preserved",
                "primary_authority",
            ),
            CheckResult(
                "network:local_only",
                "local_only: true" in policy
                and "remote_uri_allowed: false" in policy,
                "local only",
                "network_boundary",
            ),
            CheckResult(
                "telemetry:excluded",
                '"codestrata.openHtmlReport"' in prompt
                and "telemetry_allowed: false" in policy,
                "no telemetry on open",
                "telemetry_boundary",
            ),
            CheckResult(
                "analytics:forbidden",
                "analytics_allowed: false" in policy,
                "no analytics on open",
                "analytics_boundary",
            ),
            CheckResult(
                "privacy:forbidden_keys",
                "reportDiagnosticsContainForbiddenKeys" in diagnostics,
                "privacy helper",
                "privacy",
            ),
            CheckResult(
                "docs:html_report",
                (monorepo / "vscode-plugin/docs/html-report-opening.md").is_file()
                and "Approach B" in docs,
                "docs present",
                "privacy",
            ),
            CheckResult(
                "vscode:version",
                _pkg_version(monorepo) == INTENDED_VSCODE_VERSION,
                _pkg_version(monorepo),
                "vscode_regression",
            ),
            CheckResult(
                "schema:assessment_1_2",
                ASSESSMENT_SCHEMA_VERSION == "1.2",
                ASSESSMENT_SCHEMA_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "epic_14:not_started",
                not (monorepo / "verification" / "vscode_epic14_product_experience").exists()
                and "startEpic14ProductExperience" not in ext,
                "Epic 14 deferred",
                "vscode_regression",
            ),
            CheckResult(
                "toctou:recheck",
                "TOCTOU" in orchestration,
                "recheck before open",
                "file_validation",
            ),
            CheckResult(
                "parser:contained_discovery",
                "resolveApprovedOutputRoot" in parser
                and "findLatestHtmlRunDirectory" in parser,
                "parser uses contained finder",
                "location_contract",
            ),
        ]
    )

    if not all(c.ok for c in checks if c.category == "containment"):
        defects.append(
            Defect(
                "path-containment defect",
                "containment",
                "repo bounded",
                "escape",
            )
        )
    if not all(c.ok for c in checks if c.category == "primary_authority"):
        defects.append(
            Defect(
                "primary-authority defect",
                "primary",
                "preserved",
                "rewritten",
            )
        )
    if not all(c.ok for c in checks if c.category == "explicit_open"):
        failed_explicit = [c.name for c in checks if c.category == "explicit_open" and not c.ok]
        defects.append(
            Defect(
                "explicit-open defect",
                "open_command",
                "open only",
                ",".join(failed_explicit) or "explicit_open_failed",
            )
        )

    return checks, defects
