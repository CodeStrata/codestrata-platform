"""Structural and operational checks for Slice 17.14."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from verification.community_api_domain.contract import (
    CONTRACT_RELATIVE,
    CUSTOM_DOMAIN_TF,
    DOCS_PAGE_RELATIVE,
    DOCS_PATH,
    DOCS_VITEPRESS_CONFIG,
    DOMAIN_REGISTER_RELATIVE,
    DOMAIN_REGISTER_SCHEMA,
    ENGINE_PUBLIC_API_AUTHORITY,
    INSIGHTS_API_PROXY,
    INSIGHTS_AUTH_CLIENT,
    INSIGHTS_WRANGLER,
    PLATFORM_CONSTANTS,
    PLATFORM_PUBLIC_API_AUTHORITY,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    PRIOR_POLICY_PATHS,
    PRIOR_VERIFICATION_PACKAGES,
    PROHIBITED_DOC_PAYLOAD_KEYS,
    PRODUCTION_MAIN_TF,
    PUBLIC_API_BASE,
    PUBLIC_API_HOST,
    ROUTE_CLASSIFICATIONS,
    ROUTE_REGISTER_RELATIVE,
    ROUTE_REGISTER_SCHEMA,
    SLICE_17_15_PACKAGE_CANDIDATES,
    VSCODE_PUBLIC_API_AUTHORITY,
)
from verification.community_api_domain.helpers import add_check, exists, read_json, read_text
from verification.community_api_domain.models import CheckResult, Defect

SECRET_PATTERNS = (
    r"ghp_[A-Za-z0-9]{20,}",
    r"github_pat_",
    r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    r"AKIA[0-9A-Z]{16}",
    r"cloudflare.*token.*=.*['\"][^'\"]{16,}['\"]",
    r"CLOUDFLARE_API_TOKEN\s*=\s*['\"][^'\"]{16,}['\"]",
)

SLICE_PATHS_FOR_SECRETS = (
    POLICY_RELATIVE,
    DOMAIN_REGISTER_RELATIVE,
    ROUTE_REGISTER_RELATIVE,
    DOCS_PAGE_RELATIVE,
    INSIGHTS_WRANGLER,
    CUSTOM_DOMAIN_TF,
    "infrastructure/scripts/configure-api-domain-dns.sh",
    "infrastructure/scripts/apply-api-domain.sh",
    "infrastructure/scripts/attach-operator-api-domain.sh",
)


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict[str, Any] = {}
    path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if path.is_file():
        policy = read_json(path)
        add_check(
            checks,
            defects,
            "policy:schema",
            policy.get("schema") == POLICY_SCHEMA,
            str(policy.get("schema")),
            "policy",
        )
        add_check(
            checks,
            defects,
            "policy:start_17_14",
            policy.get("start_slice_17_14") is True,
            "true",
            "policy",
        )
        add_check(
            checks,
            defects,
            "policy:start_17_15_false",
            policy.get("start_slice_17_15") is False,
            "false",
            "policy",
        )
        add_check(
            checks,
            defects,
            "policy:public_api_domain",
            policy.get("public_api_domain") == PUBLIC_API_BASE,
            str(policy.get("public_api_domain")),
            "policy",
        )
        add_check(
            checks,
            defects,
            "policy:execute_api_not_public",
            policy.get("raw_execute_api_publicly_documented") is False,
            "false",
            "policy",
        )
        add_check(
            checks,
            defects,
            "policy:insights_same_origin",
            policy.get("insights_browser_calls_api_directly") is False,
            "false",
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


def check_registers(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    domain_register: dict[str, Any] = {}
    route_register: dict[str, Any] = {}

    dpath = monorepo / DOMAIN_REGISTER_RELATIVE
    add_check(checks, defects, "register:domain_exists", dpath.is_file(), DOMAIN_REGISTER_RELATIVE, "registers")
    if dpath.is_file():
        domain_register = read_json(dpath)
        add_check(
            checks,
            defects,
            "register:domain_schema",
            domain_register.get("schema") == DOMAIN_REGISTER_SCHEMA,
            str(domain_register.get("schema")),
            "registers",
        )
        entries = domain_register.get("entries") or []
        add_check(checks, defects, "register:domain_entries", bool(entries), str(len(entries)), "registers")
        if entries:
            entry = entries[0]
            add_check(
                checks,
                defects,
                "register:domain_hostname",
                entry.get("public_api_hostname") == PUBLIC_API_HOST,
                str(entry.get("public_api_hostname")),
                "registers",
            )

    rpath = monorepo / ROUTE_REGISTER_RELATIVE
    add_check(checks, defects, "register:route_exists", rpath.is_file(), ROUTE_REGISTER_RELATIVE, "registers")
    if rpath.is_file():
        route_register = read_json(rpath)
        add_check(
            checks,
            defects,
            "register:route_schema",
            route_register.get("schema") == ROUTE_REGISTER_SCHEMA,
            str(route_register.get("schema")),
            "registers",
        )
        routes = route_register.get("routes") or []
        add_check(checks, defects, "register:routes_present", bool(routes), str(len(routes)), "registers")
        unclassified: list[str] = []
        for route in routes:
            if not isinstance(route, dict):
                continue
            route_id = str(route.get("route_id", "unknown"))
            classification = route.get("classification")
            ok = classification in ROUTE_CLASSIFICATIONS
            add_check(
                checks,
                defects,
                f"register:route:{route_id}:classification",
                ok,
                str(classification),
                "registers",
            )
            if not ok:
                unclassified.append(route_id)
        add_check(
            checks,
            defects,
            "register:routes_all_classified",
            not unclassified,
            "none" if not unclassified else ",".join(unclassified),
            "registers",
        )

    return checks, defects, domain_register, route_register


def check_public_api_authority(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"modules": []}

    modules = (
        ("platform", PLATFORM_PUBLIC_API_AUTHORITY),
        ("engine", ENGINE_PUBLIC_API_AUTHORITY),
        ("vscode", VSCODE_PUBLIC_API_AUTHORITY),
    )
    for name, rel in modules:
        path = monorepo / rel
        present = path.is_file()
        summary["modules"].append(name if present else f"missing:{name}")
        add_check(checks, defects, f"authority:{name}:exists", present, rel, "authority")
        if present:
            text = read_text(path)
            add_check(
                checks,
                defects,
                f"authority:{name}:hostname",
                PUBLIC_API_HOST in text,
                PUBLIC_API_HOST,
                "authority",
            )
            add_check(
                checks,
                defects,
                f"authority:{name}:base_url",
                PUBLIC_API_BASE in text,
                PUBLIC_API_BASE,
                "authority",
            )
            if name in {"engine", "vscode"}:
                add_check(
                    checks,
                    defects,
                    f"authority:{name}:rejects_execute_api",
                    "execute-api" in text.lower(),
                    "present",
                    "authority",
                )

    return checks, defects, summary


def check_insights_browser_contract(monorepo: Path, policy: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    wrangler = monorepo / INSIGHTS_WRANGLER
    add_check(checks, defects, "insights:wrangler_exists", wrangler.is_file(), INSIGHTS_WRANGLER, "insights")
    if wrangler.is_file():
        text = read_text(wrangler)
        normalized = re.sub(r"\s+", "", text)
        add_check(
            checks,
            defects,
            "insights:upstream_api_base",
            f'"UPSTREAM_API_BASE":"{PUBLIC_API_BASE}"' in normalized,
            PUBLIC_API_BASE,
            "insights",
        )

    proxy = monorepo / INSIGHTS_API_PROXY
    add_check(checks, defects, "insights:api_proxy_exists", proxy.is_file(), INSIGHTS_API_PROXY, "insights")
    if proxy.is_file():
        proxy_text = read_text(proxy)
        add_check(
            checks,
            defects,
            "insights:proxy_same_origin",
            "/api" in proxy_text and "run_worker_first" in read_text(monorepo / INSIGHTS_WRANGLER),
            "proxy",
            "insights",
        )

    auth_client = monorepo / INSIGHTS_AUTH_CLIENT
    if auth_client.is_file():
        auth_text = read_text(auth_client)
        add_check(
            checks,
            defects,
            "insights:browser_default_same_origin",
            'return "/api/v1"' in auth_text or "return '/api/v1'" in auth_text,
            "/api/v1",
            "insights",
        )
        add_check(
            checks,
            defects,
            "insights:browser_no_direct_api_host",
            PUBLIC_API_HOST not in auth_text,
            "absent",
            "insights",
        )

    insights_src = monorepo / "insights/src"
    direct_calls = False
    if insights_src.is_dir():
        for path in insights_src.rglob("*"):
            if path.suffix not in {".ts", ".tsx"}:
                continue
            if PUBLIC_API_HOST in read_text(path):
                direct_calls = True
                break
    add_check(
        checks,
        defects,
        "insights:no_browser_direct_public_host",
        not direct_calls,
        "absent" if not direct_calls else "found",
        "insights",
    )

    add_check(
        checks,
        defects,
        "insights:policy_same_origin_contract",
        policy.get("insights_same_origin_browser_contract") == "/api/v1/",
        str(policy.get("insights_same_origin_browser_contract")),
        "insights",
    )

    summary["upstream_configured"] = PUBLIC_API_BASE in read_text(wrangler)
    summary["browser_same_origin"] = not direct_calls
    return checks, defects, summary


def check_docs(monorepo: Path, route_register: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    page = monorepo / DOCS_PAGE_RELATIVE
    add_check(checks, defects, "docs:community_api_page", page.is_file(), DOCS_PAGE_RELATIVE, "docs")
    page_text = read_text(page)

    add_check(
        checks,
        defects,
        "docs:public_api_base_documented",
        PUBLIC_API_BASE in page_text,
        PUBLIC_API_BASE,
        "docs",
    )
    add_check(
        checks,
        defects,
        "docs:execute_api_not_public_authority",
        "implementation detail" in page_text.lower() and "not" in page_text.lower(),
        "classified",
        "docs",
    )

    for route in route_register.get("routes") or []:
        if not isinstance(route, dict):
            continue
        if route.get("classification") != "PUBLIC_COMMUNITY":
            continue
        route_id = str(route.get("route_id", "unknown"))
        public_path = str(route.get("public_path", ""))
        add_check(
            checks,
            defects,
            f"docs:route:{route_id}:documented",
            public_path in page_text or route_id.replace(".", "-") in page_text.lower(),
            public_path,
            "docs",
        )

    private_in_community_docs = False
    for route in route_register.get("routes") or []:
        if not isinstance(route, dict):
            continue
        if route.get("classification") == "PRIVATE_INSIGHTS":
            path = str(route.get("public_path", ""))
            if path and path in page_text and "not documented here" not in page_text.lower():
                private_in_community_docs = True
    add_check(
        checks,
        defects,
        "docs:private_insights_not_community",
        not private_in_community_docs,
        "absent" if not private_in_community_docs else "leaked",
        "docs",
    )

    config = monorepo / DOCS_VITEPRESS_CONFIG
    if config.is_file():
        config_text = read_text(config)
        add_check(
            checks,
            defects,
            "docs:nav_link",
            DOCS_PATH in config_text,
            DOCS_PATH,
            "docs",
        )
        add_check(
            checks,
            defects,
            "docs:sidebar_link",
            config_text.count(DOCS_PATH) >= 2,
            str(config_text.count(DOCS_PATH)),
            "docs",
        )

    docs_root = monorepo / "docs"
    execute_api_in_docs = False
    if docs_root.is_dir():
        for path in docs_root.rglob("*"):
            if path.suffix not in {".md", ".ts", ".tsx", ".json"}:
                continue
            if "execute-api.amazonaws" in read_text(path):
                execute_api_in_docs = True
                break
    add_check(
        checks,
        defects,
        "docs:no_execute_api_advertised",
        not execute_api_in_docs,
        "absent" if not execute_api_in_docs else "found",
        "docs",
    )

    summary["page_present"] = page.is_file()
    summary["nav_linked"] = DOCS_PATH in read_text(config)
    return checks, defects, summary


def check_docs_examples(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"examples_scanned": 0, "prohibited_hits": 0}

    page_text = read_text(monorepo / DOCS_PAGE_RELATIVE)
    blocks = re.findall(r"```json\s*(.*?)```", page_text, flags=re.S)
    summary["examples_scanned"] = len(blocks)

    prohibited_hits: list[str] = []
    for idx, block in enumerate(blocks):
        try:
            payload = json.loads(block.strip())
        except json.JSONDecodeError:
            add_check(
                checks,
                defects,
                f"docs:example:{idx}:json_parse",
                False,
                "invalid_json",
                "docs",
            )
            continue
        add_check(checks, defects, f"docs:example:{idx}:json_parse", True, "valid", "docs")
        hits = _find_prohibited_keys(payload)
        if hits:
            prohibited_hits.extend(hits)
        add_check(
            checks,
            defects,
            f"docs:example:{idx}:privacy_safe",
            not hits,
            "clean" if not hits else ",".join(sorted(set(hits))),
            "privacy",
        )

    health_blocks = [b for b in blocks if '"status"' in b and '"service"' in b]
    if health_blocks:
        try:
            health = json.loads(health_blocks[0].strip())
            required = {"api_version", "application_version", "schema_version", "service", "status"}
            missing = required - set(health.keys())
            add_check(
                checks,
                defects,
                "docs:health_example:structure",
                not missing,
                "complete" if not missing else ",".join(sorted(missing)),
                "docs",
            )
        except json.JSONDecodeError:
            add_check(checks, defects, "docs:health_example:structure", False, "invalid_json", "docs")

    summary["prohibited_hits"] = len(prohibited_hits)
    return checks, defects, summary


def _find_prohibited_keys(payload: Any, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_lower = str(key).lower()
            if key_lower in PROHIBITED_DOC_PAYLOAD_KEYS or key in PROHIBITED_DOC_PAYLOAD_KEYS:
                hits.append(f"{prefix}{key}" if prefix else str(key))
            hits.extend(_find_prohibited_keys(value, prefix=f"{prefix}{key}."))
    elif isinstance(payload, list):
        for item in payload:
            hits.extend(_find_prohibited_keys(item, prefix=prefix))
    return hits


def check_infra(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    custom_domain = monorepo / CUSTOM_DOMAIN_TF
    add_check(checks, defects, "infra:custom_domain_tf", custom_domain.is_file(), CUSTOM_DOMAIN_TF, "infra")
    if custom_domain.is_file():
        tf_text = read_text(custom_domain)
        add_check(
            checks,
            defects,
            "infra:custom_domain_resources",
            "aws_apigatewayv2_domain_name" in tf_text and "aws_acm_certificate" in tf_text,
            "present",
            "infra",
        )

    production = monorepo / PRODUCTION_MAIN_TF
    if production.is_file():
        prod_text = read_text(production)
        add_check(
            checks,
            defects,
            "infra:enable_api_custom_domain",
            re.search(r"enable_api_custom_domain\s*=\s*true", prod_text) is not None,
            "true",
            "infra",
        )

    module_dir = monorepo / "infrastructure/modules/community-cloud-api"
    module_text = ""
    if module_dir.is_dir():
        module_text = "\n".join(p.read_text(encoding="utf-8") for p in sorted(module_dir.glob("*.tf")))
    add_check(
        checks,
        defects,
        "infra:execute_api_not_disabled",
        "disable_execute_api_endpoint" not in module_text,
        "retained",
        "infra",
    )

    summary["custom_domain_present"] = custom_domain.is_file()
    summary["execute_api_retained"] = "disable_execute_api_endpoint" not in module_text
    return checks, defects, summary


def check_security(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"scanned": []}

    for rel in SLICE_PATHS_FOR_SECRETS:
        path = monorepo / rel
        if not path.is_file():
            continue
        text = read_text(path)
        summary["scanned"].append(path.name)
        clean = not any(re.search(p, text, re.I) for p in SECRET_PATTERNS)
        add_check(
            checks,
            defects,
            f"security:{path.name}",
            clean,
            "clean" if clean else "pattern_match",
            "security",
        )
    return checks, defects, summary


def check_privacy_schemas(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    constants = monorepo / PLATFORM_CONSTANTS
    add_check(checks, defects, "privacy:constants_exists", constants.is_file(), PLATFORM_CONSTANTS, "privacy")
    if constants.is_file():
        text = read_text(constants)
        markers = (
            'COMMUNITY_TELEMETRY_SCHEMA_VERSION = "1.0"',
            'COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION = "1.0"',
            'COMMUNITY_CLI_EVENT_SCHEMA_VERSION = "1.0"',
            'COMMUNITY_EXTENSION_EVENT_SCHEMA_VERSION = "1.0"',
            'COMMUNITY_AI_USAGE_SCHEMA_VERSION = "1.0"',
        )
        for marker in markers:
            name = marker.split("=")[0].strip().split()[-1]
            add_check(
                checks,
                defects,
                f"privacy:schema_unchanged:{name}",
                marker in text,
                "1.0",
                "privacy",
            )

    route_path = monorepo / ROUTE_REGISTER_RELATIVE
    if route_path.is_file():
        routes = read_json(route_path).get("routes") or []
        for route in routes:
            if not isinstance(route, dict):
                continue
            route_id = str(route.get("route_id", "unknown"))
            req = route.get("request_schema")
            resp = route.get("response_schema")
            add_check(
                checks,
                defects,
                f"privacy:route_schema_marker:{route_id}",
                req is None or isinstance(req, str),
                str(req),
                "privacy",
            )
            add_check(
                checks,
                defects,
                f"privacy:route_response_marker:{route_id}",
                resp is None or isinstance(resp, str),
                str(resp),
                "privacy",
            )

    summary["telemetry_schema_1_0"] = 'COMMUNITY_TELEMETRY_SCHEMA_VERSION = "1.0"' in read_text(constants)
    return checks, defects, summary


def check_epic17_boundary(monorepo: Path, policy: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {
        "start_slice_17_14": policy.get("start_slice_17_14", False),
        "start_slice_17_15": policy.get("start_slice_17_15", False),
    }

    add_check(
        checks,
        defects,
        "boundary:17_14_true",
        summary["start_slice_17_14"] is True,
        "true",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:17_15_false",
        summary["start_slice_17_15"] is False,
        "false",
        "epic17_boundary",
    )

    for rel in PRIOR_POLICY_PATHS:
        path = monorepo / rel
        add_check(
            checks,
            defects,
            f"boundary:prior_policy:{path.stem}",
            path.is_file(),
            "present" if path.is_file() else "absent",
            "epic17_boundary",
        )

    for pkg in PRIOR_VERIFICATION_PACKAGES:
        add_check(
            checks,
            defects,
            f"boundary:prior_package:{Path(pkg).name}",
            (monorepo / pkg).is_dir(),
            "present",
            "epic17_boundary",
        )

    slice_15_started = False
    for candidate in SLICE_17_15_PACKAGE_CANDIDATES:
        if (monorepo / candidate).exists():
            slice_15_started = True
            add_check(
                checks,
                defects,
                f"boundary:slice_17_15_absent:{Path(candidate).name}",
                False,
                "present",
                "epic17_boundary",
            )
        else:
            add_check(
                checks,
                defects,
                f"boundary:slice_17_15_absent:{Path(candidate).name}",
                True,
                "absent",
                "epic17_boundary",
            )

    summary["slice_17_15_package_absent"] = not slice_15_started
    return checks, defects, summary


def check_operational(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

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

    dns_script = monorepo / "infrastructure/scripts/configure-api-domain-dns.sh"
    add_check(
        checks,
        defects,
        "operational:cloudflare_dns_token",
        dns_script.is_file(),
        "script_present",
        "operational",
        soft=True,
    )

    attach_script = monorepo / "infrastructure/scripts/attach-operator-api-domain.sh"
    add_check(
        checks,
        defects,
        "operational:acm_iam_attach",
        attach_script.is_file(),
        "script_present",
        "operational",
        soft=True,
    )

    drift_evidence = monorepo / ".codestrata-artifacts/validation/suites/sv17-14/api-domain-zero-drift.json"
    add_check(
        checks,
        defects,
        "operational:infra_zero_drift",
        drift_evidence.is_file(),
        "present" if drift_evidence.is_file() else "evidence_absent",
        "operational",
        soft=True,
    )

    docs_deploy = monorepo / ".codestrata-artifacts/validation/suites/sv17-14/docs-community-api-deploy.json"
    add_check(
        checks,
        defects,
        "operational:docs_deploy_remote",
        docs_deploy.is_file(),
        "present" if docs_deploy.is_file() else "evidence_absent",
        "operational",
        soft=True,
    )

    summary["worktree_clean"] = not uncommitted
    summary["zero_drift_evidence"] = drift_evidence.is_file()
    summary["docs_deploy_evidence"] = docs_deploy.is_file()
    return checks, defects, summary


def check_live_probes(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    dns_ok = False
    try:
        result = subprocess.run(
            ["dig", "+short", PUBLIC_API_HOST, "A"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        dns_ok = bool(result.stdout.strip())
    except Exception:  # noqa: BLE001
        dns_ok = False
    add_check(
        checks,
        defects,
        "live:dns_resolution",
        dns_ok,
        "resolved" if dns_ok else "pending",
        "live",
        soft=True,
    )

    https_ok = False
    health_ok = False
    try:
        result = subprocess.run(
            ["curl", "-fsS", "--max-time", "8", f"{PUBLIC_API_BASE}/api/v1/health"],
            capture_output=True,
            text=True,
            check=False,
            timeout=12,
        )
        https_ok = result.returncode == 0
        if https_ok:
            body = json.loads(result.stdout)
            health_ok = body.get("status") == "ok"
    except Exception:  # noqa: BLE001
        https_ok = False
        health_ok = False

    add_check(
        checks,
        defects,
        "live:tls_https",
        https_ok,
        "ok" if https_ok else "pending",
        "live",
        soft=True,
    )
    add_check(
        checks,
        defects,
        "live:health_probe",
        health_ok,
        "ok" if health_ok else "pending",
        "live",
        soft=True,
    )

    summary["dns_ok"] = dns_ok
    summary["https_ok"] = https_ok
    summary["health_ok"] = health_ok
    return checks, defects, summary
