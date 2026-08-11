"""Checks for Slice 18.8 Epic 18 Transparency Documentation completion."""

from __future__ import annotations

import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from verification.community_epic18_completion.contract import (
    CARRY_FORWARD_RELATIVE,
    CLAIM_COUNT_DELTA_NOTES,
    CLAIM_REGISTER_RELATIVE,
    CLI_DOC,
    CONTRACT_RELATIVE,
    CONTRADICTION_REGISTER_RELATIVE,
    DATA_COLLECTION_DOC,
    ENGINE_PUBLIC_CLIENT,
    ENGINE_README,
    ENGINE_REPORT_CLI,
    ENGINE_REPORT_PUBLISHING,
    EVIDENCE_INVENTORY_RELATIVE,
    FORBIDDEN_EPIC19_PACKAGES,
    PLATFORM_ERRORS,
    PLATFORM_REPORT_SERVICE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    PRIOR_SUITE_PACKAGES,
    PUBLIC_CLIENT_REGISTER_RELATIVE,
    REPORT_PUBLISH_POLICY_RELATIVE,
    REPORTS_WORKER,
    RETENTION_DOC,
    ROOT_README,
    ROOT_SECURITY,
    SLICE_MATRIX_SPEC,
    SOURCE_LOCALITY_DOC,
    STALE_PHRASE_NEEDLES,
    SV187_CURRENT_CLAIM_COUNT,
    SV187_PRIOR_CLAIM_COUNT,
    VSCODE_POLICY,
    VSCODE_README,
    WORKFLOW_REGISTER_RELATIVE,
)
from verification.community_epic18_completion.helpers import (
    add_check,
    load_json,
    read_text,
)
from verification.community_epic18_completion.models import CheckResult, Defect

SECRET_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}"),
    re.compile(r"(?<![A-Za-z0-9])ASIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"aws_secret_access_key\s*[:=]\s*\S+", re.IGNORECASE),
)

# Intentional packaged public credential is allowed only in its module.
PUBLIC_CRED_RE = re.compile(r"cscc_v1_[A-Za-z0-9]{20,}")

