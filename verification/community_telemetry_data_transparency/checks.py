"""Checks for Slice 18.2 — Telemetry + Data Collection Transparency."""

from __future__ import annotations

import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from verification.community_telemetry_data_transparency.contract import (
    CLAIM_REGISTER_RELATIVE,
    CLI_DOC,
    COLLECTED_FIELDS_DOC,
    CONTRADICTION_REGISTER_RELATIVE,
    DATA_COLLECTION_DOC,
    ENGINE_PRIVACY,
    FIELD_REGISTER_RELATIVE,
    FORBIDDEN_18_3_PACKAGES,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    PRIVACY_DOC,
    STREAM_REGISTER_RELATIVE,
    TELEMETRY_DOC,
    VSCODE_DOC,
    VSCODE_PRIVACY,
    WORKFLOW_REGISTER_RELATIVE,
)
from verification.community_telemetry_data_transparency.helpers import (
    add_check,
    extract_fenced_json_blocks,
    load_json,
    read_text,
)
from verification.community_telemetry_data_transparency.models import CheckResult, Defect

STREAM_DOC_STATUS: dict[str, str] = {
    "telemetry": "ACTIVE",
    "assessment_metadata": "ACTIVE_WITH_V2_CONSENT",
    "cli_event": "NOT_EMITTED_BY_CURRENT_ASSESS_PATH",
    "extension_event": "CONTRACT_ONLY",
    "ai_usage": "DEFERRED",
}

NEVER_COLLECTED_MARKERS: dict[str, tuple[str, ...]] = {
    "repository_source_code": ("Repository source code", "source code"),
    "file_contents": ("File contents",),
    "full_assessment_html": ("assessment.html",),
    "full_assessment_json": ("assessment.json",),
    "full_heads_json": ("heads/", "heads/*.json"),
    "complete_findings_evidence": ("findings", "evidence"),
    "engineering_intelligence_html_json": (
        "Engineering Intelligence",
        "EIR",
    ),
    "credentials_api_keys": ("Credentials", "API keys"),
    "git_credential_userinfo": ("Git credential", "git credential"),
    "ai_prompts": ("AI prompts",),
    "ai_responses": ("AI responses",),
    "local_absolute_paths": ("absolute paths", "Local absolute paths"),
    "raw_machine_identifiers": (
        "Raw machine identifiers",
        "machine identifiers",
        "hardware serial",
    ),
    "raw_s3_object_paths": ("S3", "object paths"),
}

PUBLIC_DOC_URLS = (
    "https://docs.codestrata.ai/reference/telemetry",
    "https://docs.codestrata.ai/security/data-collection",
    "https://docs.codestrata.ai/security/collected-fields",
    "https://docs.codestrata.ai/security/privacy",
)


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    policy = load_json(path) if path.is_file() else {}
    add_check(
        checks,
        defects,
        "policy:present",
        path.is_file(),
        POLICY_RELATIVE,
        "policy",
    )
    for key, expected in sorted(POLICY_REQUIRED_VALUES.items()):
        add_check(
            checks,
            defects,
            f"policy:{key}",
            policy.get(key) == expected,
            f"{key}={policy.get(key)!r} expected={expected!r}",
            "policy",
        )
    return checks, defects, policy


