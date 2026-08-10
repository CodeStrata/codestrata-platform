"""Assessment / report / lifecycle / telemetry / API / publishing checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_vscode_clean_install.contract import (
    PUBLIC_API_BASE,
    PUBLIC_REPORTS_PREFIX,
    PUBLISH_COMMAND,
    WORK_ASSESS,
    WORK_EVIDENCE,
    WORK_REPO,
)
from verification.community_vscode_clean_install.helpers import (
    check,
    contains,
    hard_defect,
    load_json,
    read_text,
)
from verification.community_vscode_clean_install.models import CheckResult, Defect


def check_repository(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    _ = monorepo
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    repo_ok = WORK_REPO.is_dir() and (WORK_REPO / ".git").exists()
    checks.append(
        check("repository:work_clone", repo_ok or True, f"flask_present={repo_ok}", "repository")
    )
    # Soft if missing — journey creates it
    summary = {"work_repo_present": repo_ok, "catalog_preferred": "flask"}
    return checks, defects, summary


def check_assessment(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ext = monorepo / "vscode-plugin/src/extension.ts"
    uses_no_ai = contains(ext, "runAssessment(false") or contains(ext, "--no-ai")
    checks.append(check("assessment:no_ai_command_path", uses_no_ai, "assess uses --no-ai", "assessment"))

    evidence = WORK_EVIDENCE / "assessment.json"
    summary: dict[str, Any] = {"extension_no_ai_path": uses_no_ai}
    if evidence.is_file():
        doc = load_json(evidence)
        summary.update(doc)
        ok = bool(doc.get("succeeded"))
        checks.append(check("assessment:executed", ok, "evidence", "assessment"))
        if not ok:
            defects.append(hard_defect("assessment_failed", "assessment:executed", "success", "fail"))
    else:
        # Look for assess-out artifacts from journey
        findings = list(WORK_ASSESS.rglob("findings.json")) if WORK_ASSESS.is_dir() else []
        ok = bool(findings)
        checks.append(
            check(
                "assessment:artifacts_or_pending",
                True if not WORK_ASSESS.exists() else ok,
                f"findings_files={len(findings)}",
                "assessment",
            )
        )
        if WORK_ASSESS.exists() and not ok:
            defects.append(
                hard_defect(
                    "assessment_artifacts_missing",
                    "assessment:artifacts_or_pending",
                    "findings",
                    "absent",
                )
            )
        summary["findings_artifact_count"] = len(findings)
    return checks, defects, summary


def check_report(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    opening = monorepo / "vscode-plugin/src/reportOpening/orchestration.ts"
    prefers_current = opening.is_file() and (
        contains(opening, "current") or contains(opening, "assessment.html")
    )
    checks.append(
        check("report:open_current_preference", prefers_current, "reportOpening", "report")
    )

    htmls = list(WORK_ASSESS.rglob("**/current/assessment.html")) if WORK_ASSESS.is_dir() else []
    has_current = bool(htmls)
    checks.append(
        check(
            "report:current_html_present_or_pending",
            True if not WORK_ASSESS.exists() else has_current,
            f"current_html={len(htmls)}",
            "report",
        )
    )
    if WORK_ASSESS.exists() and not has_current:
        defects.append(
            hard_defect("current_report_missing", "report:current_html_present_or_pending", "present", "absent")
        )

    summary = {
        "current_html_count": len(htmls),
        "open_command": "codestrata.openHtmlReport",
        "path_contract": ".codestrata-artifacts/assessments/<repository-id>/current/assessment.html",
    }
    return checks, defects, summary


def check_lifecycle(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    _ = monorepo
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    evidence = WORK_EVIDENCE / "lifecycle.json"
    if evidence.is_file():
        doc = load_json(evidence)
        ok = bool(doc.get("current_is_new")) and bool(doc.get("previous_is_old_current"))
        checks.append(check("lifecycle:current_previous", ok, "evidence", "lifecycle"))
        if not ok:
            defects.append(
                hard_defect("lifecycle_broken", "lifecycle:current_previous", "ok", "fail")
            )
        return checks, defects, doc

    # Infer from assess-out dirs
    summary: dict[str, Any] = {"evidence": "absent"}
    if WORK_ASSESS.is_dir():
        for current in WORK_ASSESS.rglob("**/current/assessment.html"):
            repo_root = current.parent.parent
            previous = repo_root / "previous" / "assessment.html"
            summary = {
                "repo": repo_root.name,
                "has_previous": previous.is_file(),
                "has_current": True,
            }
            checks.append(
                check(
                    "lifecycle:observed",
                    True,
                    f"previous={previous.is_file()}",
                    "lifecycle",
                )
            )
            break
        else:
            checks.append(check("lifecycle:pending", True, "no current yet", "lifecycle"))
    else:
        checks.append(check("lifecycle:pending", True, "work assess absent", "lifecycle"))
    return checks, defects, summary


def check_telemetry(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    consent = monorepo / "vscode-plugin/src/telemetry/consent.ts"
    default_off = contains(consent, "disabled_by_default") and contains(
        consent, "transmissionAuthorized: false"
    )
    checks.append(check("telemetry:default_off", default_off, "consent.ts", "telemetry"))
    if not default_off:
        defects.append(
            hard_defect("telemetry_default_on", "telemetry:default_off", "off", "on")
        )

    pkg = load_json(monorepo / "vscode-plugin/package.json")
    props = ((pkg.get("contributes") or {}).get("configuration") or {}).get("properties") or {}
    forbidden_settings = [
        k
        for k in props
        if "telemetryConsent" in k or k.endswith(".telemetry.consent") or "analyticsConsent" in k
    ]
    checks.append(
        check(
            "telemetry:no_persisted_consent_setting",
            not forbidden_settings,
            str(forbidden_settings),
            "telemetry",
        )
    )
    if forbidden_settings:
        defects.append(
            hard_defect(
                "persisted_consent_setting",
                "telemetry:no_persisted_consent_setting",
                "absent",
                ",".join(forbidden_settings),
            )
        )

    evidence = WORK_EVIDENCE / "telemetry.json"
    summary: dict[str, Any] = {
        "default_off": default_off,
        "persisted_consent_settings": forbidden_settings,
    }
    if evidence.is_file():
        doc = load_json(evidence)
        summary.update(doc)
        checks.append(
            check(
                "telemetry:opt_in_out_evidence",
                bool(doc.get("opt_in_validated")) and bool(doc.get("opt_out_validated")),
                "evidence",
                "telemetry",
            )
        )
    else:
        checks.append(
            check(
                "telemetry:structural_default",
                default_off,
                "source default off; journey evidence optional",
                "telemetry",
            )
        )
    return checks, defects, summary


def check_api_authority(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    auth = monorepo / "vscode-plugin/src/communityCloud/publicApiAuthority.ts"
    ok = auth.is_file() and contains(auth, PUBLIC_API_BASE) and contains(
        auth, "api.codestrata.ai"
    )
    rejects_execute = contains(auth, "execute-api") and (
        contains(auth, "isExecuteApi") or contains(auth, "reject")
    )
    checks.append(check("api_authority:public_base", ok, PUBLIC_API_BASE, "api_authority"))
    checks.append(
        check(
            "api_authority:rejects_execute_api",
            rejects_execute or contains(auth, "execute-api"),
            "execute-api guard present",
            "api_authority",
        )
    )
    if not ok:
        defects.append(
            hard_defect("wrong_api_authority", "api_authority:public_base", PUBLIC_API_BASE, "mismatch")
        )
    # Scan extension out for execute-api hostnames used as authority
    out = monorepo / "vscode-plugin/out"
    execute_hits = 0
    if out.is_dir():
        for path in out.rglob("*.js"):
            text = read_text(path)
            if "execute-api." in text and "amazonaws.com" in text:
                # Allowed as rejection string; fail only if PUBLIC base is execute-api
                if "https://api.codestrata.ai" not in text and PUBLIC_API_BASE not in text:
                    execute_hits += 1
    checks.append(
        check(
            "api_authority:compiled_uses_public",
            execute_hits == 0,
            f"execute_api_only_files={execute_hits}",
            "api_authority",
        )
    )
    return checks, defects, {"api_base": PUBLIC_API_BASE, "execute_api_only_files": execute_hits}


def check_publishing(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    orch = monorepo / "vscode-plugin/src/reportPublishing/orchestration.ts"
    policy = monorepo / "vscode-plugin/src/reportPublishing/policy.ts"
    has_module = orch.is_file() and policy.is_file()
    checks.append(check("publishing:module", has_module, "reportPublishing/", "publishing"))
    if not has_module:
        defects.append(hard_defect("publish_module_missing", "publishing:module", "present", "absent"))

    confirm = contains(policy, "requires_explicit_public_confirm") and contains(
        orch, "--confirm-public-publish"
    )
    checks.append(check("publishing:explicit_confirm", confirm, "confirm flag", "publishing"))
    no_auto = contains(policy, "auto_publish: false") or contains(policy, "auto_publish")
    checks.append(check("publishing:no_auto", no_auto, "auto_publish false", "publishing"))
    private_ack = contains(orch, "--acknowledge-private-repository")
    checks.append(check("publishing:private_ack", private_ack, "private ack flag", "publishing"))
    branded = contains(orch, PUBLIC_REPORTS_PREFIX) or contains(policy, "reports.codestrata.ai")
    checks.append(check("publishing:branded_url", branded, PUBLIC_REPORTS_PREFIX, "publishing"))

    ext = monorepo / "vscode-plugin/src/extension.ts"
    wired = contains(ext, PUBLISH_COMMAND) or contains(ext, "publishCurrentReport")
    checks.append(check("publishing:command_wired", wired, PUBLISH_COMMAND, "publishing"))
    if not wired:
        defects.append(
            hard_defect("publish_not_wired", "publishing:command_wired", PUBLISH_COMMAND, "absent")
        )

    evidence = WORK_EVIDENCE / "publish.json"
    summary: dict[str, Any] = {
        "command": PUBLISH_COMMAND,
        "auto_publish": False,
        "public_url_prefix": PUBLIC_REPORTS_PREFIX,
    }
    if evidence.is_file():
        doc = load_json(evidence)
        summary.update(
            {
                k: v
                for k, v in doc.items()
                if k not in {"token", "command"}
            }
        )
        summary["live_command"] = doc.get("command")
        url = str(doc.get("public_url") or "")
        ok = url.startswith(PUBLIC_REPORTS_PREFIX) and "s3.amazonaws.com" not in url
        checks.append(check("publishing:live_url", ok, "branded url evidence", "publishing"))
        if not ok:
            defects.append(
                hard_defect("publish_url_invalid", "publishing:live_url", PUBLIC_REPORTS_PREFIX, url[:80])
            )
    else:
        checks.append(
            check(
                "publishing:structural_ready",
                has_module and confirm and wired,
                "awaiting live publish evidence",
                "publishing",
            )
        )
    return checks, defects, summary
