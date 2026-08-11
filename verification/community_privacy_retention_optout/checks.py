"""Checks for Slice 18.3 — Privacy + Retention + Opt-Out Documentation."""

from __future__ import annotations

import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from verification.community_privacy_retention_optout.contract import (
    CLAIM_REGISTER_RELATIVE,
    CLI_DOC,
    CONTRADICTION_REGISTER_RELATIVE,
    DATA_COLLECTION_DOC,
    DATA_LAKE_LIFECYCLE,
    DATA_LAKE_VARIABLES,
    ENGINE_PRIVACY,
    FORBIDDEN_18_4_PACKAGES,
    OPT_OUT_REGISTER_RELATIVE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    PRIVACY_DOC,
    RETENTION_DOC,
    RETENTION_REGISTER_RELATIVE,
    TELEMETRY_DOC,
    VSCODE_DOC,
    VSCODE_PRIVACY,
    WORKFLOW_REGISTER_RELATIVE,
)
from verification.community_privacy_retention_optout.helpers import (
    add_check,
    load_json,
    read_text,
)
from verification.community_privacy_retention_optout.models import CheckResult, Defect

PUBLIC_DOC_URLS = (
    "https://docs.codestrata.ai/security/privacy",
    "https://docs.codestrata.ai/security/retention-and-deletion",
    "https://docs.codestrata.ai/security/data-collection",
    "https://docs.codestrata.ai/reference/telemetry",
)

FORBIDDEN_PHRASES = (
    "we delete all your data when you opt out",
    "anonymous forever",
    "completely anonymous",
    "nothing leaves your machine",
    "reports are always private",
)


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    policy = load_json(path) if path.is_file() else {}
    add_check(checks, defects, "policy:present", path.is_file(), POLICY_RELATIVE, "policy")
    for key, expected in sorted(POLICY_REQUIRED_VALUES.items()):
        add_check(
            checks,
            defects,
            f"policy:{key}",
            policy.get(key) == expected,
            f"{key}={policy.get(key)!r}",
            "policy",
        )
    return checks, defects, policy


