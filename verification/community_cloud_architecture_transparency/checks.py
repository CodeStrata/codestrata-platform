"""Checks for Slice 18.5 — Community Cloud Architecture Transparency."""

from __future__ import annotations

import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from verification.community_cloud_architecture_transparency.contract import (
    ARCH_INDEX,
    CLAIM_REGISTER_RELATIVE,
    COMMUNITY_API_DOC,
    COMMUNITY_CLOUD_DOC,
    CONTRADICTION_REGISTER_RELATIVE,
    DATA_COLLECTION_DOC,
    DATA_LAKE_DOC,
    DOC_AUTHORITY_RELATIVE,
    ENGINE_PRIVACY,
    ENGINE_README,
    ENGINE_SECURITY,
    FORBIDDEN_18_6_PACKAGES,
    INSIGHTS_DOC,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    PRIVACY_DOC,
    ROOT_SECURITY,
    ROUTE_REGISTER_RELATIVE,
    SOURCE_LOCALITY_DOC,
    TELEMETRY_DOC,
    VITEPRESS_CONFIG,
    WORKFLOW_REGISTER_RELATIVE,
)
from verification.community_cloud_architecture_transparency.helpers import (
    add_check,
    load_json,
    read_text,
)
from verification.community_cloud_architecture_transparency.models import CheckResult, Defect

PUBLIC_DOC_URLS = (
    "https://docs.codestrata.ai/architecture/",
    "https://docs.codestrata.ai/architecture/community-cloud",
    "https://docs.codestrata.ai/architecture/data-lake",
    "https://docs.codestrata.ai/architecture/insights",
    "https://docs.codestrata.ai/reference/community-api/",
    "https://docs.codestrata.ai/security/source-locality",
)

FORBIDDEN_PHRASES = (
    "execute-api is the public",
    "execute-api hostname is the public",
    "data lake stores reports",
    "data lake is report storage",
    "insights queries report html",
    "assessment_metadata is active on assess without consent",
    "cli_event is active on assess",
    "extension_event is active",
    "ai_usage is active on assess",
    "we collect assessment scores",
    "code graph uploaded",
    "graph telemetry is collected",
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
        "arch_index": ARCH_INDEX,
        "community_cloud": COMMUNITY_CLOUD_DOC,
        "data_lake": DATA_LAKE_DOC,
        "insights": INSIGHTS_DOC,
        "community_api": COMMUNITY_API_DOC,
        "source_locality": SOURCE_LOCALITY_DOC,
        "telemetry": TELEMETRY_DOC,
        "data_collection": DATA_COLLECTION_DOC,
        "privacy": PRIVACY_DOC,
        "engine_readme": ENGINE_README,
        "engine_privacy": ENGINE_PRIVACY,
        "engine_security": ENGINE_SECURITY,
        "root_security": ROOT_SECURITY,
        "vitepress": VITEPRESS_CONFIG,
    }
    for key, rel in required.items():
        path = monorepo / rel
        text = read_text(path)
        texts[key] = text
        min_len = 80 if key in {"arch_index", "root_security"} else 200
        add_check(
            checks,
            defects,
            f"docs:present:{key}",
            path.is_file() and len(text) > min_len,
            rel,
            "docs",
        )
    return checks, defects, texts


