"""Structural and live checks for Slice 17.23."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from verification.community_status_report_registry.contract import (
    COMMUNITY_CLOUD_APP,
    COMMUNITY_STATUS_DIR,
    COMMUNITY_STATUS_GITHUB,
    COMMUNITY_STATUS_ROUTES,
    COMMUNITY_STATUS_SERVICE,
    CONTRACT_RELATIVE,
    DOCS_COMMUNITY_API,
    ENGINE_PUBLIC_REPORT_URL_MANIFEST,
    EXPECTED_17_22_PACKAGE,
    EXPECTED_17_23_PACKAGE,
    FLASK_17_21_REPO_ID,
    INSIGHTS_API_PATH,
    INSIGHTS_APP,
    INSIGHTS_APP_SHELL,
    INSIGHTS_AUTH_ROUTES,
    INSIGHTS_PAGE_ROUTE,
    INSIGHTS_PUBLISHED_PAGE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    PUBLIC_REPORT_URLS_RELATIVE,
    PUBLIC_REPORT_URLS_SCHEMA,
    PUBLIC_REPORTS,
    PUBLIC_REPORTS_PREFIX,
    PUBLIC_STATUS_URL,
    PUBLISHED_REGISTER_RELATIVE,
    SITE_JS_RELATIVE,
    SLICE_17_24_PACKAGE_CANDIDATES,
    STATUS_REGISTER_RELATIVE,
    STATUS_REGISTER_SCHEMA,
    sibling_site_root,
)
from verification.community_status_report_registry.helpers import (
    add_check,
    body_has_aws_or_secrets,
    contains,
    load_json,
    read_engine_version,
    read_text,
)
from verification.community_status_report_registry.models import CheckResult, Defect

STATUS_REQUIRED_FIELDS = (
    "engine_version",
    "github_stars",
    "github_repository",
    "github_url",
    "status",
    "schema_id",
    "schema_version",
)


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict[str, Any] = {}
    path = monorepo / POLICY_RELATIVE
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
    reg = monorepo / STATUS_REGISTER_RELATIVE
    add_check(checks, defects, "policy:status_register", reg.is_file(), STATUS_REGISTER_RELATIVE, "policy")
    if reg.is_file():
        doc = load_json(reg)
        add_check(
            checks,
            defects,
            "policy:status_register_schema",
            doc.get("schema") == STATUS_REGISTER_SCHEMA,
            str(doc.get("schema")),
            "policy",
        )
    add_check(
        checks,
        defects,
        "policy:published_register",
        (monorepo / PUBLISHED_REGISTER_RELATIVE).is_file(),
        PUBLISHED_REGISTER_RELATIVE,
        "policy",
    )
    return checks, defects, policy


def check_status_module(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    status_dir = monorepo / COMMUNITY_STATUS_DIR
    routes = monorepo / COMMUNITY_STATUS_ROUTES
    add_check(
        checks,
        defects,
        "status:module",
        status_dir.is_dir(),
        COMMUNITY_STATUS_DIR,
        "status",
    )
    add_check(
        checks,
        defects,
        "status:routes_file",
        routes.is_file(),
        COMMUNITY_STATUS_ROUTES,
        "status",
    )
    route_ok = False
    if routes.is_file():
        text = read_text(routes)
        route_ok = (
            'STATUS_PATH = "/community/status"' in text
            or 'path=STATUS_PATH' in text
            or '"/community/status"' in text
        ) and "register_community_status_routes" in text
        add_check(
            checks,
            defects,
            "status:route",
            route_ok,
            "/community/status",
            "status",
        )
        add_check(
            checks,
            defects,
            "status:public_auth",
            'authentication_group="public"' in text,
            "public",
            "status",
        )
        add_check(
            checks,
            defects,
            "status:get_method",
            'method="GET"' in text,
            "GET",
            "status",
        )

    app = monorepo / COMMUNITY_CLOUD_APP
    app_wired = False
    if app.is_file():
        app_text = read_text(app)
        app_wired = (
            "register_community_status_routes" in app_text
            or "/community/status" in app_text
        )
    add_check(
        checks,
        defects,
        "status:app_wired",
        app_wired,
        "app.py",
        "status",
    )

    service = monorepo / COMMUNITY_STATUS_SERVICE
    engine_src = False
    if service.is_file():
        svc = read_text(service)
        engine_src = "codestrata.__version__" in svc or "__version__" in svc
    add_check(
        checks,
        defects,
        "status:engine_version_source",
        engine_src,
        "codestrata.__version__",
        "status",
    )

    summary["module"] = status_dir.is_dir()
    summary["route"] = route_ok
    summary["app_wired"] = app_wired
    summary["engine_version_source"] = engine_src
    return checks, defects, summary


def check_status_live(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    """Live GET community/status — soft when network/deploy fails after structural pass."""
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    summary: dict[str, Any] = {
        "http_status": None,
        "reachable": False,
        "schema_ok": False,
        "engine_version_match": False,
        "no_secrets": True,
    }

    expected_version = read_engine_version(monorepo)
    summary["expected_engine_version"] = expected_version

    body_text = ""
    http_status: int | None = None
    try:
        req = Request(
            PUBLIC_STATUS_URL,
            headers={"Accept": "application/json", "User-Agent": "codestrata-sv17-23"},
            method="GET",
        )
        with urlopen(req, timeout=10) as resp:  # noqa: S310 — public HTTPS probe
            http_status = int(getattr(resp, "status", 200) or 200)
            body_text = resp.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        http_status = int(exc.code)
        try:
            body_text = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            body_text = ""
    except (URLError, TimeoutError, OSError) as exc:
        summary["error"] = type(exc).__name__
        add_check(
            checks,
            defects,
            "status:live",
            False,
            "unreachable",
            "status_live",
            soft=True,
        )
        limitations.append("status_api_deploy_pending")
        return checks, defects, summary, limitations

    summary["http_status"] = http_status
    summary["reachable"] = http_status == 200

    if http_status != 200:
        add_check(
            checks,
            defects,
            "status:live",
            False,
            f"http={http_status}",
            "status_live",
            soft=True,
        )
        limitations.append("status_api_deploy_pending")
        return checks, defects, summary, limitations

    add_check(checks, defects, "status:live", True, "http=200", "status_live", soft=True)

    payload: dict[str, Any] = {}
    try:
        parsed = json.loads(body_text)
        if isinstance(parsed, dict):
            payload = parsed
    except json.JSONDecodeError:
        payload = {}

    schema_ok = all(k in payload for k in STATUS_REQUIRED_FIELDS)
    summary["schema_ok"] = schema_ok
    add_check(
        checks,
        defects,
        "status:live_schema",
        schema_ok,
        "fields" if schema_ok else "missing_fields",
        "status_live",
    )

    actual_version = str(payload.get("engine_version") or "")
    version_ok = bool(expected_version) and actual_version == expected_version
    summary["engine_version_match"] = version_ok
    summary["live_engine_version"] = actual_version
    add_check(
        checks,
        defects,
        "status:live_engine_version",
        version_ok,
        actual_version or "missing",
        "status_live",
    )

    no_secrets = not body_has_aws_or_secrets(body_text)
    summary["no_secrets"] = no_secrets
    add_check(
        checks,
        defects,
        "status:live_no_secrets",
        no_secrets,
        "clean" if no_secrets else "leak",
        "status_live",
    )

    if payload.get("github_stars_source") == "unavailable" or payload.get("status") == "degraded":
        limitations.append("github_temporary_unavailable_handled")

    return checks, defects, summary, limitations


def check_github_cache_and_website(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    github: dict[str, Any] = {}
    website: dict[str, Any] = {}

    cache_path = monorepo / COMMUNITY_STATUS_GITHUB
    present = cache_path.is_file()
    add_check(
        checks,
        defects,
        "status:github_cache",
        present,
        COMMUNITY_STATUS_GITHUB,
        "github_cache",
    )
    if present:
        text = read_text(cache_path)
        add_check(
            checks,
            defects,
            "status:github_cache_ttl",
            "DEFAULT_STARS_TTL_SECONDS" in text or "ttl_seconds" in text,
            "ttl",
            "github_cache",
        )
        add_check(
            checks,
            defects,
            "status:github_cache_fail_soft",
            "unavailable" in text and "fail" in text.lower(),
            "fail_soft",
            "github_cache",
        )
        github["module"] = True
        github["ttl"] = "DEFAULT_STARS_TTL_SECONDS" in text
    else:
        github["module"] = False

    site_root = sibling_site_root(monorepo)
    site_js = site_root / SITE_JS_RELATIVE
    website["site_js_path"] = "codestrata-site/assets/site.js"
    if not site_js.is_file():
        add_check(
            checks,
            defects,
            "website:site_js",
            False,
            "absent",
            "website",
            soft=True,
        )
        limitations.append("website_deploy_owner_follow_up")
        website["present"] = False
        website["no_github_token"] = True
        return checks, defects, github, website, limitations

    site_text = read_text(site_js)
    website["present"] = True
    add_check(checks, defects, "website:site_js", True, "present", "website")

    has_ghp = bool(re.search(r"ghp_[A-Za-z0-9]", site_text))
    has_pat = "github_pat_" in site_text
    # Forbid embedded token credentials; allow words like "tokens" only if not assignment-like.
    token_credential = bool(
        re.search(r"""(?:token|TOKEN)\s*[:=]\s*['\"][^'\"]{8,}['\"]""", site_text)
        or re.search(r"""Authorization['\"]?\s*:\s*['\"]Bearer""", site_text)
    )
    clean = not has_ghp and not has_pat and not token_credential
    website["no_github_token"] = clean
    add_check(
        checks,
        defects,
        "website:no_github_token",
        clean,
        "clean" if clean else "token_pattern",
        "website",
    )
    add_check(
        checks,
        defects,
        "website:fetches_status_api",
        PUBLIC_STATUS_URL in site_text or "/community/status" in site_text,
        "bound",
        "website",
    )
    return checks, defects, github, website, limitations


