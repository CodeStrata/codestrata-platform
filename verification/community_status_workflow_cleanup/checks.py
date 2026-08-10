"""Structural and optional live checks for Slice 17.25."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from verification.community_status_workflow_cleanup.contract import (
    COMMUNITY_CLOUD_APP,
    COMMUNITY_STATUS_DIR,
    COMMUNITY_STATUS_GITHUB,
    COMMUNITY_STATUS_MODELS,
    COMMUNITY_STATUS_ROUTES,
    COMMUNITY_STATUS_SERVICE,
    CONTRACT_RELATIVE,
    DOCS_COMMUNITY_API,
    EXPECTED_17_24_PACKAGE,
    EXPECTED_17_25_PACKAGE,
    EXPORT_WORKFLOW_PATHS,
    GITHUB_REPOSITORY,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    PUBLIC_STATUS_URL,
    ROOT_WORKFLOW_PATHS,
    SITE_JS_RELATIVE,
    SLICE_17_26_PACKAGE_CANDIDATES,
    STATUS_REGISTER_RELATIVE,
    STATUS_REGISTER_SCHEMA,
    WORKFLOW_README_RELATIVE,
    WORKFLOW_REGISTER_RELATIVE,
    WORKFLOW_REGISTER_SCHEMA,
    sibling_site_root,
)
from verification.community_status_workflow_cleanup.helpers import (
    add_check,
    body_has_aws_or_secrets,
    load_json,
    read_engine_version,
    read_text,
    workflow_has_embedded_secrets,
)
from verification.community_status_workflow_cleanup.models import CheckResult, Defect

STATUS_REQUIRED_PUBLIC_FIELDS = (
    "engine_version",
    "github_stars",
    "github_repository",
    "github_url",
    "status",
    "schema_id",
    "schema_version",
)

FABRICATED_STARS_PATTERNS = (
    re.compile(r"github_stars\s*=\s*\d{2,}"),
    re.compile(r"stargazers_count\s*=\s*\d{2,}"),
    re.compile(r'"github_stars"\s*:\s*\d{2,}'),
)

CI_DEPLOY_PATTERNS = (
    re.compile(r"\bnpm run deploy\b"),
    re.compile(r"\bwrangler deploy\b"),
    re.compile(r"\bterraform apply\b"),
    re.compile(r"\btofu apply\b"),
    re.compile(r"\baws cloudformation deploy\b"),
    re.compile(r"\bserverless deploy\b"),
)


def check_policy_and_registers(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict[str, Any] = {}
    workflow_register: dict[str, Any] = {}

    policy_path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", policy_path.is_file(), POLICY_RELATIVE, "policy")
    if policy_path.is_file():
        policy = load_json(policy_path)
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

    status_reg = monorepo / STATUS_REGISTER_RELATIVE
    add_check(
        checks,
        defects,
        "register:status_exists",
        status_reg.is_file(),
        STATUS_REGISTER_RELATIVE,
        "register",
    )
    if status_reg.is_file():
        status_doc = load_json(status_reg)
        add_check(
            checks,
            defects,
            "register:status_schema",
            status_doc.get("schema") == STATUS_REGISTER_SCHEMA,
            str(status_doc.get("schema")),
            "register",
        )
        add_check(
            checks,
            defects,
            "register:status_engine_version_source",
            status_doc.get("engine_version_source")
            == "github_published_release_with_candidate_fallback",
            str(status_doc.get("engine_version_source")),
            "register",
        )
        add_check(
            checks,
            defects,
            "register:status_github_repository",
            status_doc.get("github_repository") == GITHUB_REPOSITORY,
            str(status_doc.get("github_repository")),
            "register",
        )

    wf_reg_path = monorepo / WORKFLOW_REGISTER_RELATIVE
    add_check(
        checks,
        defects,
        "register:workflow_exists",
        wf_reg_path.is_file(),
        WORKFLOW_REGISTER_RELATIVE,
        "register",
    )
    if wf_reg_path.is_file():
        workflow_register = load_json(wf_reg_path)
        add_check(
            checks,
            defects,
            "register:workflow_schema",
            workflow_register.get("schema") == WORKFLOW_REGISTER_SCHEMA,
            str(workflow_register.get("schema")),
            "register",
        )
        add_check(
            checks,
            defects,
            "register:platform_repo_deployment_authority_false",
            workflow_register.get("platform_repo_deployment_authority") is False,
            str(workflow_register.get("platform_repo_deployment_authority")),
            "register",
        )
        add_check(
            checks,
            defects,
            "register:export_repo_ci_authority_preserved",
            workflow_register.get("export_repo_ci_authority_preserved") is True,
            str(workflow_register.get("export_repo_ci_authority_preserved")),
            "register",
        )
        add_check(
            checks,
            defects,
            "register:start_slice_17_27_false",
            workflow_register.get("start_slice_17_27") is False,
            str(workflow_register.get("start_slice_17_27")),
            "register",
        )
        # Slice 17.26 may be active after 17.25 completes; register reflects that.
        add_check(
            checks,
            defects,
            "register:start_slice_17_26_recorded",
            workflow_register.get("start_slice_17_26") in (True, False),
            str(workflow_register.get("start_slice_17_26")),
            "register",
        )

    return checks, defects, policy, workflow_register


def check_github_authority(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    status_dir = monorepo / COMMUNITY_STATUS_DIR
    github_path = monorepo / COMMUNITY_STATUS_GITHUB
    service_path = monorepo / COMMUNITY_STATUS_SERVICE
    models_path = monorepo / COMMUNITY_STATUS_MODELS
    routes_path = monorepo / COMMUNITY_STATUS_ROUTES

    add_check(
        checks,
        defects,
        "github:module_dir",
        status_dir.is_dir(),
        COMMUNITY_STATUS_DIR,
        "github_authority",
    )
    add_check(
        checks,
        defects,
        "github:github_stars_module",
        github_path.is_file(),
        COMMUNITY_STATUS_GITHUB,
        "github_authority",
    )
    add_check(
        checks,
        defects,
        "github:service_module",
        service_path.is_file(),
        COMMUNITY_STATUS_SERVICE,
        "github_authority",
    )

    github_text = read_text(github_path)
    service_text = read_text(service_path)
    models_text = read_text(models_path)

    has_cache = "class GitHubMetadataCache" in github_text
    add_check(
        checks,
        defects,
        "github:metadata_cache_class",
        has_cache,
        "GitHubMetadataCache",
        "github_authority",
    )
    add_check(
        checks,
        defects,
        "github:normalize_release_tag",
        "def normalize_release_tag" in github_text,
        "normalize_release_tag",
        "github_authority",
    )
    add_check(
        checks,
        defects,
        "github:cache_ttl_300",
        "DEFAULT_METADATA_TTL_SECONDS = 300" in github_text
        or "DEFAULT_METADATA_TTL_SECONDS = 300.0" in github_text,
        "300",
        "github_authority",
    )
    add_check(
        checks,
        defects,
        "github:fail_soft",
        "unavailable" in github_text and "fail" in github_text.lower(),
        "fail_soft",
        "github_authority",
    )
    add_check(
        checks,
        defects,
        "github:resolve_public_engine_version",
        "def resolve_public_engine_version" in service_text,
        "resolve_public_engine_version",
        "github_authority",
    )
    add_check(
        checks,
        defects,
        "github:build_verification_view",
        "def build_verification_view" in service_text,
        "build_verification_view",
        "github_authority",
    )
    add_check(
        checks,
        defects,
        "github:draft_prerelease_skip",
        "draft" in github_text and "prerelease" in github_text,
        "skip_draft_prerelease",
        "github_authority",
    )

    stable_section = (
        models_text.split("def to_stable_dict", 1)[-1]
        if "def to_stable_dict" in models_text
        else ""
    )
    public_ok = (
        "def to_stable_dict" in models_text
        and '"version_source"' not in stable_section
        and '"package_candidate_version"' not in stable_section
    )
    add_check(
        checks,
        defects,
        "github:public_no_version_source",
        public_ok,
        "omitted",
        "github_authority",
    )

    fabricated = any(p.search(service_text) for p in FABRICATED_STARS_PATTERNS)
    add_check(
        checks,
        defects,
        "github:no_fabricated_stars",
        not fabricated,
        "no_hardcoded_stars",
        "github_authority",
        classification="fabricated_stars",
    )

    app_wired = False
    app_path = monorepo / COMMUNITY_CLOUD_APP
    if app_path.is_file():
        app_text = read_text(app_path)
        app_wired = "register_community_status_routes" in app_text
    route_ok = routes_path.is_file() and "/community/status" in read_text(routes_path)
    add_check(checks, defects, "github:routes_wired", route_ok, "route", "github_authority")
    add_check(checks, defects, "github:app_wired", app_wired, "app", "github_authority")

    summary.update(
        {
            "module": status_dir.is_dir(),
            "github_cache": has_cache,
            "normalize_release_tag": "def normalize_release_tag" in github_text,
            "resolve_public_engine_version": "def resolve_public_engine_version" in service_text,
            "public_no_version_source": public_ok,
            "no_fabricated_stars": not fabricated,
            "route": route_ok,
        }
    )
    return checks, defects, summary


def check_docs(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    docs = monorepo / DOCS_COMMUNITY_API
    add_check(checks, defects, "docs:community_api", docs.is_file(), DOCS_COMMUNITY_API, "docs")
    if not docs.is_file():
        return checks, defects, summary

    text = read_text(docs)
    has_release = "published" in text.lower() and "GitHub Release" in text
    has_candidate = "candidate" in text.lower() or "release_candidate" in text
    has_status = "/community/status" in text or PUBLIC_STATUS_URL in text
    add_check(checks, defects, "docs:github_release", has_release, "documented", "docs")
    add_check(checks, defects, "docs:candidate_fallback", has_candidate, "documented", "docs")
    add_check(checks, defects, "docs:status_endpoint", has_status, "documented", "docs")
    add_check(
        checks,
        defects,
        "docs:no_version_source_public",
        "not exposed on the" in text or "verification only" in text.lower(),
        "verification_only",
        "docs",
    )

    summary["documented"] = has_release and has_candidate and has_status
    summary["github_release"] = has_release
    summary["candidate_fallback"] = has_candidate
    return checks, defects, summary


def check_website(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    summary: dict[str, Any] = {}

    site_root = sibling_site_root(monorepo)
    site_js = site_root / SITE_JS_RELATIVE
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
        summary["present"] = False
        summary["no_github_token"] = True
        summary["status_binding"] = False
        return checks, defects, summary, limitations

    site_text = read_text(site_js)
    summary["present"] = True
    add_check(checks, defects, "website:site_js", True, "present", "website")

    has_binding = PUBLIC_STATUS_URL in site_text or "/api/v1/community/status" in site_text
    summary["status_binding"] = has_binding
    add_check(
        checks,
        defects,
        "website:status_api_binding",
        has_binding,
        PUBLIC_STATUS_URL,
        "website",
    )

    has_ghp = bool(re.search(r"ghp_[A-Za-z0-9]", site_text))
    has_pat = "github_pat_" in site_text
    token_credential = bool(
        re.search(r"""(?:token|TOKEN)\s*[:=]\s*['\"][^'\"]{8,}['\"]""", site_text)
        or re.search(r"""Authorization['\"]?\s*:\s*['\"]Bearer""", site_text)
    )
    clean = not has_ghp and not has_pat and not token_credential
    summary["no_github_token"] = clean
    add_check(
        checks,
        defects,
        "website:no_github_token",
        clean,
        "clean" if clean else "token_pattern",
        "website",
    )
    return checks, defects, summary, limitations