def check_docs_present(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    texts: dict[str, str] = {}
    required = {
        "privacy": PRIVACY_DOC,
        "retention": RETENTION_DOC,
        "data_collection": DATA_COLLECTION_DOC,
        "telemetry": TELEMETRY_DOC,
        "cli": CLI_DOC,
        "vscode": VSCODE_DOC,
        "engine_privacy": ENGINE_PRIVACY,
        "vscode_privacy": VSCODE_PRIVACY,
    }
    for key, rel in required.items():
        path = monorepo / rel
        text = read_text(path)
        texts[key] = text
        add_check(
            checks,
            defects,
            f"docs:present:{key}",
            path.is_file() and len(text) > 200,
            rel,
            "docs",
        )
    return checks, defects, texts


def check_retention_values(
    monorepo: Path,
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    retention = load_json(monorepo / RETENTION_REGISTER_RELATIVE)
    entries = {e.get("class"): e for e in retention.get("entries") or [] if isinstance(e, dict)}
    vars_tf = read_text(monorepo / DATA_LAKE_VARIABLES)
    life_tf = read_text(monorepo / DATA_LAKE_LIFECYCLE)
    ret = texts.get("retention", "")
    priv = texts.get("privacy", "")

    add_check(
        checks,
        defects,
        "retention:register_local_assessment",
        (entries.get("local_assessment_reports") or {}).get("duration_or_semantics")
        == "current_plus_previous",
        "local assessment",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:register_raw_365",
        (entries.get("data_lake_raw") or {}).get("duration_or_semantics") == "365_days",
        "raw",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:register_quarantine_90",
        (entries.get("data_lake_quarantine") or {}).get("duration_or_semantics") == "90_days",
        "quarantine",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:register_identity_indefinite",
        "indefinite" in str((entries.get("identity_prefix") or {}).get("duration_or_semantics") or ""),
        "identity",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:iac_raw_default_365",
        "default     = 365" in vars_tf or "default = 365" in vars_tf,
        "accepted_retention_days",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:iac_quarantine_default_90",
        "default     = 90" in vars_tf or "default = 90" in vars_tf,
        "quarantine_retention_days",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:iac_identity_no_expiration",
        "identity/" in life_tf and "Do NOT apply raw/" in life_tf,
        "identity indefinite note",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:doc_365",
        "365" in ret and "365" in priv,
        "docs raw 365",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:doc_90",
        "90" in ret,
        "docs quarantine 90",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:doc_identity_indefinite",
        "Indefinite" in ret or "indefinite" in ret,
        "docs identity",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:doc_local_current_previous",
        "current + previous" in ret.lower() or "current + previous" in ret,
        "local slots",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:not_lake_as_current_previous",
        "not** a current/previous" in ret.lower()
        or "not a current/previous" in ret.lower()
        or "NOT a current/previous" in ret
        or "is **not** a current/previous" in ret,
        "lake orientation",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:not_local_365",
        "not** retained for 365" in priv.lower()
        or "not retained for 365" in priv.lower()
        or "Local reports are\n**not** retained for 365" in priv
        or "Local reports are **not** retained for 365" in priv,
        "local != 365",
        "retention",
    )
    add_check(
        checks,
        defects,
        "retention:s3_versioning_not_product_history",
        "operational recovery" in ret.lower() and "product-visible" in ret.lower(),
        "s3 versioning disclaimer",
        "retention",
    )
    return checks, defects, {"register_classes": sorted(entries.keys())}


def check_opt_out_and_capabilities(
    monorepo: Path,
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    opt = load_json(monorepo / OPT_OUT_REGISTER_RELATIVE)
    by_cap = {
        e.get("capability"): e
        for e in (opt.get("entries") or [])
        if isinstance(e, dict)
    }
    ret = texts.get("retention", "")
    priv = texts.get("privacy", "")
    dc = texts.get("data_collection", "")

    add_check(
        checks,
        defects,
        "optout:register_no_historical_erase",
        (by_cap.get("historical_telemetry_auto_erase_on_opt_out") or {}).get("implemented")
        is False,
        "register",
        "opt_out",
    )
    add_check(
        checks,
        defects,
        "optout:register_no_self_service_lake",
        (by_cap.get("data_lake_user_self_service_deletion") or {}).get("implemented") is False,
        "register",
        "opt_out",
    )
    add_check(
        checks,
        defects,
        "optout:register_no_identity_deletion",
        (by_cap.get("identity_prefix_user_deletion") or {}).get("implemented") is False,
        "register",
        "opt_out",
    )
    add_check(
        checks,
        defects,
        "optout:doc_future_only",
        "future" in ret.lower() and "--telemetry-deny" in ret,
        "future only",
        "opt_out",
    )
    add_check(
        checks,
        defects,
        "optout:doc_not_delete_historical",
        "does **not** automatically" in ret
        and "historical Data Lake" in ret,
        "no historical erase",
        "opt_out",
    )
    add_check(
        checks,
        defects,
        "optout:doc_not_revoke_reports",
        "Revoke public reports" in ret or "revoke public reports" in ret.lower(),
        "no auto revoke",
        "opt_out",
    )
    add_check(
        checks,
        defects,
        "optout:no_self_service_claim",
        "no** end-user self-service" in ret.lower()
        or "no end-user self-service" in ret.lower()
        or "Not implemented" in ret,
        "honest capability",
        "opt_out",
    )
    add_check(
        checks,
        defects,
        "optout:privacy_aligned",
        "--telemetry-deny" in priv and "historical Community Data Lake" in priv,
        "privacy page",
        "opt_out",
    )
    add_check(
        checks,
        defects,
        "optout:data_collection_aligned",
        "future" in dc.lower() and "historical Data Lake" in dc,
        "data collection page",
        "opt_out",
    )
    # Capability matrix presence
    for marker in (
        "Delete local artifacts",
        "Revoke public report",
        "Self-service delete historical Data Lake",
        "Self-service delete Data Lake identity",
    ):
        add_check(
            checks,
            defects,
            f"matrix:{re.sub(r'[^a-z0-9]+', '_', marker.lower())}",
            marker in ret,
            marker,
            "capability_matrix",
        )
    limitations.append("no_self_service_historical_telemetry_deletion")
    limitations.append("no_self_service_identity_deletion")
    return checks, defects, limitations


def check_revoke_and_consent(texts: dict[str, str], monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ret = texts.get("retention", "")
    priv = texts.get("privacy", "")
    report_py = read_text(monorepo / "engine/src/codestrata/cli/report.py")
    service = read_text(
        monorepo / "platform/src/codestrata_platform/community_cloud_api/reports/service.py"
    )
    add_check(
        checks,
        defects,
        "revoke:api_documented",
        "DELETE" in ret and "/api/v1/reports/" in ret and "404" in ret,
        "DELETE + 404",
        "revoke",
    )
    add_check(
        checks,
        defects,
        "revoke:no_cli_command_invented",
        "no Engine CLI `report revoke`" in ret
        or "no** end-user CLI `report revoke`" in ret
        or "There is **no** end-user CLI `report revoke`" in ret,
        "no invented CLI revoke",
        "revoke",
    )
    add_check(
        checks,
        defects,
        "revoke:privacy_no_cli_flow_claim",
        "CLI flow" not in priv and "no Engine CLI `report revoke`" in priv
        or "There is no Engine CLI `report revoke`" in priv,
        "privacy revoke wording",
        "revoke",
    )
    add_check(
        checks,
        defects,
        "revoke:runtime_handle_revoke",
        "def handle_revoke" in service,
        "service",
        "revoke",
    )
    add_check(
        checks,
        defects,
        "revoke:cli_has_publish_not_revoke_cmd",
        'command("publish")' in report_py and 'command("revoke")' not in report_py,
        "cli surface",
        "revoke",
    )
    add_check(
        checks,
        defects,
        "consent:telemetry_ne_publish",
        "different** consent" in ret.lower()
        or "Different** consent" in ret
        or "These are **different**" in ret,
        "separation",
        "consent",
    )
    add_check(
        checks,
        defects,
        "consent:confirm_public_publish",
        "--confirm-public-publish" in ret or "--confirm-public-publish" in priv,
        "publish flag",
        "consent",
    )
    return checks, defects


def check_quarantine_and_ai(texts: dict[str, str]) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    ret = texts.get("retention", "")
    priv = texts.get("privacy", "")
    add_check(
        checks,
        defects,
        "quarantine:reject_before_persist",
        "reject" in ret.lower() and "before" in ret.lower(),
        "reject semantics",
        "quarantine",
    )
    add_check(
        checks,
        defects,
        "quarantine:not_all_rejected_stored",
        "Do **not** assume every rejected" in ret or "do not assume every rejected" in ret.lower(),
        "honest quarantine",
        "quarantine",
    )
    add_check(
        checks,
        defects,
        "ai:not_speculated",
        "does **not** speculate" in ret or "does not speculate" in ret.lower(),
        "provider retention",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:separate_from_telemetry",
        "separate" in ret.lower() and "AI provider" in ret,
        "boundary",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:link_forward",
        "/ai-providers/" in ret and "/ai-providers/" in priv,
        "forward link",
        "ai",
    )
    limitations.append("third_party_ai_retention_deferred_to_provider_terms_or_18_4")
    return checks, defects, limitations


def check_never_collected_regression(texts: dict[str, str]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    priv = texts.get("privacy", "")
    dc = texts.get("data_collection", "")
    ret = texts.get("retention", "")
    add_check(
        checks,
        defects,
        "never:source_still_claimed",
        "Source code" in priv or "source code" in dc.lower(),
        "source",
        "never_collected",
    )
    add_check(
        checks,
        defects,
        "never:report_bodies_not_telemetry",
        "assessment.html" in priv and "telemetry" in priv.lower(),
        "report bodies",
        "never_collected",
    )
    add_check(
        checks,
        defects,
        "never:ai_prompts_through_telemetry",
        "through telemetry" in priv.lower() or "through telemetry" in dc.lower(),
        "AI wording",
        "never_collected",
    )
    add_check(
        checks,
        defects,
        "never:credentials",
        "Credentials" in priv or "credentials" in dc.lower(),
        "credentials",
        "never_collected",
    )
    add_check(
        checks,
        defects,
        "never:retention_regression_section",
        "Never-collected regression" in ret,
        "retention page",
        "never_collected",
    )
    return checks, defects


def check_language_and_corporate(texts: dict[str, str]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    blob = "\n".join(texts.values()).lower()
    for phrase in FORBIDDEN_PHRASES:
        add_check(
            checks,
            defects,
            f"language:forbid_{re.sub(r'[^a-z0-9]+', '_', phrase)[:40]}",
            phrase not in blob,
            phrase,
            "language",
        )
    priv = texts.get("privacy", "")
    ret = texts.get("retention", "")
    add_check(
        checks,
        defects,
        "language:corporate_separated",
        "codestrata.ai/privacy" in priv and "corporate" in priv.lower(),
        "corporate vs product",
        "language",
    )
    add_check(
        checks,
        defects,
        "language:product_not_corporate_on_retention",
        "not the corporate" in ret.lower() or "corporate\nlegal notice" in ret.lower()
        or "corporate legal notice" in ret.lower(),
        "retention corporate separation",
        "language",
    )
    return checks, defects


def check_cli_vscode_github(
    monorepo: Path,
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cli = texts.get("cli", "")
    vscode = texts.get("vscode", "")
    vscode_priv = texts.get("vscode_privacy", "")
    engine = texts.get("engine_privacy", "")
    assess = read_text(monorepo / "engine/src/codestrata/cli/assess.py")
    add_check(
        checks,
        defects,
        "cli:flags_exist",
        "--telemetry-allow" in assess and "--telemetry-deny" in assess,
        "assess flags",
        "cli",
    )
    add_check(
        checks,
        defects,
        "cli:docs_flags",
        "--telemetry-allow" in cli and "--telemetry-deny" in cli,
        "cli.md",
        "cli",
    )
    add_check(
        checks,
        defects,
        "cli:no_delete_telemetry_command",
        "telemetry delete" not in cli.lower() and "telemetry wipe" not in cli.lower(),
        "no invented delete",
        "cli",
    )
    add_check(
        checks,
        defects,
        "cli:publish_flag_documented",
        "--confirm-public-publish" in cli or "report publish" in cli,
        "publish",
        "cli",
    )
    add_check(
        checks,
        defects,
        "vscode:default_off",
        "default **off**" in vscode or "disabled by default" in vscode_priv.lower(),
        "default off",
        "vscode",
    )
    add_check(
        checks,
        defects,
        "vscode:optout_not_revoke",
        "does **not** revoke" in vscode or "does not revoke" in vscode_priv.lower(),
        "opt-out != revoke",
        "vscode",
    )
    add_check(
        checks,
        defects,
        "vscode:local_user_controlled",
        "user-controlled" in vscode or "user-controlled" in vscode_priv,
        "local control",
        "vscode",
    )
    add_check(
        checks,
        defects,
        "github:engine_retention_url",
        "retention-and-deletion" in engine,
        "engine PRIVACY",
        "github",
    )
    add_check(
        checks,
        defects,
        "github:vscode_retention_url",
        "retention-and-deletion" in vscode_priv,
        "vscode PRIVACY",
        "github",
    )
    return checks, defects


def check_navigation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cfg = read_text(monorepo / "docs/.vitepress/config.ts")
    for link in (
        "/security/privacy",
        "/security/retention-and-deletion",
        "/security/data-collection",
        "/security/collected-fields",
        "/reference/telemetry",
        "/reference/community-api",
        "/ai-providers",
    ):
        add_check(
            checks,
            defects,
            f"nav:{link.strip('/').replace('/', '_')}",
            link in cfg,
            link,
            "navigation",
        )
    return checks, defects


def check_t18_c005(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    contra = load_json(monorepo / CONTRADICTION_REGISTER_RELATIVE)
    entries = contra.get("entries") if isinstance(contra.get("entries"), list) else []
    c005 = next(
        (e for e in entries if isinstance(e, dict) and e.get("contradiction_id") == "T18-C005"),
        None,
    )
    add_check(
        checks,
        defects,
        "contradiction:t18_c005_resolved",
        isinstance(c005, dict) and c005.get("classification") == "RESOLVED",
        str((c005 or {}).get("classification")),
        "contradictions",
    )
    # Unrelated remain open
    open_ids = [
        str(e.get("contradiction_id"))
        for e in entries
        if isinstance(e, dict)
        and e.get("contradiction_id") in {"T18-C001", "T18-C002", "T18-C003"}
        and e.get("classification") != "RESOLVED"
    ]
    add_check(
        checks,
        defects,
        "contradiction:unrelated_remain_open",
        len(open_ids) >= 1,
        f"open={open_ids}",
        "contradictions",
    )
    return checks, defects


def check_claims(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    claims_reg = load_json(monorepo / CLAIM_REGISTER_RELATIVE)
    entries = claims_reg.get("entries") if isinstance(claims_reg.get("entries"), list) else []
    add_check(
        checks,
        defects,
        "claims:register_present",
        len(entries) >= 8,
        f"count={len(entries)}",
        "claims",
    )
    summarized: list[dict[str, Any]] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        claim_id = str(e.get("claim_id") or "")
        doc_rel = str(e.get("public_document") or "")
        doc_text = read_text(monorepo / doc_rel) if doc_rel else ""
        ok = bool(
            claim_id and doc_rel and doc_text and e.get("register_18_1") and e.get("runtime_evidence")
        )
        add_check(checks, defects, f"claims:{claim_id or 'unknown'}", ok, doc_rel, "claims")
        summarized.append(
            {
                "claim_id": claim_id,
                "public_document": doc_rel,
                "register_18_1": e.get("register_18_1"),
                "ok": ok,
            }
        )
    return checks, defects, summarized


def check_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    wf = load_json(monorepo / WORKFLOW_REGISTER_RELATIVE)
    add_check(
        checks,
        defects,
        "boundary:start_18_3",
        wf.get("start_slice_18_3") is True,
        str(wf.get("start_slice_18_3")),
        "boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:start_18_4_recorded",
        wf.get("start_slice_18_4") in (True, False),
        str(wf.get("start_slice_18_4")),
        "boundary",
        soft=True,
    )
    for pkg in FORBIDDEN_18_4_PACKAGES:
        add_check(
            checks,
            defects,
            f"boundary:absent_{Path(pkg).name}",
            not (monorepo / pkg).exists(),
            pkg,
            "boundary",
        )
    limitations.append("marketplace_content_not_published")
    limitations.append("monorepo_pre_cutover_authority")
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.stdout.strip():
        limitations.append("worktree_uncommitted")
    return checks, defects, limitations


def check_live_docs() -> tuple[list[CheckResult], list[Defect], list[str], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    results: dict[str, Any] = {}
    reachable = 0
    ssl_context = None
    try:
        import certifi
        import ssl

        ssl_context = ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001
        ssl_context = None
    for url in PUBLIC_DOC_URLS:
        code = 0
        try:
            req = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; CodeStrata-sv18-3/1.0; "
                        "+https://docs.codestrata.ai)"
                    ),
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            open_kwargs: dict[str, Any] = {"timeout": 20}
            if ssl_context is not None:
                open_kwargs["context"] = ssl_context
            with urllib.request.urlopen(req, **open_kwargs) as resp:  # noqa: S310
                code = int(getattr(resp, "status", 0) or 0)
        except urllib.error.HTTPError as exc:
            code = int(exc.code)
        except Exception:  # noqa: BLE001
            code = 0
        results[url] = code
        ok = code == 200
        if ok:
            reachable += 1
        add_check(
            checks,
            defects,
            f"live:{url.rsplit('/', 1)[-1]}",
            ok,
            f"http={code}",
            "live_docs",
            soft=True,
        )
    if reachable < len(PUBLIC_DOC_URLS):
        limitations.append("live_docs_unreachable")
    return checks, defects, limitations, results
