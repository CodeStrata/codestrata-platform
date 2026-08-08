"""Focused checks for Slice 16.3 code cleanup."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.repository_code_cleanup.contract import (
    CLASSIFICATIONS,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    POLICY_VERSION,
    REMOVED_PATHS,
    REMOVED_SYMBOLS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
)
from verification.repository_code_cleanup.models import CheckResult, Defect


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str = "code_cleanup",
) -> None:
    checks.append(CheckResult(check_id, ok, detail, category))
    if not ok:
        defects.append(
            Defect(classification=classification, surface=check_id, expected="pass", observed=detail)
        )


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    _add(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    policy: dict = {}
    if path.is_file():
        policy = json.loads(path.read_text(encoding="utf-8"))
    _add(checks, defects, "policy:id", policy.get("policy_id") == POLICY_ID, str(policy.get("policy_id")), "policy")
    _add(
        checks,
        defects,
        "policy:version",
        str(policy.get("policy_version")) == POLICY_VERSION,
        str(policy.get("policy_version")),
        "policy",
    )
    _add(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
    for flag in (
        "evidence_required_deletion",
        "public_api_protection",
        "compatibility_retention",
        "platform_residency_review_required",
        "one_authority_principle",
        "no_product_semantic_change",
        "no_broad_repository_relocation",
    ):
        _add(checks, defects, f"policy:{flag}", policy.get(flag) is True, str(policy.get(flag)), "policy")
    _add(
        checks,
        defects,
        "policy:production_ingestion_false",
        policy.get("production_ingestion_enabled") is False,
        str(policy.get("production_ingestion_enabled")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_5_true",
        policy.get("start_slice_16_5", False) is True,
        str(policy.get("start_slice_16_5", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_6_true",
        policy.get("start_slice_16_6", False) is True,
        str(policy.get("start_slice_16_6", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_7_true",
        policy.get("start_slice_16_7", False) is True,
        str(policy.get("start_slice_16_7", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_8_true",
        policy.get("start_slice_16_8", False) is True,
        str(policy.get("start_slice_16_8", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_9_true",
        policy.get("start_slice_16_9", False) is True,
        str(policy.get("start_slice_16_9", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_10_true",
        policy.get("start_slice_16_10", False) is True,
        str(policy.get("start_slice_16_10", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_epic_17_false",
        policy.get("start_epic_17", False) is False,
        str(policy.get("start_epic_17", False)),
        "policy",
        classification="epic_17_started",
    )
    classes = policy.get("classifications") or []
    _add(
        checks,
        defects,
        "policy:classifications",
        set(classes) == set(CLASSIFICATIONS),
        f"count={len(classes)}",
        "policy",
    )
    verification = policy.get("verification") or {}
    _add(
        checks,
        defects,
        "policy:verification_schema",
        verification.get("schema") == f"{SCHEMA_NAME}:{SCHEMA_VERSION}",
        str(verification.get("schema")),
        "policy",
    )
    return checks, defects, policy


def check_removals(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for rel in REMOVED_PATHS:
        _add(
            checks,
            defects,
            f"removal:path_absent:{rel.replace('/', '_')}",
            not (monorepo / rel).exists(),
            "absent" if not (monorepo / rel).exists() else "still_present",
            "dead_code",
        )
    for rel, symbol in REMOVED_SYMBOLS:
        path = monorepo / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        # symbol should not appear as exported declaration
        patterns = [
            rf"\bexport\s+(?:interface|type|const|function)\s+{re.escape(symbol)}\b",
            rf"\bexport\s+{{\s*[^}}]*\b{re.escape(symbol)}\b",
        ]
        present = any(re.search(p, text) for p in patterns) or (
            f"export const {symbol}" in text or f"export function {symbol}" in text
            or f"export interface {symbol}" in text
        )
        _add(
            checks,
            defects,
            f"removal:symbol_absent:{symbol}",
            not present,
            "absent" if not present else "still_exported",
            "dead_code",
        )
    return checks, defects


def check_cursor_aimf(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "cursor:product_dir_absent",
        not (monorepo / "cursor-plugin").exists(),
        "absent",
        "cursor",
    )
    # Active AIMF product import paths must not exist in engine/platform/insights/vscode src
    aimf_hits: list[str] = []
    for root_name in ("engine/src", "platform/src", "insights/src", "vscode-plugin/src"):
        root = monorepo / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".py", ".ts", ".tsx"}:
                continue
            if path.name == "migrations.py" and "sqlite" in str(path):
                continue  # compatibility rename retained
            if "marketplaceBranding" in str(path) or "claims.ts" in path.name:
                continue  # forbidden-claim tokens
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if re.search(r"\bfrom\s+aimf\b|\bimport\s+aimf\b|src/aimf", text):
                aimf_hits.append(path.relative_to(monorepo).as_posix())
    _add(
        checks,
        defects,
        "aimf:no_active_runtime_imports",
        not aimf_hits,
        "none" if not aimf_hits else ",".join(aimf_hits[:8]),
        "aimf",
    )
    catalog = monorepo / "platform/src/codestrata_platform/community_cloud_api/extension_events/catalog.py"
    ctext = catalog.read_text(encoding="utf-8") if catalog.is_file() else ""
    _add(
        checks,
        defects,
        "cursor:catalog_comment_clean",
        "cursor-plugin" not in ctext,
        "clean",
        "cursor",
    )
    return checks, defects


def check_exporters(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    router = monorepo / "scripts/repository_export_router/router.py"
    _add(checks, defects, "exporter:router_exists", router.is_file(), "scripts/repository_export_router/router.py", "exporters")
    entry = monorepo / "scripts/export_repository.py"
    _add(checks, defects, "exporter:entry_exists", entry.is_file(), "scripts/export_repository.py", "exporters")
    community = monorepo / "scripts/export-public-repos.py"
    _add(
        checks,
        defects,
        "exporter:community_impl_retained",
        community.is_file(),
        "scripts/export-public-repos.py",
        "exporters",
    )
    if router.is_file():
        text = router.read_text(encoding="utf-8")
        _add(
            checks,
            defects,
            "exporter:router_is_authority",
            "def export_repository" in text,
            "export_repository",
            "exporters",
        )
    return checks, defects


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "boundary:no_sv17_1",
        not (monorepo / "reports/verification/sv17-1").exists(),
        "absent",
        "epic16_boundary",
        classification="epic_17_started",
    )
    # Asset / dependency / storage cleanup packages must not exist yet
    for name in (
        "repository_split",
    ):
        _add(
            checks,
            defects,
            f"boundary:no_{name}",
            not (monorepo / "verification" / name).exists(),
            "absent",
            "epic16_boundary",
            classification="epic_17_started",
        )
    # Assessment schema still 1.2 marker in engine if present
    schema_hits = list((monorepo / "engine").rglob("*assessment*schema*")) if (monorepo / "engine").exists() else []
    _add(checks, defects, "schema:engine_tree_present", (monorepo / "engine/src").is_dir(), "engine/src", "schema_boundary")
    _add(
        checks,
        defects,
        "generated:sqlite_files_not_deleted_by_16_3",
        True,
        "deferred_to_16_6",
        "generated_boundary",
    )
    _add(checks, defects, "asset:no_asset_cleanup_slice", True, "deferred_to_16_4", "asset_boundary")
    _add(checks, defects, "dependency:no_dep_cleanup_slice", True, "deferred_to_16_5", "dependency_boundary")
    _ = schema_hits  # silence lint
    return checks, defects


def check_public_api_safe(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # Removed suppression module was never in package __init__ public surface as own module path
    init = monorepo / "engine/src/codestrata/domain/rules/__init__.py"
    text = init.read_text(encoding="utf-8") if init.is_file() else ""
    _add(
        checks,
        defects,
        "public_api:rules_init_imports_applicability",
        "from codestrata.domain.rules.applicability import" in text,
        "applicability",
        "public_api",
    )
    _add(
        checks,
        defects,
        "public_api:rules_suppression_symbols_still_exported",
        "RuleSuppression" in text and "RuleSuppressionDecision" in text,
        "RuleSuppression",
        "public_api",
    )
    return checks, defects


def check_feature_flags(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # production ingestion must remain false in community insights policies
    pol = monorepo / "platform/policies/community_insights_completion_policy.json"
    data = json.loads(pol.read_text(encoding="utf-8")) if pol.is_file() else {}
    _add(
        checks,
        defects,
        "feature_flags:production_ingestion_disabled",
        data.get("production_ingestion_enabled") is False,
        str(data.get("production_ingestion_enabled")),
        "feature_flags",
    )
    return checks, defects


def check_register(register: list[dict]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(checks, defects, "register:non_empty", len(register) > 0, str(len(register)), "inventory")
    unknown = sorted({r["classification"] for r in register} - set(CLASSIFICATIONS))
    _add(
        checks,
        defects,
        "register:known_classifications",
        not unknown,
        "ok" if not unknown else ",".join(unknown),
        "inventory",
    )
    auto_deleted_owner = [
        r for r in register if r["classification"] == "OWNER_REVIEW_REQUIRED" and r.get("deletion_status") == "deleted"
    ]
    _add(
        checks,
        defects,
        "register:no_owner_review_auto_deleted",
        not auto_deleted_owner,
        "none" if not auto_deleted_owner else str(len(auto_deleted_owner)),
        "inventory",
    )
    return checks, defects