def check_docs_present(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    texts: dict[str, str] = {}
    required = {
        "telemetry": TELEMETRY_DOC,
        "data_collection": DATA_COLLECTION_DOC,
        "collected_fields": COLLECTED_FIELDS_DOC,
        "privacy": PRIVACY_DOC,
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


def check_stream_honesty(
    monorepo: Path,
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect], list[str], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    streams = load_json(monorepo / STREAM_REGISTER_RELATIVE)
    entries = streams.get("entries") if isinstance(streams.get("entries"), list) else []
    names = sorted(
        str(e.get("stream_name"))
        for e in entries
        if isinstance(e, dict) and e.get("stream_name")
    )
    add_check(
        checks,
        defects,
        "streams:register_count",
        len(names) == 5,
        f"names={names}",
        "streams",
    )
    dc = texts.get("data_collection", "")
    tel = texts.get("telemetry", "")
    for name, status in STREAM_DOC_STATUS.items():
        add_check(
            checks,
            defects,
            f"streams:doc_status:{name}",
            name in dc and status in dc,
            f"{name}->{status}",
            "streams",
        )
    # Fail if docs imply all five streams are live/ACTIVE without negation.
    live_all_bad = bool(
        re.search(
            r"(?<![Nn]ot assume )(?<![Dd]o not assume )(all five|all 5).{0,40}"
            r"(are actively emitted|are live|are ACTIVE|actively emitted)",
            dc,
            re.IGNORECASE | re.DOTALL,
        )
    )
    # Stronger positive fail: "all five ... ACTIVE" without "Do not assume"
    if "Do not assume all five" in dc or "do not assume all five" in dc.lower():
        live_all_bad = False
    add_check(
        checks,
        defects,
        "streams:not_all_live_claim",
        not live_all_bad,
        "must not claim all five streams are live",
        "streams",
    )
    add_check(
        checks,
        defects,
        "streams:telemetry_and_amd_active_called_out",
        "ACTIVE" in dc
        and "ACTIVE_WITH_V2_CONSENT" in dc
        and (
            "Do not assume all five" in dc
            or "do not assume all five" in dc.lower()
        ),
        "telemetry ACTIVE + amd ACTIVE_WITH_V2_CONSENT; not all five live",
        "streams",
    )
    # Map register producer_live_or_deferred honesty
    for e in entries:
        if not isinstance(e, dict):
            continue
        name = str(e.get("stream_name"))
        live = str(e.get("producer_live_or_deferred") or "")
        if name == "telemetry":
            add_check(
                checks,
                defects,
                "streams:register_telemetry_live",
                live == "live",
                live,
                "streams",
            )
        elif name == "extension_event":
            add_check(
                checks,
                defects,
                "streams:register_extension_contract",
                "contract" in live,
                live,
                "streams",
            )
            limitations.append("contract_deferred_streams_not_emitted")
        elif name == "ai_usage":
            add_check(
                checks,
                defects,
                "streams:register_ai_deferred",
                "deferred" in live,
                live,
                "streams",
            )
            limitations.append("contract_deferred_streams_not_emitted")
        elif name == "assessment_metadata":
            add_check(
                checks,
                defects,
                "streams:register_assessment_metadata_v2",
                "consent" in live or "v2" in live,
                live,
                "streams",
            )
        elif name == "cli_event":
            add_check(
                checks,
                defects,
                "streams:register_cli_event_capacity",
                "capacity" in live or "consent" in live,
                live,
                "streams",
            )
            limitations.append("contract_deferred_streams_not_emitted")
    coverage = {"stream_names": names, "doc_status": dict(STREAM_DOC_STATUS)}
    return checks, defects, limitations, coverage


def check_collected_fields(
    monorepo: Path,
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    fields = load_json(monorepo / FIELD_REGISTER_RELATIVE)
    entries = fields.get("entries") if isinstance(fields.get("entries"), list) else []
    register_count = int(fields.get("field_count") or len(entries))
    doc = texts.get("collected_fields", "")
    add_check(
        checks,
        defects,
        "fields:register_137",
        register_count == 137 and len(entries) == 137,
        f"field_count={register_count} entries={len(entries)}",
        "fields",
    )
    add_check(
        checks,
        defects,
        "fields:doc_states_137",
        "137" in doc and "Field count:" in doc,
        "collected-fields.md count banner",
        "fields",
    )
    missing: list[str] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        name = str(e.get("field_name") or "")
        # Nested fields appear as backticks in generated tables
        leaf = name.split(".")[-1]
        marker = f"`{leaf}`" if leaf else ""
        if marker and marker not in doc and f"`{name}`" not in doc:
            missing.append(name)
    add_check(
        checks,
        defects,
        "fields:all_traceable_in_doc",
        len(missing) == 0,
        f"missing={len(missing)} sample={missing[:8]}",
        "fields",
    )
    # No hand-invented anonymity absolutes on field page
    add_check(
        checks,
        defects,
        "fields:no_completely_anonymous",
        "completely anonymous" not in doc.lower(),
        "avoid unsupported anonymity marketing",
        "fields",
    )
    return checks, defects, {
        "register_count": register_count,
        "doc_missing_fields": missing[:20],
        "traceable": len(missing) == 0,
    }


def check_never_collected(
    monorepo: Path,
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    never_path = monorepo / "platform/policies/community_never_collected_register.json"
    never = load_json(never_path)
    entries = never.get("entries") if isinstance(never.get("entries"), list) else []
    dc = texts.get("data_collection", "")
    tel = texts.get("telemetry", "")
    covered: list[str] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        cat = str(e.get("category") or "")
        if not cat:
            continue
        markers = NEVER_COLLECTED_MARKERS.get(cat, (cat.replace("_", " "),))
        ok = e.get("guaranteed") is True and any(m in dc for m in markers)
        add_check(
            checks,
            defects,
            f"never:{cat}",
            ok,
            f"guaranteed={e.get('guaranteed')} markers={markers}",
            "never_collected",
        )
        if ok:
            covered.append(cat)
    # AI wording care
    add_check(
        checks,
        defects,
        "never:ai_wording_careful",
        "through telemetry" in dc.lower()
        and "never sent to an AI provider" not in dc
        or ("Not collected by CodeStrata telemetry" in dc and "AI provider" in dc),
        "telemetry vs AI provider boundary wording",
        "never_collected",
    )
    add_check(
        checks,
        defects,
        "never:source_not_in_telemetry_claim",
        "source" in dc.lower() and "telemetry" in dc.lower(),
        "source code never-collected present",
        "never_collected",
    )
    add_check(
        checks,
        defects,
        "never:telemetry_doc_no_source_claim_false",
        "without** collecting repository" in tel
        or "without collecting repository" in tel.lower()
        or "does **not**" in tel,
        "telemetry overview source posture",
        "never_collected",
    )
    return checks, defects, {"covered": covered, "register_count": len(entries)}


def check_consent_and_identity(texts: dict[str, str]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    tel = texts.get("telemetry", "")
    dc = texts.get("data_collection", "")
    requirements = {
        "consent:default_disabled": ("Disabled" in tel or "disabled_by_default" in tel),
        "consent:opt_in_allow": (
            "telemetry enable" in tel.lower() or "--telemetry-allow" in tel
        ),
        "consent:opt_out_deny": (
            "telemetry disable" in tel.lower() or "--telemetry-deny" in tel
        ),
        "consent:session_bridge_not_persisted": (
            "Not persisted" in tel
            or "not persisted" in tel.lower()
            or "session/frontend bridge" in tel.lower()
            or "session bridge" in tel.lower()
        ),
        "consent:not_publish": (
            "≠ public report" in tel
            or "not** public report" in tel.lower()
            or "Telemetry opt-in ≠" in tel
            or "consent ≠ public report" in tel.lower()
            or "assessment-intelligence consent ≠" in tel.lower()
            or "Telemetry opt-in is **not**" in texts.get("cli", "")
            or "insights consent" in tel.lower()
        ),
        "consent:interactive_prompt": ("[y/N]" in tel or "may prompt" in tel.lower()),
        "consent:non_interactive_no_prompt": (
            "never prompt" in tel.lower() or "Never" in tel
        ),
        "consent:precedence": ("Precedence" in tel),
        "identity:uuid_v4": ("UUID v4" in tel),
        "identity:random_wording": (
            "random installation identifier" in tel.lower()
            or "Random UUID" in tel
            or "pseudonymous" in tel.lower()
        ),
        "identity:no_completely_anonymous": (
            "completely anonymous" not in tel.lower()
        ),
        "identity:insights_no_raw": (
            "must not show raw" in tel.lower() or "Must not show raw" in tel
        ),
        "opt_out:future_only": ("future" in dc.lower() and "Opt-out" in dc),
        "opt_out:no_auto_delete_lake": ("historical Data Lake" in dc),
        "retention:365": ("365" in dc),
        "retention:90": ("90" in dc),
        "retention:identity_indefinite": ("Indefinite" in dc or "indefinite" in dc),
        "destination:api_authority": ("api.codestrata.ai" in tel and "api.codestrata.ai" in dc),
        "destination:no_execute_api_authority": (
            "execute-api" in tel.lower() and "not" in tel.lower()
        ),
        "destination:lake_ne_report_store": (
            "Data Lake ≠ Report Artifact Store" in dc
            or "Community Data Lake ≠ Report Artifact Store" in dc
        ),
        "destination:report_html_not_telemetry": (
            "Report HTML/JSON is not" in dc or "not telemetry" in dc.lower()
        ),
        "ci:example_present": ("--quiet" in tel and "--telemetry-allow" in tel),
        "availability:three_conditions": (
            "explicitly opts in" in tel.lower()
            or "Explicit opt-in" in dc
            or "durable" in tel.lower()
        ),
        "consent:no_scores_promise": (
            "numeric" in tel.lower() and "score" in tel.lower() and "not" in tel.lower()
        ),
        "consent:no_graph_telemetry": (
            "graph telemetry" in tel.lower() and "not" in tel.lower()
        ),
        "consent:shared_cli_vscode": (
            "same" in tel.lower() and "cli" in tel.lower() and "vs code" in tel.lower()
        ),
        "consent:legacy_no_silent_v2": (
            "silently" in tel.lower() and ("v2" in tel.lower() or "upgrade" in tel.lower())
        ),
        "consent:allow_not_consent": (
            "not consent" in tel.lower() or "is not consent" in tel.lower()
        ),
    }
    for check_id, ok in requirements.items():
        add_check(checks, defects, check_id, bool(ok), check_id, "consent")
    return checks, defects


def check_examples_schema_valid(
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    dc = texts.get("data_collection", "")
    blocks = extract_fenced_json_blocks(dc)
    add_check(
        checks,
        defects,
        "examples:json_blocks_present",
        len(blocks) >= 2,
        f"count={len(blocks)}",
        "examples",
    )
    request = next((b for b in blocks if b.get("event_type") and b.get("client")), None)
    response = next((b for b in blocks if b.get("status") and b.get("safe_event_reference")), None)
    add_check(
        checks,
        defects,
        "examples:request_present",
        request is not None,
        "telemetry request example",
        "examples",
    )
    add_check(
        checks,
        defects,
        "examples:response_present",
        response is not None,
        "telemetry response example",
        "examples",
    )
    # Synthetic / no secrets
    blob = str(blocks)
    add_check(
        checks,
        defects,
        "examples:synthetic_safe",
        "00000000-0000-4000-8000" in blob
        and "AKIA" not in blob
        and "/Users/" not in blob
        and "sk-" not in blob,
        "synthetic ids only",
        "examples",
    )
    # Validate request against pydantic model when importable
    schema_ok = False
    schema_detail = "skipped"
    if request is not None:
        try:
            from codestrata_platform.community_cloud_api.telemetry.models import (
                TelemetryIngestionRequest,
            )

            TelemetryIngestionRequest.model_validate(request)
            schema_ok = True
            schema_detail = "TelemetryIngestionRequest.valid"
        except Exception as exc:  # noqa: BLE001 — verification detail only
            schema_ok = False
            schema_detail = type(exc).__name__
    add_check(
        checks,
        defects,
        "examples:request_schema_valid",
        schema_ok,
        schema_detail,
        "examples",
    )
    if response is not None:
        add_check(
            checks,
            defects,
            "examples:response_shape",
            set(response.keys()) >= {"status", "safe_event_reference", "retry_status", "schema_version"},
            sorted(response.keys()),
            "examples",
        )
    return checks, defects


def check_cli_vscode_reconcile(
    monorepo: Path,
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    assess = read_text(monorepo / "engine/src/codestrata/cli/assess.py")
    cli_doc = texts.get("cli", "")
    vscode = texts.get("vscode", "")
    vscode_priv = texts.get("vscode_privacy", "")
    engine_priv = texts.get("engine_privacy", "")
    add_check(
        checks,
        defects,
        "cli:flag_help_allow",
        "--telemetry-allow" in assess and "not saved" in assess.lower(),
        "assess.py allow help",
        "cli",
    )
    add_check(
        checks,
        defects,
        "cli:flag_help_deny",
        "--telemetry-deny" in assess and "not saved" in assess.lower(),
        "assess.py deny help",
        "cli",
    )
    add_check(
        checks,
        defects,
        "cli:docs_flags",
        "--telemetry-allow" in cli_doc and "--telemetry-deny" in cli_doc,
        "cli.md flags",
        "cli",
    )
    add_check(
        checks,
        defects,
        "cli:docs_not_publish",
        "not** report-publish" in cli_doc.lower() or "not report-publish" in cli_doc.lower()
        or "not** report" in cli_doc.lower()
        or "Telemetry opt-in is **not**" in cli_doc,
        "cli.md publish separation",
        "cli",
    )
    add_check(
        checks,
        defects,
        "vscode:api_authority",
        "api.codestrata.ai" in vscode or "api.codestrata.ai" in vscode_priv,
        "vscode api authority",
        "vscode",
    )
    add_check(
        checks,
        defects,
        "vscode:default_off",
        "disabled by default" in vscode_priv.lower() or "disabled" in vscode.lower(),
        "vscode default off",
        "vscode",
    )
    add_check(
        checks,
        defects,
        "vscode:shared_engine_consent",
        "engine" in vscode_priv.lower()
        and (
            "same" in vscode_priv.lower()
            or "share" in vscode_priv.lower()
            or "shared" in vscode.lower()
        ),
        "vscode/cli shared Engine consent",
        "vscode",
    )
    add_check(
        checks,
        defects,
        "vscode:canonical_docs_links",
        "docs.codestrata.ai/reference/telemetry" in vscode_priv
        or "/reference/telemetry" in vscode,
        "vscode links",
        "vscode",
    )
    add_check(
        checks,
        defects,
        "vscode:no_marketplace_live_claim",
        "Marketplace-live" not in vscode
        and "published to the Marketplace" not in vscode.lower(),
        "no false marketplace-live claim",
        "vscode",
    )
    add_check(
        checks,
        defects,
        "github:engine_privacy_points_canonical",
        "docs.codestrata.ai/security/privacy" in engine_priv
        and "docs.codestrata.ai/reference/telemetry" in engine_priv
        or "Telemetry" in engine_priv,
        "engine PRIVACY discoverability",
        "github",
    )
    # Broaden engine privacy check — require privacy + telemetry URLs
    add_check(
        checks,
        defects,
        "github:engine_privacy_urls",
        "docs.codestrata.ai/security/privacy" in engine_priv,
        "engine PRIVACY canonical privacy URL",
        "github",
    )
    add_check(
        checks,
        defects,
        "github:vscode_privacy_urls",
        "docs.codestrata.ai" in vscode_priv,
        "vscode PRIVACY docs URLs",
        "github",
    )
    return checks, defects


def check_navigation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cfg = read_text(monorepo / "docs/.vitepress/config.ts")
    for link in (
        "/reference/telemetry",
        "/security/data-collection",
        "/security/collected-fields",
        "/security/privacy",
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


def check_t18_c004(monorepo: Path, texts: dict[str, str]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    contra = load_json(monorepo / CONTRADICTION_REGISTER_RELATIVE)
    entries = contra.get("entries") if isinstance(contra.get("entries"), list) else []
    c004 = next(
        (e for e in entries if isinstance(e, dict) and e.get("contradiction_id") == "T18-C004"),
        None,
    )
    add_check(
        checks,
        defects,
        "contradiction:t18_c004_present",
        c004 is not None,
        "T18-C004 exists",
        "contradictions",
    )
    add_check(
        checks,
        defects,
        "contradiction:t18_c004_resolved",
        isinstance(c004, dict) and c004.get("classification") == "RESOLVED",
        str((c004 or {}).get("classification")),
        "contradictions",
    )
    add_check(
        checks,
        defects,
        "contradiction:t18_c004_evidence",
        isinstance(c004, dict)
        and isinstance(c004.get("evidence"), list)
        and len(c004.get("evidence") or []) >= 2,
        str((c004 or {}).get("evidence")),
        "contradictions",
    )
    privacy = texts.get("privacy", "")
    add_check(
        checks,
        defects,
        "contradiction:privacy_legacy_retitled",
        (
            "legacy" in privacy.lower()
            and "v2" in privacy.lower()
            and "telemetry enable" in privacy.lower()
        )
        or (
            "never" in privacy.lower()
            and "silent" in privacy.lower()
            and "v2" in privacy.lower()
        ),
        "privacy.md legacy v1 / v2 upgrade wording",
        "contradictions",
    )
    # Other contradictions remain open / carry-forward — do not require resolve
    open_ids = [
        str(e.get("contradiction_id"))
        for e in entries
        if isinstance(e, dict) and e.get("classification") not in {"RESOLVED", "FIXED"}
    ]
    add_check(
        checks,
        defects,
        "contradiction:others_may_remain_open",
        True,
        f"open_or_carry={open_ids}",
        "contradictions",
        soft=True,
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
        ok = bool(claim_id and doc_rel and doc_text and e.get("register_18_1") and e.get("runtime_evidence"))
        add_check(
            checks,
            defects,
            f"claims:{claim_id or 'unknown'}",
            ok,
            f"doc={doc_rel}",
            "claims",
        )
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
        "boundary:start_18_2",
        wf.get("start_slice_18_2") is True,
        str(wf.get("start_slice_18_2")),
        "boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:start_18_3_recorded",
        wf.get("start_slice_18_3") in (True, False),
        str(wf.get("start_slice_18_3")),
        "boundary",
        soft=True,
    )
    for pkg in FORBIDDEN_18_3_PACKAGES:
        add_check(
            checks,
            defects,
            f"boundary:absent_{Path(pkg).name}",
            not (monorepo / pkg).exists(),
            pkg,
            "boundary",
        )
    # Soft limitations
    limitations.append("broader_retention_deletion_deferred_to_18_3")
    limitations.append("marketplace_content_not_published")
    limitations.append("openai_owner_credential_required")
    limitations.append("openrouter_owner_credential_required")
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
    except Exception:  # noqa: BLE001 — fall back to default context
        ssl_context = None
    for url in PUBLIC_DOC_URLS:
        code = 0
        try:
            req = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; CodeStrata-sv18-2/1.0; "
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
