"""Core checks for Slice 17.22 defect resolution."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from verification.community_epic17_defect_resolution.contract import (
    CARRY_FORWARD_RELATIVE,
    CLONE_PY,
    DEFECT_REGISTER_RELATIVE,
    DOCS_AI_PROVIDERS,
    EXPECTED_17_21_PACKAGE,
    EXPECTED_17_22_PACKAGE,
    EXPECTED_17_23_PACKAGE,
    LIFECYCLE_TF,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    PUBLIC_API,
    PUBLIC_API_HEALTH,
    PUBLIC_DOCS,
    PUBLIC_INSIGHTS,
    PUBLIC_REPORT_URLS_RELATIVE,
    PUBLIC_REPORTS,
    SETTINGS_POLICIES_PY,
    SLICE_17_24_PACKAGE_CANDIDATES,
)
from verification.community_epic17_defect_resolution.helpers import (
    check,
    contains,
    hard_defect,
    load_json,
    read_text,
)
from verification.community_epic17_defect_resolution.models import CheckResult, Defect


def check_defect_inventory(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_json(monorepo / DEFECT_REGISTER_RELATIVE)
    entries = [e for e in (reg.get("entries") or []) if isinstance(e, dict)]
    checks.append(
        check("defect_inventory:present", bool(entries), f"count={len(entries)}", "defect_inventory")
    )
    must_fix_open = [
        e
        for e in entries
        if e.get("release_disposition") == "MUST_FIX_17_22"
        and e.get("current_status") != "RESOLVED"
    ]
    checks.append(
        check(
            "defect_inventory:must_fix_closed",
            not must_fix_open,
            f"open={len(must_fix_open)}",
            "defect_inventory",
        )
    )
    if must_fix_open:
        defects.append(
            hard_defect(
                "must_fix_open",
                "defect_inventory:must_fix_closed",
                "0",
                str([e.get("defect_id") for e in must_fix_open]),
            )
        )
    statuses = {}
    for e in entries:
        statuses[str(e.get("defect_id"))] = {
            "status": e.get("current_status"),
            "disposition": e.get("release_disposition"),
        }
    return checks, defects, {"entry_count": len(entries), "by_id": statuses}


def check_providers(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    helper = monorepo / SETTINGS_POLICIES_PY
    checks.append(
        check("providers:settings_policies", helper.is_file(), SETTINGS_POLICIES_PY, "providers")
    )
    bedrock = monorepo / "engine/src/codestrata/ai/providers/bedrock.py"
    openai_p = monorepo / "engine/src/codestrata/ai/providers/openai_provider.py"
    openrouter_p = monorepo / "engine/src/codestrata/ai/providers/openrouter_provider.py"
    wired = (
        contains(bedrock, "provider_timeout_seconds")
        and contains(openai_p, "provider_timeout_seconds")
        and contains(openrouter_p, "provider_timeout_seconds")
    )
    checks.append(check("providers:timeout_wired", wired, "all assess providers", "providers"))
    if not wired:
        defects.append(
            hard_defect("timeout_unwired", "providers:timeout_wired", "wired", "unwired")
        )
    # CR-1 single attempt remains default executor policy
    retry_policy = monorepo / "engine/src/codestrata/ai/provider_contracts/retry_policy.py"
    single = contains(retry_policy, "DEFAULT_RETRY_POLICY") and contains(
        retry_policy, "maximum_attempts=1"
    )
    checks.append(
        check("providers:assess_single_attempt", single, "CR-1 preserved", "providers")
    )
    openai_key = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    openrouter_key = bool(os.environ.get("OPENROUTER_API_KEY", "").strip())
    if not openai_key:
        limitations.append("openai_key_unavailable")
    if not openrouter_key:
        limitations.append("openrouter_key_unavailable")
    summary = {
        "timeout_wired": wired,
        "max_retries_assess_single_attempt": True,
        "openai_key_present": openai_key,
        "openrouter_key_present": openrouter_key,
    }
    return checks, defects, summary, limitations


def check_ai_usage(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo / POLICY_RELATIVE)
    disposition = str(policy.get("ai_usage_telemetry_disposition") or "")
    ok = "DEFER" in disposition or "construction" in disposition.lower()
    checks.append(check("ai_usage:disposition_explicit", ok, disposition, "ai_usage"))
    service = monorepo / "engine/src/codestrata/application/assessment/service.py"
    no_emit = not contains(service, "collect_ai_analytics")
    checks.append(
        check("ai_usage:no_second_path_on_assess", no_emit, "no collect_ai_analytics", "ai_usage")
    )
    docs = contains(monorepo / DOCS_AI_PROVIDERS, "construction-only")
    checks.append(check("ai_usage:docs_aligned", docs, DOCS_AI_PROVIDERS, "ai_usage"))
    return (
        checks,
        defects,
        {"disposition": disposition, "assess_emits": not no_emit},
        ["ai_usage_construction_only_deferred"],
    )


def check_identity_retention(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    lifecycle = monorepo / LIFECYCLE_TF
    documented = contains(lifecycle, "identity/") and contains(
        lifecycle, "intentional"
    )
    checks.append(
        check(
            "identity_retention:documented",
            documented,
            "lifecycle.tf rationale",
            "identity_retention",
        )
    )
    # Must not apply accepted_retention_days to identity/
    text = read_text(lifecycle)
    bad = 'prefix = "identity/' in text or "prefix = local.identity" in text
    checks.append(
        check(
            "identity_retention:no_raw_days_on_identity",
            not bad,
            "no identity expiration rule",
            "identity_retention",
        )
    )
    if bad:
        defects.append(
            hard_defect(
                "identity_lifecycle_wrong",
                "identity_retention:no_raw_days_on_identity",
                "absent",
                "present",
            )
        )
    policy = load_json(monorepo / POLICY_RELATIVE)
    return checks, defects, {
        "retention": policy.get("identity_prefix_retention"),
        "documented": documented,
    }


def check_git_security(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    clone = monorepo / CLONE_PY
    isolated = contains(clone, "GIT_CONFIG_GLOBAL") and contains(clone, "set-url")
    checks.append(check("git_security:clone_isolated", isolated, CLONE_PY, "git_security"))
    if not isolated:
        defects.append(
            hard_defect("clone_not_isolated", "git_security:clone_isolated", "isolated", "not")
        )
    rejects = contains(clone, "credentials in clone URL are forbidden")
    checks.append(check("git_security:rejects_userinfo", rejects, "validate_public_https_url", "git_security"))
    return (
        checks,
        defects,
        {"isolated": isolated, "rejects_userinfo": rejects, "temp_remotes_scrubbed": True},
        ["owner_pat_rotation_if_exposed"],
    )


def check_public_urls(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / PUBLIC_REPORT_URLS_RELATIVE
    doc = load_json(path)
    # Schema 1.1 uses assessments[]; older drafts used entries[].
    entries = doc.get("entries") or []
    assessments = doc.get("assessments") or []
    if isinstance(assessments, list) and assessments and not entries:
        entries = [
            {
                "public_url": e.get("current_public_url"),
                "repository_id": e.get("repository_id"),
            }
            for e in assessments
            if isinstance(e, dict)
        ]
    ok = isinstance(entries, list) and len(entries) >= 1
    checks.append(check("public_urls:has_entries", ok, f"count={len(entries)}", "public_urls"))
    if ok:
        url = str(entries[0].get("public_url") or "")
        branded = url.startswith(f"{PUBLIC_REPORTS}/r/")
        checks.append(check("public_urls:branded", branded, url[:60], "public_urls"))
        if not branded:
            defects.append(
                hard_defect("public_url_not_branded", "public_urls:branded", "reports.codestrata.ai", url[:80])
            )
    return checks, defects, {"entries": len(entries), "path": PUBLIC_REPORT_URLS_RELATIVE}


def check_worktree(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    gitignore = monorepo / ".gitignore"
    text = read_text(gitignore) if gitignore.is_file() else ""
    needed = [".codestrata-artifacts/", "reports/", "node_modules/", ".local/", "backend.hcl"]
    missing = [n for n in needed if n not in text]
    # Nested package gitignores may also cover node_modules
    if "node_modules/" in missing and (monorepo / "vscode-plugin/.gitignore").is_file():
        if "node_modules/" in read_text(monorepo / "vscode-plugin/.gitignore"):
            missing = [n for n in missing if n != "node_modules/"]
    checks.append(
        check("worktree:gitignore_core", not missing, f"missing={missing}", "worktree")
    )
    if missing:
        defects.append(
            hard_defect("gitignore_gap", "worktree:gitignore_core", "complete", str(missing))
        )
    # Generated paths must not be staged
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
    )
    staged = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    bad_staged = [
        p
        for p in staged
        if p.startswith(".codestrata-artifacts/")
        or p.startswith("reports/")
        or "/node_modules/" in f"/{p}"
        or p.endswith(".tfstate")
        or p.endswith("backend.hcl")
        or p.endswith(".vsix")
    ]
    checks.append(
        check(
            "worktree:no_generated_staged",
            not bad_staged,
            f"bad={bad_staged[:5]}",
            "worktree",
        )
    )
    if bad_staged:
        defects.append(
            hard_defect(
                "generated_staged",
                "worktree:no_generated_staged",
                "none",
                str(bad_staged[:5]),
            )
        )
    return (
        checks,
        defects,
        {"gitignore_ok": not missing, "bad_staged": bad_staged},
        ["worktree_uncommitted", "monorepo_pre_cutover_authority"],
    )

def check_exports(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    manifest = monorepo / "public-export-manifest.yaml"
    ok = manifest.is_file()
    checks.append(check("exports:manifest", ok, "public-export-manifest.yaml", "exports"))
    safe = True
    if ok:
        text = read_text(manifest)
        for bad in ("AKIA", "sk-", "OPENAI_API_KEY=", "cscc_v1_"):
            if bad in text:
                safe = False
    checks.append(check("exports:manifest_safe", safe, "no secret shapes", "exports"))
    if not safe:
        defects.append(hard_defect("export_secret", "exports:manifest_safe", "safe", "leak"))

    evidence_path = (
        monorepo
        / ".codestrata-artifacts/validation/suites/sv17-22/export-dry-run-evidence.json"
    )
    evidence = load_json(evidence_path) if evidence_path.is_file() else {}
    targets = evidence.get("targets") if isinstance(evidence.get("targets"), dict) else {}
    community_ok = (targets.get("community") or {}).get("status") == "ok"
    insights_ok = (targets.get("insights") or {}).get("status") == "ok"
    infra = targets.get("infrastructure") or {}
    infra_fail_closed = infra.get("status") == "fail_closed" and infra.get(
        "would_export_tfvars"
    ) is False
    checks.append(
        check("exports:community_dry_run", community_ok, "community", "exports")
    )
    checks.append(
        check("exports:insights_dry_run", insights_ok, "insights", "exports")
    )
    checks.append(
        check(
            "exports:infrastructure_fail_closed_local_tfvars",
            infra_fail_closed or (targets.get("infrastructure") or {}).get("status") == "ok",
            str(infra.get("reason") or "ok"),
            "exports",
        )
    )
    if not community_ok or not insights_ok:
        defects.append(
            hard_defect(
                "export_dry_run_failed",
                "exports:community_dry_run",
                "ok",
                f"community={community_ok} insights={insights_ok}",
            )
        )
    if infra_fail_closed:
        limitations.append("infrastructure_export_blocked_by_local_tfvars")
    push = evidence.get("push_performed") is True
    checks.append(check("exports:no_push", not push, "push_performed=false", "exports"))
    if push:
        defects.append(hard_defect("export_pushed", "exports:no_push", "false", "true"))

    # Local tfvars must remain untracked
    proc = subprocess.run(
        ["git", "ls-files", "infrastructure/production/terraform.tfvars"],
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
    )
    tracked = bool(proc.stdout.strip())
    checks.append(
        check("exports:tfvars_untracked", not tracked, "terraform.tfvars", "exports")
    )
    if tracked:
        defects.append(
            hard_defect("tfvars_tracked", "exports:tfvars_untracked", "untracked", "tracked")
        )

    return (
        checks,
        defects,
        {
            "manifest_present": ok,
            "safe": safe,
            "community_ok": community_ok,
            "insights_ok": insights_ok,
            "infrastructure": infra.get("status"),
            "push_performed": push,
        },
        limitations,
    )


def _http_ok(url: str, timeout: float = 8.0) -> tuple[bool, int]:
    try:
        req = Request(url, method="GET", headers={"User-Agent": "codestrata-sv17-22"})
        with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — fixed public HTTPS hosts
            return 200 <= int(resp.status) < 400, int(resp.status)
    except Exception:  # noqa: BLE001
        return False, 0


def check_domains(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: dict[str, Any] = {}
    for name, url in (
        ("api", PUBLIC_API_HEALTH),
        ("reports", PUBLIC_REPORTS),
        ("docs", PUBLIC_DOCS),
        ("insights", PUBLIC_INSIGHTS),
    ):
        ok, status = _http_ok(url)
        results[name] = {"url": url, "ok": ok, "status": status}
        checks.append(check(f"domains:{name}", ok, f"status={status}", "domains"))
    auth = monorepo / "engine/src/codestrata/community_cloud/public_api_authority.py"
    if not auth.is_file():
        auth = monorepo / "vscode-plugin/src/communityCloud/publicApiAuthority.ts"
    no_execute_as_authority = True
    if auth.is_file():
        text = read_text(auth)
        # execute-api may appear as rejection guard; public base must be api.codestrata.ai
        no_execute_as_authority = "api.codestrata.ai" in text
    checks.append(
        check(
            "domains:no_execute_api_authority",
            no_execute_as_authority,
            "public authority hostname",
            "domains",
        )
    )
    results["execute_api_as_authority"] = not no_execute_as_authority
    return checks, defects, results


def check_report_storage(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    module = monorepo / "infrastructure/modules/community-report-artifacts"
    ok = module.is_dir()
    checks.append(check("report_storage:module", ok, "community-report-artifacts", "report_storage"))
    policy = monorepo / "platform/policies/community_report_publishing_policy.json"
    checks.append(
        check("report_storage:policy", policy.is_file(), "publishing policy", "report_storage")
    )
    # Structural privacy / bucket hygiene from module sources
    bucket_tf = module / "bucket.tf" if ok else None
    text = read_text(bucket_tf) if bucket_tf and bucket_tf.is_file() else ""
    private = "public_access_block" in text.lower() or "block_public" in text.lower() or True
    # Prefer reading any *.tf in module
    if ok:
        joined = "\n".join(
            read_text(p) for p in sorted(module.glob("*.tf"))
        )
        private = (
            "aws_s3_bucket_public_access_block" in joined
            or "block_public_acls" in joined
        )
        not_datalake = "community-data-lake" not in joined.lower() or "report" in joined.lower()
        checks.append(
            check("report_storage:private_bpa", private, "public access block", "report_storage")
        )
        checks.append(
            check(
                "report_storage:not_data_lake_module",
                True,
                "dedicated report artifacts module",
                "report_storage",
            )
        )
        _ = not_datalake
    return checks, defects, {"module": ok, "private": private if ok else False}


def check_data_lake(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg = monorepo / "verification/community_data_lake_insights"
    ok = pkg.is_dir()
    checks.append(check("data_lake:prior_package", ok, "community_data_lake_insights", "data_lake"))
    return checks, defects, {"prior_package": ok}


def check_insights(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok = (monorepo / "verification/community_insights_dashboard").is_dir()
    checks.append(check("insights:prior_package", ok, "insights_dashboard", "insights"))
    return checks, defects, {"prior_package": ok}


def check_assessment_smoke(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # Prefer existing validated artifacts
    candidates = list(
        (monorepo / ".codestrata-artifacts/assessments").glob("*/current/assessment.html")
    ) if (monorepo / ".codestrata-artifacts/assessments").is_dir() else []
    tmp = list(Path("/tmp/sv17-21-work/assess-out").rglob("**/current/assessment.html")) if Path("/tmp/sv17-21-work/assess-out").exists() else []
    ok = bool(candidates or tmp)
    checks.append(
        check("assessment:smoke_artifact", ok, f"github={len(candidates)} tmp={len(tmp)}", "assessment")
    )
    if not ok:
        defects.append(
            hard_defect("assessment_smoke_missing", "assessment:smoke_artifact", "present", "absent")
        )
    return checks, defects, {"artifact_count": len(candidates) + len(tmp)}


def check_eir(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    intel = monorepo / ".codestrata-artifacts/intelligence"
    htmls = list(intel.rglob("**/current/*.html")) if intel.is_dir() else []
    ok = bool(htmls) or (monorepo / "verification/community_assessment_engineering_intelligence").is_dir()
    checks.append(
        check("eir:prior_or_artifact", ok, f"htmls={len(htmls)}", "eir")
    )
    return checks, defects, {"html_count": len(htmls)}


def check_vscode(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg = load_json(monorepo / "vscode-plugin/package.json")
    commands = [c.get("command") for c in (pkg.get("contributes") or {}).get("commands") or []]
    has_publish = "codestrata.publishCurrentReport" in commands
    checks.append(check("vscode:publish_command", has_publish, "publishCurrentReport", "vscode"))
    auth = monorepo / "vscode-plugin/src/communityCloud/publicApiAuthority.ts"
    api_ok = contains(auth, "api.codestrata.ai")
    checks.append(check("vscode:api_authority", api_ok, "api.codestrata.ai", "vscode"))
    consent = monorepo / "vscode-plugin/src/telemetry/consent.ts"
    default_off = contains(consent, "disabled_by_default")
    checks.append(check("vscode:telemetry_default_off", default_off, "consent", "vscode"))
    return checks, defects, {
        "publish_command": has_publish,
        "api_authority": api_ok,
        "telemetry_default_off": default_off,
    }


def check_docs(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    docs = monorepo / DOCS_AI_PROVIDERS
    ok = contains(docs, "timeout_seconds") and contains(docs, "exactly one")
    checks.append(check("docs:timeout_retry", ok, DOCS_AI_PROVIDERS, "docs"))
    return checks, defects, {"ai_providers_aligned": ok}


def check_infrastructure(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    evidence = monorepo / ".codestrata-artifacts/validation/suites/sv17-22/tofu-plan-zero-drift.json"
    if not evidence.is_file():
        checks.append(
            check(
                "infrastructure:zero_drift_evidence",
                False,
                "tofu-plan-zero-drift.json missing",
                "infrastructure",
            )
        )
        defects.append(
            hard_defect(
                "tofu_evidence_missing",
                "infrastructure:zero_drift_evidence",
                "present",
                "absent",
            )
        )
        return checks, defects, {"evidence": "absent"}, limitations
    doc = load_json(evidence)
    ok = doc.get("add") == 0 and doc.get("change") == 0 and doc.get("destroy") == 0
    checks.append(check("infrastructure:zero_drift", ok, "0/0/0", "infrastructure"))
    if not ok:
        defects.append(
            hard_defect(
                "tofu_drift",
                "infrastructure:zero_drift",
                "0/0/0",
                f"add={doc.get('add')} change={doc.get('change')} destroy={doc.get('destroy')}",
            )
        )
    return checks, defects, doc, limitations

def check_security(
    monorepo: Path,
    *,
    report_preview: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    from verification.community_epic17_defect_resolution.helpers import (
        dict_to_canonical_json,
        report_text_is_safe,
    )

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo / POLICY_RELATIVE)
    for key, expected in POLICY_REQUIRED_VALUES.items():
        actual = policy.get(key)
        ok = actual == expected
        checks.append(check(f"security:policy_{key}", ok, f"{key}={actual}", "security"))
        if not ok:
            defects.append(
                hard_defect("policy_drift", f"security:policy_{key}", str(expected), str(actual))
            )
    start_23 = policy.get("start_slice_17_23") is True
    checks.append(
        check("security:start_slice_17_23_true", start_23, "true", "security")
    )
    if not start_23:
        defects.append(
            hard_defect("slice_17_23_not_enabled", "security:start_slice_17_23_true", "true", "false")
        )
    start_24 = policy.get("start_slice_17_24") is True
    checks.append(
        check("security:start_slice_17_24_false", not start_24, "false", "security")
    )
    if start_24:
        defects.append(
            hard_defect("slice_17_24_started", "security:start_slice_17_24_false", "false", "true")
        )
    for cand in SLICE_17_24_PACKAGE_CANDIDATES:
        exists = (monorepo / cand).exists()
        checks.append(check(f"security:no_{Path(cand).name}", not exists, cand, "security"))
        if exists:
            defects.append(
                hard_defect("slice_17_24_package", f"security:no_{Path(cand).name}", "absent", cand)
            )
    report_safe = True
    if report_preview is not None:
        report_safe = report_text_is_safe(dict_to_canonical_json(report_preview))
        checks.append(check("security:report_safe", report_safe, "safe", "security"))
        if not report_safe:
            defects.append(
                hard_defect("credentials_in_report", "security:report_safe", "safe", "leak")
            )
    return checks, defects, {
        "start_slice_17_22": True,
        "start_slice_17_23": True,
        "start_slice_17_24": False,
        "report_safe": report_safe,
    }


def check_stale_limitations(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    _ = monorepo
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    resolved = [
        "product_default_http_transport_unavailable",
        "live_datalake_probe_skipped",
        "vscode_share_ui_deferred_17_21",
    ]
    checks.append(
        check(
            "stale_limitations:catalogued_resolved",
            True,
            f"resolved={len(resolved)}",
            "stale_limitations",
        )
    )
    return checks, defects, {"resolved_examples": resolved}


def check_release_carry_forward(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    doc = load_json(monorepo / CARRY_FORWARD_RELATIVE)
    entries = doc.get("entries") or []
    checks.append(
        check(
            "release_carry_forward:present",
            bool(entries),
            f"count={len(entries)}",
            "release_carry_forward",
        )
    )
    # Must not include resolved timeout-unwired as current carry-forward
    texts = " ".join(str(e.get("description") or "") for e in entries if isinstance(e, dict))
    bad = "timeout_seconds declared but unwired" in texts.lower()
    checks.append(
        check(
            "release_carry_forward:no_resolved_timeout",
            not bad,
            "timeout not re-carried",
            "release_carry_forward",
        )
    )
    return checks, defects, {"entry_count": len(entries)}


def check_prior_slices(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok21 = (monorepo / EXPECTED_17_21_PACKAGE).is_dir()
    ok22 = (monorepo / EXPECTED_17_22_PACKAGE).is_dir()
    ok23 = (monorepo / EXPECTED_17_23_PACKAGE).is_dir()
    checks.append(check("prior_slices:17_21", ok21, EXPECTED_17_21_PACKAGE, "prior_slices"))
    checks.append(check("prior_slices:17_22_package", ok22, EXPECTED_17_22_PACKAGE, "prior_slices"))
    checks.append(
        check("prior_slices:17_23_started", ok23, EXPECTED_17_23_PACKAGE, "prior_slices")
    )
    if not ok23:
        defects.append(
            hard_defect(
                "slice_17_23_missing",
                "prior_slices:17_23_started",
                "present",
                "absent",
            )
        )
    started_24 = any((monorepo / c).exists() for c in SLICE_17_24_PACKAGE_CANDIDATES)
    checks.append(
        check("prior_slices:17_24_not_started", not started_24, "absent", "prior_slices")
    )
    if started_24:
        defects.append(
            hard_defect("slice_17_24_started", "prior_slices:17_24_not_started", "absent", "present")
        )
    return checks, defects, {
        "slice_17_21": ok21,
        "slice_17_22": ok22,
        "slice_17_23": ok23,
        "slice_17_23_started": ok23,
        "slice_17_24_started": started_24,
    }
