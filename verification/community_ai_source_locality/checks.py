"""Checks for Slice 18.4 — AI Provider + Source-Locality Transparency."""

from __future__ import annotations

import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from verification.community_ai_source_locality.contract import (
    AI_FLOW_REGISTER_RELATIVE,
    AI_PROVIDERS_DOC,
    CLAIM_REGISTER_RELATIVE,
    CLI_DOC,
    COMMUNITY_API_DOC,
    DATA_COLLECTION_DOC,
    ENGINE_PRIVACY,
    FORBIDDEN_18_5_PACKAGES,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    PRIVACY_DOC,
    SOURCE_LOCALITY_DOC,
    SOURCE_LOCALITY_REGISTER_RELATIVE,
    TELEMETRY_DOC,
    VSCODE_DOC,
    VSCODE_PRIVACY,
    WORKFLOW_REGISTER_RELATIVE,
)
from verification.community_ai_source_locality.helpers import (
    add_check,
    load_json,
    read_text,
)
from verification.community_ai_source_locality.models import CheckResult, Defect

PUBLIC_DOC_URLS = (
    "https://docs.codestrata.ai/ai-providers/",
    "https://docs.codestrata.ai/security/source-locality",
    "https://docs.codestrata.ai/security/privacy",
    "https://docs.codestrata.ai/reference/telemetry",
    "https://docs.codestrata.ai/security/data-collection",
)

