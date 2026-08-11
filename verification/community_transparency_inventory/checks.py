"""Checks for Slice 18.1 Community Transparency Inventory."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from verification.community_transparency_inventory.contract import (
    CONTRACT_RELATIVE,
    FORBIDDEN_18_2_PACKAGES,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    REQUIRED_PUBLIC_OR_AUTH_PATHS,
    REQUIRED_REGISTERS,
    REQUIRED_STREAMS,
    WORKFLOW_REGISTER_RELATIVE,
)
from verification.community_transparency_inventory.derive import (
    derive_runtime_fields,
    derive_runtime_routes,
)
from verification.community_transparency_inventory.helpers import add_check, load_json
from verification.community_transparency_inventory.models import CheckResult, Defect


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
            add_check(
                checks,
                defects,
                f"policy:{key}",
                policy.get(key) == expected,
                f"{key}={policy.get(key)}",
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


def check_registers_present(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    loaded: dict[str, dict[str, Any]] = {}
    for key, rel in sorted(REQUIRED_REGISTERS.items()):
        path = monorepo / rel
        ok = path.is_file()
        add_check(checks, defects, f"register:{key}:exists", ok, rel, "registers")
        if ok:
            loaded[key] = load_json(path)
    return checks, defects, loaded


def check_runtime_field_coverage(
    monorepo: Path,
    field_register: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    derived = derive_runtime_fields()
    inventory = field_register.get("entries") if isinstance(field_register.get("entries"), list) else []
    inv_keys = {
        (e.get("api_route") or e.get("api"), e.get("field_name"))
        for e in inventory
        if isinstance(e, dict)
    }
    missing = []
    for d in derived:
        key = (d.get("api"), d.get("field_name"))
        # inventory uses api_route
        if key not in inv_keys and (d.get("api"), d.get("field_name")) not in {
            (e.get("api_route"), e.get("field_name")) for e in inventory if isinstance(e, dict)
        }:
            missing.append(f"{d.get('api')}::{d.get('field_name')}")
    add_check(
        checks,
        defects,
        "fields:runtime_coverage",
        not missing,
        f"missing={missing[:8]} derived={len(derived)} inventory={len(inventory)}",
        "fields",
    )
    add_check(
        checks,
        defects,
        "fields:authority_runtime",
        field_register.get("authority") == "runtime_pydantic_models",
        str(field_register.get("authority")),
        "fields",
    )
    # no invented empty inventory
    add_check(
        checks,
        defects,
        "fields:non_empty",
        len(inventory) >= len(derived),
        f"inventory={len(inventory)} derived={len(derived)}",
        "fields",
    )
    return checks, defects, {"derived": len(derived), "inventory": len(inventory), "missing": missing[:20]}


def check_runtime_route_coverage(
    monorepo: Path,
    api_register: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    derived = derive_runtime_routes()
    entries = api_register.get("entries") if isinstance(api_register.get("entries"), list) else []
    inv_paths = {(e.get("method"), e.get("path")) for e in entries if isinstance(e, dict)}
    missing = [
        f"{d['method']} {d['path']}"
        for d in derived
        if (d["method"], d["path"]) not in inv_paths
    ]
    add_check(
        checks,
        defects,
        "api:runtime_route_coverage",
        not missing,
        f"missing={missing[:8]}",
        "api",
    )
    for path in REQUIRED_PUBLIC_OR_AUTH_PATHS:
        present = any(e.get("path") == path or str(e.get("path", "")).startswith(path) for e in entries)
        # reports GET/DELETE use path params
        if path == "/api/v1/reports":
            present = any(
                e.get("path") in {path, "/api/v1/reports/{public_id}"}
                or str(e.get("path", "")).startswith("/api/v1/reports")
                for e in entries
            )
        add_check(
            checks,
            defects,
            f"api:required_path:{path}",
            present,
            path,
            "api",
        )
    # Insights must be marked private, not public community
    insights = [e for e in entries if isinstance(e, dict) and "/insights/" in str(e.get("path", ""))]
    add_check(
        checks,
        defects,
        "api:insights_private",
        all(e.get("private_insights_api") is True or e.get("classification") == "PRIVATE_INSIGHTS" for e in insights)
        and bool(insights),
        f"count={len(insights)}",
        "api",
    )
    # stale 17.14 route register noted
    old = monorepo / "platform/policies/community_api_route_register.json"
    if old.is_file():
        old_doc = load_json(old)
        old_paths = {r.get("public_path") for r in (old_doc.get("routes") or [])}
        if "/api/v1/reports" not in old_paths or "/api/v1/community/status" not in old_paths:
            limitations.append("api_route_register_stale_vs_runtime")
            add_check(
                checks,
                defects,
                "api:legacy_register_stale_noted",
                True,
                "T18-C001",
                "api",
                soft=True,
            )
    return checks, defects, {"derived": len(derived), "inventory": len(entries)}, limitations


def check_streams(
    stream_register: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    entries = stream_register.get("entries") if isinstance(stream_register.get("entries"), list) else []
    names = {e.get("stream_name") for e in entries if isinstance(e, dict)}
    for stream in REQUIRED_STREAMS:
        add_check(
            checks,
            defects,
            f"streams:{stream}",
            stream in names,
            stream,
            "streams",
        )
    for e in entries:
        if not isinstance(e, dict):
            continue
        status = str(e.get("producer_live_or_deferred") or "")
        # contract-only must not be labeled live
        if e.get("stream_name") == "extension_event":
            ok = "contract_only" in status or "deferred" in status
            add_check(
                checks,
                defects,
                "streams:extension_event_not_false_live",
                ok,
                status,
                "streams",
            )
            limitations.append("extension_event_contract_only")
        if e.get("stream_name") == "ai_usage":
            ok = "deferred" in status or "construction" in status
            add_check(
                checks,
                defects,
                "streams:ai_usage_not_false_live_assess",
                ok,
                status,
                "streams",
            )
            limitations.append("ai_usage_assess_path_deferred")
        if e.get("stream_name") == "telemetry":
            add_check(
                checks,
                defects,
                "streams:telemetry_live_after_opt_in",
                status == "live" or "live" in status,
                status,
                "streams",
            )
    return checks, defects, limitations


def check_never_collected(
    never_reg: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    entries = never_reg.get("entries") if isinstance(never_reg.get("entries"), list) else []
    required = {
        "repository_source_code",
        "file_contents",
        "full_assessment_html",
        "full_assessment_json",
        "full_heads_json",
        "complete_findings_evidence",
        "engineering_intelligence_html_json",
        "local_absolute_paths",
        "credentials_api_keys",
        "git_credential_userinfo",
        "ai_prompts",
        "ai_responses",
        "raw_machine_identifiers",
        "raw_s3_object_paths",
    }
    cats = {e.get("category") for e in entries if isinstance(e, dict)}
    missing = sorted(required - cats)
    add_check(
        checks,
        defects,
        "never_collected:categories",
        not missing,
        f"missing={missing}",
        "never_collected",
    )
    add_check(
        checks,
        defects,
        "never_collected:all_guaranteed_have_basis",
        all(isinstance(e, dict) and e.get("runtime_basis") and e.get("guaranteed") is True for e in entries),
        "runtime_basis",
        "never_collected",
    )
    return checks, defects


def check_consent_and_identity(
    consent: dict[str, Any],
    identity: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "consent:default_off",
        consent.get("default_posture") == "disabled_by_default",
        str(consent.get("default_posture")),
        "consent",
    )
    add_check(
        checks,
        defects,
        "consent:publish_not_equal_telemetry",
        consent.get("telemetry_opt_in_equals_report_publication") is False,
        "false",
        "consent",
    )
    add_check(
        checks,
        defects,
        "identity:uuid_v4",
        identity.get("identifier_type") == "random_uuid_v4",
        str(identity.get("identifier_type")),
        "identity",
    )
    add_check(
        checks,
        defects,
        "identity:not_reversible",
        identity.get("reversible_to_user_or_machine") is False,
        "false",
        "identity",
    )
    add_check(
        checks,
        defects,
        "identity:anonymous_claim_justified",
        identity.get("anonymous_claim_justified") is True,
        "true",
        "identity",
    )
    return checks, defects


def check_destinations_retention_locality(
    destinations: dict[str, Any],
    retention: dict[str, Any],
    locality: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    dest_ids = {
        e.get("destination_id")
        for e in (destinations.get("entries") or [])
        if isinstance(e, dict)
    }
    for needed in (
        "local_artifacts",
        "report_artifact_store",
        "community_data_lake",
        "secrets_manager",
    ):
        add_check(
            checks,
            defects,
            f"destinations:{needed}",
            needed in dest_ids,
            needed,
            "destinations",
        )
    # lake != report store
    lake = next(
        (
            e
            for e in (destinations.get("entries") or [])
            if isinstance(e, dict) and e.get("destination_id") == "community_data_lake"
        ),
        {},
    )
    reports = next(
        (
            e
            for e in (destinations.get("entries") or [])
            if isinstance(e, dict) and e.get("destination_id") == "report_artifact_store"
        ),
        {},
    )
    add_check(
        checks,
        defects,
        "destinations:lake_not_current_previous",
        lake.get("orientation") == "append_oriented_not_current_previous",
        str(lake.get("orientation")),
        "destinations",
    )
    add_check(
        checks,
        defects,
        "destinations:reports_current_previous",
        reports.get("orientation") == "current_previous",
        str(reports.get("orientation")),
        "destinations",
    )
    ret_classes = {
        e.get("class") for e in (retention.get("entries") or []) if isinstance(e, dict)
    }
    for needed in (
        "local_assessment_reports",
        "local_eir",
        "published_assessment_reports",
        "data_lake_raw",
        "identity_prefix",
    ):
        add_check(
            checks,
            defects,
            f"retention:{needed}",
            needed in ret_classes,
            needed,
            "retention",
        )
    surfaces = {
        e.get("surface") for e in (locality.get("entries") or []) if isinstance(e, dict)
    }
    for needed in ("Assessment", "Telemetry", "AI enrichment", "Report publishing", "Insights"):
        add_check(
            checks,
            defects,
            f"source_locality:{needed}",
            needed in surfaces,
            needed,
            "source_locality",
        )
    return checks, defects


def check_ai_providers(
    ai_reg: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    entries = ai_reg.get("entries") if isinstance(ai_reg.get("entries"), list) else []
    by_name = {e.get("provider"): e for e in entries if isinstance(e, dict)}
    add_check(
        checks,
        defects,
        "ai:bedrock_live",
        (by_name.get("bedrock") or {}).get("live_proven") is True,
        "bedrock",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:openai_not_false_live",
        (by_name.get("openai") or {}).get("live_proven") is False,
        "openai",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:openrouter_not_false_live",
        (by_name.get("openrouter") or {}).get("live_proven") is False,
        "openrouter",
        "ai",
    )
    add_check(
        checks,
        defects,
        "ai:no_ai_supported",
        "no_ai" in by_name,
        "no_ai",
        "ai",
    )
    limitations.extend(
        ["openai_owner_credential_required", "openrouter_owner_credential_required"]
    )
    return checks, defects, limitations


def check_assessment_eir_publish_insights(
    assessment: dict[str, Any],
    eir: dict[str, Any],
    publishing: dict[str, Any],
    insights: dict[str, Any],
    opt_out: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    arts = {e.get("artifact") for e in (assessment.get("entries") or []) if isinstance(e, dict)}
    add_check(
        checks,
        defects,
        "assessment:manifest_not_merged",
        "assessment.json" in arts and any("lightweight" in str(x) for x in (assessment.get("important") or [])),
        "lightweight_manifest",
        "assessment",
    )
    add_check(
        checks,
        defects,
        "eir:portfolio_not_per_repo",
        eir.get("portfolio_level") is True
        and eir.get("created_for_every_single_repository_assessment") is False
        and eir.get("hidden_rescan") is False,
        "portfolio",
        "eir",
    )
    add_check(
        checks,
        defects,
        "publish:separate_from_telemetry",
        publishing.get("separate_from_telemetry") is True
        and publishing.get("telemetry_opt_in_alone_insufficient") is True
        and publishing.get("explicit_publish_confirmation") is True,
        "gates",
        "publishing",
    )
    add_check(
        checks,
        defects,
        "insights:no_raw_install_id_ui",
        insights.get("raw_installation_id_in_ui") is False
        and insights.get("not_public_community_api") is True,
        "privacy",
        "insights",
    )
    # deletion honesty
    entries = opt_out.get("entries") if isinstance(opt_out.get("entries"), list) else []
    hist = next((e for e in entries if e.get("capability") == "historical_telemetry_auto_erase_on_opt_out"), {})
    add_check(
        checks,
        defects,
        "opt_out:no_false_historical_erase",
        hist.get("implemented") is False,
        "false",
        "opt_out",
    )
    return checks, defects


def check_topics_docs_contradictions(
    topics: dict[str, Any],
    public_docs: dict[str, Any],
    contradictions: dict[str, Any],
    authority: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    topic_names = {e.get("topic") for e in (topics.get("entries") or []) if isinstance(e, dict)}
    required_topics = {
        "Telemetry Policy",
        "Privacy Policy",
        "Data Collection Policy",
        "Every Collected Field",
        "Everything Never Collected",
        "Consent Behavior",
        "Source-Locality Boundaries",
        "Public Claims vs Runtime",
    }
    missing = sorted(required_topics - topic_names)
    add_check(
        checks,
        defects,
        "topics:core_present",
        not missing,
        f"missing={missing}",
        "topics",
    )
    docs = public_docs.get("entries") if isinstance(public_docs.get("entries"), list) else []
    statuses = {e.get("status") for e in docs if isinstance(e, dict)}
    add_check(
        checks,
        defects,
        "docs:inventory_present",
        len(docs) >= 8,
        f"count={len(docs)} statuses={sorted(statuses)}",
        "docs",
    )
    limitations.append("formal_prose_publication_deferred")
    limitations.append("marketplace_content_not_published")
    contras = contradictions.get("entries") if isinstance(contradictions.get("entries"), list) else []
    add_check(
        checks,
        defects,
        "contradictions:classified",
        len(contras) >= 1
        and all(isinstance(e, dict) and e.get("classification") and e.get("disposition") for e in contras),
        f"count={len(contras)}",
        "contradictions",
    )
    add_check(
        checks,
        defects,
        "authority:runtime_over_docs",
        authority.get("runtime_over_docs") is True,
        "true",
        "authority",
    )
    for e in contras:
        if e.get("contradiction_id") == "T18-C003":
            limitations.append("codestrata_ai_favicon_stale_must_fix_before_release")
        if e.get("contradiction_id") == "T18-C002":
            limitations.append("github_v0_1_0_release_expected_gap")
    return checks, defects, limitations


def check_boundary_and_worktree(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    wf = load_json(monorepo / WORKFLOW_REGISTER_RELATIVE)
    add_check(
        checks,
        defects,
        "boundary:start_18_1",
        wf.get("start_slice_18_1") is True,
        str(wf.get("start_slice_18_1")),
        "boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:start_18_2_recorded",
        wf.get("start_slice_18_2") in (True, False),
        str(wf.get("start_slice_18_2")),
        "boundary",
        soft=True,
    )
    for pkg in FORBIDDEN_18_2_PACKAGES:
        add_check(
            checks,
            defects,
            f"boundary:absent_{Path(pkg).name}",
            not (monorepo / pkg).exists(),
            pkg,
            "boundary",
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
    limitations.append("monorepo_pre_cutover_authority")
    return checks, defects, limitations
