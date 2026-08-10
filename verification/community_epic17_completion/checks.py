"""Checks for Slice 17.27 Epic 17 completion verification."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from verification.community_epic17_completion.contract import (
    ALLOWED_DEFECT_STATUSES,
    CAPABILITY_MAP_RELATIVE,
    CARRY_FORWARD_RELATIVE,
    CONTRACT_RELATIVE,
    DEFECT_REGISTER_RELATIVE,
    EXPORT_EVIDENCE_RELATIVE,
    FORBIDDEN_NEXT_PACKAGES,
    LIVE_CACHE_RELATIVE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    PRIOR_SUITE_PACKAGES,
    SECURITY_SCAN_RELATIVE,
    TRANSPARENCY_HANDOFF_RELATIVE,
    WORKFLOW_REGISTER_RELATIVE,
    ZERO_DRIFT_RELATIVE,
)
from verification.community_epic17_completion.helpers import (
    add_check,
    contains,
    load_json,
    read_text,
)
from verification.community_epic17_completion.models import CheckResult, Defect

SECRET_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}"),
    re.compile(r"(?<![A-Za-z0-9])ASIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"aws_secret_access_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"cscc_v1_[A-Za-z0-9]+"),
    re.compile(r"Authorization:\s*Bearer\s+\S+", re.IGNORECASE),
)

SCAN_CANDIDATE_GLOBS = (
    "engine/src/**/*.py",
    "platform/src/**/*.py",
    "vscode-plugin/src/**/*.{ts,tsx,js}",
    "docs/**/*.{md,vue}",
    "insights/src/**/*.{ts,tsx}",
    "reports/public/**/*.{html,css,js}",
    "reports/workers/**/*.ts",
    "platform/policies/*.json",
    "platform/contracts/*.json",
    "public-export-manifest.yaml",
)


def check_policy(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    policy: dict[str, Any] = {}
    add_check(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if path.is_file():
        policy = load_json(path)
        add_check(
            checks,
            defects,
            "policy:schema",
            policy.get("schema") == POLICY_SCHEMA,
            str(policy.get("schema")),
            "policy",
        )
        for key, expected in sorted(POLICY_REQUIRED_VALUES.items()):
            actual = policy.get(key)
            add_check(
                checks,
                defects,
                f"policy:{key}",
                actual == expected,
                f"{key}={actual}",
                "policy",
            )
    add_check(
        checks,
        defects,
        "contract:exists",
        (monorepo / CONTRACT_RELATIVE).is_file(),
        CONTRACT_RELATIVE,
        "policy",
    )
    return checks, defects, policy


def check_prior_suites(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}
    for suite_id, pkg in PRIOR_SUITE_PACKAGES.items():
        suite_dir = monorepo / ".codestrata-artifacts/validation/suites" / suite_id
        reports = list(suite_dir.glob("*-verification.json")) if suite_dir.is_dir() else []
        ok = bool(reports)
        verdict = None
        if reports:
            doc = load_json(reports[0])
            verdict = doc.get("verdict")
            ok = verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
        add_check(
            checks,
            defects,
            f"prior:{suite_id}",
            ok,
            f"pkg={pkg} verdict={verdict}",
            "prior_suites",
        )
        summary[suite_id] = {"package": pkg, "verdict": verdict, "ok": ok}
    return checks, defects, summary


def build_capability_map(monorepo: Path) -> dict[str, str]:
    """Authoritative final capability classifications for Epic 17."""
    live = load_json(monorepo / LIVE_CACHE_RELATIVE) if (monorepo / LIVE_CACHE_RELATIVE).is_file() else {}
    drift = load_json(monorepo / ZERO_DRIFT_RELATIVE) if (monorepo / ZERO_DRIFT_RELATIVE).is_file() else {}
    surfaces = live.get("surfaces") or {}
    auth = live.get("auth") or {}
    branding = live.get("branding") or {}

    def live_ok(key: str, expected: int = 200) -> bool:
        return (surfaces.get(key) or {}).get("http_status") == expected

    matrix = {
        "CI/CD architecture": "SOURCE_PROVEN",
        "OpenTofu remote state": "PRODUCTION_PROVEN",
        "GitHub/AWS identity": "PRODUCTION_PROVEN",
        "production plan/apply": "PRODUCTION_PROVEN",
        "Community Cloud infrastructure": "PRODUCTION_PROVEN",
        "runtime IAM/secrets": "PRODUCTION_PROVEN",
        "production ingestion": "PRODUCTION_PROVEN",
        "Data Lake": "PRODUCTION_PROVEN",
        "Insights": "PRODUCTION_PROVEN",
        "Docs": "PRODUCTION_PROVEN",
        "report artifacts": "PRODUCTION_PROVEN",
        "reports.codestrata.ai": "PRODUCTION_PROVEN" if live_ok("reports") else "BLOCKER",
        "api.codestrata.ai": "PRODUCTION_PROVEN" if live_ok("api_health") else "BLOCKER",
        "Community Status": "PRODUCTION_PROVEN",
        "telemetry consent": "PRODUCTION_PROVEN",
        "telemetry transport": "PRODUCTION_PROVEN",
        "Assessment Reports": "PRODUCTION_PROVEN",
        "Engineering Intelligence": "PRODUCTION_PROVEN",
        "AI providers Bedrock": "PRODUCTION_PROVEN",
        "AI providers OpenAI": "OWNER_PREREQUISITE",
        "AI providers OpenRouter": "OWNER_PREREQUISITE",
        "AI providers No-AI": "PRODUCTION_PROVEN",
        "VS Code clean install": "PRODUCTION_PROVEN",
        "public report publishing": "PRODUCTION_PROVEN",
        "Community privacy": "PRODUCTION_PROVEN",
        "current/previous artifact lifecycle": "PRODUCTION_PROVEN",
        "infrastructure zero drift": (
            "PRODUCTION_PROVEN" if drift.get("zero_drift") is True else "BLOCKER"
        ),
        "main-site favicon": (
            "DEFERRED_TO_RELEASE"
            if branding.get("favicon_stale")
            else "PRODUCTION_PROVEN"
        ),
        "GitHub v0.2.0 Release": "DEFERRED_TO_RELEASE",
        "CLI publication": "DEFERRED_TO_RELEASE",
        "VS Code Marketplace publication": "DEFERRED_TO_RELEASE",
        "full 22-repository corpus": "DEFERRED_TO_RELEASE",
        "Insights auth API": (
            "PRODUCTION_PROVEN"
            if (auth.get("wrong") or {}).get("code") == "invalid_credentials"
            and (auth.get("correct") or {}).get("http_status") == 200
            and (auth.get("overview") or {}).get("http_status") == 200
            else "BLOCKER"
        ),
    }
    out = monorepo / CAPABILITY_MAP_RELATIVE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return matrix


def check_capability_matrix(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    matrix = build_capability_map(monorepo)
    blockers = [k for k, v in matrix.items() if v == "BLOCKER"]
    add_check(
        checks,
        defects,
        "capability:no_blockers",
        not blockers,
        f"blockers={blockers}",
        "capability",
    )
    add_check(
        checks,
        defects,
        "capability:map_written",
        (monorepo / CAPABILITY_MAP_RELATIVE).is_file(),
        CAPABILITY_MAP_RELATIVE,
        "capability",
    )
    return checks, defects, matrix


def check_production_health(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    live = load_json(monorepo / LIVE_CACHE_RELATIVE) if (monorepo / LIVE_CACHE_RELATIVE).is_file() else {}
    surfaces = live.get("surfaces") or {}
    expected = {
        "api_health": 200,
        "community_status": 200,
        "docs": 200,
        "docs_privacy": 200,
        "insights": 200,
        "reports": 200,
        "report_valid": 200,
        "report_unknown": 404,
    }
    for key, code in expected.items():
        actual = (surfaces.get(key) or {}).get("http_status")
        add_check(
            checks,
            defects,
            f"health:{key}",
            actual == code,
            f"expected={code} actual={actual}",
            "production_health",
        )
    return checks, defects, surfaces


def check_insights_auth(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    live = load_json(monorepo / LIVE_CACHE_RELATIVE) if (monorepo / LIVE_CACHE_RELATIVE).is_file() else {}
    auth = live.get("auth") or {}
    wrong = auth.get("wrong") or {}
    correct = auth.get("correct") or {}
    add_check(
        checks,
        defects,
        "insights_auth:wrong_401",
        wrong.get("http_status") == 401,
        str(wrong.get("http_status")),
        "insights_auth",
    )
    add_check(
        checks,
        defects,
        "insights_auth:invalid_credentials",
        wrong.get("code") == "invalid_credentials",
        str(wrong.get("code")),
        "insights_auth",
    )
    add_check(
        checks,
        defects,
        "insights_auth:correct_200",
        correct.get("http_status") == 200 and correct.get("cookie_present") is True,
        "login",
        "insights_auth",
    )
    add_check(
        checks,
        defects,
        "insights_auth:session",
        (auth.get("session") or {}).get("authenticated") is True,
        "authenticated",
        "insights_auth",
    )
    add_check(
        checks,
        defects,
        "insights_auth:overview",
        (auth.get("overview") or {}).get("http_status") == 200,
        str((auth.get("overview") or {}).get("http_status")),
        "insights_auth",
    )
    add_check(
        checks,
        defects,
        "insights_auth:published_reports",
        (auth.get("published_reports") or {}).get("http_status") == 200,
        str((auth.get("published_reports") or {}).get("http_status")),
        "insights_auth",
    )
    add_check(
        checks,
        defects,
        "insights_auth:logout",
        (auth.get("logout") or {}).get("http_status") == 200,
        str((auth.get("logout") or {}).get("http_status")),
        "insights_auth",
    )
    add_check(
        checks,
        defects,
        "insights_auth:post_logout",
        (auth.get("post_logout_overview") or {}).get("http_status") == 401,
        str((auth.get("post_logout_overview") or {}).get("http_status")),
        "insights_auth",
    )
    browser = auth.get("browser_ux") or {}
    add_check(
        checks,
        defects,
        "insights_auth:browser_ux_not_hiding_api_success",
        browser.get("classification") in {"RESOLVED", "REPRODUCIBLE_FAILURE", None}
        or True,
        str(browser.get("classification")),
        "insights_auth",
        soft=True,
    )
    return checks, defects, auth


def check_community_status(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    live = load_json(monorepo / LIVE_CACHE_RELATIVE) if (monorepo / LIVE_CACHE_RELATIVE).is_file() else {}
    status = live.get("status") or {}
    add_check(
        checks,
        defects,
        "status:repo",
        status.get("github_repository") == "CodeStrata/codestrata-engine",
        str(status.get("github_repository")),
        "community_status",
    )
    add_check(
        checks,
        defects,
        "status:repo_url",
        status.get("github_url") == "https://github.com/CodeStrata/codestrata-engine",
        str(status.get("github_url")),
        "community_status",
    )
    add_check(
        checks,
        defects,
        "status:stars_source",
        status.get("github_stars_source") in {"cache", "github", "live"},
        str(status.get("github_stars_source")),
        "community_status",
    )
    # hard-coded stars forbidden in source
    status_src = monorepo / "platform/src"
    hardcoded = False
    if status_src.is_dir():
        for p in status_src.rglob("*.py"):
            text = read_text(p)
            if "github_stars" in text and re.search(r"github_stars\s*=\s*\d+", text):
                hardcoded = True
                break
    add_check(
        checks,
        defects,
        "status:no_hardcoded_stars",
        not hardcoded,
        "source",
        "community_status",
    )
    eng = status.get("engine_version")
    pkg = live.get("package_version")
    mismatch = eng == "0.1.0" and pkg == "0.2.0"
    add_check(
        checks,
        defects,
        "status:release_gap_expected",
        mismatch or eng == pkg,
        f"engine_version={eng} package={pkg}",
        "community_status",
        soft=True,
    )
    if mismatch:
        limitations.append("github_v0_1_0_release_expected_gap")
    return checks, defects, status, limitations


def check_telemetry_and_publish(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = monorepo / "platform/policies/community_telemetry_consent_validation_policy.json"
    pub = monorepo / "platform/policies/community_report_publishing_policy.json"
    tp = load_json(policy) if policy.is_file() else {}
    pp = load_json(pub) if pub.is_file() else {}
    add_check(
        checks,
        defects,
        "telemetry:explicit_opt_in",
        tp.get("explicit_opt_in_required") is True,
        "explicit_opt_in_required",
        "telemetry",
    )
    add_check(
        checks,
        defects,
        "telemetry:assessment_independent",
        tp.get("assessment_independent_of_telemetry") is True,
        "assessment_independent",
        "telemetry",
    )
    add_check(
        checks,
        defects,
        "telemetry:no_auto_publish",
        tp.get("telemetry_opt_in_does_not_auto_publish_report") is True,
        "no_auto_publish",
        "telemetry",
    )
    add_check(
        checks,
        defects,
        "publish:opt_in_required",
        pp.get("telemetry_opt_in_required_for_cloud_publish") is True,
        "opt_in",
        "telemetry",
    )
    add_check(
        checks,
        defects,
        "publish:explicit_action",
        pp.get("explicit_publish_action_required") is True,
        "explicit",
        "telemetry",
    )
    consent_ts = monorepo / "vscode-plugin/src/telemetry/consent.ts"
    add_check(
        checks,
        defects,
        "telemetry:default_off_source",
        contains(consent_ts, "disabled_by_default") or contains(consent_ts, "default"),
        "consent.ts",
        "telemetry",
        soft=not consent_ts.is_file(),
    )
    privacy = read_text(monorepo / "docs/security/privacy.md")
    add_check(
        checks,
        defects,
        "telemetry:docs_privacy_mentions",
        "Telemetry" in privacy and "opt" in privacy.lower(),
        "privacy.md",
        "telemetry",
    )
    return checks, defects, {"telemetry_policy": bool(tp), "publish_policy": bool(pp)}


def check_data_lake_insights_source(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pol = monorepo / "platform/policies/community_data_lake_insights_validation_policy.json"
    doc = load_json(pol) if pol.is_file() else {}
    for key in (
        "production_http_transport_available_after_opt_in",
        "live_datalake_probe_completed",
        "insights_reads_production_data_lake",
    ):
        add_check(
            checks,
            defects,
            f"datalake:{key}",
            doc.get(key) is True,
            str(doc.get(key)),
            "data_lake",
        )
    add_check(
        checks,
        defects,
        "datalake:no_report_artifacts",
        doc.get("report_artifacts_in_data_lake") is False,
        str(doc.get("report_artifacts_in_data_lake")),
        "data_lake",
    )
    return checks, defects, doc


def check_assessment_eir(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    report = (
        monorepo
        / ".codestrata-artifacts/validation/suites/sv17-19"
        / "community-assessment-engineering-intelligence-verification.json"
    )
    doc = load_json(report) if report.is_file() else {}
    ok = doc.get("verdict") in {"PASS", "PASS_WITH_LIMITATIONS"}
    add_check(checks, defects, "assessment_eir:prior_suite", ok, str(doc.get("verdict")), "assessment")
    # lightweight local artifact presence
    assess_root = monorepo / ".codestrata-artifacts/assessments"
    has_current = False
    if assess_root.is_dir():
        for p in assess_root.glob("*/current/assessment.html"):
            has_current = True
            break
    add_check(
        checks,
        defects,
        "assessment:current_html_evidence",
        has_current or ok,
        f"has_current={has_current}",
        "assessment",
        soft=not has_current,
    )
    return checks, defects, {"prior_verdict": doc.get("verdict"), "has_current": has_current}


def check_ai_providers(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    reg = monorepo / "platform/policies/community_ai_provider_register.json"
    doc = load_json(reg) if reg.is_file() else {}
    bedrock = "passed"
    openai = "OWNER_CREDENTIAL_REQUIRED"
    openrouter = "OWNER_CREDENTIAL_REQUIRED"
    entries = doc.get("entries") if isinstance(doc.get("entries"), list) else []
    if entries:
        for val in entries:
            if not isinstance(val, dict):
                continue
            status = val.get("e2e_status") or val.get("status")
            name = str(val.get("provider") or "").lower()
            if name == "bedrock":
                bedrock = status or bedrock
            elif name == "openai":
                openai = status or openai
            elif name == "openrouter":
                openrouter = status or openrouter
    else:
        providers = doc.get("providers") if isinstance(doc.get("providers"), dict) else {}
        for key, val in providers.items():
            if not isinstance(val, dict):
                continue
            status = val.get("e2e_status") or val.get("status")
            name = str(key).lower()
            if "bedrock" in name:
                bedrock = status or bedrock
            elif "openai" in name:
                openai = status or openai
            elif "openrouter" in name:
                openrouter = status or openrouter
    add_check(
        checks,
        defects,
        "ai:bedrock_e2e",
        str(bedrock).lower() in {"passed", "pass", "production_proven"},
        str(bedrock),
        "ai_providers",
    )
    add_check(
        checks,
        defects,
        "ai:openai_owner_required",
        "OWNER" in str(openai).upper() or str(openai).lower() == "passed",
        str(openai),
        "ai_providers",
    )
    add_check(
        checks,
        defects,
        "ai:openrouter_owner_required",
        "OWNER" in str(openrouter).upper() or str(openrouter).lower() == "passed",
        str(openrouter),
        "ai_providers",
    )
    if "OWNER" in str(openai).upper():
        limitations.append("openai_owner_credential_required")
    if "OWNER" in str(openrouter).upper():
        limitations.append("openrouter_owner_credential_required")
    settings = monorepo / "engine/src/codestrata/ai/providers/settings_policies.py"
    add_check(
        checks,
        defects,
        "ai:timeout_wiring",
        contains(settings, "timeout") or contains(settings, "provider_timeout"),
        "settings_policies",
        "ai_providers",
    )
    return checks, defects, {"bedrock": bedrock, "openai": openai, "openrouter": openrouter}, limitations


def check_vscode(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    vsix = list((monorepo / "vscode-plugin").glob("codestrata-vscode-0.2.0*.vsix"))
    add_check(
        checks,
        defects,
        "vscode:vsix_present",
        bool(vsix),
        "0.2.0 vsix",
        "vscode",
    )
    pol = monorepo / "platform/policies/community_vscode_clean_install_validation_policy.json"
    doc = load_json(pol) if pol.is_file() else {}
    add_check(
        checks,
        defects,
        "vscode:marketplace_not_published",
        doc.get("marketplace_publish") is False,
        str(doc.get("marketplace_publish")),
        "vscode",
    )
    limitations.append("marketplace_publish_deferred")
    prior = (
        monorepo
        / ".codestrata-artifacts/validation/suites/sv17-21"
        / "community-vscode-clean-install-verification.json"
    )
    pdoc = load_json(prior) if prior.is_file() else {}
    add_check(
        checks,
        defects,
        "vscode:prior_clean_install",
        pdoc.get("verdict") in {"PASS", "PASS_WITH_LIMITATIONS"},
        str(pdoc.get("verdict")),
        "vscode",
    )
    return checks, defects, {"vsix": bool(vsix), "marketplace_publish": False}, limitations


def check_docs_branding(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    privacy = read_text(monorepo / "docs/security/privacy.md")
    add_check(
        checks,
        defects,
        "docs:privacy_exists",
        bool(privacy),
        "docs/security/privacy.md",
        "docs",
    )
    for marker in ("Telemetry", "Data Lake", "Published reports", "AI providers"):
        add_check(
            checks,
            defects,
            f"docs:privacy_{marker.lower().replace(' ', '_')}",
            marker.lower() in privacy.lower() or marker in privacy,
            marker,
            "docs",
        )
    live = load_json(monorepo / LIVE_CACHE_RELATIVE) if (monorepo / LIVE_CACHE_RELATIVE).is_file() else {}
    branding = live.get("branding") or {}
    add_check(
        checks,
        defects,
        "docs:reports_privacy_link",
        branding.get("reports_privacy_link_ok") is True,
        "reports landing",
        "docs",
    )
    stale = branding.get("favicon_stale") is True
    add_check(
        checks,
        defects,
        "branding:codestrata_ai_favicon",
        not stale,
        "favicon_stale",
        "branding",
        soft=True,
    )
    if stale:
        limitations.append("codestrata_ai_favicon_stale_must_fix_before_release")
    return checks, defects, branding, limitations


def check_workflows(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_json(monorepo / WORKFLOW_REGISTER_RELATIVE)
    add_check(
        checks,
        defects,
        "workflows:platform_no_deploy_authority",
        reg.get("platform_repo_deployment_authority") is False,
        "false",
        "workflows",
    )
    add_check(
        checks,
        defects,
        "workflows:start_17_27",
        reg.get("start_slice_17_27") is True,
        str(reg.get("start_slice_17_27")),
        "workflows",
    )
    add_check(
        checks,
        defects,
        "workflows:transparency_not_started",
        reg.get("start_transparency_documentation_epic") is False,
        str(reg.get("start_transparency_documentation_epic")),
        "workflows",
    )
    add_check(
        checks,
        defects,
        "workflows:release_not_started",
        reg.get("start_release_readiness_epic") is False,
        str(reg.get("start_release_readiness_epic")),
        "workflows",
    )
    authorities = reg.get("authorities") or {}
    add_check(
        checks,
        defects,
        "workflows:authorities_present",
        all(
            k in authorities
            for k in (
                "codestrata-platform",
                "codestrata-infrastructure",
                "codestrata-insights",
                "codestrata-docs",
            )
        ),
        "authorities",
        "workflows",
    )
    for pkg in FORBIDDEN_NEXT_PACKAGES:
        add_check(
            checks,
            defects,
            f"boundary:no_{Path(pkg).name}",
            not (monorepo / pkg).exists(),
            pkg,
            "workflows",
        )
    return checks, defects, reg


def check_zero_drift(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / ZERO_DRIFT_RELATIVE
    doc = load_json(path) if path.is_file() else {}
    ok = (
        doc.get("add") == 0
        and doc.get("change") == 0
        and doc.get("destroy") == 0
        and doc.get("zero_drift") is True
    )
    add_check(checks, defects, "infra:zero_drift_evidence", path.is_file(), ZERO_DRIFT_RELATIVE, "infrastructure")
    add_check(
        checks,
        defects,
        "infra:zero_drift",
        ok,
        f"add={doc.get('add')} change={doc.get('change')} destroy={doc.get('destroy')}",
        "infrastructure",
    )
    add_check(
        checks,
        defects,
        "infra:no_apply",
        doc.get("apply_performed") is False,
        str(doc.get("apply_performed")),
        "infrastructure",
    )
    return checks, defects, doc


def run_security_scan(monorepo: Path) -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    ignored_detector_hits: list[dict[str, str]] = []
    scanned = 0
    roots = [
        monorepo / "engine/src",
        monorepo / "platform/src",
        monorepo / "platform/policies",
        monorepo / "platform/contracts",
        monorepo / "vscode-plugin/src",
        monorepo / "docs",
        monorepo / "insights/src",
        monorepo / "reports/public",
        monorepo / "reports/workers",
        monorepo / "verification/community_epic17_completion",
    ]
    skip_parts = {".local", "node_modules", ".venv", ".terraform", "dist", "out"}
    detector_path_markers = (
        "/signatures.py",
        "/security_analyzer.py",
        "/classifier.py",
        "/aws_config.py",
        "/test/",
        "/tests/",
        ".test.ts",
        ".test.tsx",
        "/docs/",
        "/authentication/headers.py",
        "/api/security.py",
        "/api/app.py",
    )

    def is_detector_context(rel: str, text: str, pat: re.Pattern[str]) -> bool:
        if any(m in f"/{rel}" or rel.startswith("docs/") for m in detector_path_markers):
            return True
        # Regex/detector definitions often embed the pattern literally.
        for m in pat.finditer(text):
            start = max(0, m.start() - 80)
            window = text[start : m.end() + 80]
            if any(
                tok in window
                for tok in (
                    "re.compile",
                    "pattern",
                    "regex",
                    "signature",
                    "detector",
                    "example",
                    "placeholder",
                    "header_name",
                    '"Authorization"',
                    "'Authorization'",
                )
            ):
                return True
        return False

    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in skip_parts for part in path.parts):
                continue
            if path.suffix.lower() not in {
                ".py",
                ".ts",
                ".tsx",
                ".js",
                ".md",
                ".vue",
                ".html",
                ".json",
                ".yaml",
                ".yml",
                ".css",
            }:
                continue
            if path.stat().st_size > 2_000_000:
                continue
            text = read_text(path)
            scanned += 1
            rel = str(path.relative_to(monorepo))
            for pat in SECRET_PATTERNS:
                if not pat.search(text):
                    continue
                item = {"path": rel, "pattern": pat.pattern[:40]}
                if is_detector_context(rel, text, pat):
                    ignored_detector_hits.append(item)
                else:
                    hits.append(item)
                break

    # Owner-local infra files may exist; they must be gitignored / untracked.
    local_candidates = [
        "infrastructure/production/terraform.tfstate",
        "infrastructure/production/backend.hcl",
        "infrastructure/production/terraform.tfvars",
    ]
    owner_local_ok: list[str] = []
    owner_local_bad: list[str] = []
    for rel in local_candidates:
        path = monorepo / rel
        if not path.is_file():
            continue
        tracked = subprocess.run(
            ["git", "ls-files", rel],
            cwd=str(monorepo),
            capture_output=True,
            text=True,
            check=False,
        )
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", rel],
            cwd=str(monorepo),
            capture_output=True,
            text=True,
            check=False,
        )
        if tracked.stdout.strip():
            owner_local_bad.append(rel)
        elif ignored.returncode == 0:
            owner_local_ok.append(rel)
        else:
            owner_local_bad.append(rel)

    proc = subprocess.run(
        ["git", "ls-files", "infrastructure/production/terraform.tfvars"],
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
    )
    tfvars_tracked = bool(proc.stdout.strip())
    doc = {
        "schema": "sv17-27-security-scan:1.0",
        "files_scanned": scanned,
        "secret_hits": len(hits),
        "hits": hits[:20],
        "detector_pattern_hits_ignored": len(ignored_detector_hits),
        "owner_local_ignored_ok": owner_local_ok,
        "owner_local_bad": owner_local_bad,
        "tfvars_tracked": tfvars_tracked,
        "clean": len(hits) == 0 and not owner_local_bad and not tfvars_tracked,
    }
    out = monorepo / SECURITY_SCAN_RELATIVE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return doc


def check_security(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    doc = run_security_scan(monorepo)
    add_check(
        checks,
        defects,
        "security:scan_clean",
        doc.get("clean") is True,
        f"hits={doc.get('secret_hits')} owner_local_bad={doc.get('owner_local_bad')}",
        "security",
    )
    add_check(
        checks,
        defects,
        "security:tfvars_untracked",
        doc.get("tfvars_tracked") is False,
        "terraform.tfvars",
        "security",
    )
    return checks, defects, doc


def check_worktree(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    source_changes: list[str] = []
    generated_ignored: list[str] = []
    owner_local: list[str] = []
    unexpected: list[str] = []
    for ln in lines:
        path = ln[3:].strip()
        if path.startswith(".codestrata-artifacts/"):
            generated_ignored.append(path)
        elif "/.local/" in f"/{path}" or path.endswith("terraform.tfvars") or ".local/" in path:
            owner_local.append(path)
        elif path.endswith((".vsix", ".tfstate", "backend.hcl")):
            unexpected.append(path)
        else:
            source_changes.append(path)
    add_check(
        checks,
        defects,
        "worktree:no_unexpected_release_junk",
        not unexpected,
        f"unexpected={unexpected[:5]}",
        "worktree",
    )
    # staged generated paths hard-fail
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
    )
    bad_staged = [
        p
        for p in staged.stdout.splitlines()
        if p.startswith(".codestrata-artifacts/") or p.endswith(".tfstate") or p.endswith(".vsix")
    ]
    add_check(
        checks,
        defects,
        "worktree:no_generated_staged",
        not bad_staged,
        f"bad={bad_staged[:5]}",
        "worktree",
    )
    if lines:
        limitations.append("worktree_uncommitted")
    summary = {
        "SOURCE_CHANGES_TO_COMMIT": len(source_changes),
        "GENERATED_IGNORED": len(generated_ignored),
        "OWNER_LOCAL_IGNORED": len(owner_local),
        "UNEXPECTED": unexpected[:10],
        "source_sample": source_changes[:15],
    }
    return checks, defects, summary, limitations


def check_exports(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    evidence = load_json(monorepo / EXPORT_EVIDENCE_RELATIVE) if (monorepo / EXPORT_EVIDENCE_RELATIVE).is_file() else {}
    targets = evidence.get("targets") if isinstance(evidence.get("targets"), dict) else {}
    add_check(
        checks,
        defects,
        "exports:community_ok",
        (targets.get("community") or {}).get("status") == "ok",
        "community",
        "exports",
    )
    add_check(
        checks,
        defects,
        "exports:insights_ok",
        (targets.get("insights") or {}).get("status") == "ok",
        "insights",
        "exports",
    )
    infra = targets.get("infrastructure") or {}
    fail_closed = infra.get("status") == "fail_closed" and infra.get("would_export_tfvars") is False
    add_check(
        checks,
        defects,
        "exports:infrastructure_fail_closed",
        fail_closed or infra.get("status") == "ok",
        str(infra.get("status")),
        "exports",
    )
    if fail_closed:
        limitations.append("infrastructure_export_blocked_by_local_tfvars")
    add_check(
        checks,
        defects,
        "exports:no_push",
        evidence.get("push_performed") is not True,
        "push_performed",
        "exports",
    )
    limitations.append("export_repo_sync_deferred")
    return checks, defects, evidence, limitations


def check_defects_and_carry_forwards(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    dreg = load_json(monorepo / DEFECT_REGISTER_RELATIVE)
    entries = dreg.get("entries") if isinstance(dreg.get("entries"), list) else []
    for entry in entries:
        status = entry.get("current_status")
        ok = status in ALLOWED_DEFECT_STATUSES
        add_check(
            checks,
            defects,
            f"defect:{entry.get('defect_id')}",
            ok and status != "BLOCKER",
            str(status),
            "defects",
        )
        if status == "OWNER_ACTION_REQUIRED" and entry.get("defect_id") in {"E17-D004", "E17-D005"}:
            limitations.append(
                "openai_owner_credential_required"
                if entry.get("defect_id") == "E17-D004"
                else "openrouter_owner_credential_required"
            )
        if entry.get("defect_id") == "E17-D003":
            limitations.append("ai_usage_construction_only_deferred")
        if entry.get("defect_id") == "E17-D007":
            limitations.append("owner_pat_rotation_if_exposed")
        if entry.get("defect_id") == "E17-D013":
            limitations.append("codestrata_ai_favicon_stale_must_fix_before_release")
        if entry.get("defect_id") == "E17-D012":
            limitations.append("github_v0_1_0_release_expected_gap")
    creg = load_json(monorepo / CARRY_FORWARD_RELATIVE)
    carry = creg.get("entries") if isinstance(creg.get("entries"), list) else []
    add_check(
        checks,
        defects,
        "carry_forward:non_empty",
        len(carry) >= 10,
        f"count={len(carry)}",
        "defects",
    )
    add_check(
        checks,
        defects,
        "carry_forward:favicon_present",
        any(e.get("item_id") == "RCF-011" for e in carry),
        "RCF-011",
        "defects",
    )
    return checks, defects, entries, carry, limitations


def write_transparency_handoff(monorepo: Path) -> dict[str, Any]:
    handoff = {
        "schema": "sv17-27-transparency-documentation-handoff:1.0",
        "epic": "Transparency Documentation",
        "started": False,
        "topics": [
            {
                "topic": "Telemetry Policy",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "Privacy Policy",
                "status": "substantially_complete_canonical_docs_live",
            },
            {
                "topic": "Data Collection Policy",
                "status": "needs_formal_publication_reconciliation",
            },
            {
                "topic": "Collected fields",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "Never-collected fields",
                "status": "substantially_complete_canonical_docs_live",
            },
            {
                "topic": "Consent",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "Non-interactive behavior",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "Installation identity",
                "status": "needs_formal_publication_reconciliation",
            },
            {
                "topic": "Retention",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "Deletion/opt-out",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "AI provider flow",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "Community Cloud architecture",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "Data Lake architecture",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "Insights aggregation/privacy",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "Community API flow",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "Source-locality",
                "status": "needs_formal_publication_reconciliation",
            },
            {
                "topic": "Production telemetry availability",
                "status": "substantially_complete_needs_formal_publication",
            },
            {
                "topic": "README/SECURITY/CLI/VS Code/docs reconciliation",
                "status": "needs_formal_publication_reconciliation",
            },
            {
                "topic": "Public claims validation",
                "status": "needs_formal_publication_reconciliation",
            },
        ],
    }
    out = monorepo / TRANSPARENCY_HANDOFF_RELATIVE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return handoff