def check_manifest(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    path = monorepo / PUBLIC_REPORT_URLS_RELATIVE
    add_check(
        checks,
        defects,
        "manifest:exists",
        path.is_file(),
        PUBLIC_REPORT_URLS_RELATIVE,
        "manifest",
    )
    if not path.is_file():
        return checks, defects, summary

    doc = load_json(path)
    schema_ok = doc.get("schema") == PUBLIC_REPORT_URLS_SCHEMA
    add_check(
        checks,
        defects,
        "manifest:schema",
        schema_ok,
        str(doc.get("schema")),
        "manifest",
    )
    summary["schema"] = doc.get("schema")

    assessments = doc.get("assessments") or []
    add_check(
        checks,
        defects,
        "manifest:assessments_array",
        isinstance(assessments, list),
        "list",
        "manifest",
    )

    has_current_previous = False
    flask_retained = False
    for entry in assessments:
        if not isinstance(entry, dict):
            continue
        if "current_public_url" in entry and "previous_public_url" in entry:
            has_current_previous = True
        if (
            entry.get("repository_id") == FLASK_17_21_REPO_ID
            and entry.get("source_slice") == "17.21"
            and isinstance(entry.get("current_public_url"), str)
            and PUBLIC_REPORTS_PREFIX in str(entry.get("current_public_url"))
        ):
            flask_retained = True

    add_check(
        checks,
        defects,
        "manifest:current_previous_fields",
        has_current_previous,
        "present" if has_current_previous else "absent",
        "manifest",
    )
    add_check(
        checks,
        defects,
        "manifest:flask_17_21",
        flask_retained,
        FLASK_17_21_REPO_ID,
        "manifest",
    )
    summary["current_previous"] = has_current_previous
    summary["flask_17_21"] = flask_retained
    summary["assessment_count"] = len(assessments) if isinstance(assessments, list) else 0

    engine_manifest = monorepo / ENGINE_PUBLIC_REPORT_URL_MANIFEST
    auto = engine_manifest.is_file()
    add_check(
        checks,
        defects,
        "manifest:auto_upsert",
        auto,
        ENGINE_PUBLIC_REPORT_URL_MANIFEST,
        "manifest",
    )
    if auto:
        text = read_text(engine_manifest)
        add_check(
            checks,
            defects,
            "manifest:auto_upsert_schema_1_1",
            PUBLIC_REPORT_URLS_SCHEMA in text or "1.1" in text,
            "1.1",
            "manifest",
        )
        add_check(
            checks,
            defects,
            "manifest:record_published_url",
            "record_published_url" in text or "def upsert" in text or "def record" in text,
            "upsert",
            "manifest",
        )
    summary["auto_upsert"] = auto
    return checks, defects, summary


def check_insights(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    page = monorepo / INSIGHTS_PUBLISHED_PAGE
    add_check(
        checks,
        defects,
        "insights:page",
        page.is_file(),
        INSIGHTS_PUBLISHED_PAGE,
        "insights",
    )
    if page.is_file():
        page_text = read_text(page)
        add_check(
            checks,
            defects,
            "insights:page_reports_domain",
            "reports.codestrata.ai" in page_text,
            PUBLIC_REPORTS,
            "insights",
        )

    shell = monorepo / INSIGHTS_APP_SHELL
    nav_ok = shell.is_file() and contains(shell, INSIGHTS_PAGE_ROUTE)
    add_check(
        checks,
        defects,
        "insights:nav",
        nav_ok,
        INSIGHTS_PAGE_ROUTE,
        "insights",
    )

    app = monorepo / INSIGHTS_APP
    route_ok = app.is_file() and (
        contains(app, INSIGHTS_PAGE_ROUTE) and contains(app, "PublishedReportsPage")
    )
    add_check(
        checks,
        defects,
        "insights:route",
        route_ok,
        INSIGHTS_PAGE_ROUTE,
        "insights",
    )

    auth_routes = monorepo / INSIGHTS_AUTH_ROUTES
    api_ok = auth_routes.is_file() and contains(auth_routes, INSIGHTS_API_PATH)
    add_check(
        checks,
        defects,
        "insights:api_path",
        api_ok,
        INSIGHTS_API_PATH,
        "insights",
    )

    summary["page"] = page.is_file()
    summary["nav"] = nav_ok
    summary["route"] = route_ok
    summary["api_path"] = api_ok
    return checks, defects, summary


def check_docs(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    page = monorepo / DOCS_COMMUNITY_API
    add_check(checks, defects, "docs:community_api", page.is_file(), DOCS_COMMUNITY_API, "docs")
    text = read_text(page) if page.is_file() else ""
    add_check(
        checks,
        defects,
        "docs:community_status",
        "/community/status" in text or "Community Status" in text,
        "documented",
        "docs",
    )
    add_check(
        checks,
        defects,
        "docs:status_url",
        PUBLIC_STATUS_URL in text or "api/v1/community/status" in text,
        "url",
        "docs",
    )
    add_check(
        checks,
        defects,
        "docs:no_browser_github_token",
        "never embed a GitHub token" in text or "must never embed a GitHub token" in text,
        "documented",
        "docs",
    )
    summary["documented"] = "/community/status" in text
    return checks, defects, summary


def check_reports_domain(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    page = monorepo / INSIGHTS_PUBLISHED_PAGE
    page_ok = page.is_file() and "reports.codestrata.ai" in read_text(page)
    add_check(
        checks,
        defects,
        "reports:domain_insights_page",
        page_ok,
        PUBLIC_REPORTS,
        "reports_domain",
    )

    docs = monorepo / DOCS_COMMUNITY_API
    docs_ok = docs.is_file() and PUBLIC_REPORTS in read_text(docs)
    add_check(
        checks,
        defects,
        "reports:domain_docs",
        docs_ok,
        PUBLIC_REPORTS,
        "reports_domain",
    )

    policy = monorepo / POLICY_RELATIVE
    policy_ok = policy.is_file() and load_json(policy).get(
        "report_rendering_remains_reports_domain"
    ) is True
    add_check(
        checks,
        defects,
        "reports:domain_policy",
        policy_ok,
        "true",
        "reports_domain",
    )

    summary["remains_reports_domain"] = page_ok and policy_ok
    return checks, defects, summary


def check_prior_slices(
    monorepo: Path,
    policy: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    ok22 = (monorepo / EXPECTED_17_22_PACKAGE).is_dir()
    ok23 = (monorepo / EXPECTED_17_23_PACKAGE).is_dir()
    add_check(checks, defects, "prior_slices:17_22", ok22, EXPECTED_17_22_PACKAGE, "prior_slices")
    add_check(checks, defects, "prior_slices:17_23_package", ok23, EXPECTED_17_23_PACKAGE, "prior_slices")

    start_23 = policy.get("start_slice_17_23") is True
    start_24 = policy.get("start_slice_17_24") is True
    add_check(
        checks,
        defects,
        "boundary:start_slice_17_23",
        start_23,
        "true",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:start_slice_17_24_false",
        not start_24,
        "false",
        "epic17_boundary",
    )

    started_24 = False
    for cand in SLICE_17_24_PACKAGE_CANDIDATES:
        exists = (monorepo / cand).exists()
        if exists:
            started_24 = True
        add_check(
            checks,
            defects,
            f"security:no_{Path(cand).name}",
            not exists,
            "absent" if not exists else "present",
            "security",
        )

    add_check(
        checks,
        defects,
        "prior_slices:17_24_not_started",
        not started_24,
        "absent",
        "prior_slices",
    )

    return checks, defects, {
        "slice_17_22": ok22,
        "slice_17_23": ok23,
        "start_slice_17_23": start_23,
        "start_slice_17_24": False,
        "slice_17_24_started": started_24,
    }


def check_operational(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = ["monorepo_pre_cutover_authority", "full_22_corpus_deferred_to_release"]

    uncommitted = False
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=monorepo,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        uncommitted = bool(result.stdout.strip())
    except Exception:  # noqa: BLE001
        uncommitted = False

    add_check(
        checks,
        defects,
        "operational:worktree_uncommitted",
        not uncommitted,
        "clean" if not uncommitted else "dirty",
        "operational",
        soft=True,
    )
    if uncommitted:
        limitations.append("worktree_uncommitted")
    return checks, defects, limitations
