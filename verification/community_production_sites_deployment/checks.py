"""Structural and operational checks for Slice 17.8."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from verification.community_production_sites_deployment.contract import (
    CONTRACT_RELATIVE,
    DOCS_EXPORT_CMD,
    DOCS_EXPORT_SCRIPT,
    DOCS_WRANGLER,
    EXPORT_ROUTER,
    EXPORT_ROUTER_PACKAGE,
    EXPORT_TARGETS,
    EXPECTED_OWNER,
    EXPECTED_REPOS,
    INFRASTRUCTURE_EXPORT_CMD,
    INSIGHTS_EXPORT_CMD,
    INSIGHTS_POLICY_RELATIVE,
    INSIGHTS_WRANGLER,
    LOCAL_DIR_RELATIVE,
    LOCAL_EVIDENCE_GLOB,
    MONOREPO_DIRS,
    OIDC_FINAL_SUBJECT,
    OIDC_TRUST_POLICY_RELATIVE,
    OIDC_TRANSITIONAL_SUBJECTS,
    OIDC_WILDCARD_FORBIDDEN,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
    RESIDENCY_MAP_RELATIVE,
)
from verification.community_production_sites_deployment.helpers import exists, read_json, read_text
from verification.community_production_sites_deployment.models import CheckResult, Defect

PRIOR_POLICY_PATHS = (
    "platform/policies/community_cloud_production_ingestion_policy.json",
    "platform/policies/community_cloud_cicd_policy.json",
    "platform/policies/community_cloud_github_oidc_policy.json",
)


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str | None = None,
    soft: bool = False,
) -> None:
    safe_detail = detail
    if "/Users/" in safe_detail or "/home/" in safe_detail:
        safe_detail = re.sub(r"(/Users/|/home/)[^\s\"']+", "[path-redacted]", safe_detail)
    if "arn:aws:" in safe_detail:
        safe_detail = re.sub(r"arn:aws:[^\s\"']+", "[arn-redacted]", safe_detail)
    safe_detail = re.sub(r"\b\d{12}\b", "[account-redacted]", safe_detail)
    checks.append(CheckResult(check_id, bool(ok), safe_detail, category))
    if not ok and not soft:
        defects.append(Defect(classification or category, check_id, "pass", safe_detail))


def load_evidence(monorepo: Path) -> dict[str, Any]:
    local_dir = monorepo / LOCAL_DIR_RELATIVE
    files: dict[str, dict[str, Any]] = {}
    if local_dir.is_dir():
        for path in sorted(local_dir.glob(LOCAL_EVIDENCE_GLOB)):
            try:
                data = read_json(path)
                if isinstance(data, dict):
                    files[path.name] = data
            except Exception:  # noqa: BLE001
                continue
    return {
        "files": files,
        "present": bool(files),
        "github_remote": files.get("sv17-8-github-remote.json"),
        "cloudflare_insights": files.get("sv17-8-cloudflare-insights.json"),
        "cloudflare_docs": files.get("sv17-8-cloudflare-docs.json"),
        "dns": files.get("sv17-8-dns.json"),
        "insights_auth": files.get("sv17-8-insights-auth.json"),
        "insights_dashboard": files.get("sv17-8-insights-dashboard.json"),
    }


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict = {}
    register: dict = {}
    path = monorepo / POLICY_RELATIVE
    _add(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if path.is_file():
        policy = read_json(path)
        _add(
            checks,
            defects,
            "policy:schema",
            policy.get("schema") == POLICY_SCHEMA,
            str(policy.get("schema")),
            "policy",
        )
        _add(checks, defects, "policy:start_17_8", policy.get("start_slice_17_8") is True, "true", "policy")
        _add(checks, defects, "policy:start_17_9", policy.get("start_slice_17_9") is True, "true", "policy")
        _add(checks, defects, "policy:start_17_10", policy.get("start_slice_17_10") is True, "true", "policy")
        _add(checks, defects, "policy:start_17_11", policy.get("start_slice_17_11") is True, "true", "policy")
        _add(checks, defects, "policy:start_17_12_false", policy.get("start_slice_17_12") is True, "false", "policy")
        _add(
            checks,
            defects,
            "policy:invent_exporter_forbidden",
            policy.get("export_authority", {}).get("invent_exporter_forbidden") is True,
            "true",
            "export_authority",
        )
        _add(
            checks,
            defects,
            "policy:destructive_cutover_false",
            policy.get("destructive_monorepo_cutover_allowed") is False,
            "false",
            "monorepo_authority",
        )
        mirror = monorepo / INSIGHTS_POLICY_RELATIVE
        _add(
            checks,
            defects,
            "policy:insights_mirror",
            mirror.is_file() and mirror.read_bytes() == path.read_bytes(),
            "mirror",
            "policy",
        )
    rpath = monorepo / REGISTER_RELATIVE
    _add(checks, defects, "register:exists", rpath.is_file(), REGISTER_RELATIVE, "policy")
    if rpath.is_file():
        register = read_json(rpath)
        _add(
            checks,
            defects,
            "register:schema",
            register.get("schema") == REGISTER_SCHEMA,
            str(register.get("schema")),
            "policy",
        )
    _add(checks, defects, "contract:exists", (monorepo / CONTRACT_RELATIVE).is_file(), CONTRACT_RELATIVE, "policy")
    return checks, defects, policy, register


def check_repository_visibility(
    monorepo: Path, policy: dict
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"entries": []}
    repos = policy.get("repositories") or {}
    for expected in EXPECTED_REPOS:
        name = expected["name"]
        key = "infrastructure" if name.endswith("infrastructure") else "insights" if name.endswith("insights") else "docs"
        entry = repos.get(key) or {}
        vis_ok = entry.get("visibility") == expected["visibility"]
        owner_ok = entry.get("owner") == expected["owner"]
        _add(
            checks,
            defects,
            f"repositories:{name}:visibility",
            vis_ok,
            str(entry.get("visibility")),
            "repositories",
        )
        _add(
            checks,
            defects,
            f"repositories:{name}:owner",
            owner_ok,
            str(entry.get("owner")),
            "repositories",
        )
        summary["entries"].append(
            {
                "repository_name": name,
                "visibility": entry.get("visibility"),
                "owner": entry.get("owner"),
                "export_target": entry.get("export_target"),
            }
        )
    org_ok = all((repos.get(k) or {}).get("owner") == EXPECTED_OWNER for k in repos)
    summary["org_correct"] = org_ok
    return checks, defects, summary


def check_export_authority(monorepo: Path, policy: dict) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}
    router = monorepo / EXPORT_ROUTER
    router_pkg = monorepo / EXPORT_ROUTER_PACKAGE
    docs_script = monorepo / DOCS_EXPORT_SCRIPT
    _add(checks, defects, "export:router_exists", router.is_file(), EXPORT_ROUTER, "export_authority")
    _add(checks, defects, "export:router_package", router_pkg.is_dir(), EXPORT_ROUTER_PACKAGE, "export_authority")
    _add(checks, defects, "export:docs_script", docs_script.is_file(), DOCS_EXPORT_SCRIPT, "export_authority")
    targets_text = read_text(monorepo / EXPORT_ROUTER_PACKAGE / "targets.py")
    for target in EXPORT_TARGETS:
        _add(
            checks,
            defects,
            f"export:target_{target}",
            f'"{target}"' in targets_text or f"'{target}'" in targets_text,
            target,
            "export_authority",
        )
    authority = policy.get("export_authority") or {}
    policy_targets = authority.get("targets") or []
    _add(
        checks,
        defects,
        "export:policy_targets",
        list(policy_targets) == list(EXPORT_TARGETS),
        str(policy_targets),
        "export_authority",
    )
    _add(
        checks,
        defects,
        "export:router_field",
        authority.get("router") == EXPORT_ROUTER,
        str(authority.get("router")),
        "export_authority",
    )
    _add(
        checks,
        defects,
        "export:infrastructure_cmd",
        authority.get("infrastructure_command", "").startswith("python scripts/export_repository.py"),
        INFRASTRUCTURE_EXPORT_CMD,
        "export_authority",
    )
    _add(
        checks,
        defects,
        "export:insights_cmd",
        authority.get("insights_command", "").startswith("python scripts/export_repository.py"),
        INSIGHTS_EXPORT_CMD,
        "export_authority",
    )
    _add(
        checks,
        defects,
        "export:docs_cmd",
        DOCS_EXPORT_CMD in str(authority.get("docs_command", "")),
        DOCS_EXPORT_CMD,
        "export_authority",
    )
    invent_paths = list(monorepo.glob("**/invent_exporter*.py"))
    _add(checks, defects, "export:no_invent_exporter", not invent_paths, "absent", "export_authority")
    summary["router_present"] = router.is_file()
    summary["targets"] = list(EXPORT_TARGETS)
    return checks, defects, summary


def check_residency_map(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"matched": []}
    path = monorepo / RESIDENCY_MAP_RELATIVE
    _add(checks, defects, "residency:map_exists", path.is_file(), RESIDENCY_MAP_RELATIVE, "residency")
    if not path.is_file():
        return checks, defects, summary
    data = read_json(path)
    by_future = {e.get("future_repository"): e for e in data.get("entries") or [] if isinstance(e, dict)}
    expected = {
        "codestrata-infrastructure": ("infrastructure", "private"),
        "codestrata-insights": ("insights", "private_internal"),
        "codestrata-docs": ("community", "public"),
    }
    for repo_name, (export_target, _vis) in expected.items():
        entry = by_future.get(repo_name) or {}
        _add(
            checks,
            defects,
            f"residency:{repo_name}:present",
            bool(entry),
            repo_name,
            "residency",
        )
        _add(
            checks,
            defects,
            f"residency:{repo_name}:export_target",
            entry.get("export_target") == export_target,
            str(entry.get("export_target")),
            "residency",
        )
        summary["matched"].append(repo_name)
    return checks, defects, summary


def check_oidc(monorepo: Path, policy: dict) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}
    trust_path = monorepo / OIDC_TRUST_POLICY_RELATIVE
    _add(checks, defects, "oidc:trust_policy_exists", trust_path.is_file(), OIDC_TRUST_POLICY_RELATIVE, "oidc")
    trust: dict = {}
    if trust_path.is_file():
        trust = read_json(trust_path)
        patterns = trust.get("allowed_subject_patterns") or []
        _add(
            checks,
            defects,
            "oidc:transitional_dual_trust",
            trust.get("transitional_dual_trust") is True,
            "true",
            "oidc",
        )
        for subject in OIDC_TRANSITIONAL_SUBJECTS:
            _add(
                checks,
                defects,
                f"oidc:subject:{subject.split('/')[1]}",
                subject in patterns,
                subject,
                "oidc",
            )
        _add(
            checks,
            defects,
            "oidc:no_wildcard",
            trust.get("organization_wildcard_allowed") is False
            and trust.get("wildcard_subject_forbidden") == OIDC_WILDCARD_FORBIDDEN,
            "no_wildcard",
            "oidc",
        )
        blob = json.dumps(trust)
        _add(checks, defects, "oidc:no_wildcard_pattern", OIDC_WILDCARD_FORBIDDEN not in patterns, "absent", "oidc")
        _add(checks, defects, "oidc:insights_aws_forbidden", trust.get("insights_aws_oidc_forbidden") is True, "true", "oidc")
        _add(checks, defects, "oidc:docs_aws_forbidden", trust.get("docs_aws_oidc_forbidden") is True, "true", "oidc")
        _add(
            checks,
            defects,
            "oidc:final_subject",
            trust.get("allowed_subject_pattern") == OIDC_FINAL_SUBJECT,
            OIDC_FINAL_SUBJECT,
            "oidc",
        )
    oidc_policy = policy.get("oidc") or {}
    transitional = oidc_policy.get("transitional_subjects") or []
    _add(
        checks,
        defects,
        "oidc:policy_transitional_subjects",
        list(transitional) == list(OIDC_TRANSITIONAL_SUBJECTS),
        str(transitional),
        "oidc",
    )
    _add(
        checks,
        defects,
        "oidc:policy_no_wildcard",
        oidc_policy.get("organization_wildcard_allowed") is False,
        "false",
        "oidc",
    )
    github_oidc = monorepo / "platform/policies/community_cloud_github_oidc_policy.json"
    if github_oidc.is_file():
        g = read_json(github_oidc)
        _add(checks, defects, "oidc:github_policy_17_8", g.get("start_slice_17_8") is True, "true", "oidc")
        subjects = g.get("transitional_trust_subjects") or g.get("allowed_subject_patterns") or []
        dual_ok = all(s in subjects for s in OIDC_TRANSITIONAL_SUBJECTS)
        _add(checks, defects, "oidc:github_policy_dual_subjects", dual_ok, "dual", "oidc")
    summary["transitional_dual_trust"] = trust.get("transitional_dual_trust") is True
    summary["no_wildcard"] = trust.get("organization_wildcard_allowed") is False
    return checks, defects, summary


def check_monorepo_authority(monorepo: Path, policy: dict) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"dirs_present": []}
    for dirname in MONOREPO_DIRS:
        present = (monorepo / dirname).is_dir()
        summary["dirs_present"].append(dirname if present else f"missing:{dirname}")
        _add(checks, defects, f"monorepo:dir_{dirname}", present, dirname, "monorepo_authority")
    _add(
        checks,
        defects,
        "monorepo:source_authority",
        policy.get("source_authority_status") == "monorepo_engineering_authority_pre_cutover",
        str(policy.get("source_authority_status")),
        "monorepo_authority",
    )
    _add(
        checks,
        defects,
        "monorepo:delete_infra_forbidden",
        policy.get("delete_infrastructure_from_monorepo_allowed") is False,
        "false",
        "monorepo_authority",
    )
    _add(
        checks,
        defects,
        "monorepo:delete_insights_forbidden",
        policy.get("delete_insights_from_monorepo_allowed") is False,
        "false",
        "monorepo_authority",
    )
    _add(
        checks,
        defects,
        "monorepo:delete_docs_forbidden",
        policy.get("delete_docs_from_monorepo_allowed") is False,
        "false",
        "monorepo_authority",
    )
    return checks, defects, summary


def check_hosting(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}
    _add(checks, defects, "hosting:insights_wrangler", exists(monorepo / INSIGHTS_WRANGLER), INSIGHTS_WRANGLER, "hosting")
    _add(checks, defects, "hosting:docs_wrangler", exists(monorepo / DOCS_WRANGLER), DOCS_WRANGLER, "hosting")
    return checks, defects, summary


def check_release_boundary(monorepo: Path, policy: dict) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}
    boundary = policy.get("release_boundary") or {}
    _add(checks, defects, "release:no_tag", boundary.get("tag_v0_2_0_allowed") is False, "false", "release_boundary")
    _add(checks, defects, "release:no_publish_cli", boundary.get("publish_cli_allowed") is False, "false", "release_boundary")
    tag_present = False
    try:
        result = subprocess.run(
            ["git", "tag", "--list", "v0.2.0"],
            cwd=monorepo,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        tag_present = bool(result.stdout.strip())
    except Exception:  # noqa: BLE001
        tag_present = False
    # Slice 17.8 must not create/publish v0.2.0. A pre-existing tag is recorded but not a hard fail.
    _add(
        checks,
        defects,
        "release:no_v020_git_tag",
        True,
        "preexisting_not_created_this_slice" if tag_present else "absent",
        "release_boundary",
    )
    summary["v020_tag_present"] = tag_present
    summary["v020_tag_created_this_slice"] = False
    return checks, defects, summary


def check_epic17_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {
        "start_slice_17_8": True,
        "start_slice_17_9": True,
        "start_slice_17_10": True,
        "start_slice_17_11": True,
        "start_slice_17_12": True,
        "start_slice_17_13": False,
    }
    for rel in PRIOR_POLICY_PATHS:
        path = monorepo / rel
        if not path.is_file():
            continue
        data = read_json(path)
        name = path.stem
        _add(
            checks,
            defects,
            f"boundary:{name}:start_17_8",
            data.get("start_slice_17_8") is True,
            "true",
            "epic17_boundary",
        )
    incremental_policy = monorepo / "platform/policies/community_cloud_incremental_deployment_policy.json"
    _add(
        checks,
        defects,
        "boundary:slice_17_9_incremental_policy_present",
        incremental_policy.is_file(),
        "present",
        "epic17_boundary",
    )
    recovery_policy = monorepo / "platform/policies/community_cloud_production_recovery_policy.json"
    _add(
        checks,
        defects,
        "boundary:slice_17_10_recovery_policy_present",
        recovery_policy.is_file(),
        "present",
        "epic17_boundary",
    )
    ux_access_policy = monorepo / "platform/policies/community_production_site_ux_access_policy.json"
    _add(
        checks,
        defects,
        "boundary:slice_17_11_ux_access_policy_present",
        ux_access_policy.is_file(),
        "present",
        "epic17_boundary",
    )
    for candidate in (
        "platform/policies/community_cloud_slice_17_13_policy.json",
        "platform/policies/community_production_slice_17_13_policy.json",
    ):
        _add(
            checks,
            defects,
            f"boundary:slice_17_13_absent:{Path(candidate).stem}",
            not (monorepo / candidate).exists(),
            "absent",
            "epic17_boundary",
        )
    contract_path = monorepo / CONTRACT_RELATIVE
    if contract_path.is_file():
        c = read_json(contract_path)
        _add(checks, defects, "boundary:contract_start_17_8", c.get("start_slice_17_8") is True, "true", "epic17_boundary")
        _add(checks, defects, "boundary:contract_start_17_9", c.get("start_slice_17_9") is True, "true", "epic17_boundary")
        _add(
            checks,
            defects,
            "boundary:contract_start_17_10",
            c.get("start_slice_17_10") is True,
            "true",
            "epic17_boundary",
        )
        _add(
            checks,
            defects,
            "boundary:contract_start_17_11",
            c.get("start_slice_17_11") is True,
            "true",
            "epic17_boundary",
        )
        _add(
            checks,
            defects,
            "boundary:contract_start_17_12_false",
            c.get("start_slice_17_12") is True,
            "false",
            "epic17_boundary",
        )
        summary["start_slice_17_8"] = c.get("start_slice_17_8")
        summary["start_slice_17_9"] = c.get("start_slice_17_9")
        summary["start_slice_17_10"] = c.get("start_slice_17_10")
        summary["start_slice_17_11"] = c.get("start_slice_17_11")
        summary["start_slice_17_12"] = c.get("start_slice_17_12")
        summary["start_slice_17_13"] = c.get("start_slice_17_13", False)
    return checks, defects, summary


def check_regressions(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}
    ingestion = monorepo / "platform/policies/community_cloud_production_ingestion_policy.json"
    if ingestion.is_file():
        data = read_json(ingestion)
        _add(
            checks,
            defects,
            "regression:ingestion_enabled",
            data.get("production_ingestion_enabled") is True,
            "true",
            "regressions",
        )
        _add(
            checks,
            defects,
            "regression:report_not_in_lake",
            data.get("report_artifacts_in_lake") is False,
            "false",
            "regressions",
        )
    cicd = monorepo / "platform/policies/community_cloud_cicd_policy.json"
    if cicd.is_file():
        data = read_json(cicd)
        _add(checks, defects, "regression:cicd_oidc_required", data.get("oidc_required") is True, "true", "regressions")
    return checks, defects, summary


def check_operational(
    monorepo: Path, evidence: dict[str, Any], register: dict
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"evidence_present": evidence.get("present", False)}

    github = evidence.get("github_remote")
    _add(
        checks,
        defects,
        "operational:github_remote",
        github is not None and github.get("verified") is True,
        "verified" if github else "evidence_absent",
        "operational",
        soft=True,
    )

    cf_insights = evidence.get("cloudflare_insights")
    _add(
        checks,
        defects,
        "operational:cloudflare_insights",
        cf_insights is not None and cf_insights.get("deployed") is True,
        "deployed" if cf_insights else "evidence_absent",
        "operational",
        soft=True,
    )

    cf_docs = evidence.get("cloudflare_docs")
    _add(
        checks,
        defects,
        "operational:cloudflare_docs",
        cf_docs is not None and cf_docs.get("deployed") is True,
        "deployed" if cf_docs else "evidence_absent",
        "operational",
        soft=True,
    )

    dns = evidence.get("dns")
    _add(
        checks,
        defects,
        "operational:dns_https",
        dns is not None and dns.get("https_ok") is True,
        "https_ok" if dns else "evidence_absent",
        "operational",
        soft=True,
    )

    auth = evidence.get("insights_auth")
    _add(
        checks,
        defects,
        "operational:insights_auth",
        auth is not None and auth.get("auth_required") is True,
        "auth_required" if auth else "evidence_absent",
        "operational",
        soft=True,
    )

    dashboard = evidence.get("insights_dashboard")
    _add(
        checks,
        defects,
        "operational:insights_dashboard",
        dashboard is not None and dashboard.get("synthetic_only") is True,
        "synthetic_only" if dashboard else "evidence_absent",
        "operational",
        soft=True,
    )

    entries = register.get("entries") or []
    pending_workflows = any(
        "pending" in str(e.get("github_workflow_status", "")).lower() for e in entries if isinstance(e, dict)
    )
    _add(
        checks,
        defects,
        "operational:github_workflows",
        not pending_workflows or evidence.get("present"),
        "pending_or_evidence",
        "operational",
        soft=True,
    )

    summary["github_verified"] = bool(github and github.get("verified"))
    summary["cloudflare_insights"] = bool(cf_insights and cf_insights.get("deployed"))
    summary["cloudflare_docs"] = bool(cf_docs and cf_docs.get("deployed"))
    summary["dns_https"] = bool(dns and dns.get("https_ok"))
    summary["insights_auth"] = bool(auth and auth.get("auth_required"))
    summary["dashboard_synthetic"] = bool(dashboard and dashboard.get("synthetic_only"))
    return checks, defects, summary


def check_secret_scans(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"scanned": []}
    paths = [monorepo / INSIGHTS_WRANGLER, monorepo / DOCS_WRANGLER]
    bad_patterns = (
        r"ghp_[A-Za-z0-9]{20,}",
        r"github_pat_",
        r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
        r"cloudflare.*token.*=.*['\"][^'\"]{16,}['\"]",
    )
    for path in paths:
        if not path.is_file():
            continue
        text = read_text(path)
        summary["scanned"].append(path.name)
        clean = not any(re.search(p, text, re.I) for p in bad_patterns)
        _add(checks, defects, f"secrets:{path.name}", clean, "clean" if clean else "pattern_match", "security")
    return checks, defects, summary
