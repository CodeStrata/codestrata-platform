"""Structural and evidence-based checks for Slice 17.11."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from verification.community_production_site_ux_access.contract import (
    CONTRACT_RELATIVE,
    DESIGN_SYSTEM_FAVICON,
    DOCS_CONFIG,
    DOCS_CUSTOM_CSS,
    DOCS_FAVICON,
    DOCS_FOOTER,
    DOCS_HOME_LINK,
    EVIDENCE_DIR_RELATIVE,
    EVIDENCE_FILES,
    EXPECTED_AUTH_ROOT_CAUSE,
    EXPECTED_DOCS_LOGO_DESTINATION,
    EXPECTED_DOCS_MAIN_SITE,
    INSIGHTS_AUTH_CONTEXT,
    INSIGHTS_FAVICON,
    INSIGHTS_INDEX,
    INSIGHTS_LOGIN_PAGE,
    INSIGHTS_POLICY_RELATIVE,
    INSIGHTS_REGISTER_RELATIVE,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    PRIOR_VERIFICATION_PACKAGES,
    REGISTER_FIELDS,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
    SLICE_17_12_POLICY_CANDIDATES,
    SITES_POLICY_RELATIVE,
)
from verification.community_production_site_ux_access.helpers import read_json, read_text, sha256_hex
from verification.community_production_site_ux_access.models import CheckResult, Defect


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


def _register_field_ok(data: dict[str, Any], field: str, expected: Any) -> bool:
    return data.get(field) == expected


def load_evidence(monorepo: Path) -> dict[str, Any]:
    evidence_dir = monorepo / EVIDENCE_DIR_RELATIVE
    files: dict[str, dict[str, Any]] = {}
    if evidence_dir.is_dir():
        for name in EVIDENCE_FILES:
            path = evidence_dir / name
            if path.is_file():
                try:
                    data = read_json(path)
                    if isinstance(data, dict):
                        files[name] = data
                except Exception:  # noqa: BLE001
                    continue
    return {
        "files": files,
        "present": bool(files),
        "password_rca": files.get("password-rca.json"),
        "live_auth": files.get("live-auth.json"),
        "live_docs": files.get("live-docs.json"),
        "github_visibility": files.get("github-visibility.json"),
        "deploy": files.get("deploy.json"),
    }


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict[str, Any] = {}
    register: dict[str, Any] = {}

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
        _add(checks, defects, "policy:start_17_11", policy.get("start_slice_17_11") is True, "true", "policy")
        _add(checks, defects, "policy:start_17_12_false", policy.get("start_slice_17_12") is True, "false", "policy")
        for field in REGISTER_FIELDS:
            reg_val = policy.get(field)
            _add(
                checks,
                defects,
                f"policy:field:{field}",
                reg_val is not None,
                "present" if reg_val is not None else "missing",
                "policy",
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
        _add(checks, defects, "register:start_17_11", register.get("start_slice_17_11") is True, "true", "policy")
        _add(checks, defects, "register:start_17_12_false", register.get("start_slice_17_12") is True, "false", "policy")
        for field in REGISTER_FIELDS:
            _add(
                checks,
                defects,
                f"register:field:{field}",
                register.get(field) is not None,
                "present" if register.get(field) is not None else "missing",
                "policy",
            )
        rmirror = monorepo / INSIGHTS_REGISTER_RELATIVE
        _add(
            checks,
            defects,
            "register:insights_mirror",
            rmirror.is_file() and rmirror.read_bytes() == rpath.read_bytes(),
            "mirror",
            "policy",
        )

    _add(checks, defects, "contract:exists", (monorepo / CONTRACT_RELATIVE).is_file(), CONTRACT_RELATIVE, "policy")
    if (monorepo / CONTRACT_RELATIVE).is_file():
        contract = read_json(monorepo / CONTRACT_RELATIVE)
        _add(checks, defects, "contract:start_17_11", contract.get("start_slice_17_11") is True, "true", "policy")
        _add(checks, defects, "contract:start_17_12_false", contract.get("start_slice_17_12") is True, "false", "policy")

    return checks, defects, policy, register


def check_docs_ux(monorepo: Path, policy: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    config_text = read_text(monorepo / DOCS_CONFIG)
    logo_ok = 'logoLink: "/"' in config_text or "logoLink: '/'" in config_text
    _add(checks, defects, "docs:logo_link", logo_ok, EXPECTED_DOCS_LOGO_DESTINATION, "docs_ux")
    main_site_ok = EXPECTED_DOCS_MAIN_SITE in config_text and "Main Site" in config_text
    _add(checks, defects, "docs:main_site_nav", main_site_ok, EXPECTED_DOCS_MAIN_SITE, "docs_ux")
    trust_sidebar_ok = "Trust & Community" in config_text
    _add(checks, defects, "docs:trust_sidebar", trust_sidebar_ok, "Trust & Community", "docs_ux")

    css_text = read_text(monorepo / DOCS_CUSTOM_CSS)
    nav_offset_ok = (
        ".VPHero.VPHomeHero" in css_text
        and "var(--vp-nav-height" in css_text
        and "+ 48px" in css_text
        and "+ 80px" in css_text
    )
    scroll_ok = "scroll-margin-top" in css_text
    _add(checks, defects, "docs:header_nav_offset", nav_offset_ok, "VPHero padding-top", "docs_ux")
    _add(checks, defects, "docs:scroll_margin", scroll_ok, "scroll-margin-top", "docs_ux")
    header_fixed = policy.get("docs_header_overlap_fixed") is True and nav_offset_ok and scroll_ok
    summary["docs_header_overlap_fixed"] = header_fixed

    footer_text = read_text(monorepo / DOCS_FOOTER)
    home_footer_ok = "cs-footer" in footer_text and "isHome" in footer_text
    minimal_ok = "cs-footer--minimal" in footer_text and 'v-else' in footer_text
    _add(checks, defects, "docs:footer_home_split", home_footer_ok, "isHome", "docs_ux")
    _add(checks, defects, "docs:footer_inner_minimal", minimal_ok, "minimal", "docs_ux")

    home_link_text = read_text(monorepo / DOCS_HOME_LINK)
    _add(
        checks,
        defects,
        "docs:home_link_wiring",
        'DOCS_HOME = "/"' in home_link_text and "wireLogoLink" in home_link_text,
        "/",
        "docs_ux",
    )

    source_hash = sha256_hex(monorepo / DESIGN_SYSTEM_FAVICON)
    docs_hash = sha256_hex(monorepo / DOCS_FAVICON)
    favicon_match = bool(source_hash) and source_hash == docs_hash
    _add(checks, defects, "docs:favicon_hash_match", favicon_match, "match" if favicon_match else "mismatch", "docs_ux")

    summary["docs_logo_destination"] = EXPECTED_DOCS_LOGO_DESTINATION if logo_ok else "ambiguous"
    summary["docs_main_site_destination"] = EXPECTED_DOCS_MAIN_SITE if main_site_ok else "missing"
    summary["docs_favicon_status"] = policy.get("docs_favicon_status")
    summary["docs_inner_footer_posture"] = policy.get("docs_inner_footer_posture")
    return checks, defects, summary


def check_insights_ux(monorepo: Path, policy: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    index_text = read_text(monorepo / INSIGHTS_INDEX)
    favicon_path_ok = "/brand/codestrata-mark-on-dark.svg" in index_text
    _add(checks, defects, "insights:favicon_path", favicon_path_ok, "/brand/codestrata-mark-on-dark.svg", "insights_ux")

    source_hash = sha256_hex(monorepo / DESIGN_SYSTEM_FAVICON)
    insights_hash = sha256_hex(monorepo / INSIGHTS_FAVICON)
    favicon_match = bool(source_hash) and source_hash == insights_hash
    _add(
        checks,
        defects,
        "insights:favicon_hash_match",
        favicon_match,
        "match" if favicon_match else "mismatch",
        "insights_ux",
    )

    login_text = read_text(monorepo / INSIGHTS_LOGIN_PAGE)
    auth_text = read_text(monorepo / INSIGHTS_AUTH_CONTEXT)
    login_clarity = "Secrets Manager verifier" in login_text or "plaintext owner password" in login_text
    auth_generic = "Invalid password" in auth_text
    _add(checks, defects, "insights:login_page_soft", login_clarity, "clarity", "insights_ux", soft=True)
    _add(checks, defects, "insights:auth_context_soft", auth_generic, "generic_error", "insights_ux", soft=True)

    summary["insights_favicon_status"] = policy.get("insights_favicon_status")
    summary["insights_login_status"] = policy.get("insights_login_status")
    return checks, defects, summary


def check_sites_posture(
    monorepo: Path, policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    sites_policy: dict[str, Any] = {}
    sites_path = monorepo / SITES_POLICY_RELATIVE
    if sites_path.is_file():
        sites_policy = read_json(sites_path)
    docs_repo = (sites_policy.get("repositories") or {}).get("docs") or {}
    insights_repo = (sites_policy.get("repositories") or {}).get("insights") or {}

    _add(
        checks,
        defects,
        "sites:docs_repo_private",
        docs_repo.get("visibility") == "private",
        str(docs_repo.get("visibility")),
        "sites_posture",
    )
    _add(
        checks,
        defects,
        "sites:docs_site_public",
        docs_repo.get("site_public") is True,
        str(docs_repo.get("site_public")),
        "sites_posture",
    )
    _add(
        checks,
        defects,
        "sites:insights_repo_private",
        insights_repo.get("visibility") == "private",
        str(insights_repo.get("visibility")),
        "sites_posture",
    )

    ux_docs = (policy.get("repositories") or {}).get("docs") or {}
    _add(
        checks,
        defects,
        "sites:policy_docs_private",
        ux_docs.get("visibility") == "private",
        str(ux_docs.get("visibility")),
        "sites_posture",
    )
    _add(
        checks,
        defects,
        "sites:policy_docs_site_public",
        ux_docs.get("site_public") is True,
        str(ux_docs.get("site_public")),
        "sites_posture",
    )

    summary["docs_repo_visibility"] = policy.get("docs_repo_visibility")
    summary["docs_site_public"] = policy.get("docs_site_public")
    summary["production_sites_status"] = policy.get("production_sites_status")
    return checks, defects, summary


def check_auth_rca(
    monorepo: Path, policy: dict[str, Any], evidence: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    expected_cause = EXPECTED_AUTH_ROOT_CAUSE
    policy_cause = policy.get("insights_auth_root_cause")
    _add(
        checks,
        defects,
        "auth:root_cause_encoded",
        policy_cause == expected_cause,
        str(policy_cause),
        "auth_rca",
    )

    rca = evidence.get("password_rca")
    _add(
        checks,
        defects,
        "auth:password_rca_evidence",
        rca is not None,
        "present" if rca else "absent",
        "auth_rca",
        soft=True,
    )

    rotation_required = False
    owner_once_matches = False
    if isinstance(rca, dict):
        rotation_required = rca.get("rotation_required") is True
        owner_once_matches = rca.get("owner_once_matches_sm") is True
        cause_code = rca.get("root_cause_code")
        if cause_code:
            _add(
                checks,
                defects,
                "auth:rca_code_matches",
                cause_code == expected_cause,
                str(cause_code),
                "auth_rca",
                soft=True,
            )
        for forbidden in ("password", "verifier", "salt", "derived_key", "owner_once_value"):
            if forbidden in rca and rca[forbidden] not in (None, "", False):
                _add(
                    checks,
                    defects,
                    f"auth:rca_no_{forbidden}",
                    False,
                    "secret_field_present",
                    "auth_rca",
                )

    policy_rotation = policy.get("insights_password_rotation_performed")
    rotation_ok = policy_rotation is False and not rotation_required
    if owner_once_matches:
        rotation_ok = policy_rotation is False
    _add(
        checks,
        defects,
        "auth:rotation_not_required",
        rotation_ok,
        "false",
        "auth_rca",
    )

    summary["insights_auth_root_cause"] = policy_cause
    summary["insights_password_rotation_performed"] = policy_rotation
    summary["owner_once_matches_sm"] = owner_once_matches if rca else None
    summary["evidence_present"] = rca is not None
    return checks, defects, summary


def check_operational(evidence: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"evidence_present": evidence.get("present", False)}

    live_auth = evidence.get("live_auth")
    _add(
        checks,
        defects,
        "operational:live_auth",
        live_auth is not None and live_auth.get("auth_required") is True,
        "auth_required" if live_auth else "absent",
        "operational",
        soft=True,
    )

    live_docs = evidence.get("live_docs")
    _add(
        checks,
        defects,
        "operational:live_docs",
        live_docs is not None and live_docs.get("public") is True,
        "public" if live_docs else "absent",
        "operational",
        soft=True,
    )

    github_vis = evidence.get("github_visibility")
    docs_private_ok = github_vis is None or github_vis.get("codestrata-docs", {}).get("visibility") == "private"
    _add(
        checks,
        defects,
        "operational:github_visibility",
        github_vis is not None and docs_private_ok,
        "private" if github_vis else "absent",
        "operational",
        soft=True,
    )

    deploy = evidence.get("deploy")
    _add(
        checks,
        defects,
        "operational:deploy",
        deploy is not None and deploy.get("sites_live") is True,
        "live" if deploy else "absent",
        "operational",
        soft=True,
    )

    summary["live_auth"] = bool(live_auth and live_auth.get("auth_required"))
    summary["live_docs"] = bool(live_docs and live_docs.get("public"))
    summary["github_visibility"] = bool(github_vis)
    summary["deploy"] = bool(deploy and deploy.get("sites_live"))
    return checks, defects, summary


def check_regressions(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"prior_packages": []}

    for pkg in PRIOR_VERIFICATION_PACKAGES:
        present = (monorepo / pkg).is_dir()
        summary["prior_packages"].append({"package": pkg, "present": present})
        _add(
            checks,
            defects,
            f"regression:package:{pkg.split('/')[-1]}",
            present,
            "present" if present else "missing",
            "regressions",
            soft=True,
        )

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

    return checks, defects, summary


def check_epic17_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"start_slice_17_11": True, "start_slice_17_12": True}

    for candidate in SLICE_17_12_POLICY_CANDIDATES:
        _add(
            checks,
            defects,
            f"boundary:slice_17_13_absent:{Path(candidate).stem}",
            not (monorepo / candidate).exists(),
            "absent",
            "epic17_boundary",
        )

    pkg_dir = monorepo / "verification/community_production_site_ux_access"
    _add(checks, defects, "boundary:package_present", pkg_dir.is_dir(), "present", "epic17_boundary")

    if (monorepo / CONTRACT_RELATIVE).is_file():
        contract = read_json(monorepo / CONTRACT_RELATIVE)
        _add(checks, defects, "boundary:contract_17_11", contract.get("start_slice_17_11") is True, "true", "epic17_boundary")
        _add(
            checks,
            defects,
            "boundary:contract_17_12_false",
            contract.get("start_slice_17_12") is True,
            "false",
            "epic17_boundary",
        )
        summary["start_slice_17_11"] = contract.get("start_slice_17_11")
        summary["start_slice_17_12"] = contract.get("start_slice_17_12")

    return checks, defects, summary