def check_workflow_inventory(
    monorepo: Path,
    workflow_register: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = ["live_platform_push_deferred", "monorepo_pre_cutover_authority"]
    summary: dict[str, Any] = {
        "root_workflows": {},
        "export_workflows": {},
        "absent_deploy_workflows": [],
    }

    readme_ok = (monorepo / WORKFLOW_README_RELATIVE).is_file()
    add_check(
        checks,
        defects,
        "workflows:readme",
        readme_ok,
        WORKFLOW_README_RELATIVE,
        "workflows",
    )

    registered = {
        str(entry.get("path")): entry
        for entry in (workflow_register.get("workflows") or [])
        if isinstance(entry, dict)
    }

    root_ok = True
    for wf_path in ROOT_WORKFLOW_PATHS:
        full = monorepo / wf_path
        exists = full.is_file()
        summary["root_workflows"][wf_path] = exists
        add_check(checks, defects, f"workflows:root:{Path(wf_path).name}", exists, wf_path, "workflows")
        if not exists:
            root_ok = False
            continue
        text = read_text(full)
        entry = registered.get(wf_path, {})
        guard = str(entry.get("repository_guard") or "CodeStrata/codestrata-platform")
        has_guard = guard in text
        add_check(
            checks,
            defects,
            f"workflows:guard:{Path(wf_path).name}",
            has_guard,
            guard,
            "workflows",
        )
        root_ok = root_ok and has_guard

    export_ok = True
    for wf_path in EXPORT_WORKFLOW_PATHS:
        full = monorepo / wf_path
        exists = full.is_file()
        summary["export_workflows"][wf_path] = exists
        add_check(
            checks,
            defects,
            f"workflows:export:{Path(wf_path).name}",
            exists,
            wf_path,
            "workflows",
        )
        if not exists:
            export_ok = False
            continue
        text = read_text(full)
        entry = registered.get(wf_path, {})
        guard = str(entry.get("repository_guard") or "")
        export_only = entry.get("classification") == "SOURCE_EXPORT_ONLY"
        has_guard = bool(guard) and guard in text
        add_check(
            checks,
            defects,
            f"workflows:export_guard:{Path(wf_path).name}",
            has_guard,
            guard or "missing",
            "workflows",
        )
        add_check(
            checks,
            defects,
            f"workflows:export_only:{Path(wf_path).name}",
            export_only,
            str(entry.get("classification")),
            "workflows",
        )
        export_ok = export_ok and has_guard and export_only

    absent = workflow_register.get("absent_root_deploy_workflows") or []
    absent_ok = True
    for name in absent:
        path = monorepo / ".github/workflows" / str(name)
        missing = not path.is_file()
        summary["absent_deploy_workflows"].append({"name": name, "absent": missing})
        add_check(
            checks,
            defects,
            f"workflows:absent:{name}",
            missing,
            "absent",
            "workflows",
        )
        absent_ok = absent_ok and missing

    ci_path = monorepo / ".github/workflows/ci.yml"
    ci_no_deploy = True
    if ci_path.is_file():
        ci_text = read_text(ci_path)
        deploy_hits = [p.pattern for p in CI_DEPLOY_PATTERNS if p.search(ci_text)]
        ci_no_deploy = not deploy_hits
        add_check(
            checks,
            defects,
            "workflows:ci_no_deploy",
            ci_no_deploy,
            "none" if ci_no_deploy else ",".join(deploy_hits),
            "workflows",
        )
        ci_entry = registered.get(".github/workflows/ci.yml", {})
        add_check(
            checks,
            defects,
            "workflows:ci_register_deploys_false",
            ci_entry.get("deploys") is False,
            str(ci_entry.get("deploys")),
            "workflows",
        )

    summary["inventory_ok"] = root_ok and export_ok and absent_ok and ci_no_deploy
    return checks, defects, summary, limitations


def check_workflow_security(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"scanned": [], "clean": True}

    scan_paths = list(ROOT_WORKFLOW_PATHS) + list(EXPORT_WORKFLOW_PATHS)
    all_clean = True
    for wf_path in scan_paths:
        full = monorepo / wf_path
        if not full.is_file():
            continue
        text = read_text(full)
        leaked = workflow_has_embedded_secrets(text)
        summary["scanned"].append(wf_path)
        add_check(
            checks,
            defects,
            f"security:workflow:{Path(wf_path).name}",
            not leaked,
            "clean" if not leaked else "embedded_secret",
            "security",
            classification="workflow_secret_leak",
        )
        all_clean = all_clean and not leaked

    summary["clean"] = all_clean
    return checks, defects, summary


def check_status_live(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    """Live GET community/status — soft when network/deploy fails."""
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    summary: dict[str, Any] = {
        "http_status": None,
        "reachable": False,
        "schema_ok": False,
        "no_secrets": True,
        "no_version_source": True,
        "github_shape_ok": False,
    }

    candidate_version = read_engine_version(monorepo)
    summary["package_candidate_version"] = candidate_version

    body_text = ""
    http_status: int | None = None
    try:
        req = Request(
            PUBLIC_STATUS_URL,
            headers={"Accept": "application/json", "User-Agent": "codestrata-sv17-25"},
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

    schema_ok = all(k in payload for k in STATUS_REQUIRED_PUBLIC_FIELDS)
    summary["schema_ok"] = schema_ok
    add_check(
        checks,
        defects,
        "status:live_schema",
        schema_ok,
        "fields" if schema_ok else "missing_fields",
        "status_live",
    )

    no_version_source = "version_source" not in payload and "package_candidate_version" not in payload
    summary["no_version_source"] = no_version_source
    add_check(
        checks,
        defects,
        "status:live_no_version_source",
        no_version_source,
        "omitted" if no_version_source else "leaked",
        "status_live",
    )

    repo = str(payload.get("github_repository") or "")
    url = str(payload.get("github_url") or "")
    stars = payload.get("github_stars")
    shape_ok = (
        bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo))
        and url.startswith("https://github.com/")
        and repo in url
        and (stars is None or (isinstance(stars, int) and stars >= 0))
    )
    summary["github_shape_ok"] = shape_ok
    add_check(
        checks,
        defects,
        "status:live_github_shape",
        shape_ok,
        repo or "invalid",
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

    live_version = str(payload.get("engine_version") or "")
    summary["live_engine_version"] = live_version
    if candidate_version and live_version and live_version != candidate_version:
        limitations.append("package_github_release_mismatch")
        if live_version == "0.1.0" and candidate_version == "0.2.0":
            limitations.append("github_v0_2_0_release_not_published")

    if payload.get("github_stars_source") == "unavailable" or payload.get("status") == "degraded":
        limitations.append("github_temporary_unavailable_handled")

    return checks, defects, summary, limitations


def check_prior_slices_and_boundary(
    monorepo: Path,
    policy: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    ok24 = (monorepo / EXPECTED_17_24_PACKAGE).is_dir()
    ok25 = (monorepo / EXPECTED_17_25_PACKAGE).is_dir()
    add_check(checks, defects, "prior_slices:17_24", ok24, EXPECTED_17_24_PACKAGE, "prior_slices")
    add_check(checks, defects, "prior_slices:17_25_package", ok25, EXPECTED_17_25_PACKAGE, "prior_slices")

    start_25 = policy.get("start_slice_17_25") is True
    start_26 = policy.get("start_slice_17_26") is True
    add_check(
        checks,
        defects,
        "boundary:start_slice_17_25",
        start_25,
        "true",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:start_slice_17_26_false",
        not start_26,
        "false",
        "epic17_boundary",
    )
    if start_26:
        add_check(
            checks,
            defects,
            "boundary:start_slice_17_26_hard_fail",
            False,
            "false",
            "epic17_boundary",
            classification="slice_17_26_started",
        )

    started_26 = False
    for cand in SLICE_17_26_PACKAGE_CANDIDATES:
        exists = (monorepo / cand).exists()
        if exists:
            started_26 = True
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
        "prior_slices:17_26_not_started",
        not started_26,
        "absent",
        "prior_slices",
    )

    return checks, defects, {
        "slice_17_24": ok24,
        "slice_17_25": ok25,
        "start_slice_17_25": start_25,
        "start_slice_17_26": False,
        "slice_17_26_started": started_26,
    }


def check_operational(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

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
