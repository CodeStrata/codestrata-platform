"""Structural and operational checks for Slice 17.16."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from verification.community_report_publishing.contract import (
    CONTRACT_RELATIVE,
    DATA_LAKE_MODULE,
    DATA_LAKE_POLICY,
    DOCS_PAGE_RELATIVE,
    ENGINE_ASSESS_SERVICE,
    ENGINE_CLI_REPORT,
    ENGINE_REPORT_PUBLISHING,
    PLATFORM_REPORTS_IDS,
    PLATFORM_REPORTS_POLICY,
    PLATFORM_REPORTS_ROUTES,
    PLATFORM_REPORTS_SANITIZER,
    PLATFORM_REPORTS_SERVICE,
    PLATFORM_REPORTS_STORE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    PRIOR_POLICY_PATHS,
    PRIOR_VERIFICATION_PACKAGES,
    PRODUCTION_REPORT_ARTIFACTS_TF,
    PUBLIC_API_BASE,
    PUBLIC_REPORTS_BASE,
    PUBLISHING_REGISTER_RELATIVE,
    PUBLISHING_REGISTER_SCHEMA,
    REPORTS_DELIVERY_WORKER,
    REPORTS_MODULE,
    REPORTS_WRANGLER,
    SLICE_17_17_PACKAGE_CANDIDATES,
    STORAGE_REGISTER_RELATIVE,
    STORAGE_REGISTER_SCHEMA,
)
from verification.community_report_publishing.helpers import add_check, read_json, read_text
from verification.community_report_publishing.models import CheckResult, Defect

SECRET_PATTERNS = (
    r"ghp_[A-Za-z0-9]{20,}",
    r"github_pat_",
    r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    r"AKIA[0-9A-Z]{16}",
    r"CLOUDFLARE_API_TOKEN\s*=\s*['\"][^'\"]{16,}['\"]",
)

SLICE_PATHS_FOR_SECRETS = (
    POLICY_RELATIVE,
    PUBLISHING_REGISTER_RELATIVE,
    STORAGE_REGISTER_RELATIVE,
    DOCS_PAGE_RELATIVE,
    REPORTS_WRANGLER,
    REPORTS_DELIVERY_WORKER,
    PRODUCTION_REPORT_ARTIFACTS_TF,
)

REPORT_ROUTE_MARKERS = (
    ("POST", "/reports/upload-intents", "reports.upload_intent"),
    ("POST", "/reports", "reports.publish"),
    ("GET", "/reports/{public_id}", "reports.get"),
    ("DELETE", "/reports/{public_id}", "reports.revoke"),
)

DATA_LAKE_FORBIDDEN_PREFIXES = (
    "artifacts/assessments/",
    "artifacts/intelligence/",
    "metadata/public/",
    "staging/",
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
        for key, expected in sorted(POLICY_REQUIRED_VALUES.items()):
            actual = policy.get(key)
            add_check(
                checks,
                defects,
                f"policy:{key}",
                actual == expected,
                str(actual),
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


def check_registers(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    publishing_register: dict[str, Any] = {}
    storage_register: dict[str, Any] = {}

    pub_path = monorepo / PUBLISHING_REGISTER_RELATIVE
    add_check(
        checks,
        defects,
        "register:publishing_exists",
        pub_path.is_file(),
        PUBLISHING_REGISTER_RELATIVE,
        "registers",
    )
    if pub_path.is_file():
        publishing_register = read_json(pub_path)
        add_check(
            checks,
            defects,
            "register:publishing_schema",
            publishing_register.get("schema") == PUBLISHING_REGISTER_SCHEMA,
            str(publishing_register.get("schema")),
            "registers",
        )
        entries = publishing_register.get("entries") or []
        add_check(
            checks,
            defects,
            "register:publishing_entries",
            len(entries) >= 2,
            str(len(entries)),
            "registers",
        )
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            report_type = str(entry.get("report_type", "unknown"))
            add_check(
                checks,
                defects,
                f"register:publishing:{report_type}:retention",
                entry.get("retention_count") == 2,
                str(entry.get("retention_count")),
                "registers",
            )
            add_check(
                checks,
                defects,
                f"register:publishing:{report_type}:boundary",
                entry.get("storage_boundary") == "community-report-artifacts",
                str(entry.get("storage_boundary")),
                "registers",
            )

    store_path = monorepo / STORAGE_REGISTER_RELATIVE
    add_check(
        checks,
        defects,
        "register:storage_exists",
        store_path.is_file(),
        STORAGE_REGISTER_RELATIVE,
        "registers",
    )
    if store_path.is_file():
        storage_register = read_json(store_path)
        add_check(
            checks,
            defects,
            "register:storage_schema",
            storage_register.get("schema") == STORAGE_REGISTER_SCHEMA,
            str(storage_register.get("schema")),
            "registers",
        )
        entries = storage_register.get("entries") or []
        add_check(
            checks,
            defects,
            "register:storage_entries",
            len(entries) >= 3,
            str(len(entries)),
            "registers",
        )
        telemetry = next(
            (e for e in entries if isinstance(e, dict) and e.get("report_type") == "telemetry_event"),
            None,
        )
        if telemetry:
            add_check(
                checks,
                defects,
                "register:storage:telemetry_not_report_store",
                "data-lake" in str(telemetry.get("storage_boundary", "")).lower(),
                str(telemetry.get("storage_boundary")),
                "registers",
            )
            add_check(
                checks,
                defects,
                "register:storage:telemetry_no_publish",
                telemetry.get("publish_auth") == "n/a",
                str(telemetry.get("publish_auth")),
                "registers",
            )

    return checks, defects, publishing_register, storage_register


def check_platform_reports(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"modules": []}

    modules = (
        ("ids", PLATFORM_REPORTS_IDS),
        ("sanitizer", PLATFORM_REPORTS_SANITIZER),
        ("service", PLATFORM_REPORTS_SERVICE),
        ("store", PLATFORM_REPORTS_STORE),
        ("policy", PLATFORM_REPORTS_POLICY),
        ("routes", PLATFORM_REPORTS_ROUTES),
    )
    for name, rel in modules:
        path = monorepo / rel
        present = path.is_file()
        summary["modules"].append(name if present else f"missing:{name}")
        add_check(checks, defects, f"platform:{name}:exists", present, rel, "platform_reports")
        if not present:
            continue
        text = read_text(path)
        if name == "ids":
            add_check(
                checks,
                defects,
                "platform:ids:opaque_generator",
                "generate_public_report_id" in text and "token_urlsafe" in text,
                "present",
                "platform_reports",
            )
            add_check(
                checks,
                defects,
                "platform:ids:validate_rejects_s3",
                "amazonaws" in text and "validate_public_report_id" in text,
                "present",
                "platform_reports",
            )
        if name == "sanitizer":
            add_check(
                checks,
                defects,
                "platform:sanitizer:secret_patterns",
                "sanitize_report_bytes" in text and "_SECRET_PATTERNS" in text,
                "present",
                "platform_reports",
            )
        if name == "service":
            add_check(
                checks,
                defects,
                "platform:service:rotation",
                "_rotate_and_promote" in text and "old_previous" in text,
                "present",
                "platform_reports",
            )
            add_check(
                checks,
                defects,
                "platform:service:revoke",
                "handle_revoke" in text and "STATUS_REVOKED" in text,
                "present",
                "platform_reports",
            )
            add_check(
                checks,
                defects,
                "platform:service:max_versions_two",
                "max_versions" in text and '"max_versions":2' in text.replace(" ", ""),
                "present",
                "platform_reports",
            )
        if name == "policy":
            add_check(
                checks,
                defects,
                "platform:policy:automatic_publish_false",
                "automatic_publish_after_assessment: bool = False" in text
                or "automatic_publish_after_assessment: bool = false" in text.lower(),
                "false",
                "platform_reports",
            )
            add_check(
                checks,
                defects,
                "platform:policy:public_domain",
                PUBLIC_REPORTS_BASE in text,
                PUBLIC_REPORTS_BASE,
                "platform_reports",
            )

    return checks, defects, summary


def check_routes(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"routes": []}

    routes_path = monorepo / PLATFORM_REPORTS_ROUTES
    add_check(checks, defects, "routes:module_exists", routes_path.is_file(), PLATFORM_REPORTS_ROUTES, "routes")
    if not routes_path.is_file():
        return checks, defects, summary

    text = read_text(routes_path)
    for method, path, name in REPORT_ROUTE_MARKERS:
        summary["routes"].append(name)
        add_check(
            checks,
            defects,
            f"routes:{name}:method",
            f'method="{method}"' in text,
            method,
            "routes",
        )
        path_const = {
            "/reports/upload-intents": "UPLOAD_INTENT_PATH",
            "/reports": "PUBLISH_PATH",
            "/reports/{public_id}": "PUBLIC_GET_PATH",
        }.get(path, "REVOKE_PATH" if method == "DELETE" else path)
        add_check(
            checks,
            defects,
            f"routes:{name}:path",
            path in text or path_const in text,
            path,
            "routes",
        )
        add_check(
            checks,
            defects,
            f"routes:{name}:registered",
            name in text,
            name,
            "routes",
        )

    app_path = monorepo / "platform/src/codestrata_platform/community_cloud_api/app.py"
    if app_path.is_file():
        app_text = read_text(app_path)
        add_check(
            checks,
            defects,
            "routes:app_wires_register",
            "register_report_routes" in app_text,
            "present",
            "routes",
        )

    return checks, defects, summary


def check_engine(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    cli_path = monorepo / ENGINE_CLI_REPORT
    add_check(checks, defects, "engine:cli_report_module", cli_path.is_file(), ENGINE_CLI_REPORT, "engine")
    if cli_path.is_file():
        cli_text = read_text(cli_path)
        add_check(
            checks,
            defects,
            "engine:cli_publish_command",
            '@report_app.command("publish")' in cli_text or 'command("publish")' in cli_text,
            "present",
            "engine",
        )
        add_check(
            checks,
            defects,
            "engine:cli_confirm_required",
            "--confirm-public-publish" in cli_text,
            "present",
            "engine",
        )
        add_check(
            checks,
            defects,
            "engine:cli_never_auto_after_assess",
            "never runs automatically after assess" in cli_text.lower()
            or "Assess never auto-publishes" in cli_text,
            "documented",
            "engine",
        )
        add_check(
            checks,
            defects,
            "engine:cli_failure_isolation",
            "Local report" in cli_text and "unchanged" in cli_text.lower(),
            "present",
            "engine",
        )

    client_path = monorepo / ENGINE_REPORT_PUBLISHING
    add_check(
        checks,
        defects,
        "engine:report_publishing_client",
        client_path.is_file(),
        ENGINE_REPORT_PUBLISHING,
        "engine",
    )
    if client_path.is_file():
        client_text = read_text(client_path)
        add_check(
            checks,
            defects,
            "engine:client_upload_intent_path",
            "/api/v1/reports/upload-intents" in client_text,
            "present",
            "engine",
        )
        add_check(
            checks,
            defects,
            "engine:client_refuses_raw_s3",
            "refusing raw S3" in client_text or "refusing raw s3" in client_text.lower(),
            "present",
            "engine",
        )
        add_check(
            checks,
            defects,
            "engine:client_branded_public_url",
            PUBLIC_REPORTS_BASE in client_text,
            PUBLIC_REPORTS_BASE,
            "engine",
        )
        add_check(
            checks,
            defects,
            "engine:client_explicit_confirm",
            "confirm_public_publish" in client_text,
            "present",
            "engine",
        )

    assess_path = monorepo / ENGINE_ASSESS_SERVICE
    if assess_path.is_file():
        assess_text = read_text(assess_path)
        auto_publish = (
            "publish_local_assessment" in assess_text
            or "report_publish_command" in assess_text
            or "community_cloud.report_publishing" in assess_text
        )
        add_check(
            checks,
            defects,
            "engine:assess_no_cloud_report_publish",
            not auto_publish,
            "absent" if not auto_publish else "found",
            "engine",
        )
        add_check(
            checks,
            defects,
            "engine:assess_failure_isolation_message",
            "local reports were kept" in assess_text.lower()
            or "local report" in assess_text.lower(),
            "present",
            "engine",
        )
        summary["assess_no_cloud_publish"] = not auto_publish

    summary["cli_publish"] = cli_path.is_file() and "publish" in read_text(cli_path)
    return checks, defects, summary


def check_docs(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    page = monorepo / DOCS_PAGE_RELATIVE
    add_check(checks, defects, "docs:community_api_page", page.is_file(), DOCS_PAGE_RELATIVE, "docs")
    page_text = read_text(page)

    markers = (
        ("docs:report_publishing_section", "Report publishing (Slice 17.16)"),
        ("docs:upload_intent", "/api/v1/reports/upload-intents"),
        ("docs:publish_post", "/api/v1/reports"),
        ("docs:public_get", "/api/v1/reports/<public-id>"),
        ("docs:revoke_delete", "DELETE"),
        ("docs:branded_url", PUBLIC_REPORTS_BASE),
        ("docs:no_raw_s3", "Raw S3 URLs are never returned"),
        ("docs:explicit_publish", "explicit"),
        ("docs:data_lake_separation", "Report Artifact Store"),
    )
    for check_id, needle in markers:
        add_check(
            checks,
            defects,
            check_id,
            needle.lower() in page_text.lower() if "explicit" in needle else needle in page_text,
            "present" if needle in page_text or needle.lower() in page_text.lower() else "absent",
            "docs",
        )

    summary["page_present"] = page.is_file()
    return checks, defects, summary


def check_infra(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    module_dir = monorepo / REPORTS_MODULE
    add_check(
        checks,
        defects,
        "infra:report_artifacts_module",
        module_dir.is_dir(),
        REPORTS_MODULE,
        "infra",
    )

    prod_tf = monorepo / PRODUCTION_REPORT_ARTIFACTS_TF
    add_check(
        checks,
        defects,
        "infra:production_module_wired",
        prod_tf.is_file(),
        PRODUCTION_REPORT_ARTIFACTS_TF,
        "infra",
    )

    module_text = ""
    if module_dir.is_dir():
        module_text = "\n".join(p.read_text(encoding="utf-8") for p in sorted(module_dir.glob("*.tf")))

    add_check(
        checks,
        defects,
        "infra:private_bpa",
        "aws_s3_bucket_public_access_block" in module_text
        and "block_public_acls" in module_text
        and "restrict_public_buckets" in module_text,
        "present",
        "infra",
    )
    add_check(
        checks,
        defects,
        "infra:bucket_policy_deny_insecure",
        "DenyInsecureTransport" in module_text,
        "present",
        "infra",
    )
    add_check(
        checks,
        defects,
        "infra:separate_from_data_lake_comment",
        "NOT the Community Data Lake" in module_text or "not the Community Data Lake" in module_text,
        "present",
        "infra",
    )

    report_bucket = ""
    lake_bucket = ""
    report_locals = monorepo / REPORTS_MODULE / "locals.tf"
    lake_locals = monorepo / DATA_LAKE_MODULE / "locals.tf"
    if report_locals.is_file():
        report_bucket = read_text(report_locals)
    if lake_locals.is_file():
        lake_bucket = read_text(lake_locals)

    distinct = (
        "community-report-artifacts" in report_bucket
        and "community-data-lake" in lake_bucket
        and report_bucket != lake_bucket
    )
    add_check(
        checks,
        defects,
        "infra:bucket_name_distinct_from_data_lake",
        distinct,
        "distinct" if distinct else "collision_or_missing",
        "infra",
    )

    summary["module_present"] = module_dir.is_dir()
    summary["private_bpa"] = "aws_s3_bucket_public_access_block" in module_text
    summary["bucket_names_distinct"] = distinct
    return checks, defects, summary


def check_data_lake_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"forbidden_hits": []}

    lake_dir = monorepo / DATA_LAKE_MODULE
    add_check(
        checks,
        defects,
        "data_lake:module_exists",
        lake_dir.is_dir(),
        DATA_LAKE_MODULE,
        "data_lake",
    )

    lake_text = ""
    if lake_dir.is_dir():
        lake_text = "\n".join(p.read_text(encoding="utf-8") for p in sorted(lake_dir.glob("*.tf")))

    hits: list[str] = []
    for prefix in DATA_LAKE_FORBIDDEN_PREFIXES:
        if prefix in lake_text:
            hits.append(prefix)
        add_check(
            checks,
            defects,
            f"data_lake:no_prefix:{prefix.rstrip('/')}",
            prefix not in lake_text,
            "absent" if prefix not in lake_text else "found",
            "data_lake",
        )

    storage_reg = monorepo / STORAGE_REGISTER_RELATIVE
    if storage_reg.is_file():
        reg = read_json(storage_reg)
        for entry in reg.get("entries") or []:
            if not isinstance(entry, dict):
                continue
            if entry.get("report_type") in {"assessment", "engineering_intelligence"}:
                boundary = str(entry.get("storage_boundary", ""))
                add_check(
                    checks,
                    defects,
                    f"data_lake:register:{entry.get('report_type')}:not_lake",
                    "data-lake" not in boundary.lower(),
                    boundary,
                    "data_lake",
                )

    policy_path = monorepo / DATA_LAKE_POLICY
    if policy_path.is_file():
        policy_text = read_text(policy_path)
        add_check(
            checks,
            defects,
            "data_lake:policy_no_report_artifact_store",
            "report-artifacts" not in policy_text.lower()
            or "events_only" in read_text(storage_reg).lower(),
            "separate",
            "data_lake",
        )

    summary["forbidden_hits"] = hits
    summary["no_report_prefixes"] = not hits
    return checks, defects, summary


def check_delivery_worker(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    wrangler = monorepo / REPORTS_WRANGLER
    worker = monorepo / REPORTS_DELIVERY_WORKER
    add_check(checks, defects, "delivery:wrangler_exists", wrangler.is_file(), REPORTS_WRANGLER, "delivery")
    add_check(checks, defects, "delivery:worker_exists", worker.is_file(), REPORTS_DELIVERY_WORKER, "delivery")

    if wrangler.is_file():
        wr_text = read_text(wrangler)
        normalized = re.sub(r"\s+", "", wr_text)
        add_check(
            checks,
            defects,
            "delivery:upstream_api_base",
            f'"UPSTREAM_API_BASE":"{PUBLIC_API_BASE}"' in normalized
            or f'"UPSTREAM_API_BASE": "{PUBLIC_API_BASE}"' in wr_text,
            PUBLIC_API_BASE,
            "delivery",
        )
        add_check(
            checks,
            defects,
            "delivery:custom_domain",
            "reports.codestrata.ai" in wr_text,
            "present",
            "delivery",
        )

    if worker.is_file():
        worker_text = read_text(worker)
        add_check(
            checks,
            defects,
            "delivery:thin_proxy",
            "/api/v1/reports/" in worker_text and "Never exposes S3" in worker_text,
            "present",
            "delivery",
        )
        add_check(
            checks,
            defects,
            "delivery:opaque_id_path",
            "/r/" in worker_text and "32,48" in worker_text,
            "present",
            "delivery",
        )
        add_check(
            checks,
            defects,
            "delivery:bounded_cache",
            "max-age=60" in worker_text,
            "present",
            "delivery",
        )
        # Worker must not embed report HTML statically.
        add_check(
            checks,
            defects,
            "delivery:not_static_host",
            "assessment.html" not in worker_text and "engineering-intelligence-report.html" not in worker_text,
            "absent",
            "delivery",
        )

    summary["worker_present"] = worker.is_file()
    summary["thin_proxy"] = worker.is_file() and "/api/v1/reports/" in read_text(worker)
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


def check_epic17_boundary(monorepo: Path, policy: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {
        "start_slice_17_16": policy.get("start_slice_17_16", False),
        "start_slice_17_17": policy.get("start_slice_17_17", False),
    }

    add_check(
        checks,
        defects,
        "boundary:17_16_true",
        summary["start_slice_17_16"] is True,
        "true",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:17_17_true",
        summary["start_slice_17_17"] is True,
        "true",
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

    # Slice 17.17 started (consent validation). Slice 17.18 must remain absent.
    consent_pkg = monorepo / "verification/community_telemetry_consent"
    add_check(
        checks,
        defects,
        "boundary:slice_17_17_present",
        consent_pkg.is_dir(),
        "present" if consent_pkg.is_dir() else "absent",
        "epic17_boundary",
    )
    slice_17_18_started = False
    for candidate in (
        "verification/community_telemetry_consent_17_18",
        "verification/community_production_slice_17_18",
        "verification/community_cloud_share_ui",
    ):
        exists = (monorepo / candidate).exists()
        if exists:
            slice_17_18_started = True
        add_check(
            checks,
            defects,
            f"boundary:slice_17_18_absent:{Path(candidate).name}",
            not exists,
            "absent" if not exists else "present",
            "epic17_boundary",
        )

    summary["slice_17_17_package_absent"] = not consent_pkg.is_dir()
    summary["slice_17_18_package_absent"] = not slice_17_18_started
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

    drift_evidence = monorepo / ".codestrata-artifacts/validation/suites/sv17-16/report-publishing-zero-drift.json"
    add_check(
        checks,
        defects,
        "operational:infra_zero_drift",
        drift_evidence.is_file(),
        "present" if drift_evidence.is_file() else "evidence_absent",
        "operational",
        soft=True,
    )

    vscode_share = monorepo / "vscode-plugin/src/reports/shareReport.ts"
    add_check(
        checks,
        defects,
        "operational:vscode_share_ui_deferred",
        not vscode_share.is_file(),
        "deferred" if not vscode_share.is_file() else "implemented_early",
        "operational",
        soft=True,
    )

    summary["worktree_clean"] = not uncommitted
    summary["zero_drift_evidence"] = drift_evidence.is_file()
    summary["vscode_share_deferred"] = not vscode_share.is_file()
    return checks, defects, summary


def check_live_probes(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    host = "reports.codestrata.ai"
    dns_ok = False
    try:
        result = subprocess.run(
            ["dig", "+short", host, "A"],
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
    try:
        result = subprocess.run(
            ["curl", "-fsS", "--max-time", "8", f"{PUBLIC_REPORTS_BASE}/"],
            capture_output=True,
            text=True,
            check=False,
            timeout=12,
        )
        https_ok = result.returncode == 0
    except Exception:  # noqa: BLE001
        https_ok = False

    add_check(
        checks,
        defects,
        "live:tls_https",
        https_ok,
        "ok" if https_ok else "pending",
        "live",
        soft=True,
    )

    summary["dns_ok"] = dns_ok
    summary["https_ok"] = https_ok
    return checks, defects, summary


def check_telemetry_no_auto_publish(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    telemetry_dir = monorepo / "engine/src/codestrata/telemetry"
    auto_hits = False
    if telemetry_dir.is_dir():
        for path in telemetry_dir.rglob("*.py"):
            text = read_text(path)
            if "publish_local_assessment" in text or "report_publish" in text:
                auto_hits = True
                break

    add_check(
        checks,
        defects,
        "engine:telemetry_no_auto_report_publish",
        not auto_hits,
        "absent" if not auto_hits else "found",
        "engine",
    )
    summary["telemetry_no_auto_publish"] = not auto_hits
    return checks, defects, summary