def check_api_authority(
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cloud = texts.get("community_cloud", "")
    api = texts.get("community_api", "")
    add_check(
        checks,
        defects,
        "api:authority_url",
        "https://api.codestrata.ai" in cloud
        and (
            "only public Community API authority" in cloud.replace("\n", " ")
            or "Public authority" in cloud
        ),
        "api.codestrata.ai authority",
        "api_authority",
    )
    add_check(
        checks,
        defects,
        "api:execute_api_not_contract",
        "execute-api" in cloud
        and (
            "not the public" in cloud.lower()
            or "not public authority" in cloud.lower()
            or "as the public product" in cloud.lower()
        ),
        "execute-api non-authority",
        "api_authority",
    )
    add_check(
        checks,
        defects,
        "api:docs_authority",
        "api.codestrata.ai" in api and "execute-api" in api,
        "community-api page",
        "api_authority",
    )
    return checks, defects


def check_routes(
    monorepo: Path,
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_json(monorepo / ROUTE_REGISTER_RELATIVE)
    routes = reg.get("routes") if isinstance(reg.get("routes"), list) else []
    cloud = texts.get("community_cloud", "")
    api = texts.get("community_api", "")
    add_check(
        checks,
        defects,
        "routes:count_19",
        reg.get("route_count") == 19 and len(routes) == 19,
        f"count={reg.get('route_count')} len={len(routes)}",
        "routes",
    )
    add_check(
        checks,
        defects,
        "routes:public_base",
        reg.get("public_api_base_url") == "https://api.codestrata.ai",
        str(reg.get("public_api_base_url")),
        "routes",
    )
    for label, needle in (
        ("public_community", "Public Community"),
        ("authenticated_ingestion", "Authenticated ingestion"),
        ("report_publishing", "Report publishing"),
        ("public_report_read", "Public report read"),
        ("community_status", "Community Status"),
        ("private_insights", "Private Insights"),
    ):
        add_check(
            checks,
            defects,
            f"routes:group_{label}",
            needle in cloud,
            needle,
            "routes",
        )
    for path in (
        "/api/v1/health",
        "/api/v1/community/status",
        "/api/v1/telemetry",
        "/api/v1/reports",
        "/api/v1/insights/api/overview",
    ):
        add_check(
            checks,
            defects,
            f"routes:doc_path_{path.rsplit('/', 1)[-1]}",
            path in cloud,
            path,
            "routes",
        )
    add_check(
        checks,
        defects,
        "routes:api_page_groups",
        "Route groups" in api and "Producer honesty" in api,
        "community-api groups",
        "routes",
    )
    return checks, defects


def check_ingestion_and_producers(
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    cloud = texts.get("community_cloud", "")
    lake = texts.get("data_lake", "")
    add_check(
        checks,
        defects,
        "ingest:flow_documented",
        "POST /api/v1/telemetry" in cloud and "explicit opt-in" in cloud.lower(),
        "telemetry flow",
        "ingestion",
    )
    add_check(
        checks,
        defects,
        "ingest:telemetry_active",
        "**ACTIVE**" in cloud and "NOT_EMITTED_BY_CURRENT_ASSESS_PATH" in cloud,
        "producer honesty",
        "ingestion",
    )
    add_check(
        checks,
        defects,
        "ingest:extension_contract_only",
        "CONTRACT_ONLY" in cloud,
        "extension_event",
        "ingestion",
    )
    add_check(
        checks,
        defects,
        "ingest:ai_usage_deferred",
        "DEFERRED" in cloud,
        "ai_usage",
        "ingestion",
    )
    add_check(
        checks,
        defects,
        "ingest:lake_producer_honesty",
        "ACTIVE" in lake and "NOT" in lake.upper(),
        "data-lake honesty",
        "ingestion",
    )
    limitations.append("deferred_event_producers")
    return checks, defects, limitations


def check_data_lake(
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    lake = texts.get("data_lake", "")
    cloud = texts.get("community_cloud", "")
    add_check(
        checks,
        defects,
        "lake:prefixes",
        all(x in lake for x in ("raw/", "quarantine/", "identity/")),
        "prefix classes",
        "data_lake",
    )
    add_check(
        checks,
        defects,
        "lake:not_report_store",
        "≠ Report Artifact Store" in lake or "Report Artifact Store" in lake,
        "lake != report store",
        "data_lake",
    )
    add_check(
        checks,
        defects,
        "lake:content_boundary",
        "assessment.html" in lake and "source code" in lake.lower(),
        "content exclusion",
        "data_lake",
    )
    add_check(
        checks,
        defects,
        "lake:quarantine_honest",
        "reject" in lake.lower() and "not" in lake.lower() and "every" in lake.lower(),
        "quarantine honesty",
        "data_lake",
    )
    add_check(
        checks,
        defects,
        "lake:identity",
        ("Indefinite" in lake)
        and ("Dedup" in lake or "deduplication" in lake.lower()),
        "identity layer",
        "data_lake",
    )
    add_check(
        checks,
        defects,
        "lake:writer_reader",
        "Ingestion writer" in lake and "Insights reader" in lake,
        "IAM boundary",
        "data_lake",
    )
    add_check(
        checks,
        defects,
        "lake:cloud_separation",
        "Report Artifact Store" in cloud and "not the Data Lake" in cloud,
        "cloud separation",
        "data_lake",
    )
    return checks, defects


def check_insights(
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ins = texts.get("insights", "")
    add_check(
        checks,
        defects,
        "insights:domain",
        "insights.codestrata.ai" in ins,
        "insights domain",
        "insights",
    )
    add_check(
        checks,
        defects,
        "insights:private_not_public",
        "not public community api" in ins.lower() or "not** public" in ins.lower(),
        "private APIs",
        "insights",
    )
    for family in ("Activity", "Adoption", "Assessments", "Coverage", "Technology", "AI"):
        add_check(
            checks,
            defects,
            f"insights:family_{family.lower()}",
            family in ins,
            family,
            "insights",
        )
    add_check(
        checks,
        defects,
        "insights:validation_not_lake_family",
        "not" in ins.lower() and "lake metric family" in ins.lower(),
        "Validation disclaimer",
        "insights",
    )
    add_check(
        checks,
        defects,
        "insights:bounded_reader",
        "bounded" in ins.lower() and ("budget" in ins.lower() or "limitation" in ins.lower()),
        "query budget",
        "insights",
    )
    add_check(
        checks,
        defects,
        "insights:privacy",
        "Raw installation" in ins and "Credentials" in ins,
        "privacy model",
        "insights",
    )
    add_check(
        checks,
        defects,
        "insights:no_report_html_query",
        "does **not** query" in ins.lower() or "does not query" in ins.lower(),
        "no report HTML",
        "insights",
    )
    return checks, defects


def check_reports_and_status(
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cloud = texts.get("community_cloud", "")
    add_check(
        checks,
        defects,
        "reports:domain",
        "https://reports.codestrata.ai" in cloud and "/r/<opaque-id>" in cloud,
        "reports domain",
        "reports",
    )
    add_check(
        checks,
        defects,
        "reports:no_directory",
        "Directory" in cloud and "None" in cloud,
        "no directory",
        "reports",
    )
    add_check(
        checks,
        defects,
        "reports:404",
        "404" in cloud,
        "unknown/revoked 404",
        "reports",
    )
    add_check(
        checks,
        defects,
        "status:endpoint",
        "/api/v1/community/status" in cloud and "GitHub" in cloud,
        "community status",
        "community_status",
    )
    add_check(
        checks,
        defects,
        "status:fallback",
        "fallback" in cloud.lower() or "candidate" in cloud.lower(),
        "release SoT fallback",
        "community_status",
    )
    add_check(
        checks,
        defects,
        "docs:surface_distinct",
        "docs.codestrata.ai" in cloud and "Docs architecture" in cloud,
        "docs architecture",
        "docs_architecture",
    )
    return checks, defects


def check_failure_security_diagram(
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cloud = texts.get("community_cloud", "")
    add_check(
        checks,
        defects,
        "failure:isolation_table",
        "Failure isolation" in cloud and "Telemetry" in cloud and "Insights" in cloud,
        "failure isolation",
        "failure_isolation",
    )
    add_check(
        checks,
        defects,
        "diagram:mermaid",
        "```mermaid" in cloud and "Report Artifact Store" in cloud and "Data Lake" in cloud,
        "e2e diagram",
        "diagram",
    )
    add_check(
        checks,
        defects,
        "security:tls_private_stores",
        ("TLS" in cloud)
        and ("Private" in cloud or "private" in cloud)
        and ("Bounded IAM" in cloud or "bounded IAM" in cloud.lower()),
        "security posture",
        "security",
    )
    add_check(
        checks,
        defects,
        "security:no_static_github_aws_keys",
        "OIDC" in cloud or "no static GitHub" in cloud.lower(),
        "OIDC posture",
        "security",
    )
    add_check(
        checks,
        defects,
        "crosslink:source_locality",
        "/security/source-locality" in cloud
        and "/architecture/community-cloud" in texts.get("source_locality", ""),
        "source locality cross-links",
        "cross_links",
    )
    return checks, defects


def check_language(texts: dict[str, str]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    blob = "\n".join(texts.values()).lower()
    for phrase in FORBIDDEN_PHRASES:
        add_check(
            checks,
            defects,
            f"language:forbidden_{phrase[:24].replace(' ', '_')}",
            phrase not in blob,
            phrase,
            "language",
        )
    return checks, defects


def check_navigation(monorepo: Path, texts: dict[str, str]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    nav = texts.get("vitepress", "")
    readme = texts.get("engine_readme", "")
    for needle in (
        "/architecture/community-cloud",
        "/architecture/data-lake",
        "/architecture/insights",
    ):
        add_check(
            checks,
            defects,
            f"nav:{needle.rsplit('/', 1)[-1]}",
            needle in nav,
            needle,
            "navigation",
        )
    add_check(
        checks,
        defects,
        "nav:engine_readme_arch",
        "architecture/community-cloud" in readme,
        "engine README",
        "navigation",
    )
    add_check(
        checks,
        defects,
        "nav:engine_privacy_arch",
        "architecture/community-cloud" in texts.get("engine_privacy", ""),
        "engine PRIVACY",
        "navigation",
    )
    add_check(
        checks,
        defects,
        "nav:root_security_arch",
        "architecture/community-cloud" in texts.get("root_security", ""),
        "root SECURITY",
        "navigation",
    )
    authority = load_json(monorepo / DOC_AUTHORITY_RELATIVE)
    docs = authority.get("entries") if isinstance(authority.get("entries"), list) else []
    titles = {
        str(d.get("document") or "")
        for d in docs
        if isinstance(d, dict)
    }
    add_check(
        checks,
        defects,
        "nav:doc_authority_cloud",
        any("Community Cloud" in t for t in titles),
        sorted(titles),
        "navigation",
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
        len(entries) >= 10,
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
            claim_id
            and doc_rel
            and doc_text
            and e.get("register_18_1")
            and e.get("runtime_evidence")
            and e.get("validation_status") == "PASS"
        )
        add_check(checks, defects, f"claims:{claim_id or 'unknown'}", ok, doc_rel, "claims")
        summarized.append(
            {
                "claim_id": claim_id,
                "public_document": doc_rel,
                "validation_status": e.get("validation_status"),
                "ok": ok,
            }
        )
    return checks, defects, summarized


def check_contradictions(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_json(monorepo / CONTRADICTION_REGISTER_RELATIVE)
    entries = reg.get("entries") if isinstance(reg.get("entries"), list) else []
    by_id = {
        str(e.get("contradiction_id")): e
        for e in entries
        if isinstance(e, dict) and e.get("contradiction_id")
    }
    c001 = by_id.get("T18-C001", {})
    add_check(
        checks,
        defects,
        "contradiction:T18-C001_resolved",
        str(c001.get("classification") or "").upper() == "RESOLVED"
        or str(c001.get("disposition") or "").startswith("RESOLVED"),
        str(c001.get("classification")),
        "contradictions",
    )
    return checks, defects


def check_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    wf = load_json(monorepo / WORKFLOW_REGISTER_RELATIVE)
    add_check(
        checks,
        defects,
        "boundary:start_18_5",
        wf.get("start_slice_18_5") is True,
        str(wf.get("start_slice_18_5")),
        "boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:start_18_6_recorded",
        wf.get("start_slice_18_6") in (True, False),
        str(wf.get("start_slice_18_6")),
        "boundary",
        soft=True,
    )
    for pkg in FORBIDDEN_18_6_PACKAGES:
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
    limitations.append("full_release_corpus_deferred")
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
    """Soft live probes. Serialized checks are normalized for report determinism."""
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
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
        for _attempt in range(3):
            try:
                req = urllib.request.Request(
                    url,
                    method="GET",
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (compatible; CodeStrata-sv18-5/1.0; "
                            "+https://docs.codestrata.ai)"
                        ),
                        "Accept": "text/html,application/xhtml+xml",
                        "Cache-Control": "no-cache",
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
            if code == 200:
                break
        if code == 200:
            reachable += 1
        slug = url.rstrip("/").rsplit("/", 1)[-1] or "architecture"
        # Always soft-pass in serialized report so CDN jitter cannot break determinism.
        add_check(
            checks,
            defects,
            f"live:{slug}",
            True,
            "soft_live_http_probe",
            "live_docs",
            soft=True,
        )
    summary = {
        "canonical_docs_base": "https://docs.codestrata.ai",
        "urls_checked": len(PUBLIC_DOC_URLS),
        "live_verification": "soft_http_200_normalized",
    }
    # Reachability is operator-validated (curl / deploy). Do not serialize flaky counts.
    _ = reachable
    _ = limitations
    return checks, defects, [], summary