FORBIDDEN_PHRASES = (
    "nothing leaves your machine",
    "nothing leaves the machine",
    "all providers live-proven",
    "all three production-proven",
    "every ai request is recorded",
    "ai is required",
    "silent fallback",
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
        "source_locality": SOURCE_LOCALITY_DOC,
        "ai_providers": AI_PROVIDERS_DOC,
        "privacy": PRIVACY_DOC,
        "telemetry": TELEMETRY_DOC,
        "data_collection": DATA_COLLECTION_DOC,
        "community_api": COMMUNITY_API_DOC,
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


def check_source_locality(
    monorepo: Path,
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_json(monorepo / SOURCE_LOCALITY_REGISTER_RELATIVE)
    entries = reg.get("entries") if isinstance(reg.get("entries"), list) else []
    surfaces = {
        str(e.get("surface"))
        for e in entries
        if isinstance(e, dict) and e.get("surface")
    }
    sl = texts.get("source_locality", "")
    add_check(
        checks,
        defects,
        "locality:register_five_surfaces",
        surfaces
        >= {"Assessment", "Telemetry", "AI enrichment", "Report publishing", "Insights"},
        sorted(surfaces),
        "source_locality",
    )
    for name in (
        "Deterministic Assessment",
        "Telemetry",
        "AI enrichment",
        "Report publishing",
        "Insights",
    ):
        add_check(
            checks,
            defects,
            f"locality:matrix_row_{re.sub(r'[^a-z]+', '_', name.lower())}",
            name.split()[0] in sl or name in sl,
            name,
            "source_locality",
        )
    add_check(
        checks,
        defects,
        "locality:matrix_heading",
        "Source-locality matrix" in sl,
        "matrix",
        "source_locality",
    )
    add_check(
        checks,
        defects,
        "locality:three_paths",
        "Three independent outbound paths" in sl or "independent outbound" in sl.lower(),
        "three paths",
        "source_locality",
    )
    add_check(
        checks,
        defects,
        "locality:mermaid_diagrams",
        sl.count("```mermaid") >= 4,
        f"mermaid_blocks={sl.count('```mermaid')}",
        "source_locality",
    )
    add_check(
        checks,
        defects,
        "locality:no_absolute_nothing_leaves",
        "nothing leaves your machine" not in sl.lower()
        or "only true for" in sl.lower(),
        "qualified locality language",
        "source_locality",
    )
    add_check(
        checks,
        defects,
        "locality:evidence_clips_honest",
        "excerpt" in sl.lower() or "path/excerpt" in sl.lower(),
        "evidence clips",
        "source_locality",
    )
    return checks, defects


def check_ai_providers(
    monorepo: Path,
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    flow = load_json(monorepo / AI_FLOW_REGISTER_RELATIVE)
    by_prov = {
        str(e.get("provider")): e
        for e in (flow.get("entries") or [])
        if isinstance(e, dict) and e.get("provider")
    }
    ai = texts.get("ai_providers", "")
    add_check(
        checks,
        defects,
        "ai:optional_default_no_ai",
        "--no-ai" in ai and "optional" in ai.lower() and "default" in ai.lower(),
        "optional/default",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:what_sends_section",
        "What AI enrichment sends" in ai,
        "sends",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:not_sent_section",
        "What is not sent to AI providers" in ai,
        "not sent",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:full_tree_not_uploaded",
        "full repository source tree" in ai.lower() or "full repository source trees" in ai.lower(),
        "no full tree",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:excerpt_clips_disclosed",
        "excerpt" in ai.lower() and "clip" in ai.lower(),
        "clips disclosed",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:bedrock_live",
        (by_prov.get("bedrock") or {}).get("live_proven") is True
        and ("passed_live" in ai or "LIVE E2E" in ai or "live proven" in ai.lower()),
        "bedrock",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:openai_owner_prereq",
        (by_prov.get("openai") or {}).get("e2e_status") == "OWNER_CREDENTIAL_REQUIRED"
        and "OWNER_CREDENTIAL_REQUIRED" in ai,
        "openai",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:openrouter_owner_prereq",
        (by_prov.get("openrouter") or {}).get("e2e_status") == "OWNER_CREDENTIAL_REQUIRED"
        and "OWNER_CREDENTIAL_REQUIRED" in ai
        and "alias for openai" in ai.lower(),
        "openrouter distinct",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:no_cross_fallback",
        flow.get("cross_provider_fallback") is False
        and (
            "no silent cross-provider" in ai.lower()
            or "There is **no** silent cross-provider" in ai
        ),
        "fallback",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:single_attempt",
        "exactly one" in ai.lower() or "single attempt" in ai.lower() or "CR-1" in ai,
        "retry",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:timeout_wired",
        "timeout_seconds" in ai and "60" in ai,
        "timeout",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:fail_soft",
        "non-blocking" in ai.lower() or "fail-soft" in ai.lower(),
        "failure",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:deterministic_vs_ai",
        "Deterministic vs AI" in ai or "provider-independent" in ai.lower(),
        "boundary",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:prompts_not_telemetry",
        "not sent through CodeStrata Community telemetry" in ai
        or "not** mirrored into Community telemetry" in ai
        or "are not sent through CodeStrata" in ai,
        "prompts vs telemetry",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:usage_deferred",
        "deferred" in ai.lower() and "ai_usage" in ai,
        "ai_usage",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:eir_boundary",
        bool(
            re.search(
                r"does\s+\*\*not\*\*\s+use\s+AI-provider\s+enrichment",
                ai,
                re.IGNORECASE,
            )
        )
        or bool(
            re.search(
                r"does\s+not\s+use\s+AI-provider\s+enrichment",
                ai,
                re.IGNORECASE,
            )
        ),
        "EIR",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:retention_not_speculated",
        "does **not** invent" in ai or "does not invent provider retention" in ai.lower()
        or "does not invent" in ai.lower(),
        "retention",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:credentials_not_in_artifacts",
        "does **not** place provider credentials" in ai
        or "not** place provider credentials" in ai
        or "does not place provider credentials" in ai.lower(),
        "credentials",
        "ai",
    )
    # Runtime CR-1 evidence
    assess = read_text(monorepo / "engine/src/codestrata/cli/assess.py")
    add_check(
        checks,
        defects,
        "ai:cli_default_no_ai",
        "--no-ai" in assess and "--with-ai" in assess,
        "assess flags",
        "ai",
    )
    limitations.append("openai_owner_credential_required")
    limitations.append("openrouter_owner_credential_required")
    limitations.append("third_party_ai_retention_governed_externally")
    limitations.append("vscode_provider_selection_ui_deferred")
    return checks, defects, limitations


def check_api_cli_vscode(texts: dict[str, str]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    api = texts.get("community_api", "")
    cli = texts.get("cli", "")
    vscode = texts.get("vscode", "")
    vscode_priv = texts.get("vscode_privacy", "")
    engine = texts.get("engine_privacy", "")
    priv = texts.get("privacy", "")
    add_check(
        checks,
        defects,
        "api:not_proxy",
        "Not an AI proxy" in api or "not** an AI proxy" in api or "not an AI proxy" in api.lower(),
        "ai_usage non-proxy",
        "api",
    )
    add_check(
        checks,
        defects,
        "cli:no_ai_with_ai",
        "--no-ai" in cli and "--with-ai" in cli and "default" in cli.lower(),
        "cli flags",
        "cli",
    )
    add_check(
        checks,
        defects,
        "cli:openrouter_mentioned",
        "OpenRouter" in cli or "openrouter" in cli,
        "openrouter",
        "cli",
    )
    add_check(
        checks,
        defects,
        "vscode:no_invented_provider_ui",
        "no** separate VS Code provider-selection" in vscode.lower()
        or "no separate VS Code provider-selection" in vscode.lower()
        or "There is **no** separate VS Code provider-selection" in vscode,
        "vscode UI honesty",
        "vscode",
    )
    add_check(
        checks,
        defects,
        "github:engine_source_locality",
        "source-locality" in engine and "ai-providers" in engine,
        "engine PRIVACY",
        "github",
    )
    add_check(
        checks,
        defects,
        "github:vscode_source_locality",
        "source-locality" in vscode_priv and "ai-providers" in vscode_priv,
        "vscode PRIVACY",
        "github",
    )
    add_check(
        checks,
        defects,
        "privacy:cross_links",
        "/security/source-locality" in priv and "/ai-providers/" in priv,
        "privacy links",
        "privacy",
    )
    return checks, defects


def check_language(texts: dict[str, str]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ai = texts.get("ai_providers", "")
    # Affirmative forbidden claims must not appear without negation nearby.
    affirmative_forbidden = (
        ("nothing leaves your machine", r"(?i)(?<!not )(?<!never )nothing leaves your machine"),
        ("all providers live-proven", r"(?i)all (three )?providers (are )?live-proven"),
        ("all three production-proven", r"(?i)all three production-proven"),
        ("every ai request is recorded", r"(?i)every ai request is recorded"),
        ("ai is required", r"(?i)(?<!not )ai is required"),
    )
    for name, pattern in affirmative_forbidden:
        add_check(
            checks,
            defects,
            f"language:forbid_{re.sub(r'[^a-z0-9]+', '_', name)[:48]}",
            re.search(pattern, ai) is None,
            name,
            "language",
        )
    # "silent fallback" is allowed only as an explicit negation.
    silent_ok = (
        "silent fallback" not in ai.lower()
        or "no silent fallback" in ai.lower()
        or "no** silent" in ai.lower()
        or "**no** silent" in ai.lower()
    )
    add_check(
        checks,
        defects,
        "language:forbid_silent_fallback",
        silent_ok,
        "silent fallback",
        "language",
    )
    return checks, defects


def check_navigation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cfg = read_text(monorepo / "docs/.vitepress/config.ts")
    for link in (
        "/ai-providers/",
        "/security/source-locality",
        "/security/privacy",
        "/reference/telemetry",
        "/security/data-collection",
        "/security/retention-and-deletion",
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


def check_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    wf = load_json(monorepo / WORKFLOW_REGISTER_RELATIVE)
    add_check(
        checks,
        defects,
        "boundary:start_18_4",
        wf.get("start_slice_18_4") is True,
        str(wf.get("start_slice_18_4")),
        "boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:start_18_5_recorded",
        wf.get("start_slice_18_5") in (True, False),
        str(wf.get("start_slice_18_5")),
        "boundary",
        soft=True,
    )
    for pkg in FORBIDDEN_18_5_PACKAGES:
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
                        "Mozilla/5.0 (compatible; CodeStrata-sv18-4/1.0; "
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
            f"live:{url.rstrip('/').rsplit('/', 1)[-1]}",
            ok,
            f"http={code}",
            "live_docs",
            soft=True,
        )
    if reachable < len(PUBLIC_DOC_URLS):
        limitations.append("live_docs_unreachable")
    return checks, defects, limitations, results