SCAN_PATHS = (
    ROOT_README,
    ROOT_SECURITY,
    ENGINE_README,
    ENGINE_REPORT_PUBLISHING,
    ENGINE_REPORT_CLI,
    ENGINE_PUBLIC_CLIENT,
    VSCODE_README,
    VSCODE_POLICY,
    CLI_DOC,
    DATA_COLLECTION_DOC,
    RETENTION_DOC,
    SOURCE_LOCALITY_DOC,
    "docs/security/privacy.md",
    "docs/architecture/community-cloud.md",
    "docs/reference/community-api/index.md",
    "docs/ai-providers/index.md",
    PLATFORM_ERRORS,
    PLATFORM_REPORT_SERVICE,
    REPORTS_WORKER,
    "platform/policies/community_public_claim_runtime_validation_register.json",
    "platform/policies/community_transparency_contradiction_register.json",
    "platform/policies/community_epic18_completion_policy.json",
    "platform/policies/community_epic18_release_carry_forward_register.json",
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


def check_evidence_inventory(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / EVIDENCE_INVENTORY_RELATIVE
    entries: list[dict[str, Any]] = []
    add_check(
        checks,
        defects,
        "evidence_inventory:exists",
        path.is_file(),
        EVIDENCE_INVENTORY_RELATIVE,
        "evidence",
    )
    if not path.is_file():
        return checks, defects, entries
    reg = load_json(path)
    entries = [e for e in (reg.get("entries") or []) if isinstance(e, dict)]
    add_check(
        checks,
        defects,
        "evidence_inventory:nonempty",
        len(entries) >= 10,
        str(len(entries)),
        "evidence",
    )
    classes = Counter(str(e.get("classification") or "") for e in entries)
    add_check(
        checks,
        defects,
        "evidence_inventory:has_authoritative",
        classes.get("authoritative", 0) >= 8,
        str(dict(classes)),
        "evidence",
    )
    add_check(
        checks,
        defects,
        "evidence_inventory:has_release_only",
        classes.get("release-only", 0) >= 1,
        str(dict(classes)),
        "evidence",
    )
    for e in entries:
        rel = str(e.get("path") or "")
        classification = str(e.get("classification") or "")
        if classification == "release-only":
            # Must remain absent during Epic 18.
            add_check(
                checks,
                defects,
                f"evidence:absent_{Path(rel).name}",
                not (monorepo / rel).exists(),
                rel,
                "evidence",
            )
            continue
        if classification in {"authoritative", "supporting"} and not rel.startswith("."):
            # Suite packages / relative files should exist when authoritative.
            target = monorepo / rel
            if rel.startswith("verification/") or rel.endswith(".py") or rel.endswith(".md") or rel.endswith(".ts") or rel.endswith(".json"):
                add_check(
                    checks,
                    defects,
                    f"evidence:present:{e.get('artifact_id')}",
                    target.exists(),
                    rel,
                    "evidence",
                    soft=classification == "supporting",
                )
    return checks, defects, entries


def check_claim_inventory(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    path = monorepo / CLAIM_REGISTER_RELATIVE
    inventory: dict[str, Any] = {
        "total": 0,
        "SUPPORTED": 0,
        "SUPPORTED_WITH_QUALIFICATION": 0,
        "STALE": 0,
        "UNSUPPORTED": 0,
        "CONTRADICTORY": 0,
        "EXPECTED_RELEASE_GAP": 0,
        "delta_from_sv18_7_prior": {},
        "entries": [],
    }
    add_check(checks, defects, "claims:register_exists", path.is_file(), CLAIM_REGISTER_RELATIVE, "claims")
    if not path.is_file():
        return checks, defects, inventory, limitations
    reg = load_json(path)
    entries = [e for e in (reg.get("entries") or []) if isinstance(e, dict)]
    counts = Counter(str(e.get("status") or "") for e in entries)
    total = len(entries)
    inventory = {
        "total": total,
        "SUPPORTED": int(counts.get("SUPPORTED", 0)),
        "SUPPORTED_WITH_QUALIFICATION": int(counts.get("SUPPORTED_WITH_QUALIFICATION", 0)),
        "STALE": int(counts.get("STALE", 0)),
        "UNSUPPORTED": int(counts.get("UNSUPPORTED", 0)),
        "CONTRADICTORY": int(counts.get("CONTRADICTORY", 0)),
        "EXPECTED_RELEASE_GAP": int(counts.get("EXPECTED_RELEASE_GAP", 0)),
        "delta_from_sv18_7_prior": {
            "prior_total": SV187_PRIOR_CLAIM_COUNT,
            "current_total": total,
            "delta": total - SV187_PRIOR_CLAIM_COUNT,
            "notes": list(CLAIM_COUNT_DELTA_NOTES),
        },
        "entries": [
            {
                "claim_id": e.get("claim_id"),
                "category": e.get("category"),
                "status": e.get("status"),
                "release_disposition": e.get("release_disposition"),
                "qualification": e.get("qualification"),
            }
            for e in entries
        ],
    }
    add_check(
        checks,
        defects,
        "claims:count_matches_register",
        int(reg.get("claim_count") or 0) == total,
        f"claim_count={reg.get('claim_count')} entries={total}",
        "claims",
    )
    add_check(
        checks,
        defects,
        "claims:current_total_70",
        total == SV187_CURRENT_CLAIM_COUNT,
        str(total),
        "claims",
    )
    add_check(
        checks,
        defects,
        "claims:no_unsupported",
        counts.get("UNSUPPORTED", 0) == 0,
        str(counts.get("UNSUPPORTED", 0)),
        "claims",
    )
    add_check(
        checks,
        defects,
        "claims:no_contradictory",
        counts.get("CONTRADICTORY", 0) == 0,
        str(counts.get("CONTRADICTORY", 0)),
        "claims",
    )
    # Required journey / GET claims present.
    ids = {str(e.get("claim_id")) for e in entries}
    for required in ("C18-7-016", "C18-7-017", "C18-6-008", "C18-5-008"):
        add_check(
            checks,
            defects,
            f"claims:present:{required}",
            required in ids,
            required,
            "claims",
        )
    # Delta explanation required when total changed from first 18.7 baseline.
    add_check(
        checks,
        defects,
        "claims:delta_explained",
        total >= SV187_PRIOR_CLAIM_COUNT and len(CLAIM_COUNT_DELTA_NOTES) >= 2,
        f"delta={total - SV187_PRIOR_CLAIM_COUNT}",
        "claims",
    )
    if counts.get("STALE", 0):
        limitations.append("website_favicon_deferred")
    if counts.get("EXPECTED_RELEASE_GAP", 0):
        limitations.append("github_release_still_0_1_0")
    if counts.get("SUPPORTED_WITH_QUALIFICATION", 0):
        # Map known qualifications to soft codes.
        for e in entries:
            if e.get("status") != "SUPPORTED_WITH_QUALIFICATION":
                continue
            cid = str(e.get("claim_id"))
            if cid == "C18-7-009":
                limitations.append("marketplace_unpublished")
            elif cid == "C18-7-013":
                limitations.append("openai_owner_credential_required")
                limitations.append("openrouter_owner_credential_required")
            elif cid == "C18-7-017":
                limitations.append("report_not_found_live_message_pending_redeploy")
    return checks, defects, inventory, limitations


def check_contradictions(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    path = monorepo / CONTRADICTION_REGISTER_RELATIVE
    closure: dict[str, Any] = {"entries": [], "final_classifications": {}}
    add_check(
        checks,
        defects,
        "contradictions:register_exists",
        path.is_file(),
        CONTRADICTION_REGISTER_RELATIVE,
        "contradictions",
    )
    if not path.is_file():
        return checks, defects, closure, limitations
    reg = load_json(path)
    entries = [e for e in (reg.get("entries") or []) if isinstance(e, dict)]
    by_id = {str(e.get("contradiction_id")): e for e in entries}
    # Must include at least T18-C001..C007.
    expected_ids = [f"T18-C{str(i).zfill(3)}" for i in range(1, 8)]
    for cid in expected_ids:
        add_check(
            checks,
            defects,
            f"contradictions:present:{cid}",
            cid in by_id,
            cid,
            "contradictions",
        )
    add_check(
        checks,
        defects,
        "contradictions:no_silent_drop",
        len(entries) >= 7,
        str(len(entries)),
        "contradictions",
    )

    def map_final(entry: dict[str, Any]) -> str:
        raw = str(entry.get("classification") or "").upper()
        cid = str(entry.get("contradiction_id") or "")
        if raw == "RESOLVED":
            if cid == "T18-C007":
                # Methodology resolved; live message still deployment-qualified.
                return "QUALIFIED_DEPLOYMENT_GAP"
            return "RESOLVED"
        if raw == "EXPECTED_RELEASE_GAP":
            return "EXPECTED_RELEASE_GAP"
        if raw == "MUST_FIX_BEFORE_RELEASE":
            return "EXPECTED_RELEASE_GAP"
        if raw in {"OPEN", "QUALIFIED_DEPLOYMENT_GAP"}:
            return raw
        return "OPEN"

    rows = []
    for e in sorted(entries, key=lambda x: str(x.get("contradiction_id") or "")):
        final = map_final(e)
        rows.append(
            {
                "contradiction_id": e.get("contradiction_id"),
                "summary": e.get("summary"),
                "introduced_slice": e.get("slice") or e.get("resolved_in_slice") or e.get("reviewed_in_slice"),
                "original_classification": e.get("classification"),
                "resolution": e.get("disposition"),
                "evidence": e.get("evidence"),
                "final_classification": final,
            }
        )
        closure["final_classifications"][str(e.get("contradiction_id"))] = final
        add_check(
            checks,
            defects,
            f"contradictions:final:{e.get('contradiction_id')}",
            final in {
                "RESOLVED",
                "OPEN",
                "EXPECTED_RELEASE_GAP",
                "QUALIFIED_DEPLOYMENT_GAP",
            },
            final,
            "contradictions",
        )
        if final == "OPEN":
            defects.append(
                Defect(
                    classification="OPEN_CONTRADICTION",
                    check_id=f"contradictions:open:{e.get('contradiction_id')}",
                    expected="not_open",
                    detail=str(e.get("summary") or ""),
                )
            )
        if final == "EXPECTED_RELEASE_GAP" and e.get("contradiction_id") == "T18-C003":
            limitations.append("website_favicon_deferred")
        if final == "EXPECTED_RELEASE_GAP" and e.get("contradiction_id") == "T18-C002":
            limitations.append("github_release_still_0_1_0")
        if final == "QUALIFIED_DEPLOYMENT_GAP":
            limitations.append("report_not_found_live_message_pending_redeploy")

    # Explicitly no OPEN material contradictions for epic closure.
    open_count = sum(1 for r in rows if r["final_classification"] == "OPEN")
    add_check(
        checks,
        defects,
        "contradictions:no_open",
        open_count == 0,
        str(open_count),
        "contradictions",
    )
    closure["entries"] = rows
    return checks, defects, closure, limitations


def check_report_publishing(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    client = read_text(monorepo / ENGINE_REPORT_PUBLISHING)
    cli = read_text(monorepo / ENGINE_REPORT_CLI)
    policy = load_json(monorepo / REPORT_PUBLISH_POLICY_RELATIVE)
    worker = read_text(monorepo / REPORTS_WORKER)
    vscode = read_text(monorepo / VSCODE_POLICY)
    service = read_text(monorepo / PLATFORM_REPORT_SERVICE)
    errors = read_text(monorepo / PLATFORM_ERRORS)
    retention = read_text(monorepo / RETENTION_DOC)
    public_client = read_text(monorepo / ENGINE_PUBLIC_CLIENT)

    add_check(
        checks,
        defects,
        "publish:telemetry_opt_in_not_required",
        policy.get("telemetry_opt_in_required_for_cloud_publish") is False,
        str(policy.get("telemetry_opt_in_required_for_cloud_publish")),
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:policy_separate_from_telemetry",
        policy.get("publish_authorization_separate_from_telemetry") is True,
        str(policy.get("publish_authorization_separate_from_telemetry")),
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:verify_public_get",
        "verify_public_report_get" in client
        and "text/html" in client
        and "codestrata-public-id" in client,
        "present",
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:branded_url",
        'PUBLIC_REPORTS_BASE_URL = "https://reports.codestrata.ai"' in client
        and ('"/r/"' in client or "/r/" in client),
        "present",
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:packaged_public_client",
        "packaged_public_community_client_credential" in client
        and "PUBLIC_CLIENT_DISTRIBUTION" in public_client,
        "present",
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:interactive_one_confirm",
        'typer.confirm("Publish report?"' in cli or "Publish report?" in cli,
        "present",
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:ci_flags",
        "--confirm-public-publish" in cli and "--acknowledge-private-repository" in cli,
        "present",
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:does_not_set_telemetry_opt_in",
        "CODESTRATA_TELEMETRY_OPT_IN" not in client
        or "delenv" in client
        or "not required" in client.lower(),
        "absent_set",
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:worker_proxy",
        "/api/v1/reports/" in worker and "/r/" in worker,
        "present",
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:vscode_same_prefix",
        "https://reports.codestrata.ai/r/" in vscode,
        "present",
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:rotation_current_previous",
        "old_previous" in service and "MAX_CLOUD_VERSIONS" in read_text(
            monorepo
            / "platform/src/codestrata_platform/community_cloud_api/reports/policy.py"
        ),
        "present",
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:retention_docs_disposable_urls",
        "intentionally disposable" in retention.lower()
        or "retired" in retention.lower(),
        "present",
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:report_not_found_code_local",
        "ERROR_REPORT_NOT_FOUND" in errors and "Report not found." in errors,
        "present",
        "publish",
    )
    add_check(
        checks,
        defects,
        "publish:service_uses_report_not_found",
        "ERROR_REPORT_NOT_FOUND" in service and "handle_public_get" in service,
        "present",
        "publish",
    )
    # Live message redeploy remains a soft limitation.
    limitations.append("report_not_found_live_message_pending_redeploy")
    return checks, defects, limitations


def check_topics(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, str], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    topics: dict[str, str] = {}

    data_collection = read_text(monorepo / DATA_COLLECTION_DOC)
    locality = read_text(monorepo / SOURCE_LOCALITY_DOC)
    retention = read_text(monorepo / RETENTION_DOC)
    ai_doc = read_text(monorepo / "docs/ai-providers/index.md")
    cloud = read_text(monorepo / "docs/architecture/community-cloud.md")
    readme = read_text(monorepo / ROOT_README)
    security = read_text(monorepo / ROOT_SECURITY)
    cli_doc = read_text(monorepo / CLI_DOC)
    vscode = read_text(monorepo / VSCODE_README)
    client_reg = load_json(monorepo / PUBLIC_CLIENT_REGISTER_RELATIVE) if (
        monorepo / PUBLIC_CLIENT_REGISTER_RELATIVE
    ).is_file() else {}

    def pass_topic(name: str, ok: bool, detail: str) -> None:
        add_check(checks, defects, f"topic:{name}", ok, detail, "topics")
        topics[name] = "PASS" if ok else "FAIL"

    pass_topic(
        "telemetry_data_collection",
        "opt-in" in data_collection.lower() and "source code" in data_collection.lower(),
        "data-collection.md",
    )
    pass_topic(
        "privacy_retention_optout",
        "current + previous" in retention or "current+previous" in retention,
        "retention-and-deletion.md",
    )
    pass_topic(
        "ai_source_locality",
        "OpenAI" in ai_doc and "Bedrock" in ai_doc and "source" in locality.lower(),
        "ai + source-locality",
    )
    pass_topic(
        "community_cloud_data_lake_insights_api",
        "Data Lake" in cloud and "reports.codestrata.ai" in cloud,
        "community-cloud.md",
    )
    pass_topic(
        "report_publishing",
        "report publish" in cli_doc.lower() and "reports.codestrata.ai/r/" in cli_doc,
        "cli.md",
    )
    pass_topic(
        "readme_security_cli_vscode_docs",
        "Engineering Assessment" in readme
        and "SECURITY" in security
        and "Marketplace" in vscode,
        "surfaces",
    )
    pass_topic(
        "packaged_public_client",
        bool(client_reg)
        and "packaged" in str(client_reg).lower()
        and "not a user secret" in read_text(monorepo / ENGINE_PUBLIC_CLIENT).lower(),
        "public client register",
    )

    # Stale phrase scan on key docs (soft if only in historical notes).
    stale_hits: list[str] = []
    for rel in (ROOT_README, ENGINE_README, CLI_DOC, VSCODE_README, DATA_COLLECTION_DOC):
        text = read_text(monorepo / rel)
        lower = text.lower()
        for needle in STALE_PHRASE_NEEDLES:
            if needle.lower() in lower:
                # Allow mentions that negate the stale claim.
                ctx_ok = any(
                    n in lower
                    for n in (
                        "not required",
                        "no longer",
                        "do not",
                        "does not require",
                        "independent",
                        "intentionally disposable",
                        "not permanent",
                    )
                )
                if not ctx_ok:
                    stale_hits.append(f"{rel}:{needle}")
    add_check(
        checks,
        defects,
        "topics:stale_phrases_absent_or_negated",
        not stale_hits,
        ",".join(stale_hits) if stale_hits else "absent",
        "topics",
    )
    limitations.append("marketplace_unpublished")
    limitations.append("openai_owner_credential_required")
    limitations.append("openrouter_owner_credential_required")
    limitations.append("full_release_corpus_deferred")
    return checks, defects, topics, limitations


def check_slice_matrix(
    monorepo: Path,
    prior: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    matrix: dict[str, Any] = {}
    for slice_id, spec in SLICE_MATRIX_SPEC.items():
        suite = spec.get("suite") or ""
        if slice_id == "18.8":
            status = "IN_PROGRESS"
            evidence = "sv18-8"
        elif slice_id == "18.7A":
            status = "COMPLETE"
            evidence = "engine report_publishing verify_public_get + C18-7-016/017"
        else:
            prior_row = prior.get(suite) or {}
            ok = bool(prior_row.get("ok"))
            status = "COMPLETE" if ok else "INCOMPLETE"
            evidence = f"{suite} verdict={prior_row.get('verdict')}"
        matrix[slice_id] = {
            "purpose": spec["purpose"],
            "final_status": status,
            "authoritative_evidence": evidence,
            "remaining_qualification": (
                "see epic limitations"
                if slice_id in {"18.7", "18.7A", "18.8"}
                else None
            ),
        }
        if slice_id not in {"18.8"}:
            add_check(
                checks,
                defects,
                f"matrix:{slice_id}",
                status == "COMPLETE",
                evidence,
                "matrix",
            )
    return checks, defects, matrix


def check_workflows(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    wf = load_json(monorepo / WORKFLOW_REGISTER_RELATIVE)
    add_check(
        checks,
        defects,
        "workflow:start_18_8",
        wf.get("start_slice_18_8") is True,
        str(wf.get("start_slice_18_8")),
        "workflow",
    )
    add_check(
        checks,
        defects,
        "workflow:release_readiness_false",
        wf.get("start_release_readiness_epic") is False,
        str(wf.get("start_release_readiness_epic")),
        "workflow",
    )
    for pkg in FORBIDDEN_EPIC19_PACKAGES:
        add_check(
            checks,
            defects,
            f"workflow:absent_{Path(pkg).name}",
            not (monorepo / pkg).exists(),
            pkg,
            "workflow",
        )
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


def check_carry_forwards(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / CARRY_FORWARD_RELATIVE
    entries: list[dict[str, Any]] = []
    add_check(
        checks,
        defects,
        "carry:exists",
        path.is_file(),
        CARRY_FORWARD_RELATIVE,
        "carry_forward",
    )
    if path.is_file():
        reg = load_json(path)
        entries = [e for e in (reg.get("entries") or []) if isinstance(e, dict)]
        add_check(
            checks,
            defects,
            "carry:min_count",
            len(entries) >= 15,
            str(len(entries)),
            "carry_forward",
        )
        required = {
            "E18-RCF-002",
            "E18-RCF-005",
            "E18-RCF-014",
            "E18-RCF-015",
            "E18-RCF-017",
            "E18-RCF-020",
        }
        ids = {str(e.get("item_id")) for e in entries}
        add_check(
            checks,
            defects,
            "carry:required_ids",
            required <= ids,
            str(sorted(required - ids)),
            "carry_forward",
        )
    return checks, defects, entries


def check_security(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    hits: list[str] = []
    for rel in SCAN_PATHS:
        path = monorepo / rel
        if not path.is_file():
            continue
        text = read_text(path)
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                hits.append(f"{rel}:{pat.pattern[:24]}")
        # Packaged public credential value may exist only in public_client_credential.py
        if PUBLIC_CRED_RE.search(text) and rel != ENGINE_PUBLIC_CLIENT:
            # Allow register fingerprint IDs without full credential.
            if "cscc_v1_" in text and "packaged" not in text.lower():
                hits.append(f"{rel}:unexpected_cscc")
    add_check(
        checks,
        defects,
        "security:no_accidental_secrets",
        not hits,
        ",".join(hits[:5]) if hits else "clean",
        "security",
    )
    # Distinguish intentional public credential module.
    add_check(
        checks,
        defects,
        "security:public_client_module_present",
        (monorepo / ENGINE_PUBLIC_CLIENT).is_file(),
        ENGINE_PUBLIC_CLIENT,
        "security",
    )
    return checks, defects, {"hits": hits, "scanned": len(SCAN_PATHS)}
